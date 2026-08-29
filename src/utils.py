from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


GOODS = ("crab", "octopus", "fish")
POSITION_KEYS = ("1", "2", "3")


@dataclass(frozen=True)
class FishingTrialSpec:
    session_trial: int
    goal_index: int
    goal_trial: int
    goal_started: bool
    net_size: float
    accumulated: float
    current_good: str | None
    offers: dict[str, float]
    display_order: tuple[str, str, str]
    points: int
    trials_remaining: int
    condition: str = "decision_trial"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __hash__(self) -> int:
        """Support PsyFlow's condition-distribution audit without mutating the plan."""

        return hash(
            (
                self.session_trial,
                self.goal_index,
                self.goal_trial,
                self.goal_started,
                self.net_size,
                self.accumulated,
                self.current_good,
                tuple((good, self.offers[good]) for good in GOODS),
                self.display_order,
                self.points,
                self.trials_remaining,
                self.condition,
            )
        )


class FishingNetController:
    """Generate cited offer trajectories and update choice-dependent net state."""

    _ALLOWED = {
        "seed",
        "schedule_mode",
        "net_size_min",
        "net_size_max",
        "initial_offer_mean",
        "initial_offer_sd",
        "walk_sd",
        "jump_up_probability",
        "jump_down_probability",
        "jump_min",
        "jump_max",
        "feasible_min_trials",
        "feasible_max_trials",
        "scripted_trials",
    }

    def __init__(
        self,
        *,
        seed: int = 110110,
        schedule_mode: str = "stochastic",
        net_size_min: int = 12,
        net_size_max: int = 72,
        initial_offer_mean: float = 6.0,
        initial_offer_sd: float = 1.0,
        walk_sd: float = math.sqrt(0.8),
        jump_up_probability: float = 0.1,
        jump_down_probability: float = 0.1,
        jump_min: float = 3.0,
        jump_max: float = 9.0,
        feasible_min_trials: int = 4,
        feasible_max_trials: int = 14,
        scripted_trials: Iterable[Mapping[str, Any]] | None = None,
    ) -> None:
        if schedule_mode not in {"stochastic", "scripted"}:
            raise ValueError(f"Unsupported schedule_mode: {schedule_mode}")
        if net_size_min > net_size_max:
            raise ValueError("net_size_min must not exceed net_size_max")
        if jump_up_probability < 0 or jump_down_probability < 0:
            raise ValueError("jump probabilities must be non-negative")
        if jump_up_probability + jump_down_probability > 1:
            raise ValueError("jump probabilities must sum to at most one")

        self.seed = int(seed)
        self.schedule_mode = schedule_mode
        self.net_size_min = int(net_size_min)
        self.net_size_max = int(net_size_max)
        self.initial_offer_mean = float(initial_offer_mean)
        self.initial_offer_sd = float(initial_offer_sd)
        self.walk_sd = float(walk_sd)
        self.jump_up_probability = float(jump_up_probability)
        self.jump_down_probability = float(jump_down_probability)
        self.jump_min = float(jump_min)
        self.jump_max = float(jump_max)
        self.feasible_min_trials = int(feasible_min_trials)
        self.feasible_max_trials = int(feasible_max_trials)
        self.scripted_trials = [dict(item) for item in (scripted_trials or [])]
        self._rng = random.Random(self.seed)

        self.goal_index = 0
        self.goal_trial = 0
        self.net_size = 0.0
        self.accumulated = 0.0
        self.current_good: str | None = None
        self.offers = {good: 0.0 for good in GOODS}
        self.anchors = {good: 0.0 for good in GOODS}
        self.points = 0
        self._needs_new_goal = True
        self._pending_session_trial: int | None = None

    @classmethod
    def from_dict(cls, config: Mapping[str, Any] | None) -> "FishingNetController":
        raw = dict(config or {})
        extra = sorted(set(raw) - cls._ALLOWED)
        if extra:
            raise ValueError(f"Unsupported FishingNetController keys: {extra}")
        return cls(**raw)

    def _sample_goal(self) -> tuple[float, dict[str, float]]:
        """Sample a non-trivial initial net/offer combination from cited ranges."""

        last_size = float(self.net_size_min)
        last_offers = {good: self.initial_offer_mean for good in GOODS}
        for _ in range(500):
            size = float(self._rng.randint(self.net_size_min, self.net_size_max))
            offers = {
                good: float(self._rng.gauss(self.initial_offer_mean, self.initial_offer_sd))
                for good in GOODS
            }
            steps = math.ceil(size / max(0.1, max(offers.values())))
            last_size, last_offers = size, offers
            if self.feasible_min_trials <= steps <= self.feasible_max_trials:
                return size, offers
        return last_size, last_offers

    def _start_goal(self, *, net_size_override: float | None = None) -> None:
        self.goal_index += 1
        self.goal_trial = 0
        self.accumulated = 0.0
        self.current_good = None
        sampled_size, sampled_offers = self._sample_goal()
        self.net_size = float(net_size_override) if net_size_override is not None else sampled_size
        self.offers = dict(sampled_offers)
        self.anchors = dict(sampled_offers)
        self._needs_new_goal = False

    def _evolve_offers(self) -> None:
        for good in GOODS:
            jump_draw = self._rng.random()
            if jump_draw < self.jump_up_probability:
                self.anchors[good] += self._rng.uniform(self.jump_min, self.jump_max)
                self.offers[good] = self.anchors[good]
            elif jump_draw < self.jump_up_probability + self.jump_down_probability:
                self.anchors[good] -= self._rng.uniform(self.jump_min, self.jump_max)
                self.offers[good] = self.anchors[good]
            else:
                self.offers[good] += self._rng.gauss(0.0, self.walk_sd)

    @staticmethod
    def _validated_order(value: Iterable[str]) -> tuple[str, str, str]:
        order = tuple(str(item) for item in value)
        if len(order) != 3 or set(order) != set(GOODS):
            raise ValueError(f"display_order must contain each good once, got {order}")
        return order  # type: ignore[return-value]

    def next_trial(self, *, session_trial: int, total_trials: int) -> FishingTrialSpec:
        if self._pending_session_trial is not None:
            raise RuntimeError("Previous FishingTrialSpec has not been resolved")

        scripted: dict[str, Any] | None = None
        if self.schedule_mode == "scripted":
            if session_trial >= len(self.scripted_trials):
                raise ValueError("scripted_trials is shorter than task.total_trials")
            scripted = self.scripted_trials[session_trial]

        goal_started = self._needs_new_goal
        if goal_started:
            override = scripted.get("net_size") if scripted else None
            self._start_goal(net_size_override=float(override) if override is not None else None)
        elif self.schedule_mode == "stochastic":
            self._evolve_offers()

        if scripted is not None:
            offers = {good: float(scripted["offers"][good]) for good in GOODS}
            self.offers = offers
            order = self._validated_order(scripted["display_order"])
        else:
            order_list = list(GOODS)
            self._rng.shuffle(order_list)
            order = self._validated_order(order_list)

        self._pending_session_trial = int(session_trial)
        return FishingTrialSpec(
            session_trial=int(session_trial),
            goal_index=int(self.goal_index),
            goal_trial=int(self.goal_trial),
            goal_started=bool(goal_started),
            net_size=float(self.net_size),
            accumulated=float(self.accumulated),
            current_good=self.current_good,
            offers={good: float(self.offers[good]) for good in GOODS},
            display_order=order,
            points=int(self.points),
            trials_remaining=max(0, int(total_trials) - int(session_trial)),
        )

    def apply_choice(self, plan: FishingTrialSpec, response_key: str | None) -> dict[str, Any]:
        if self._pending_session_trial != plan.session_trial:
            raise RuntimeError("FishingTrialSpec does not match pending controller state")

        previous_good = self.current_good
        previous_accumulated = float(self.accumulated)
        chosen_good: str | None = None
        selected_offer: float | None = None
        abandoned_quantity = 0.0

        if response_key in POSITION_KEYS:
            chosen_good = plan.display_order[POSITION_KEYS.index(str(response_key))]
            selected_offer = float(plan.offers[chosen_good])
            if previous_good is None:
                choice_type = "initial"
                new_accumulated = max(0.0, selected_offer)
            elif chosen_good == previous_good:
                choice_type = "persistence"
                new_accumulated = max(0.0, previous_accumulated + selected_offer)
            else:
                choice_type = "abandonment"
                abandoned_quantity = previous_accumulated
                new_accumulated = max(0.0, selected_offer)
            self.current_good = chosen_good
            self.accumulated = new_accumulated
        else:
            choice_type = "timeout"

        self.goal_trial += 1
        completed = bool(chosen_good is not None and self.accumulated >= self.net_size)
        if completed:
            self.points += 1
            self._needs_new_goal = True

        self._pending_session_trial = None
        return {
            "choice_type": choice_type,
            "chosen_good": chosen_good,
            "selected_offer": selected_offer,
            "previous_good": previous_good,
            "previous_accumulated": previous_accumulated,
            "abandoned_quantity": abandoned_quantity,
            "accumulated_after": float(self.accumulated),
            "goal_progress_before": previous_accumulated / plan.net_size if plan.net_size else 0.0,
            "goal_progress_after": min(1.0, self.accumulated / plan.net_size) if plan.net_size else 0.0,
            "goal_completed": completed,
            "points_after": int(self.points),
        }


