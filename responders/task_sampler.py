from __future__ import annotations

import random as _py_random
from dataclasses import dataclass
from typing import Any

from psyflow.sim.contracts import Action, Feedback, Observation, SessionInfo


@dataclass
class TaskSamplerResponder:
    response_rate: float = 0.98
    rt_mean_s: float = 0.35
    rt_sd_s: float = 0.08

    def __post_init__(self) -> None:
        self._rng: Any = None
        self.response_rate = min(1.0, max(0.0, float(self.response_rate)))

    def start_session(self, session: SessionInfo, rng: Any) -> None:
        self._rng = rng

    def on_feedback(self, fb: Feedback) -> None:
        return None

    def end_session(self) -> None:
        self._rng = None

    def _random(self) -> float:
        return float(self._rng.random()) if self._rng is not None else float(_py_random.random())

    def _normal(self) -> float:
        if self._rng is not None and hasattr(self._rng, "normal"):
            return float(self._rng.normal(self.rt_mean_s, self.rt_sd_s))
        if self._rng is not None and hasattr(self._rng, "gauss"):
            return float(self._rng.gauss(self.rt_mean_s, self.rt_sd_s))
        return float(_py_random.gauss(self.rt_mean_s, self.rt_sd_s))

    def act(self, obs: Observation) -> Action:
        valid_keys = list(obs.valid_keys or [])
        if not valid_keys:
            return Action(key=None, rt_s=None, meta={"source": "fishing_net_sampler", "reason": "no_valid_keys"})
        if obs.phase != "choice":
            return Action(key=valid_keys[0], rt_s=max(0.02, self._normal()), meta={"source": "fishing_net_sampler"})
        if self._random() > self.response_rate:
            return Action(key=None, rt_s=None, meta={"source": "fishing_net_sampler", "outcome": "timeout"})

        features = dict(obs.stim_features or {})
        order = [str(item) for item in features.get("display_order", [])]
        offers = {str(key): float(value) for key, value in dict(features.get("offers", {})).items()}
        current_good = features.get("current_good")
        accumulated = float(features.get("accumulated", 0.0))
        if len(order) != 3 or not offers:
            chosen_key = valid_keys[0]
        else:
            values = {
                good: offers[good] + (accumulated if good == current_good else 0.0)
                for good in order
            }
            best_good = max(order, key=lambda good: values[good])
            chosen_key = str(order.index(best_good) + 1)
            if chosen_key not in valid_keys:
                chosen_key = valid_keys[0]
        return Action(
            key=chosen_key,
            rt_s=max(0.02, self._normal()),
            meta={"source": "fishing_net_sampler", "strategy": "myopic"},
        )

