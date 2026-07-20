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

## Conditional logic
- If `<experiment>` is `polar_twist_mcmc_comparison`:
  - Use `mess_ellipse_diagnostics` module.
- Else:
  - Use the experiment-specific ellipse diagnostics module defined in `instructions/experiments/<experiment>.md`.

- If required trace sidecars are missing:
  - Stop plotting request.
  - Ask to run chains with trace capture enabled and explicit iteration targets.

## Validation
- Confirm generated overlay figure(s) and interval-panel figure(s) are present.
- Confirm output names include method settings and iteration anchors.

## Example invocation
```text
Use plot-ellipses for polar_twist_mcmc_comparison to generate MESS ellipse diagnostics for captured iterations.
```