def _good_icon(stim_bank, good: str, *, pos: tuple[float, float], size: tuple[float, float]):
    if good not in GOODS:
        raise ValueError(f"Unsupported good: {good}")
    return stim_bank.rebuild(f"{good}_icon", update_cache=False, pos=pos, size=size)


def build_goal_intro_stimuli(stim_bank, settings, plan: FishingTrialSpec) -> list[Any]:
    stimuli = [
        stim_bank.get("ocean_panel"),
        stim_bank.get("goal_intro_text"),
        stim_bank.get("net_label"),
        stim_bank.get("net_track"),
        stim_bank.get_and_format(
            "status_text",
            points=plan.points,
            remaining=plan.trials_remaining,
            total=int(settings.total_trials),
        ),
    ]
    return stimuli


def build_offer_stimuli(
    stim_bank,
    settings,
    plan: FishingTrialSpec,
    *,
    show_question: bool,
    accumulated: float | None = None,
    current_good: str | None = None,
    completed: bool = False,
    points: int | None = None,
) -> list[Any]:
    row_y = [float(value) for value in settings.option_row_y]
    if len(row_y) != 3:
        raise ValueError("task.option_row_y must contain three values")
    zero_x = float(settings.offer_zero_x)
    px_per_unit = float(settings.offer_pixels_per_unit)
    max_width = float(settings.offer_max_width)
    net_left = float(settings.net_left_x)
    net_width = float(settings.net_width)
    net_y = float(settings.net_y)

    shown_accumulated = float(plan.accumulated if accumulated is None else accumulated)
    shown_good = plan.current_good if current_good is None else current_good
    shown_points = plan.points if points is None else int(points)

    stimuli: list[Any] = [
        stim_bank.get("ocean_panel"),
        stim_bank.get_and_format(
            "status_text",
            points=shown_points,
            remaining=plan.trials_remaining,
            total=int(settings.total_trials),
        ),
        stim_bank.get("net_label"),
        stim_bank.rebuild("net_track", update_cache=False, pos=(net_left + net_width / 2.0, net_y), width=net_width),
    ]

    for position, good in enumerate(plan.display_order):
        y = row_y[position]
        stimuli.append(_good_icon(stim_bank, good, pos=(float(settings.creature_x), y), size=(64, 64)))
        stimuli.append(
            stim_bank.rebuild(
                "offer_track",
                update_cache=False,
                pos=(zero_x + max_width / 2.0, y),
                width=max_width,
            )
        )
        offer = float(plan.offers[good])
        width = min(max_width, max(2.0, abs(offer) * px_per_unit))
        direction = 1.0 if offer >= 0 else -1.0
        bar_name = "offer_positive_bar" if offer >= 0 else "offer_negative_bar"
        stimuli.append(
            stim_bank.rebuild(
                bar_name,
                update_cache=False,
                pos=(zero_x + direction * width / 2.0, y),
                width=width,
            )
        )

    fill_ratio = min(1.0, max(0.0, shown_accumulated / plan.net_size)) if plan.net_size else 0.0
    if fill_ratio > 0:
        fill_width = max(2.0, net_width * fill_ratio)
        stimuli.append(
            stim_bank.rebuild(
                "net_fill",
                update_cache=False,
                pos=(net_left + fill_width / 2.0, net_y),
                width=fill_width,
            )
        )
    if shown_good in GOODS:
        stimuli.append(
            _good_icon(
                stim_bank,
                str(shown_good),
                pos=(float(settings.net_icon_x), net_y),
                size=(58, 58),
            )
        )
    else:
        stimuli.append(stim_bank.get("net_empty_text"))

    if show_question:
        stimuli.append(stim_bank.get("choice_prompt"))
    if completed:
        stimuli.append(stim_bank.get_and_format("complete_text", points=shown_points))
    return stimuli


