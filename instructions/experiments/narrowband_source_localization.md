# Experiment: narrowband_source_localization

## Objective
Implement and evaluate a 2D whitened Bayesian inverse problem for narrowband wave-source localization with analytically marginalized complex source amplitude/phase. The model and workflow are implemented in script-first form with deterministic data generation and reproducible run layout.

The full scientific specification is archived at:
- instructions/experiments/archive/source_localization.md

## Source modules
- Problem module:
  - src/mess/problems/narrowband_source_localization.py
- Experiment package:
  - src/mess/experiments/narrowband_source_localization/config.py
  - src/mess/experiments/narrowband_source_localization/run_chains.py
  - src/mess/experiments/narrowband_source_localization/compute_metrics.py
  - src/mess/experiments/narrowband_source_localization/run_workflow.py
  - src/mess/experiments/narrowband_source_localization/compute_metrics_workflow.py
  - src/mess/experiments/narrowband_source_localization/report_workflow.py
  - src/mess/experiments/narrowband_source_localization/report_availability.py
- Job wrapper:
  - jobs/narrowband_source_localization/run.py

## Deterministic run layout
Uses the shared run-layout helpers in src/mess/experiments/common/run_layout.py.

- data_id hash input: data-generation configuration from ExperimentConfig.data_config()
- run_id hash input: algorithm/sampler configuration from ExperimentConfig.algorithm_config()
- estimations root:
  - estimations/narrowband_source_localization/<data_id>/fixed/<run_id>/
- reports root:
  - reports/narrowband_source_localization/<data_id>/fixed/<run_id>/

## Execution entrypoints
Run stage (chains):
- python -m mess.experiments.narrowband_source_localization.run_chains --grid-count 1 --grid-index 0
- or wrapper:
  - python jobs/narrowband_source_localization/run.py --grid-count 1 --grid-index 0

Run workflow wrapper:
- python -m mess.experiments.narrowband_source_localization.run_workflow --grid-count 1 --grid-index 0

Metrics stage:
- python -m mess.experiments.narrowband_source_localization.compute_metrics
- python -m mess.experiments.narrowband_source_localization.compute_metrics_workflow

Report stage:
- python -m mess.experiments.narrowband_source_localization.report_workflow

Ellipse diagnostics:
- python -m mess.experiments.narrowband_source_localization.mess_ellipse_diagnostics --start-iter 200 --n-iters 3 --variant uniform --M-list 1,2,5,10

## Artifacts
Expected run artifacts include:
- data_and_latent.npz
- data_manifest.json
- diagnostics/start_points.npz
- chain_*.npz files for MESS, EP-ESS, and MPCN
- worker_<grid_index>_runs.json
- optional geometry_worker_<grid_index>.json from trace-enabled MESS diagnostics

Expected metrics/report artifacts include:
- diagnostics/availability_report.json
- tables/metrics_per_chain.json
- tables/metrics_per_replicate.json
- tables/metrics_summary.json
- reports/.../summary.md

## Notes
- Problem state is whitened z in R^2. Physical location q is recovered by q = mu_q + L_q z.
- Unknown complex source amplitude is integrated out analytically in the likelihood.
- Baseline amplitude model is phase_only; spherical_spreading is available as an ablation setting.
- Stage separation: this implementation file set does not execute chains or plotting by default.
