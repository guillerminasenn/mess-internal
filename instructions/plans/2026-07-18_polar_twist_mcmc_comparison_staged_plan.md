# Staged Plan: Polar Twist MCMC Comparison Script Experiment

Date: 2026-07-18
Scope: script-first experiment setup for polar_twist_mcmc_comparison, instruction clarity updates, workflow parity, EP baseline final stage
Status: planned (no implementation yet)

## Hard Constraints (must hold in all stages)

1. Do not execute experiment pipelines from notebooks.
2. Notebook files may be read only when explicitly authorized by the user for configuration parity.
3. Do not modify `.npz` chain contents.
4. Do not delete `.npz` files.
5. Keep problem definitions under `src/mess/problems`; experiments must construct/import problem objects from there.
6. Keep run outputs policy-compliant under `estimations/<dataset>/<data_id>/<sweep|fixed>/<run_id>/` and reports under `reports/<dataset>/<data_id>/<sweep|fixed>/<run_id>/`.
7. Any policy/design change introduced during implementation must be reflected in instruction files in the same workstream.
8. If an implementation decision conflicts with existing instructions, pause and resolve in instructions before proceeding.

## Canonical Experiment Decisions (fixed before implementation)

1. Experiment package name: `polar_twist_mcmc_comparison`.
2. Data-generation preset (from notebook parity):
   - `alpha=2`
   - `sigma_noise=1.0`
   - `prior_std=2.0`
   - `prior_cov=(prior_std^2)*[[1.0, 0.3], [0.3, 0.5]]`
   - `prior_mean=[0.0, 0.0]`
   - `weight_x=1.0`, `weight_y=1.0`
   - `data_seed=202`
3. Main sweeps:
   - `P_list=[2, 5, 10, 20, 50]`
   - `rho_list=np.arange(0.0, 1.0001, 0.025)`
   - `M_list=[1, 2, 5, 10, 20, 50]`
4. Methods in scope:
   - mPCN with varying `P` and `rho`
   - pCN with matching `rho` values
   - MESS with `M in {1,2,5,10,20,50}`
   - MH baseline (prior-covariance proposal, scalar step tuned toward 23.4% acceptance)
5. Explicitly out of scope: mTPCN.
6. EP stage must be last major stage:
   - embarrassingly-parallel pCN
   - embarrassingly-parallel ESS (MESS with `M=1`)
   - EP group size equals `P` for direct comparison with `mPCN(P)`
   - do `B=20` replicates of EP-PCN with group size `P`, similarly for MESS, and compare against `B=20` MESS(M) chains and `B=20` MPCN(P) chains. 
   - The `B=20` MESS(M) and MPCN(P) chains should be started from the same B random prior samples, and each first chain of the `P` or `M` sized group of EP chains should have the first chain starting from one of this B random prior samples, for the B replicates.
7. Metrics required for reporting and comparison:
   - ESS for `x1`, `x2`, and mean across both
   - MSJD for `x1`, `x2`, and mean across both

## Stage 0: Instruction and Policy Clarification

Goal: ensure instruction docs explicitly support script/job/report structure and notebook-avoidance policy for experiments.

Actions:
- Update `instructions/AGENT.md` to explicitly state:
  - experiment execution is script-first
  - notebook experiments are not the default execution path
  - instruction files must be updated when policy/design changes
- Update `instructions/src.md` to clearly document:
  - expected structure for new experiment packages
  - responsibilities of experiment modules vs job wrappers
  - symmetry between `estimations/` and `reports/` artifact roots

Deliverables:
- Updated `instructions/AGENT.md` policy text.
- Updated `instructions/src.md` structure guidance.

Approval gate:
- Confirm updated instruction wording before adding new experiment code.

## Stage 1: Experiment Spec File and Directory Skeleton

Goal: create the experiment instruction spec and skeleton paths before implementation details.

Actions:
- Create `instructions/experiments/polar_twist_mcmc_comparison.md` with:
  - canonical constants
  - sweep definitions
  - method matrix and exclusions
  - run outputs and report outputs expectations
  - reproducibility/hash ID requirements
- Create package skeleton:
  - `src/mess/experiments/polar_twist_mcmc_comparison/`
  - `jobs/polar_twist_mcmc_comparison/`

Deliverables:
- New experiment instruction spec.
- Empty-but-structured package/job directories ready for staged implementation.

Approval gate:
- Confirm spec completeness and naming before coding internals.

## Stage 2: Problem Module and Config Context

Goal: establish deterministic problem/data construction and run context.

Actions:
- Add `src/mess/problems/polar_twist.py` with:
  - forward map and custom likelihood definitions
  - Gaussian-prior compatible problem wrapper
  - deterministic synthetic data builder from canonical config
- Add experiment config/context modules:
  - `config.py` for `ExperimentConfig`
  - deterministic `data_id` and `run_id` payload hashing
  - path context via common run-layout helpers

Deliverables:
- Reusable polar-twist problem module.
- Deterministic config/context plumbing for all later workflows.

Approval gate:
- Validate config parity against canonical notebook settings and deterministic ID fields.

## Stage 3: Chain Generation Workflow Implementation (Core Methods)

Goal: implement chain-generation scripts and shardable entrypoints for mPCN, pCN, MESS, and MH.

Actions:
- Implement naming/task modules:
  - `naming.py`, `tasks.py`
- Implement chain run modules:
  - `run_chains.py`
  - `run_workflow.py`
- Add method adapters for:
  - mPCN over `(P, rho)` grid
  - pCN over `rho` grid
  - MESS over `M` grid
  - MH with tuned scalar step and persisted tuning metadata
