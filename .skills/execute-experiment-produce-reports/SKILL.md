---
name: execute-experiment-produce-reports
description: Run the report-generation phase for an experiment by resolving report entrypoints from instructions/experiments; default is full report set unless a subset is requested.
---

# Execute Experiment: Produce Reports

Use this skill when the user asks for figures/checklists/reports from an experiment.

## Resolve target experiment
1. Determine `<experiment>` from the user request.
2. Read `instructions/experiments/<experiment>.md`.
3. Resolve package path as `<repo>.experiments.<experiment>`.
4. Resolve available report modules from the experiment spec.

## Default behavior
- If user does not request a subset: run full report workflow.
- If user requests a subset: run only the corresponding module entrypoints.

## Generic full-report command (default)
- `<activate_env_command> && python -m <repo>.experiments.<experiment>.report_workflow`

## Environment placeholder
- `<activate_env_command>` means the repository-specific environment activation command
  (for example `source .venv/bin/activate` or equivalent for the active workspace).

## Conditional execution (if/else)
- If `instructions/experiments/<experiment>.md` defines a `report_workflow` entrypoint:
  - Use it when no subset is requested.
- Else:
  - Run the report modules listed in the experiment spec one by one.

- If subset is requested:
  - Map requested subset names to module entrypoints listed in `instructions/experiments/<experiment>.md`.
  - Run only requested subsets.

- If `<experiment>` is `solute_transport_dim_sweep_shared_draws_pcn_mpcn`:
  - Full workflow:
    - `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_workflow`
  - Supported subsets:
    - `visual_checks` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.visual_checks`
    - `traceplots` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.traceplots`
    - `panels` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.panels`
    - `ess_msjd` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots`
    - `pairplots` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.pairplots`
    - `parity_checklist` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_parity_checklist`
- Else:
  - Use only report modules declared in `instructions/experiments/<experiment>.md`.

## Required precondition checks
- If any selected report module depends on metrics (for example ESS/MSJD plots):
  - Ensure required metrics tables exist first.
  - If missing, run the metrics workflow for `<experiment>` before report plotting.

## Output checks
- Validate report outputs declared in `instructions/experiments/<experiment>.md`.
- For solute dim-sweep, expected checks include:
  - pairplots around 40 files for default grid.
  - ESS/MSJD folder with 8 files (mean/mean_log and component variants).

## Example invocation
```text
Use execute-experiment-produce-reports for <experiment>. If no subset is given,
run full report workflow. If subset is requested, run only those modules defined
for that experiment in instructions/experiments/<experiment>.md.
```
