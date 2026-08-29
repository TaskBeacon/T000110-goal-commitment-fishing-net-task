# Goal Commitment / Fishing-Net Task

| Field | Value |
|---|---|
| Name | Goal Commitment / Fishing-Net Task |
| Version | v0.1.0 |
| URL / Repository | https://github.com/TaskBeacon/T000110-goal-commitment-fishing-net-task |
| Short Description | Sequential persistence-versus-abandonment decisions while accumulating one of three dynamically changing resources |
| Created By | TaskBeacon |
| Date Updated | 2026-08-29 |
| PsyFlow Version | 0.1.0 |
| PsychoPy Version | 2025.1.1 |
| Modality | Behavior |
| Language | Chinese |
| Voice Name | zh-CN-YunyangNeural (configured; voice disabled) |

## 1. Task Overview

Participants try to fill as many fishing nets as possible within a fixed trial budget. Each decision displays offers for crab, octopus, and fish. Choosing the current goal good preserves accumulated progress; choosing another good abandons the old contents and begins again with the newly selected offer. Because offers drift and occasionally jump, participants must balance commitment against flexible abandonment. The implementation is grounded in Holton et al. (2024) and provides a 100-trial decision-only behavioral baseline.

## 2. Task Flow

![Task Flow](task_flow.png)

### Block-Level Flow

| Step | Description |
|---|---|
| Session setup | Load the selected mode, collect or inject subject information, initialize the window, stimuli, triggers, and deterministic controller. |
| Instructions | Explain positive and negative offers, one-good-only nets, switching costs, spatial keys, scoring, and the trial budget. |
| New net | Draw a net size from 12-72 and initialize three offers; show the empty target net. |
| Sequential decisions | Continue trials for the same net until the net is full or the fixed session budget ends. |
| Net completion | Award one point and initialize a new net before the next session trial. |
| Save and finish | Export one logical trial per row, write the fishing-net summary JSON, and show completed nets. |

### Trial-Level Flow

| Step | Duration | Description |
|---|---:|---|
| Goal intro | Until Space | Appears only on the first trial of a new net and shows the empty target bar. |
| Offer preview | 2,000 ms | Three randomized-position seafood offers and the current net appear; response is disabled. |
| Choice | Free response (30 s safety cap) | The same display gains a question mark; keys 1/2/3 choose top/middle/bottom. |
| Net update | 2,400 ms | The selected quantity is applied after persistence or abandonment logic. |

### Controller Logic

| Component | Description |
|---|---|
| Net target | Uniform integer draw from 12 through 72; clearly trivial initial combinations are rejected by a documented feasibility bound. |
| Initial offers | Independent normal draws with mean 6 and variance 1. |
| Offer drift | Independent Gaussian random walks with variance 0.8. |
| Offer jumps | Per good and trial: 0.1 probability upward and 0.1 downward, with a 3-9 point anchor shift. |
| State update | Persistence adds to the existing net; abandonment discards old contents before applying the new offer; negative accumulation is floored at zero. |
| Reproducibility | Human and validation schedules are controlled by explicit seeds; QA/sim use a mechanism-complete six-trial schedule. |

### Other Logic

| Component | Description |
|---|---|
| Display randomization | The three goods change top/middle/bottom positions each trial to separate goal persistence from motor repetition. |
| Session stopping rule | The task stops after the configured number of trials even if the final net is incomplete. |
| Summary measures | Completed nets, persistence and abandonment counts, abandonment rate, abandoned quantity, progress at abandonment, timeouts, and trials per completed net. |

## 3. Configuration Summary

All participant-facing text, layout templates, timings, triggers, and controller parameters are defined in `config/config.yaml`; QA and simulation profiles use separate mode-specific files.

### a. Subject Info

| Field | Meaning |
|---|---|
| `subject_id` | Three-digit participant identifier in human mode; deterministic identifier in QA/simulation. |

### b. Window Settings

| Parameter | Value |
|---|---|
| Resolution | 1280 x 720 px |
| Units | Pixels |
| Background | Dark navy with black task panel and gold border |
| Fullscreen | Disabled by default for portable behavioral deployment |

### c. Stimuli

| Name | Type | Description |
|---|---|---|
| Seafood icons | Licensed PNG | Twemoji crab, octopus, and fish assets. |
| Offer tracks/bars | PsychoPy rectangles | Shared-scale horizontal bars; green for positive and red for negative offers. |
| Current net | PsychoPy rectangles and image | Grey capacity bar, blue accumulated fill, and current goal icon. |
| Status/prompt text | Configured text | Completed-net count, remaining trials, instructions, decision mark, and completion message. |

### d. Timing

| Phase | Duration |
|---|---:|
| Offer preview | 2.0 s |
| Choice | Free response; 30 s unattended-run cap |
| Net update | 2.4 s |

### e. Triggers

| Event | Code |
|---|---:|
| Experiment onset / end | 1 / 2 |
| Net onset / end | 10 / 11 |
| Goal intro | 12 |
| Offer preview | 20 |
| Choice onset | 30 |
| Top / middle / bottom response | 31 / 32 / 33 |
| Choice timeout | 34 |
| Net update / completion | 40 / 41 |
| Final screen | 60 |

### f. Adaptive Controller

| Parameter | Value |
|---|---|
| Schedule seed | 110110 |
| Net-size range | 12-72 |
| Initial offer | Normal(mean 6, SD 1) |
| Walk SD | sqrt(0.8) |
| Up/down jump probability | 0.1 / 0.1 |
| Jump magnitude | 3-9 |

## 4. Methods (for academic publication)

Participants completed a computerized incremental goal-pursuit task adapted from Holton et al. (2024). On each of 100 decision trials, three seafood offers were displayed as proportional horizontal bars. The offer display was visible for 2 s before a free-response choice. Participants selected the top, middle, or bottom good using keys 1, 2, or 3. Only one seafood type could occupy a net: choosing the same good added its current offer to accumulated contents, whereas choosing a different good discarded prior contents before applying the new offer. Positive and negative offers were shown in green and red, respectively, and net contents could not fall below zero. The updated net was displayed for 2.4 s. Filling a net awarded one point and started a new net on the following trial.

Net sizes were uniformly sampled from 12 to 72. Initial offers were independently sampled from a normal distribution with mean 6 and variance 1, then evolved through independent Gaussian random walks with variance 0.8. Each good also had a 0.1 probability of an upward jump and a 0.1 probability of a downward jump per trial; jump magnitudes ranged from 3 to 9 points and established a new local walk anchor. Good-to-position mappings were randomized every trial. The session stopped after its fixed trial budget. The main outcomes were completed nets, persistence and abandonment decisions, abandoned quantity, and goal progress at abandonment.

Primary protocol: Holton, E., Grohn, J., Ward, H., et al. (2024). Goal commitment is supported by vmPFC through selective attention. *Nature Human Behaviour, 8*, 1351-1365. https://doi.org/10.1038/s41562-024-01844-5
