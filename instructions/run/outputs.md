# Run Outputs Policy

## Goal
Store outputs under deterministic run-specific directories so cache reuse is safe and accidental mixing of configurations is avoided.

## Required configuration hashing
- Build `data_id` from stable data-generation fields only (dataset hyperparameters, observation config, data seeds).
- Build `run_id` from algorithm/statistical configuration only (method, proposal settings, M/P/rho grids, `n_iters`, `burn_in`, sweep settings).
- Do not include execution-only settings in `run_id` unless they change statistical output.

## Required layout
- `estimations/<dataset>/<data_id>/<sweep|fixed>/<run_id>/...`
- `reports/<dataset>/<data_id>/<sweep|fixed>/<run_id>/...`

## Required artifacts
- Save full run payload to `config.json` under the estimations directory.
- Store chains, metrics, diagnostics, and derived tables under estimations.
- Store figures and manifests under reports.
- Never write outputs under `notebooks/`.

## Naming conventions
- Use the dimension-tagged chain stem `chain_d{d}_...` for sweep outputs.
- MESS chain: `chain_d{d}_mess_M{M}.npz`
- ESS chain (when represented as MESS with `M=1`): `chain_d{d}_mess_M1.npz`
- MH chain: `chain_d{d}_mh_sigma2{proposal_std}[_cov{proposal_cov}].npz`
- pCN chain: `chain_d{d}_pcn_rho{rho_tag}.npz`
- mpCN chain: `chain_d{d}_mpcn_P{P}_rho{rho_tag}.npz`
- Auxiliary data artifact (when applicable): `data_and_latent.npz`
- Worker runtime metadata artifact (when applicable): `worker_{grid_index}_runs.json`
- Metrics sidecar convention for per-chain metrics: `<chain_stem>_metrics.json`
- Keep algorithm-specific diagnostics adjacent to chain artifacts or in a dedicated diagnostics subfolder.

Notes:
- `rho_tag` uses fixed formatting with `.` replaced by `p` (for example `0.50000 -> 0p50000`).
- Prefer algorithm-specific stems (`mess_M`, `mpcn_P..._rho`, `pcn_rho`, `mh_sigma2...`) and avoid legacy/ambiguous rho tags on MESS/ESS filenames.

## Independent-chain variants
- Store independent-chain outputs in a subfolder of the base run (for example `chains/independent_chains`).
- Use stable names such as `pcn_independent_rho{rho}_seed{seed}_chain{idx}.npz`.
- Maintain an index JSON per `(algorithm, rho, seed)` listing chain files and metadata.
- Treat `P` as an aggregation count for independent chains; do not encode requested chain count into `data_id`/`run_id`.

## Variants and sub-experiments
- Secondary experiments that share base configuration should live under subfolders of the base run directory.
- Preserve base `run_id`; use subfolders for variant-specific outputs.

## Path resolution helper
When constructing paths, resolve repo root from `MULTIPROPOSAL_RUN_ROOT` or by walking up to `pyproject.toml`; do not assume `Path.cwd()` is the repo root.
