---
name: create-experiment
description: Create a new experiment package under src/<repo>/experiments with matching instructions and job wrapper, following repo run/output/diagnostics policy and src/<repo>/problems separation.
---

# Create Experiment

Use this skill when the user asks to create a new experiment workflow in this repository.

## Scope
- Create experiment package structure under `src/<repo>/experiments/<experiment_name>/`.
- Keep problem definitions in `src/<repo>/problems/`; do not put problem classes in experiment modules.
- Create or update matching docs under `instructions/experiments/`.
- Create or update matching job wrapper under `jobs/<experiment_name>/`.
- Ensure run layout uses deterministic `data_id` and `run_id` hashing conventions.

## Required policy checks
- Do not read from `notebooks/` unless explicitly requested.
- Do not edit, delete, or rewrite `.npz` contents.
- If policy/docs are changed, update affected files in `instructions/` in the same workstream.
- If request contradicts existing instructions, ask for confirmation before applying.

## Standard structure to create
- `src/<repo>/experiments/<experiment_name>/config.py`
- `src/<repo>/experiments/<experiment_name>/run_chains.py`
- `src/<repo>/experiments/<experiment_name>/compute_metrics.py`
- `src/<repo>/experiments/<experiment_name>/report_workflow.py`
- `src/<repo>/experiments/<experiment_name>/__init__.py`
- `jobs/<experiment_name>/run.py`
- `instructions/experiments/<experiment_name>.md`

## Implementation guidance
1. Start from `ExperimentConfig` + `build_context` patterns used in existing experiments.
2. Use `<repo>.experiments.common` helpers (`run_layout`, artifacts/checklists, plotting utilities) where possible.
3. Provide explicit workflow entrypoints for:
   - running chains
   - computing metrics
   - producing reports
4. Prefer backward-compatible wrappers only if user asks to preserve old entrypoints.
5. Validate with `python -m compileall` and dry-run commands.

## Done criteria
- Experiment package imports compile.
- Job wrapper resolves and runs in dry-run mode.
- Experiment instruction file documents run, metrics, and report entrypoints.

## Example invocation
```text
Use the create-experiment skill to scaffold a new experiment named
solute_transport_obs_scale_sweep with config.py, run_chains.py,
compute_metrics.py, report_workflow.py, jobs wrapper, and instructions doc.
```
