# Staged Plan: MESS Ellipse Historical Playback

Date: 2026-07-20
Scope: exact historical playback for MESS ellipse diagnostics, first integrated in polar_twist_mcmc_comparison and reusable across experiments.
Status: implemented

## Hard Constraints

1. Do not read notebooks for implementation unless explicitly requested.
2. Do not modify `.npz` chain contents.
3. Do not delete `.npz` files.
4. Keep problem definitions under `src/mess/problems`.
5. Reflect policy and workflow updates in instruction/skill files in the same workstream.

## Stage 0: Architecture Decision

Goal: lock exact playback behavior.

Decision:
- Ellipse diagnostics rely on exact historical MESS traces captured during chain generation.
- Report-phase plotting consumes trace sidecars, not approximate replay.

## Stage 1: Core Algorithm Support

Goal: expose a trace payload for one MESS step.

Actions:
- Extend `mess_step` with optional `return_trace` output.
- Keep backward compatibility for existing callers.

## Stage 2: Shared Plotting Utilities

Goal: reusable ellipse plotting for all experiments.

Actions:
- Add common utilities for:
  - contiguous ellipse overlays
  - interval-level proposal/acceptance panels
  - trace serialization helpers

## Stage 3: Polar-Twist Runtime Capture

Goal: capture exact traces at configured iterations.

Actions:
- Add config controls for trace capture targets and optional run-phase plotting.
- Capture trace sidecars in `run_chains.py` for MESS tasks.
- Register sidecars/figures in run artifacts.

## Stage 4: Polar-Twist Report Integration

Goal: generate ellipse diagnostics from sidecars.

Actions:
- Add `mess_ellipse_diagnostics.py` report module.
- Integrate into `report_workflow.py` and parity checklist.

## Stage 5: Instruction + Skill Updates

Goal: make usage explicit and reusable.

Actions:
- Update plotting and diagnostics policy docs.
- Update polar-twist experiment instructions.
- Add `.skills/plot-ellipses/SKILL.md`.
- Extend `execute-experiment-produce-reports` subset routing.

## Stage 6: Verification

Goal: confirm behavior and reproducibility.

Checks:
- Compile/import checks for updated modules.
- Dry-run chain execution unaffected when capture disabled.
- Trace sidecars created when capture enabled.
- Report module renders expected figures from sidecars.
