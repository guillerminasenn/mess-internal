---
name: execute-experiment-compute-metrics
description: Run the metrics phase for solute_transport_dim_sweep_shared_draws_pcn_mpcn to compute availability, runtime, ESS, and MSJD artifacts.
---

# Execute Experiment: Compute Metrics

Use this skill when the user asks to compute metrics after chains are available.

## Experiment target
- Package: `<repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn`
- Primary entrypoint: `compute_metrics_workflow`

## Default command
- `source .venv-mess/bin/activate && python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.compute_metrics_workflow`

## Workflow outputs to verify
- Diagnostics:
  - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../diagnostics/chain_availability.json`
- Tables:
  - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../tables/runtime_summary.json`
  - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../tables/metrics_summary.json`
- Manifests:
  - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../manifests/metrics_workflow_artifacts.json`
  - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../manifests/metrics_workflow_artifacts.md`

## Fallback behavior
- If metrics summary is missing in solute report root but exists in advection report root for same run, copy the table into solute root before report plotting, then rerun metrics/report phase.

## Safety
- Do not alter chain `.npz` contents.
- Do not delete chain artifacts.

## Example invocation
```text
Use execute-experiment-compute-metrics to run the metrics workflow for
solute transport dim sweep and report the generated diagnostics/tables/manifests.
```
