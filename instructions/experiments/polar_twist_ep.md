# Experiment Spec: polar_twist_ep

Date: 2026-07-21
Status: implementation scaffold and execution-ready workflows

## Objective
Compare a multiproposal MESS(M) chain against an embarrassingly parallel EP-ESS approach for polar-twist sampling.

For each M in [1, 2, 5, 10, 20, 50]:
- MESS branch: run B independent MESS(M) chains.
- EP-ESS branch: run B replicates, each replicate containing M independent ESS chains.

Here ESS means elliptical slice sampling, i.e. MESS(1).

Default B is 20.

## Iteration regime
- n_iters = 20000
- burn_in = 1000
- post-burn stationarity window = 19000 iterations

Convergence diagnostics use the first warmup iterations (default 1000), while ESS metrics are computed post burn-in.

## Start-point contract
- Sample B prior starts for MESS chains.
- Sample B x max(M) prior starts for EP-ESS chains.
- Enforce that first EP chain in each replicate starts from the same point as the corresponding MESS replicate.

## Deterministic IDs and paths
- output dataset: polar_twist_ep
- run layout:
  - estimations/polar_twist_ep/<data_id>/fixed/<run_id>/...
  - reports/polar_twist_ep/<data_id>/fixed/<run_id>/...

## Execution entrypoints
Run/chains:
- python jobs/polar_twist_ep/run.py --dry-run --grid-count <N> --grid-index <I>
- python -m mess.experiments.polar_twist_ep.run_workflow --dry-run --grid-count <N> --grid-index <I>
- python -m mess.experiments.polar_twist_ep.run_chains --dry-run --grid-count <N> --grid-index <I>

Metrics:
- python -m mess.experiments.polar_twist_ep.report_availability
- python -m mess.experiments.polar_twist_ep.benchmark_runtime
- python -m mess.experiments.polar_twist_ep.compute_metrics
- python -m mess.experiments.polar_twist_ep.compute_metrics_workflow

Reports:
- python -m mess.experiments.polar_twist_ep.ess_vs_m_plots
- python -m mess.experiments.polar_twist_ep.report_parity_checklist
- python -m mess.experiments.polar_twist_ep.report_workflow

## Metric aggregation contract
For fixed M and replicate b:
- EP raw ESS (component-wise) is the sum of ESS across its M independent ESS chains.
- MESS raw ESS is the raw ESS of that replicate's MESS(M) chain.

By-M comparison uses replicate average over B replicates:
- average_raw_ESS_variant(M) = (1/B) sum_{b=1}^B raw_ESS_variant(M, b)

Normalization for EP branch:
- per parallel likelihood step:
  - denominator = (sum of likelihood steps over M chains) / M cores
- per energy likelihood evaluation:
  - denominator = sum of likelihood evaluations over M chains

Normalization for MESS branch:
- per parallel likelihood step:
  - denominator = total interval rounds after burn-in
- per energy likelihood evaluation:
  - denominator = M x total interval rounds after burn-in

## Artifact expectations
Run workflow artifacts include:
- generated chain files for mess and ep_ess variants
- diagnostics/start_points.npz
- worker_<grid_index>_runs.json

Compute-metrics workflow artifacts include:
- diagnostics/chain_availability.json
- tables/runtime_summary.json
- tables/metrics_per_chain.json
- tables/metrics_per_replicate.json
- tables/metrics_summary.json

Report workflow artifacts include:
- figures/ess_msjd_vs_rho/mess_ess_vs_M_raw.png
- figures/ess_msjd_vs_rho/mess_ess_vs_M_per_parallel_lik_step.png
- figures/ess_msjd_vs_rho/mess_ess_vs_M_per_energy_lik_eval.png
- figures/ess_msjd_vs_rho/mess_ess_vs_M_availability.json
- manifests/report_parity_checklist.{md,json}

## Coupling with convergence reports
Convergence-phase diagnostics for EP versus MESS are emitted by the polar_twist_convergence package under reports/polar_twist_convergence, using this experiment's chains as source artifacts.
