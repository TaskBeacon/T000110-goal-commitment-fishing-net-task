# Task Plot Brief

Title: Goal Commitment / Fishing-Net Task

Construct: goal commitment / cognitive flexibility

## Evidence Basis

- Canonical flow: `main.py`, `src/run_trial.py`, `src/utils.py`, and `config/config.yaml`.
- Protocol basis: Holton et al. (2024), Figure 1 and Extended Data Figure 1.
- Participant sees crab, octopus, and fish offers as horizontal quantity bars. Positive offers are green; negative offers are red.
- The three goods are randomly reordered top/middle/bottom on each decision, and keys `1`, `2`, `3` select those positions.
- A net can contain only one good. Re-selecting the current good preserves accumulated progress; selecting another good abandons the old contents before applying the new offer.
- Completing the target bar awards `+1` and starts a fresh net.

## Representative Rows

1. **Start new net**: empty target net, preview three dynamic offers, choose a position, then show the first accumulated quantity.
2. **Keep current goal**: preview offers plus the partially filled current net, choose the same seafood, then add the selected offer without losing progress.
3. **Switch goal**: preview offers plus the partially filled current net, choose a different seafood, discard the old fill, then begin the new seafood total; show `+1` only if the new total reaches the target.

## Timings and Responses

- New-net intro: until `SPACE`; only at the start of a new net.
- Offer preview: `2,000 ms`; response disabled.
- Choice: until `1`, `2`, or `3` response; implementation safety cap `30 s`.
- Net update: `2,400 ms`.

## Visual Content

- Use one clean row per representative trial type.
- Each screen is a plain dark-gray participant display within the scientific diagram, not a decorative ocean scene.
- Show three vertically stacked seafood icons with horizontal green/red offer bars.
- Show a single target/progress bar at the bottom of every decision and update screen.
- For the keep row, make the current and selected seafood visibly the same.
- For the switch row, make the current seafood and selected seafood visibly different and show the old progress removed before the new fill.
- Keep textual labels in English and very short to reduce raster-text errors.

## Unknown/Omitted

- The cited free-response choice has no published timeout; the `30 s max` label is the documented implementation safety cap.
- Scanner-only fixation/ITI and post-scan spatial judgments are outside this decision-only behavioral baseline and must not appear.
