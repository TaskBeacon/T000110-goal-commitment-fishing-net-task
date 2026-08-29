# Parameter Mapping

## Mapping Table

| Parameter ID | Config Path | Implemented Value | Source Paper ID | Evidence (quote/figure/table) | Decision Type | Notes |
|---|---|---|---|---|---|---|
| `session_trials` | `task.total_trials` | `100` | `HOLTON2024` | Methods, Experimental procedure: 300 scanner trials and 100 post-scan trials | `inferred` | Decision-only behavioral baseline uses the 100-trial behavioral-session budget. |
| `net_size_range` | `controller.net_size_min/max` | `12-72` | `HOLTON2024` | Methods, Schedule generation procedure | `exact` | Uniform integer draw within the cited range. |
| `initial_offer_distribution` | `controller.initial_offer_mean/sd` | `Normal(6, 1)` | `HOLTON2024` | Methods: mean 6, variance 1 | `exact` | Config stores SD = 1. |
| `offer_walk_distribution` | `controller.walk_sd` | `sqrt(0.8)` | `HOLTON2024` | Methods: independent Gaussian walks with variance 0.8 | `exact` | Independent across the three goods. |
| `jump_probabilities` | `controller.jump_up_probability/down_probability` | `0.1 / 0.1` | `HOLTON2024` | Methods, Schedule generation procedure | `exact` | Mutually exclusive up/down branch per good and trial. |
| `jump_magnitude` | `controller.jump_min/max` | `3-9` | `HOLTON2024` | Methods: new value 3 to 9 points above or below the option's starting offer | `exact` | Jump resets the option's local random-walk anchor. |
| `offer_preview` | `timing.offer_preview_s` | `2.0 s` | `HOLTON2024` | Extended Data Fig. 1d, `view offers` | `exact` | Responses are disabled during preview. |
| `choice_window` | `timing.choice_window_s` | `30.0 s` | `HOLTON2024` | Extended Data Fig. 1d/e: free response | `inferred` | Safety cap only; recorded as timeout if reached. |
| `net_update` | `timing.net_update_s` | `2.4 s` | `HOLTON2024` | Fig. 1c and Extended Data Fig. 1d/e | `exact` | Selected offer and resulting net contents remain visible. |
| `display_order` | `FishingTrialSpec.display_order` | `random each trial` | `HOLTON2024` | Methods, Primary decision task | `exact` | Prevents persistence from being confounded with motor repetition. |
| `points_rule` | `FishingNetController.apply_choice` | `+1 per completed net` | `HOLTON2024` | Methods and Extended Data Fig. 1a/c | `exact` | The original bonus conversion is documented but not paid by software. |
| `bar_scale` | `task.offer_pixels_per_unit` | `24 px/unit` | `HOLTON2024` | Fig. 1a and Extended Data Fig. 1a | `inferred` | Shared scale keeps bar length proportional to quantity on 1280 x 720 displays. |

