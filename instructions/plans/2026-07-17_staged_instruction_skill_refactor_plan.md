# Staged Plan: Instructions, Skills, and Solute-Transport Rename

Date: 2026-07-17
Scope: instruction reorganization, skill implementation, experiment refactor, naming migration
Status: stages 0, 1, 2, 3, 4, and 5 implemented

## Hard Constraints (must hold in all stages)

1. Do not read any file under `notebooks/`.
2. Do not modify `.npz` chain contents.
3. Do not delete `.npz` files.
4. `.npz` files may only be renamed/moved if necessary for naming consistency.
5. Keep the `src/<repo>/problems` design: experiments must construct/import problem objects from `src/mess/problems`.
6. Any instruction updates must be reflected in affected instruction files.
7. If a user request contradicts existing instructions, the agent must ask for confirmation before applying the contradictory change.

## Stage 0: Safety + Baseline Inventory

Goal: establish safe migration boundaries before edits.

Actions:
- Inventory instruction files under `instructions/` and classify as:
  - general policy
  - run execution policy
  - diagnostics/plotting policy
  - experiment-specific
  - historical/archive notes
- Inventory non-notebook references to old naming (`advection_diffusion`, `AD_toy`) in:
  - `src/`
  - `jobs/`
  - `instructions/`
  - top-level docs/config
- Identify `.npz` locations potentially affected by path renames; mark move-only policy.

Deliverables:
- Classification table in this plan file (append section `Stage 0 findings`).
- Candidate rename map (path old -> new) for code/docs/jobs only.

Approval gate:
- Confirm stage-0 inventory and rename map before any structural edits.

## Stage 1: Instructions Folder Restructure (No code refactor yet)

Goal: reorganize `instructions/` into clearer policy + experiment structure.

Actions:
- Split `instructions/run_policy.md` into:
  - `instructions/run/outputs.md`
  - `instructions/run/jobs.md`
  - `instructions/run/parallelization.md`
  - `instructions/run/checkpoints.md`
- Move/rename:
  - `instructions/plot_policy.md` -> `instructions/plotting/plot_policy.md`
  - `instructions/diagnostics.md` -> `instructions/diagnostics/diagnostics.md`
- Generalize diagnostics text to all algorithms (MESS/ESS/MH/pCN/mpCN + future), preserving valid method-agnostic formulas.
- Move experiment-specific docs into `instructions/experiments/` and rename solute-transport-only files accordingly.
- Keep historical migration notes under `instructions/experiments/archive/`.

Deliverables:
- New folder structure under `instructions/`.
- Updated generalized diagnostics policy.
- Renamed solute-transport-specific instruction files.

Approval gate:
- Review and approve the reorganized instruction hierarchy and document naming.

## Stage 2: AGENT Instructions Normalization

Goal: convert `instructions/AGENT.md` into stable agent behavior rules only.

Actions:
- Rewrite `instructions/AGENT.md` to remove task/todo content.
- Include explicit evergreen rules:
  - update affected instruction files whenever user updates repo instructions
  - ask user for confirmation when request conflicts with existing instructions
  - never read `notebooks/` unless explicitly instructed
  - keep implementations concise/reproducible
  - follow run/output/diagnostics/plot policies
  - use `src/mess/problems` for problem definitions
- Add pointer to `.skills/` workflows for on-demand operational tasks.

Deliverables:
- Clean, policy-only `instructions/AGENT.md`.

Approval gate:
- Approve final AGENT behavior text before proceeding to code renames.

## Stage 3: Create Reusable Source Template Docs

Goal: document a portable source architecture for this repo and other repos.

Actions:
- Create `instructions/src.md` describing:
  - `src/<repo>/problems/`
  - `src/<repo>/experiments/<experiment_name>/`
  - `src/<repo>/experiments/common/`
  - interactions with `jobs/`, `estimations/`, `reports/`
  - data_id/run_id conventions and execution/report artifacts
- Create experiment instruction file:
  - `instructions/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn.md`

Deliverables:
- New `src.md` template-quality document.
- New experiment-specific instruction spec.

Approval gate:
- Approve template and experiment spec before code refactor.

## Stage 4: Internal Refactor of Dim-Sweep Experiment (Simplify, preserve behavior)

Goal: reduce complexity and duplication before broader rename migration.

Actions:
- Refactor experiment internals to stable helper modules (within experiment package):
  - chain/path naming helpers
  - task construction/missing detection
  - shared draws/problem factory helpers
- Replace ambiguous phase orchestration naming with explicit workflow naming:
  - run workflow
  - compute-metrics workflow
  - report workflow
