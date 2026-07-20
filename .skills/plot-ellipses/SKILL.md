---
name: plot-ellipses
description: Generate exact historical MESS ellipse diagnostics from trace sidecars captured during chain runs.
---

# Plot Ellipses

Use this skill when the user asks for MESS ellipse diagnostics (contiguous overlays or interval-level panels).

## Core behavior
- Use exact historical playback traces captured during original chain generation.
- Do not generate publication/parity ellipse diagnostics from approximate replay when exact playback is required.

## Resolve target
1. Determine `<experiment>` from the user request.
2. Read `instructions/experiments/<experiment>.md`.
3. Confirm trace sidecar artifacts exist for requested method/iterations.

## Commands
- Polar twist default module:
  - `<activate_env_command> && python -m <repo>.experiments.polar_twist_mcmc_comparison.mess_ellipse_diagnostics`
- Polar twist with contiguous window filter:
  - `<activate_env_command> && python -m <repo>.experiments.polar_twist_mcmc_comparison.mess_ellipse_diagnostics --start-iter <START> --n-iters <COUNT>`
- Polar twist with explicit iteration list:
  - `<activate_env_command> && python -m <repo>.experiments.polar_twist_mcmc_comparison.mess_ellipse_diagnostics --iters <I1,I2,...>`

## Conditional logic
- If `<experiment>` is `polar_twist_mcmc_comparison`:
  - Use `mess_ellipse_diagnostics` module.
- Else:
  - Use the experiment-specific ellipse diagnostics module defined in `instructions/experiments/<experiment>.md`.

- If required trace sidecars are missing:
  - Backfill exact traces using run wrapper overrides, then re-run plotting.
  - Backfill command (contiguous window):
    - `<activate_env_command> && python jobs/<experiment>/run.py --capture-ellipse-traces --ellipse-start-iter <START> --ellipse-count <COUNT> --grid-count <N> --grid-index <I>`
  - Backfill command (explicit list):
    - `<activate_env_command> && python jobs/<experiment>/run.py --capture-ellipse-traces --ellipse-iters <I1,I2,...> --grid-count <N> --grid-index <I>`

## Validation
- Confirm generated overlay figure(s) and interval-panel figure(s) are present.
- Confirm output names include method settings and iteration anchors.
- Confirm interval panels start at interval 1 (no full-bracket panel).
- Confirm current state is marked with a blue triangle and accepted state with a hollow square.
- Confirm legend is visible and interval titles report `valid/M` proposal counts.

## Example invocation
```text
Use plot-ellipses for polar_twist_mcmc_comparison to generate MESS ellipse diagnostics
for iterations 10000 to 10010.
```
