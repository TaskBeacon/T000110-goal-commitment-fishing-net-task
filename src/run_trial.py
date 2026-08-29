from __future__ import annotations

from typing import Any

from psyflow import StimUnit, next_trial_id, set_trial_context

from .utils import (
    FishingNetController,
    FishingTrialSpec,
    POSITION_KEYS,
    build_goal_intro_stimuli,
    build_offer_stimuli,
)


def _add_all(unit: StimUnit, stimuli: list[Any]) -> StimUnit:
    for stimulus in stimuli:
        unit.add_stim(stimulus)
    return unit


def run_trial(
    win,
    kb,
    settings,
    condition,
    stim_bank,
    trigger_runtime,
    controller: FishingNetController,
    block_id=None,
    block_idx=None,
):
    """Run one cited preview-choice-update Fishing-Net decision."""

    if not isinstance(condition, FishingTrialSpec):
        raise TypeError(f"Expected FishingTrialSpec, got {type(condition).__name__}")
    plan = condition
    trial_id = int(next_trial_id())
    block_id_value = str(block_id or f"net_{plan.goal_index:03d}")
    block_idx_value = int(block_idx if block_idx is not None else plan.goal_index - 1)
    condition_id = f"net_{plan.goal_index:03d}_trial_{plan.goal_trial:02d}"

    factors = {
        **plan.to_dict(),
        "stage": "planned",
        "block_idx": block_idx_value,
    }
    trial_data: dict[str, Any] = {
        "trial_id": trial_id,
        "block_id": block_id_value,
        "block_idx": block_idx_value,
        "condition": "decision_trial",
        "condition_id": condition_id,
        **plan.to_dict(),
    }

    if plan.goal_started:
        trigger_runtime.send(settings.triggers.get("block_onset"))
        intro = _add_all(
            StimUnit("goal_intro", win, kb, runtime=trigger_runtime),
            build_goal_intro_stimuli(stim_bank, settings, plan),
        )
        set_trial_context(
            intro,
            trial_id=trial_id,
            phase="goal_intro",
            deadline_s=None,
            valid_keys=[str(settings.continue_key)],
            block_id=block_id_value,
            condition_id=condition_id,
            task_factors={**factors, "stage": "goal_intro"},
            stim_id="ocean_panel+goal_intro_text+net_track+status_text",
            stim_features={"net_size": plan.net_size, "goal_index": plan.goal_index},
        )
        trigger_runtime.send(settings.triggers.get("goal_intro_onset"))
        intro.wait_and_continue(keys=[str(settings.continue_key)]).to_dict(trial_data)

    preview = _add_all(
        StimUnit("offer_preview", win, kb, runtime=trigger_runtime),
        build_offer_stimuli(stim_bank, settings, plan, show_question=False),
    )
    set_trial_context(
        preview,
        trial_id=trial_id,
        phase="offer_preview",
        deadline_s=float(settings.offer_preview_s),
        valid_keys=[],
        block_id=block_id_value,
        condition_id=condition_id,
        task_factors={**factors, "stage": "offer_preview"},
        stim_id="seafood_offers+current_net+status_text",
        stim_features=plan.to_dict(),
    )
    preview.show(
        duration=float(settings.offer_preview_s),
        onset_trigger=settings.triggers.get("offer_preview_onset"),
    ).to_dict(trial_data)

    choice = _add_all(
        StimUnit("choice", win, kb, runtime=trigger_runtime),
        build_offer_stimuli(stim_bank, settings, plan, show_question=True),
    )
    valid_keys = list(POSITION_KEYS)
    set_trial_context(
        choice,
        trial_id=trial_id,
        phase="choice",
        deadline_s=float(settings.choice_window_s),
        valid_keys=valid_keys,
        block_id=block_id_value,
        condition_id=condition_id,
        task_factors={**factors, "stage": "choice"},
        stim_id="seafood_offers+current_net+choice_prompt+status_text",
        stim_features=plan.to_dict(),
    )
    choice.capture_response(
        keys=valid_keys,
        duration=float(settings.choice_window_s),
        onset_trigger=settings.triggers.get("choice_onset"),
        response_trigger={
            "1": settings.triggers.get("choice_top"),
            "2": settings.triggers.get("choice_middle"),
            "3": settings.triggers.get("choice_bottom"),
        },
        timeout_trigger=settings.triggers.get("choice_timeout"),
    ).to_dict(trial_data)

    response_key = str(choice.get_state("response", "") or "")
    response_rt = choice.get_state("rt", None)
    outcome = controller.apply_choice(plan, response_key or None)
    trial_data.update(outcome)
    trial_data.update(
        {
            "response_key": response_key,
            "response_rt": float(response_rt) if isinstance(response_rt, (int, float)) else None,
            "timed_out": not bool(response_key),
            "display_order": list(plan.display_order),
            "offers": dict(plan.offers),
        }
    )

    update = _add_all(
        StimUnit("net_update", win, kb, runtime=trigger_runtime),
        build_offer_stimuli(
            stim_bank,
            settings,
            plan,
            show_question=False,
            accumulated=float(outcome["accumulated_after"]),
            current_good=outcome["chosen_good"] or plan.current_good,
            completed=bool(outcome["goal_completed"]),
            points=int(outcome["points_after"]),
        ),
    )
    update_features = {**plan.to_dict(), **outcome}
    set_trial_context(
        update,
        trial_id=trial_id,
        phase="net_update",
        deadline_s=float(settings.net_update_s),
        valid_keys=[],
        block_id=block_id_value,
        condition_id=condition_id,
        task_factors={**factors, **outcome, "stage": "net_update"},
        stim_id="seafood_offers+updated_net+status_text",
        stim_features=update_features,
    )
    update.show(
        duration=float(settings.net_update_s),
        onset_trigger=settings.triggers.get(
            "goal_complete_onset" if outcome["goal_completed"] else "net_update_onset"
        ),
    ).to_dict(trial_data)
    if outcome["goal_completed"]:
        trigger_runtime.send(settings.triggers.get("block_end"))

    return trial_data
