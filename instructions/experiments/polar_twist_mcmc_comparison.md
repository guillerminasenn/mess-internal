# Experiment Spec: polar_twist_mcmc_comparison

Date: 2026-07-18
Status: stage-1 specification (scaffold only)

## Objective
Create a script-first MCMC comparison experiment for the 2D polar-twist likelihood problem, comparing mPCN, pCN, MESS, and MH over shared canonical settings, with EP baselines added as the final stage.

## Scope and Non-Goals
In scope:
- script/job workflow under `src/mess/experiments/polar_twist_mcmc_comparison/` and `jobs/polar_twist_mcmc_comparison/`
- deterministic data generation and run identifiers
- run, metrics, and report workflows
- EP pCN and EP ESS baselines as final stage

Out of scope:
- mTPCN
- notebook-driven execution as the primary experiment pipeline

## Canonical Configuration (fixed)
Data/problem settings:
- `alpha = 2`
- `sigma_noise = 1.0`
- `prior_std = 2.0`
- `prior_cov = (prior_std**2) * [[1.0, 0.3], [0.3, 0.5]]`
- `prior_mean = [0.0, 0.0]`
- `weight_x = 1.0`
- `weight_y = 1.0`
- `data_seed = 202`

Sweep settings:
- `P_list = [2, 5, 10, 20, 50]`
- `rho_list = np.arange(0.0, 1.0001, 0.025)`
- `M_list = [1, 2, 5, 10, 20, 50]`

Method matrix:
- mPCN over `(P, rho)`
- pCN over matching `rho`
- MESS over `M`
- MH baseline with prior-covariance proposal and tuned scalar step targeting 23.4% acceptance

EP stage requirements (final stage only):
- EP pCN and EP ESS (ESS as MESS with `M=1`)
- group size equals `P`
- `B=20` replicate groups for EP pCN and EP ESS
- compare against `B=20` MESS(M) and `B=20` mPCN(P) chains
- initialize replicate comparisons with aligned prior-draw starts as specified in the staged plan

## Required Metrics
For each comparable method/sweep cell:
- ESS for `x1`, `x2`, and mean across both
- MSJD for `x1`, `x2`, and mean across both
- acceptance/rejection summaries where applicable
- runtime summaries

## Deterministic IDs and Paths
`data_id` requirements:
- computed from stable data-generation payload only
- excludes algorithm/runtime toggles

`run_id` requirements:
- computed from algorithm and execution payloads
- deterministic under stable sorted payload serialization

Run layout must follow:
- `estimations/<dataset>/<data_id>/<sweep|fixed>/<run_id>/...`
- `reports/<dataset>/<data_id>/<sweep|fixed>/<run_id>/...`

## Execution Entrypoints (to be implemented in later stages)
Experiment package entrypoints:
- `run_chains.py`
- `run_workflow.py`
- `compute_metrics.py`
- `compute_metrics_workflow.py`
- `report_workflow.py`

Report module entrypoints:
- `visual_checks.py`
- `traceplots.py`
- `panels.py`
- `ess_msjd_plots.py`
- `mess_ess_vs_m_plots.py`
- `rejection_plots.py`
- `pairplots.py`
- `report_parity_checklist.py`

Job wrapper entrypoint:
- `jobs/polar_twist_mcmc_comparison/run.py`

## Artifacts Expectations
Estimations artifacts:
- chain files and run metadata
- config snapshots and run manifests
- optional MESS historical playback trace sidecars for selected iterations

Reports artifacts:
- diagnostics tables (ESS/MSJD, runtime, acceptance)
- figures mirroring the target report workflow style where meaningful for fixed d=2
- MESS-only ESS-vs-M figures under `figures/ess_msjd_vs_rho/`:
	- `mess_ess_vs_M_raw.png`
	- `mess_ess_vs_M_per_energy_lik_eval.png` (when exact sub-iteration counts are available)
	- `mess_ess_vs_M_per_parallel_lik_step.png` (when exact sub-iteration counts are available)
	- `mess_ess_vs_M_availability.json` availability manifest
- parity checklist manifests
- MESS ellipse playback figures when trace sidecars are present

Storage rule for non-significant artifacts:
- Availability/runtime/metrics JSON artifacts should be written under `estimations/.../<run_id>/`.
- `reports/.../<run_id>/` should be materialized lazily when significant report outputs are written (figures or `tables/*.tex`).

## MESS Ellipse Diagnostics (Exact Playback)

Goal:
- Support exact historical ellipse playback for selected MESS iterations.

Capture rules:
- Enable capture via experiment config controls.
- Capture only targeted iteration sets and/or contiguous windows.
- Persist trace sidecars alongside MESS chain artifacts.

Rendering rules:
- Report workflow loads sidecar traces and generates:
	- contiguous ellipse overlays
	- interval-level proposal/acceptance panels

Reproducibility:
- Playback plots must reflect exact historical MESS proposals from the original run, not approximate local replay.

## Policy Alignment
- Keep problem definitions in `src/mess/problems/`.
- Do not modify or delete `.npz` contents.
- Do not run experiments primarily from notebooks.
- Any implementation-stage policy changes must update `instructions/` in the same workstream.

## Identical-rerun replacement rule
- For statistically identical reruns (same data/problem/algorithm seeds and parameters), reuse the same deterministic `run_id` directory.
- If rerunning only to enrich chain artifacts (for example adding `mess_subiters_per_iter`), replacing existing chains in-place is allowed and preferred over creating a new run directory.