def summarize_trials(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    records = [dict(row) for row in rows]
    decided = [row for row in records if row.get("choice_type") in {"initial", "persistence", "abandonment"}]
    revisits = [row for row in records if row.get("choice_type") in {"persistence", "abandonment"}]
    abandonments = [row for row in records if row.get("choice_type") == "abandonment"]
    completions = [row for row in records if bool(row.get("goal_completed"))]
    completed_lengths = [int(row.get("goal_trial", 0)) + 1 for row in completions]
    return {
        "total_trials": len(records),
        "decided_trials": len(decided),
        "completed_nets": len(completions),
        "persistence_count": sum(row.get("choice_type") == "persistence" for row in records),
        "abandonment_count": len(abandonments),
        "abandonment_rate": len(abandonments) / len(revisits) if revisits else None,
        "mean_abandoned_quantity": (
            sum(float(row.get("abandoned_quantity", 0.0)) for row in abandonments) / len(abandonments)
            if abandonments
            else None
        ),
        "mean_goal_progress_at_abandonment": (
            sum(float(row.get("goal_progress_before", 0.0)) for row in abandonments) / len(abandonments)
            if abandonments
            else None
        ),
        "mean_trials_per_completed_net": (
            sum(completed_lengths) / len(completed_lengths) if completed_lengths else None
        ),
        "timeout_count": sum(row.get("choice_type") == "timeout" for row in records),
    }
