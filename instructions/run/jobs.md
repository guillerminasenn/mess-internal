# Job Execution Policy

## Job script placement
- Place long-running scripts under `jobs/<dataset>/<run_id>_data_<data_id>/`.
- Primary entrypoint should be `run.py`.
- Keep notebooks focused on loading cached outputs and plotting.

## Launching workers
- Launch from repo root with project launchers (for example `launch_independent_workers.sh`).
- Allow optional worker/grid arguments for reproducible sharding.
- Keep logs under `jobs/<dataset>/<run_id>_data_<data_id>/logs/`.

## Grid sharding guidance
- Prefer multiple scripts with disjoint sweep slices over nested process pools.
- Use deterministic slicing (`grid_index/grid_count`) so reruns are reproducible.
- Avoid oversubscription by clearly separating inter-job and intra-algorithm parallelism.

## Reproducible execution rules
- Record worker execution settings in `config.json` under an execution section.
- Keep deterministic worker output ordering where feasible.
- Reuse cached chains/metrics instead of rerunning existing artifacts.