- Remove duplicated chain filename/path logic from multiple modules.
- Remove report-generation dependence on private helpers in `run_chains.py` by exposing clean helper surfaces.
- Keep algorithm behavior and outputs functionally equivalent.

Deliverables:
- Cleaner module boundaries in experiment package.
- No reliance on private underscore helpers across module boundaries.

Approval gate:
- Approve refactor diff before naming migration.

## Stage 5: Rename Migration to Solute Transport (Code + Jobs + Docs)

Goal: align naming with `solute_transport` across maintained source surfaces.

Actions:
- Rename experiment package directory and imports from advection-diffusion naming to solute-transport naming.
- Rename problem/data modules and exported symbols to solute-transport naming.
- Rename job folder and wrapper imports/descriptions.
- Update instruction/doc references outside notebooks.
- Preserve old generated outputs; move/rename only where necessary, never delete `.npz`.

Deliverables:
- Source and jobs use solute-transport naming.
- Instruction files and references updated accordingly.

Approval gate:
- Approve rename impact summary and compatibility notes.

## Stage 6: Skills Implementation Under `.skills/` (in progress)

Goal: implement requested workflow skills in repo-root `.skills`.

Actions:
- Create:
  - `.skills/create-experiment/SKILL.md`
  - `.skills/execute-experiment-run-chains/SKILL.md`
  - `.skills/execute-experiment-compute-metrics/SKILL.md`
  - `.skills/execute-experiment-produce-reports/SKILL.md`
- Defer by user request:
  - `.skills/plot-slices/SKILL.md`
- Ensure each skill reflects current instructions and policy split.
- Ensure plot-slices explicitly follows plotting policy and ESS/MESS ellipse/slice rendering intent.

Deliverables:
- Four callable skill definitions in `.skills/` for create/run/metrics/reports.
- `plot-slices` skill intentionally deferred until requested.

Approval gate:
- Approve skill wording and trigger descriptions.

## Stage 7: Verification and Final Consistency Pass

Goal: verify migration without violating constraints.

Actions:
- Non-notebook search for stale naming in maintained code/docs/jobs.
- Import/compile checks for renamed modules.
- Dry-run execution checks for renamed job and experiment entrypoints.
- Validate instruction cross-links and AGENT policy consistency.
- Confirm no `.npz` content edits/deletions occurred.

Deliverables:
- Verification summary with remaining known exceptions (if any).

Approval gate:
- Final sign-off.

## Proposed Execution Order

1. Stage 0
2. Stage 1
3. Stage 2
4. Stage 3
5. Stage 4
6. Stage 5
7. Stage 6
8. Stage 7

## Notes on Contradictions Policy

This plan will enforce the following in AGENT/instructions text:
- If a new user instruction conflicts with an existing instruction file, pause and request confirmation before applying the conflicting change.
- Once confirmed, update the affected instruction file(s) in the same workstream so guidance remains current.

## Stage 0 findings (completed)

### Instructions classification

- General policy:
  - `instructions/AGENT.md`
- Run execution policy:
  - `instructions/run_policy.md` (now index)
- Diagnostics/plotting policy:
  - `instructions/diagnostics/diagnostics.md`
  - `instructions/plotting/plot_policy.md`
- Experiment-specific docs:
  - `instructions/experiments/solute_transport_convergence.md`
  - `instructions/experiments/solute_transport_observables_structured_sparse_antisymmetric_A.md`
- Historical/archive notes:
  - `instructions/experiments/archive/2026-07-16_notebook11_advection_diffusion_script_migration_phase1.md`
  - `instructions/experiments/archive/2026-07-16_notebook11_advection_diffusion_script_migration_phase2.md`

### Non-notebook legacy naming inventory summary

- `src/`: legacy names appear in experiment package path, imports, dataset identifiers, and problem/data module names.
- `jobs/`: legacy names appear in job folder and wrapper imports; numerous legacy references also exist in job logs.
- `instructions/`: legacy names appear mostly in archived migration notes and prior plan text.
- top-level docs/config searched: no relevant legacy-name hits in current scan set.

### Candidate rename map (code/docs/jobs surfaces)

- `src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn`
  -> `src/mess/experiments/solute_transport_dim_sweep_shared_draws_pcn_mpcn`
- `src/mess/problems/advection_diffusion.py`
  -> `src/mess/problems/solute_transport.py`
- `src/mess/data/advection_diffusion.py`
  -> `src/mess/data/solute_transport.py`
- `jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn`
  -> `jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn`

### `.npz` safety boundaries

- No `.npz` contents will be edited.
- No `.npz` files will be deleted.
- If naming migration requires consistency moves, `.npz` artifacts can be moved/renamed only.