- Add job wrappers:
  - `jobs/polar_twist_mcmc_comparison/run.py`
  - `jobs/polar_twist_mcmc_comparison/launch_workers.sh`

Deliverables:
- Worker-shard execution path and run manifests implemented in code.
- No chain execution in this stage unless explicitly requested.

Approval gate:
- Module/API review and dry-run command readiness approved.

## Stage 3.5: Chain Execution (separate skill stage)

Goal: execute or dry-run Stage 3 entrypoints without additional implementation changes.

Actions:
- Use run-chains skill to execute `jobs/polar_twist_mcmc_comparison/run.py` (dry-run first).
- Validate assigned task counts, output roots, and manifests.

Deliverables:
- Chain artifacts under `estimations/` and run manifests under `reports/.../manifests/`.

Approval gate:
- Execution logs and artifact inventory approved before metrics stage.

## Stage 4: Metrics and Diagnostics Workflow

Goal: produce consistent ESS/MSJD and acceptance diagnostics for method comparison.

Actions:
- Implement:
  - `report_availability.py`
  - `benchmark_runtime.py`
  - `compute_metrics.py`
  - `compute_metrics_workflow.py`
- Compute and store, at minimum:
  - ESS (`x1`, `x2`, mean)
  - MSJD (`x1`, `x2`, mean)
  - acceptance/rejection summaries
  - runtime summaries
- Emit diagnostics/tables/manifests under `reports/` according to policy.

Deliverables:
- Reproducible metrics tables and diagnostic manifests.

Approval gate:
- Confirm metric definitions and aggregation semantics match diagnostics policy.

## Stage 5: Report Workflow Parity (Core, Non-EP)

Goal: mirror report module breadth from the solute transport dim-sweep experiment where meaningful for fixed dimension 2.

Actions:
- Implement report helper and plot modules:
  - `report_helpers.py`
  - `visual_checks.py`
  - `traceplots.py`
  - `panels.py`
  - `ess_msjd_plots.py`
  - `rejection_plots.py`
  - `pairplots.py`
  - `report_parity_checklist.py`
  - `report_workflow.py`
- Ensure plot/table output structure is policy-compliant and includes parity checklist artifacts.
- Keep scope to main rho grid only (no additional edge-rho stage).

Deliverables:
- Full core report workflow output under `reports/.../sweep/<run_id>/`.
- Parity checklist markdown/json manifests.

Approval gate:
- Review visual/table parity against target experiment style.

## Stage 6: EP Baselines (Final Stage)

Goal: add embarrassingly-parallel baselines as the final comparison layer.

Actions:
- Add EP pCN and EP ESS generation logic (ESS implemented as MESS with `M=1`).
- Enforce EP group size `= P` for each corresponding comparison arm.
- Integrate EP baselines into metrics tables and report figures alongside `mPCN(P)`.

Deliverables:
- EP baseline artifacts and merged comparison outputs.

Approval gate:
- Confirm direct comparability of EP vs mPCN(P) in final figures/tables.

## Stage 7: Verification, Reproducibility, and Handoff

Goal: finish with a complete verification pass and implementation-ready checklist.

Actions:
- Compile/import validation on new problem + experiment package.
- Dry-run worker checks (`--dry-run`, shard accounting).
- Smoke-run checks with reduced iterations.
- Metrics workflow and report workflow end-to-end checks.
- Verify required manifests/checklists are produced.
- Confirm instruction cross-links and output path compliance.

Deliverables:
- Verification summary with pass/fail checklist and any residual risks.

Approval gate:
- Final sign-off for stage-by-stage self-implementation.

## Addendum: Historical MESS Ellipse Playback

As of 2026-07-20, exact historical MESS ellipse playback is tracked in:
- `instructions/plans/2026-07-20_mess_ellipse_historical_playback_staged_plan.md`

Key decision:
- Ellipse diagnostics must use exact historical trace sidecars captured during chain generation when reproducibility is required.

## Proposed Execution Order

1. Stage 0
2. Stage 1
3. Stage 2
4. Stage 3
5. Stage 4
6. Stage 5
7. Stage 6
8. Stage 7

## Stage Dependencies and Parallelism Notes

1. Stages 0 and 1 should complete before any code implementation.
3. Stage 2 is required before Stages 3, 3.5, 4, 5, and 6.
4. Stage 3.5 depends on Stage 3 implementation readiness.
5. Stage 4 depends on usable outputs from Stage 3.5 execution.
6. Stage 5 depends on Stage 4 outputs for summary plots/tables.
7. Stage 6 is intentionally last major implementation stage; its reporting integration can be developed in parallel with late Stage 5 polishing but finalized only after core metrics are stable.
8. Stage 7 runs after all prior stages and should include small-run reproducibility checks.

## Verification Checklist (for implementation owner)

1. Config parity: canonical constants in `ExperimentConfig` exactly match the fixed decisions above.
2. Determinism: `data_id` and `run_id` remain stable for unchanged payloads.
3. Output layout: no report/estimation artifacts outside policy-approved directories.
4. Metrics presence: ESS/MSJD for `x1`, `x2`, and mean exist for all in-scope methods.
5. Method coverage: mPCN, pCN, MESS, MH present in core stage; EP pCN and EP ESS present in final stage.
6. EP comparability: EP group size equals `P` in all EP-vs-mPCN comparisons.
7. Instruction sync: any design drift discovered during implementation is reflected in instruction docs before closeout.
