# Task Logic Audit

## 1. Paradigm Intent

- Primary question: how people balance commitment to an accumulated goal against abandoning sunk progress when alternative options become more valuable.
- Primary construct: goal commitment / persistence versus flexible goal abandonment.
- Primary evidence: Holton et al. (2024), especially Fig. 1, Extended Data Fig. 1, and the Methods sections "Primary decision task" and "Schedule generation procedure".
- The implementation is the decision-only behavioral baseline. It does not include the paper's optional interleaved spatial-attention probe or MRI acquisition layer.

## 2. Block/Trial Workflow

Conceptual blocks are individual fishing nets. The session has a fixed trial budget, while each net ends when it is filled.

1. `goal_intro` (first trial of a new net only): show the empty target bar and wait for the participant to start.
2. `offer_preview`: show crab, octopus, and fish offers for 2,000 ms without accepting a response.
3. `choice`: keep the same offers visible, add the decision prompt, and accept a top/middle/bottom choice.
4. `net_update`: show the chosen offer applied to the current net for 2,400 ms.
5. If the net is full, award one point and start a new net on the next session trial; otherwise update all three offers and continue the same net.
6. End after the configured fixed number of session trials, even if the final net is incomplete.

The source used 300 decision-only MRI trials and 100 post-scan trials. This behavioral package uses 100 decision trials to preserve the paper's behavioral-session budget while omitting the separate spatial-memory probe.

## 3. Condition Semantics

- `decision_trial`: the only label-level condition. Its core factors are carried in a `FishingTrialSpec`: net index, within-net trial index, net size, accumulated quantity, current goal good, three current offers, randomized display order, points, and trials remaining.
- `initial`: the first selection for an empty net establishes the current goal.
- `persistence`: selecting the same good preserves accumulated progress and adds the selected offer.
- `abandonment`: selecting a different good forfeits all old progress, changes the goal good, and begins the new accumulation with the selected offer.
- `timeout`: the inferred safety deadline was reached; no good is selected and net progress does not change.
- Positive offers add quantity and use green bars. Negative offers subtract quantity and use red bars, with the net floor clamped at zero.

## 4. Response and Scoring Rules

- Keys `1`, `2`, and `3` select the top, middle, and bottom option respectively. This keyboard mapping is an inferred behavioral adaptation of the paper's three-button top/middle/bottom mapping.
- The paper used free response. The implementation adds a 30 s fail-safe timeout for unattended runs; this is not an experimental deadline.
- Every completed net awards one point. A completed net resets goal identity, progress, target size, and offer trajectories before the next session trial.
- Primary derived measures are abandonment count/rate, persistence count/rate, abandoned quantity, goal progress at abandonment, completed nets, and trials per completed net.

## 5. Stimulus Layout Plan

- Canvas: 1280 x 720 px, black underwater panel with a restrained gold border.
- Top-right status: completed nets above remaining trials, matching Extended Data Fig. 1a.
- Offer rows: three vertically separated rows at y = 155, 25, and -105 px. Each row contains one sea-creature icon and a horizontal offer track with a shared zero point. Positive bars extend right in green; negative bars extend left in red.
- The three goods are randomly reassigned to the three row positions every trial to prevent motor perseveration.
- Net display: a separate horizontal bar near the bottom. A blue fill shows accumulated quantity relative to net size; the current goal icon appears to its left. Empty space remains light grey.
- Choice prompt: a large question mark appears only after the 2 s offer-preview period.
- Completion update: the full net remains visible and a concise point-award message is overlaid without obscuring the offer rows.

## 6. Trigger Plan

- Experiment: `exp_onset=1`, `exp_end=2`.
- Net lifecycle: `block_onset=10`, `block_end=11`, `goal_intro_onset=12`.
- Trial phases: `offer_preview_onset=20`, `choice_onset=30`, `net_update_onset=40`, `goal_complete_onset=41`.
- Responses: top/middle/bottom choices `31/32/33`; fail-safe timeout `34`.
- End screen: `good_bye_onset=60`.

## 7. Architecture Decisions (Auditability)

- Built-in independent condition balancing is insufficient because offers follow three cross-trial random walks and the start of the next net depends on the participant's previous choices. A custom `FishingNetController` is therefore required.
- The controller owns deterministic schedule generation from a documented seed and prepares the complete `FishingTrialSpec` before `run_trial()` is called. `run_trial.py` does not randomly choose offers, display order, net size, or goal state.
- A one-condition `BlockUnit` executes each session trial so the dynamically prepared spec remains the canonical condition passed into `run_trial()`. The participant-visible net lifecycle is recorded separately through net indices and lifecycle triggers.
- Timing RNG and schedule RNG are not shared; durations are config values handled by `StimUnit`.
- Participant-facing wording and static visual templates remain in YAML. `src/utils.py` only rebuilds those templates with plan-specific positions, widths, and formatted values.
- Trial IDs come from `psyflow.next_trial_id()`. Phase data use `set_trial_context(...)` and `StimUnit.to_dict(...)`.

## 8. Inference Log

- `inferred`: Chinese localization and `SimHei` font; the cited task was presented in English.
- `inferred`: keyboard keys `1/2/3` adapt the cited three-button spatial response mapping for standard computers.
- `inferred`: 30 s unattended-run timeout operationalizes the cited free-response choice without normally constraining behavior.
- `inferred`: the implementation uses a 100-trial decision-only behavioral session; the paper used 300 scanner decisions and 100 post-scan decisions with interleaved spatial probes.
- `inferred`: the source screened pre-generated schedules with a stochastic tree-search model. This implementation preserves the cited net-size and offer-generating distributions and rejects only clearly trivial initial combinations using a documented 4-14-step initial-offer feasibility bound; it does not claim to reproduce the unpublished exact schedule bank.
- `inferred`: pixel dimensions, shared zero point, and bar scale are reconstructed from Fig. 1 and Extended Data Fig. 1 for a 1280 x 720 display.

