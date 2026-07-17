# Experiment Spec: solute_transport_dim_sweep_shared_draws_pcn_mpcn

## Objective
Compare chain behavior and diagnostics across problem dimensions using shared data-generating draws and multiple samplers (MESS, MH, pCN, mpCN), then generate phase-style figures/tables/manifests.

## Source package
- `src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/`

Note:
- The current source package still uses legacy advection-diffusion naming.
- Planned migration renames it to a solute-transport package while preserving behavior.

## Configuration model
Main config object: `ExperimentConfig` in `config.py`.

Key groups:
- Data generation/shared draws:
  - `seed_data`, `shared_draws_seed`, `kappa`, `sigma`, `alpha`, `gamma`, `tau2`, `a_mode`, `use_prior_A`
  - observation controls: `obs_highest_freq`, `obs_bandwidth`, `obs_config`
  - sweep dimensions: `d_list`, `d_max`
- Algorithm settings:
  - `n_iters`, `burn_in`, `thin`, `max_lag`
  - `M_list` (MESS), `P_list` (mpCN), `rho_algo`
  - MH proposal settings
- Run metadata:
  - `dataset`, `algorithm`, `sweep_mode`
  - `legacy_output_group` for backwards-compatible chain location

## Run IDs and directories
- `data_id` is hashed from data-generation payload.
- `run_id` is hashed from algorithm payload.

Run layout:
- `estimations/<dataset>/<data_id>/sweep/<run_id>/...`
- `reports/<dataset>/<data_id>/sweep/<run_id>/...`

Legacy compatibility path also exists for chain files under:
- `estimations/<legacy_output_group>/<run_tag>/...`

## Problem construction contract
- Problem objects are constructed from `src/mess/problems` helpers/classes.
- Shared draws are generated once at `d_max` and restricted for each target `d`.
- Each task uses per-dimension parameter/observation selection before sampling.

## Execution entrypoints
Phase 1:
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.run_chains`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase1_all`

Phase 2:
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.visual_checks`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.traceplots`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.panels`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.pairplots`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_parity_checklist`
- `python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_all`

Job wrapper:
- `jobs/AD_toy_dim_M_sweep_shared_draws_pcn_mpcn/run.py`

## Artifacts
Phase 1 artifacts include:
- generated chains
- chain availability diagnostics
- runtime summary table
- ESS/MSJD metrics summary table
- artifact manifests (JSON + markdown)

Phase 2 artifacts include:
- visual checks
- trace and panel figures
- ESS/MSJD diagnostic figures
- pairplots
- parity checklist outputs
- phase artifact manifests

## Caching and reuse behavior
- Existing readable chain files are skipped.
- Availability/metrics scripts consume cached chains and regenerate report artifacts.

## Policy coupling
This experiment must follow:
- `instructions/run/outputs.md`
- `instructions/run/jobs.md`
- `instructions/run/parallelization.md`
- `instructions/run/checkpoints.md`
- `instructions/diagnostics/diagnostics.md`
- `instructions/plotting/plot_policy.md`
