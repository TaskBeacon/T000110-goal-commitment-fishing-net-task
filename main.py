from __future__ import annotations

import json
from contextlib import nullcontext
from functools import partial
from pathlib import Path

import pandas as pd
from psychopy import core
from psyflow import (
    BlockUnit,
    StimBank,
    StimUnit,
    SubInfo,
    TaskRunOptions,
    TaskSettings,
    context_from_config,
    initialize_exp,
    initialize_triggers,
    load_config,
    parse_task_run_options,
    runtime_context,
)

from src import FishingNetController, run_trial, summarize_trials


MODES = ("human", "qa", "sim")
DEFAULT_CONFIG_BY_MODE = {
    "human": "config/config.yaml",
    "qa": "config/config_qa.yaml",
    "sim": "config/config_scripted_sim.yaml",
}


def run(options: TaskRunOptions) -> None:
    """Run the decision-only Goal Commitment / Fishing-Net Task."""

    task_root = Path(__file__).resolve().parent
    cfg = load_config(str(options.config_path))
    output_dir: Path | None = None
    runtime_scope = nullcontext()
    runtime_ctx = None
    if options.mode in ("qa", "sim"):
        runtime_ctx = context_from_config(task_dir=task_root, config=cfg, mode=options.mode)
        output_dir = runtime_ctx.output_dir
        runtime_scope = runtime_context(runtime_ctx)

    with runtime_scope:
        if options.mode == "qa":
            subject_data = {"subject_id": "qa110"}
        elif options.mode == "sim":
            participant_id = "sim110"
            if runtime_ctx is not None and runtime_ctx.session is not None:
                participant_id = str(runtime_ctx.session.participant_id or participant_id)
            subject_data = {"subject_id": participant_id}
        else:
            subject_data = SubInfo(cfg["subform_config"]).collect()

        settings = TaskSettings.from_dict(cfg["task_config"])
        settings.add_subinfo(subject_data)
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.save_path = str(output_dir)
            prefix = "qa" if options.mode == "qa" else "sim"
            settings.res_file = str(output_dir / f"{prefix}_trace.csv")
            settings.log_file = str(output_dir / f"{prefix}_psychopy.log")
            settings.json_file = str(output_dir / f"{prefix}_settings.json")

        settings.triggers = cfg["trigger_config"]
        trigger_runtime = (
            initialize_triggers(mock=True)
            if options.mode in ("qa", "sim")
            else initialize_triggers(cfg)
        )
        win, kb = initialize_exp(settings)
        stim_bank = StimBank(win, cfg["stim_config"]).preload_all()
        controller = FishingNetController.from_dict(cfg.get("controller_config", {}))
        settings.save_to_json()

        trigger_runtime.send(settings.triggers.get("exp_onset"))
        StimUnit("instruction", win, kb, runtime=trigger_runtime).add_stim(
            stim_bank.get("instruction_text")
        ).wait_and_continue(keys=[str(settings.continue_key)])

        all_rows: list[dict] = []
        for session_trial in range(int(settings.total_trials)):
            plan = controller.next_trial(
                session_trial=session_trial,
                total_trials=int(settings.total_trials),
            )
            block_id = f"net_{plan.goal_index:03d}"
            trial_block = (
                BlockUnit(
                    block_id=block_id,
                    block_idx=plan.goal_index - 1,
                    settings=settings,
                    window=win,
                    keyboard=kb,
                    seed=int(settings.overall_seed) + session_trial,
                )
                .add_condition([plan])
                .run_trial(
                    partial(
                        run_trial,
                        stim_bank=stim_bank,
                        trigger_runtime=trigger_runtime,
                        controller=controller,
                        block_id=block_id,
                        block_idx=plan.goal_index - 1,
                    )
                )
            )
            rows = trial_block.get_all_data()
            if len(rows) != 1:
                raise RuntimeError(f"Expected one row for session trial {session_trial}, got {len(rows)}")
            row = dict(rows[0])
            row["condition"] = "decision_trial"
            row["trial_index"] = session_trial
            all_rows.append(row)

        result_path = Path(settings.res_file)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(all_rows).to_csv(result_path, index=False)
        summary = summarize_trials(all_rows)
        result_path.with_name(f"{result_path.stem}_fishing_net_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        trigger_runtime.send(settings.triggers.get("good_bye_onset"))
        StimUnit("good_bye", win, kb, runtime=trigger_runtime).add_stim(
            stim_bank.get_and_format(
                "good_bye_text",
                points=summary["completed_nets"],
                trials=summary["total_trials"],
            )
        ).wait_and_continue(keys=[str(settings.continue_key)])
        trigger_runtime.send(settings.triggers.get("exp_end"))
        trigger_runtime.close()
        win.close()
        core.quit()


def main() -> None:
    run(
        parse_task_run_options(
            task_root=Path(__file__).resolve().parent,
            description="Run the Goal Commitment / Fishing-Net Task.",
            default_config_by_mode=DEFAULT_CONFIG_BY_MODE,
            modes=MODES,
        )
    )


if __name__ == "__main__":
    main()

