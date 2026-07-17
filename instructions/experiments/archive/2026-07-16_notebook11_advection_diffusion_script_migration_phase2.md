# Notebook 11 AD Sweep Migration - Phase 2

Date: 2026-07-16
Notebook source: notebooks/jcgs-notebooks/11_advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.ipynb

## Goal
Migrate plotting and publication-figure sections from notebook to reusable script modules, with orchestration and a parity checklist.

## Scope (Phase 2)
- Visual checks module (A/theta/y figures)
- Traceplots module (publication trace grids)
- Trace-hist panel module
- ESS/MSJD plotting module
- Pairplots module
- Phase-2 orchestration script
- Notebook parity checklist output (markdown + JSON)
- Cross-experiment reusable plotting/checklist helpers in common modules

## Implemented Files
- src/mess/experiments/common/plotting_utils.py
- src/mess/experiments/common/checklist.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/phase2_helpers.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/visual_checks.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/traceplots.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/panels.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/ess_msjd_plots.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/pairplots.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/phase2_parity_checklist.py
- src/mess/experiments/advection_diffusion_dim_sweep_shared_draws_pcn_mpcn/phase2_all.py

## Entry Points
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.visual_checks
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.traceplots
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.panels
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.pairplots
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_parity_checklist
- python -m mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_all

## Notes
- Figure outputs are written to reports/advection_diffusion/<data_id>/sweep/<run_id>/figures/...
- Parity checklist is written to reports/advection_diffusion/<data_id>/sweep/<run_id>/manifests/phase2_notebook_parity_checklist.*
- ESS/MSJD plotting auto-triggers metrics_summary generation if missing.
- Full metrics generation may be slow depending on chain size.
