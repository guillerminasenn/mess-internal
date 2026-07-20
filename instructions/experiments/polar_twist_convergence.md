# Experiment Spec: polar_twist_convergence

Date: 2026-07-20
Status: implementation scaffold and execution-ready report workflow

## Objective
Compare warmup convergence speed across previously computed polar-twist chains by focusing on the first iterations and plotting trace behavior for `x1` and `x2`.

## Scope
In scope:
- reuse existing chains from:
  - `reports/polar_twist_mcmc_comparison`
  - `reports/polar_twist_distance_comparison`
- no new chain generation
- two warmup traceplot figures:
  - one for `x1`
  - one for `x2`
- each figure uses one subplot per algorithm variant found

Out of scope:
- re-running MCMC samplers
- modifying prior chain `.npz` artifacts

## Default Comparison Set
- MH
- pCN at `rho=0.5`
- mPCN at `rho=0.5` for `P in [2, 5, 10, 20, 50]`
- MESS uniform for `M in [1, 2, 5, 10, 20, 50]`
- MESS angular for `M in [5, 10, 20, 50]` when present
- MESS euclidean for `M in [5, 10, 20, 50]` when present
- ESS proxy as `MESS (M=1)`

## Warmup Window
- default `warmup_iters = 100`
- traceplots use `chain[:warmup_iters]` for each selected method

## Deterministic IDs and Paths
- output dataset: `polar_twist_convergence`
- run layout:
  - `estimations/polar_twist_convergence/<data_id>/fixed/<run_id>/...`
  - `reports/polar_twist_convergence/<data_id>/fixed/<run_id>/...`

## Execution Entrypoints
Run/chains (reuse mode):
- `python jobs/polar_twist_convergence/run.py --dry-run --grid-count <N> --grid-index <I>`
- `python -m mess.experiments.polar_twist_convergence.run_workflow --dry-run --grid-count <N> --grid-index <I>`

Metrics:
- `python -m mess.experiments.polar_twist_convergence.compute_metrics_workflow`

Reports:
- full report workflow:
  - `python -m mess.experiments.polar_twist_convergence.report_workflow`
- subset module:
  - `python -m mess.experiments.polar_twist_convergence.traceplots`

## Artifact Expectations
- diagnostics:
  - `reports/.../diagnostics/source_chain_summary.json`
- tables:
  - `reports/.../tables/source_availability.json`
- figures:
  - `reports/.../figures/warmup_traceplots/traceplots_warmup_x1.png`
  - `reports/.../figures/warmup_traceplots/traceplots_warmup_x2.png`

## Notes
- Missing source chains are shown in subplot panels as `missing chain`.
- This experiment intentionally reuses historical outputs and does not alter source run folders.