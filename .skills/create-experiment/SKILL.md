---
name: create-experiment
description: Create a new experiment package under src/<repo>/experiments with matching instructions and job wrapper, using repo policies and a generic, experiment-agnostic scaffold.
---

# Create Experiment

Use this skill when the user asks to create a new experiment workflow in this repository.

## Scope
- Create experiment package structure under `src/<repo>/experiments/<experiment>/`.
- Keep problem definitions in `src/<repo>/problems/`; do not put problem classes in experiment modules.
- Create or update matching docs under `instructions/experiments/`.
- Create or update matching job wrapper under `jobs/<experiment>/`.
- Ensure run layout uses deterministic `data_id` and `run_id` hashing conventions.
- Implement code and entrypoints only; do not execute chain generation as part of this skill.

## Required policy checks
- Do not read from `notebooks/` unless explicitly requested.
- Do not edit, delete, or rewrite `.npz` contents.
- If policy/docs are changed, update affected files in `instructions/` in the same workstream.
- If request contradicts existing instructions, ask for confirmation before applying.
- For staged experiment plans, stop after implementation and hand off execution to `execute-experiment-run-chains`.

## Standard structure to create
- `src/<repo>/experiments/<experiment>/config.py`
- `src/<repo>/experiments/<experiment>/run_chains.py`
- `src/<repo>/experiments/<experiment>/run_workflow.py`
- `src/<repo>/experiments/<experiment>/compute_metrics.py`
- `src/<repo>/experiments/<experiment>/compute_metrics_workflow.py`
- `src/<repo>/experiments/<experiment>/report_workflow.py`
- `src/<repo>/experiments/<experiment>/__init__.py`
- `jobs/<experiment>/run.py`
- `instructions/experiments/<experiment>.md`

## Implementation guidance
1. Start from `ExperimentConfig` + `build_context` patterns used in existing experiments.
2. Use `<repo>.experiments.common` helpers (`run_layout`, artifacts/checklists, plotting utilities) where possible.
3. Provide explicit workflow entrypoints for:
   - running chains
   - computing metrics
   - producing reports
4. Prefer backward-compatible wrappers only if user asks to preserve old entrypoints.
5. Validate with `python -m compileall` and dry-run commands.
6. If the experiment includes a MESS sweep over multiple `M` values, include by default:
   - persisted per-iteration MESS sub-iteration counts in chain artifacts (`mess_subiters_per_iter`)
   - metrics fields for ESS normalized by energy likelihood cost and parallel likelihood-step cost
   - report plots for MESS-only ESS-vs-M (raw and normalized variants) with component panels.

## Conditional experiment handling (if/else)
- If `instructions/experiments/<experiment>.md` already exists:
   - Extend existing behavior instead of replacing it.
   - Preserve existing entrypoint/module names documented there.
- Else:
   - Create a new instruction spec at `instructions/experiments/<experiment>.md`.
   - Include sections: objective, config, run IDs/paths, execution entrypoints, artifacts.

- If `<experiment>` is `solute_transport_dim_sweep_shared_draws_pcn_mpcn`:
   - Keep current module split (`run_chains`, `run_workflow`, `compute_metrics_workflow`, `report_workflow`, and report submodules).
   - Preserve compatibility fields (for example legacy output-group style behavior) unless user requests removal.
- Else:
   - Use the same workflow pattern, but define module names and outputs from the new experiment spec.
   - Do not inherit solute-transport-specific assumptions.

## Done criteria
- Experiment package imports compile.
- Job wrapper resolves (syntax/import checks only unless user explicitly requests execution).
- Experiment instruction file documents run, metrics, and report entrypoints.

## Stage-separation rule
- This skill is for create/implement phases.
- Do not run chains, metrics, or plotting commands unless the user explicitly asks for combined execution.
- Recommend next-step skill invocations in order:
   1) `execute-experiment-run-chains`
   2) `execute-experiment-compute-metrics`
   3) `execute-experiment-produce-reports`

## Example invocation
```text
Use create-experiment to scaffold <experiment> in src/<repo>/experiments,
add jobs/<experiment>/run.py, and write instructions/experiments/<experiment>.md
with run, metrics, and report entrypoints.
```
