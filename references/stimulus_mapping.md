# Stimulus Mapping

## Mapping Table

| Condition | Stage/Phase | Stimulus IDs | Participant-Facing Content | Source Paper ID | Evidence (quote/figure/table) | Implementation Mode | Asset References | Notes |
|---|---|---|---|---|---|---|---|---|
| `decision_trial` | `goal_intro` | `ocean_panel`, `goal_intro_text`, `net_track`, `net_label` | Empty target net and start instruction | `HOLTON2024` | Extended Data Fig. 1b | `psychopy_builtin` | `n/a` | Appears on the first trial of each net. |
| `decision_trial` | `offer_preview` | `crab_icon`, `octopus_icon`, `fish_icon`, `offer_track`, `offer_positive_bar`, `offer_negative_bar`, `net_track`, `net_fill`, `status_text` | Three seafood offers and current net, with no response prompt | `HOLTON2024` | Fig. 1a; Extended Data Fig. 1a/d | `licensed_asset_plus_psychopy_builtin` | `assets/crab.png`, `assets/octopus.png`, `assets/fish.png` | Positive quantities are green; negative quantities are red. |
| `decision_trial` | `choice` | `choice_prompt` plus all offer-preview stimuli | Same offers with a large question mark; choose top/middle/bottom | `HOLTON2024` | Fig. 1c; Extended Data Fig. 1d/e | `licensed_asset_plus_psychopy_builtin` | `assets/crab.png`, `assets/octopus.png`, `assets/fish.png` | Display order is randomized every trial. |
| `decision_trial` | `net_update` | `net_fill`, `current_goal_icon`, `complete_text` plus offer stimuli | Selected good is applied to the net; completed nets show a one-point award | `HOLTON2024` | Fig. 1a/c; Extended Data Fig. 1c/d/e | `licensed_asset_plus_psychopy_builtin` | `assets/crab.png`, `assets/octopus.png`, `assets/fish.png` | Switching replaces the goal icon and clears old progress before adding the new offer. |
| `all` | `instruction` | `instruction_text` | Chinese explanation of persistence, abandonment, positive/negative offers, keys, and the fixed trial budget | `HOLTON2024` | Methods, Primary decision task and Schedules | `psychopy_builtin` | `n/a` | Localized from the cited rules; no raw internal condition labels are shown. |

