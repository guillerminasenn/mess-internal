# Notebook 11 AD Sweep Migration - Phase 1

Date: 2026-07-16
Notebook source: notebooks/jcgs-notebooks/11_solute_transport_dim_sweep_shared_draws_pcn_mpcn.ipynb

## Goal
Migrate chain-generation and phase-1 diagnostics from notebook to reusable scripts while preserving current job execution behavior.

## Scope (Phase 1)
- Add reusable experiment modules under src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn.
- Keep job orchestration entrypoint in jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py as a thin wrapper.
- Preserve legacy chain output naming/paths for compatibility with existing outputs and worker scripts.
- Add policy-style run IDs and report directories via shared run layout helpers.
- Add phase-1 artifact reporting so scripts print what was generated and where.

## Implemented Files
- src/mess/experiments/common/run_layout.py
- src/mess/experiments/common/artifacts.py
- src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn/config.py
- src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run_chains.py
- src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn/report_availability.py
- src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn/benchmark_runtime.py
- src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn/compute_metrics.py
- src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn/phase1_all.py
- jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py

## Expected Usage
- Worker mode (existing launcher compatibility):
  - python jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py --grid-count 4 --grid-index 0
- Full phase-1 local pipeline:
  - python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.phase1_all

## Notes
- Chain filenames remain compatible with the existing runner conventions.
- New report outputs are written under reports/advection_diffusion/<data_id>/sweep/<run_id>/.
- Legacy chain outputs remain under estimations/AD_toy_dim_M_sweep_shared_draws/<run_tag>/.
- Phase 2 will migrate plotting-focused notebook sections and add figure script entrypoints.
