---
name: execute-experiment-compute-metrics
description: Run the metrics phase for an experiment by resolving metrics entrypoints and expected outputs from instructions/experiments.
---

# Execute Experiment: Compute Metrics

Use this skill when the user asks to compute metrics after chains are available.

## Resolve target experiment
1. Determine `<experiment>` from the user request.
2. Read `instructions/experiments/<experiment>.md`.
3. Resolve package path as `<repo>.experiments.<experiment>`.
4. Resolve metrics entrypoint(s) from the experiment spec.

## Generic default command
- `<activate_env_command> && python -m <repo>.experiments.<experiment>.compute_metrics_workflow`

## Environment placeholder
- `<activate_env_command>` means the repository-specific environment activation command
  (for example `source .venv/bin/activate` or equivalent for the active workspace).

## Conditional execution (if/else)
- If `instructions/experiments/<experiment>.md` includes `compute_metrics_workflow`:
  - Run `python -m <repo>.experiments.<experiment>.compute_metrics_workflow`.
- Else if the spec lists module-level metric steps (for example availability/runtime/metrics modules):
  - Run those listed modules in documented order.
- Else:
  - Attempt `python -m <repo>.experiments.<experiment>.compute_metrics` and verify outputs.

## Outputs to verify (from spec)
- Read expected metric artifacts from `instructions/experiments/<experiment>.md`.
- Validate presence of diagnostics/tables/manifests declared there.
- If the experiment includes MESS-over-M sweeps, verify rows expose MESS cost fields and normalized ESS fields when `mess_subiters_per_iter` exists; otherwise verify explicit unavailability flags/NaNs are present.

## Solute transport branch
- If `<experiment>` is `solute_transport_dim_sweep_shared_draws_pcn_mpcn`:
  - Run `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.compute_metrics_workflow`.
  - Verify:
    - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../diagnostics/chain_availability.json`
    - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../tables/runtime_summary.json`
    - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../tables/metrics_summary.json`
    - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../manifests/metrics_workflow_artifacts.json`
    - `reports/solute_transport_dim_sweep_shared_draws_pcn_mpcn/.../manifests/metrics_workflow_artifacts.md`

## Safety
- Do not alter chain `.npz` contents.
- Do not delete chain artifacts.

## Example invocation
```text
Use execute-experiment-compute-metrics for <experiment>; resolve the metrics
workflow from instructions/experiments/<experiment>.md, run it, and report
the generated diagnostics/tables/manifests.
```
