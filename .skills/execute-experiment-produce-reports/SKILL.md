---
name: execute-experiment-produce-reports
description: Run the report-generation phase for solute_transport_dim_sweep_shared_draws_pcn_mpcn; by default generate all report artifacts, or only user-requested subsets.
---

# Execute Experiment: Produce Reports

Use this skill when the user asks for figures/checklists/reports from the solute transport dim sweep experiment.

## Experiment target
- Package: `mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn`

## Default behavior
- If user does not request a subset: run full report workflow.
- If user requests a subset: run only the corresponding module entrypoints.

## Full report command (default)
- `source .venv-mess/bin/activate && python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_workflow`

## Subset mapping
- `visual_checks`:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.visual_checks`
- `traceplots`:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.traceplots`
- `panels`:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.panels`
- `ess_msjd`:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots`
- `pairplots`:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.pairplots`
- `parity_checklist`:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_parity_checklist`

## Required precondition checks
- Ensure `metrics_summary.json` exists under the solute report tables path before running `ess_msjd_plots`.
- If missing, run metrics workflow first:
  - `python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.compute_metrics_workflow`

## Output checks
- Pairplots folder should contain ~40 files for default d/M/P lists.
- ESS/MSJD folder should contain 8 files:
  - mean + mean_log
  - a_01 + a_01_log
  - a_12 + a_12_log
  - a_21 + a_21_log

## Example invocation
```text
Use execute-experiment-produce-reports to generate only pairplots and ESS/MSJD
for the solute transport dim sweep run; do not run the other report modules.
```
