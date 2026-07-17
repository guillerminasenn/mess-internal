---
name: execute-experiment-run-chains
description: Run the chain-generation phase for solute_transport_dim_sweep_shared_draws_pcn_mpcn, usually through jobs sharding or run_workflow dry-runs.
---

# Execute Experiment: Run Chains

Use this skill when the user asks to run (or dry-run) chain generation for the solute transport dim sweep experiment.

## Experiment target
- Package: `mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn`
- Job wrapper: `jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py`

## Defaults
- Prefer job wrapper for worker/grid execution.
- Use `--dry-run` first unless user explicitly requests full execution.
- Keep `grid-count` and `grid-index` explicit for reproducibility.

## Commands
- Dry-run worker shard:
  - `source .venv-mess/bin/activate && python jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py --dry-run --grid-count <N> --grid-index <I>`
- Full worker shard:
  - `source .venv-mess/bin/activate && python jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py --grid-count <N> --grid-index <I>`
- Direct workflow dry-run:
  - `source .venv-mess/bin/activate && python -m mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.run_workflow --dry-run --grid-count <N> --grid-index <I>`

## Validation expectations
- Output includes missing/assigned task counts.
- Run summary prints estimations/reports/legacy output directories.
- Run manifest files are generated under reports manifests directory.

## Safety
- Never modify `.npz` content.
- Never delete `.npz` files.
- Do not read notebooks unless explicitly requested.

## Example invocation
```text
Use execute-experiment-run-chains to dry-run worker 0/2 for the
solute transport dim sweep experiment and summarize assigned tasks.
```
