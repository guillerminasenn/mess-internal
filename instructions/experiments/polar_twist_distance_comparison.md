# Experiment Spec: polar_twist_distance_comparison

Date: 2026-07-20
Status: scaffold and script entrypoints implemented

## Objective
Compare posterior mixing on the 2D polar-twist inverse problem using MESS with M=50 under three transition-matrix variants:
- uniform transition matrix (reuse existing chain from `polar_twist_mcmc_comparison`)
- LP distance-informed with angular distance
- LP distance-informed with euclidean distance

This experiment is script-first and notebook-independent.

## Source package
- `src/mess/experiments/polar_twist_distance_comparison/`

## Configuration model
Main config object: `ExperimentConfig` in `config.py`.

Key groups:
- Data/problem settings: `alpha`, `sigma_noise`, `prior_mean`, `prior_cov`, `weight_x`, `weight_y`, `data_seed`
- Run settings: `n_iters`, `burn_in`, `thin`, `max_lag`, `seed_mcmc`
- Comparison settings:
  - `M` (default `50`)
  - `variant_list` from `uniform`, `lp_angular`, `lp_euclidean`
  - `lp_lam` for LP solver regularization/penalty parameter
  - `run_uniform_if_missing` (default `False`)
  - optional `uniform_chain_path` override for explicit reuse

## Deterministic IDs and paths
- `data_id` is hashed from data-generation payload only.
- `run_id` is hashed from algorithm/execution payload for this comparison run.

Run layout:
- `estimations/polar_twist_distance_comparison/<data_id>/fixed/<run_id>/...`
- `reports/polar_twist_distance_comparison/<data_id>/fixed/<run_id>/...`

Uniform-chain reuse source:
- preferred auto-discovery in
  `estimations/polar_twist_mcmc_comparison/<data_id>/sweep/run_h*/chain_mess_M50.npz`
- fallback search across all `data_h*/sweep/run_h*` for `chain_mess_M50.npz`
- explicit override via `uniform_chain_path`

## Execution entrypoints
Run workflow (chain generation and manifest):
- `python -m mess.experiments.polar_twist_distance_comparison.run_chains`
- `python -m mess.experiments.polar_twist_distance_comparison.run_workflow`
- job wrapper: `python jobs/polar_twist_distance_comparison/run.py`

Compute-metrics workflow:
- `python -m mess.experiments.polar_twist_distance_comparison.report_availability`
- `python -m mess.experiments.polar_twist_distance_comparison.benchmark_runtime`
- `python -m mess.experiments.polar_twist_distance_comparison.compute_metrics`
- `python -m mess.experiments.polar_twist_distance_comparison.compute_metrics_workflow`

Report workflow:
- `python -m mess.experiments.polar_twist_distance_comparison.report_workflow`

Report submodules (style-aligned mixing diagnostics):
- `python -m mess.experiments.polar_twist_distance_comparison.traceplots`
- `python -m mess.experiments.polar_twist_distance_comparison.panels`
- `python -m mess.experiments.polar_twist_distance_comparison.ess_msjd_plots`

Cross-M mixing comparison (uniform vs LP angular/euclidean):
- `python -m mess.experiments.polar_twist_distance_comparison.cross_m_comparison`

## Job wrapper controls
`jobs/polar_twist_distance_comparison/run.py` supports:
- `--grid-count`, `--grid-index`, `--dry-run`
- `--variants uniform,lp_angular,lp_euclidean`
- `--run-uniform-if-missing`

Examples:
- run only LP angular:
  - `python jobs/polar_twist_distance_comparison/run.py --variants lp_angular`
- run both LP distances:
  - `python jobs/polar_twist_distance_comparison/run.py --variants lp_angular,lp_euclidean`
- include uniform generation only when reuse is unavailable:
  - `python jobs/polar_twist_distance_comparison/run.py --variants uniform,lp_angular,lp_euclidean --run-uniform-if-missing`

## Artifacts
Run workflow artifacts:
- `data_and_latent.npz`
- generated LP chain files
- reference artifact entry for reused uniform chain (when found)
- run manifest JSON/markdown

Compute-metrics workflow artifacts:
- `diagnostics/chain_availability.json`
- `tables/runtime_summary.json`
- `tables/metrics_summary.json`
- metrics manifest JSON/markdown

Report workflow artifacts:
- `figures/distance_comparison_summary.png`
- `distance_comparison_summary.md`
- `figures/traceplots_pub/traceplots_variant_comp0.png`
- `figures/traceplots_pub/traceplots_variant_comp1.png`
- `figures/trace_hist_panels/trace_hist_variant_comp0.png`
- `figures/trace_hist_panels/trace_hist_variant_comp1.png`
- `figures/ess_msjd_variant_panels/ess_msjd_mean_variant.png`
- `figures/ess_msjd_variant_panels/ess_msjd_components_variant.png`
- `figures/ess_msjd_variant_panels/runtime_variant.png`
- `tables/cross_m_metrics_summary.json`
- `tables/cross_m_ess_table.tex`
- `tables/cross_m_msjd_table.tex`
- `figures/cross_m/cross_m_ess_grouped.png`
- `figures/cross_m/cross_m_msjd_grouped.png`
- report manifest JSON/markdown

## Reuse and non-rerun policy
- Uniform transition-matrix chains previously produced in `polar_twist_mcmc_comparison` must not be rerun by default.
- This experiment reuses those chains when available and only generates uniform locally when `run_uniform_if_missing=True`.

## Policy alignment
This experiment follows:
- `instructions/run/outputs.md`
- `instructions/run/jobs.md`
- `instructions/run/parallelization.md`
- `instructions/run/checkpoints.md`
- `instructions/diagnostics/diagnostics.md`
- `instructions/plotting/plot_policy.md`
