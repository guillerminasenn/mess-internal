---
name: execute-experiment-run-chains
description: Run the chain-generation phase for an experiment in src/<repo>/experiments by resolving entrypoints from instructions/experiments.
---

# Execute Experiment: Run Chains

Use this skill when the user asks to run (or dry-run) chain generation for any experiment.

## Stage-separation rule
- This skill is execution-only.
- Do not create or refactor experiment modules here; use `create-experiment` for implementation changes.
- If required run entrypoints are missing, stop and request implementation via `create-experiment` first.

## Resolve target experiment
1. Determine `<experiment>` from the user request.
2. Read `instructions/experiments/<experiment>.md`.
3. Resolve package path as `<repo>.experiments.<experiment>`.
4. Prefer job wrapper `jobs/<experiment>/run.py` when present.

## Defaults
- Prefer job wrapper for worker/grid execution.
- Use `--dry-run` first unless user explicitly requests full execution.
- Keep `grid-count` and `grid-index` explicit for reproducibility.
- When normalized MESS ESS-vs-M reporting is expected, ensure generated MESS chains include persisted `mess_subiters_per_iter`.
- For statistically identical reruns that only enrich stored diagnostics, prefer in-place replacement under the same `run_id` directory (for example via `--replace-existing-identical` when supported).

## Environment placeholder
- `<activate_env_command>` means the repository-specific environment activation command
  (for example `source .venv/bin/activate` or equivalent for the active workspace).

## Generic commands
- Dry-run worker shard:
  - `<activate_env_command> && python jobs/<experiment>/run.py --dry-run --grid-count <N> --grid-index <I>`
- Full worker shard:
  - `<activate_env_command> && python jobs/<experiment>/run.py --grid-count <N> --grid-index <I>`
- Direct workflow dry-run:
  - `<activate_env_command> && python -m <repo>.experiments.<experiment>.run_workflow --dry-run --grid-count <N> --grid-index <I>`

## Conditional execution (if/else)
- If `instructions/experiments/<experiment>.md` declares a run-workflow entrypoint:
  - Run that declared entrypoint first.
- Else if `jobs/<experiment>/run.py` exists:
  - Use the job wrapper as primary entrypoint.
- Else:
  - Try `python -m <repo>.experiments.<experiment>.run_chains`.

- If `<experiment>` is `solute_transport_dim_sweep_shared_draws_pcn_mpcn`:
  - Prefer `jobs/solute_transport_dim_sweep_shared_draws_pcn_mpcn/run.py` for sharded runs.
  - Alternative dry-run path is `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.run_workflow --dry-run ...`.
- Else:
  - Follow the run entrypoints listed in `instructions/experiments/<experiment>.md`.

## Validation expectations
- Output includes missing/assigned task counts.
- Run summary prints estimations/reports/legacy output directories.
- Run manifest files are generated under reports manifests directory.
- For EP grouped-chain experiments, validate task cardinality by M:
  - MESS tasks: `B` chains per `M`.
  - EP tasks: `B * M` chains per `M`.
  - If start-point coupling is required by spec, verify diagnostics include persisted start points and the replicate-aligned first EP chain starts.

## EP grouped-chain branch
- If `<experiment>` uses EP independent-chain groups (for example `polar_twist_ep`):
  - Run a dry-run first and report expected counts for `mess` and `ep_ess` tasks separately.
  - Keep `grid-count` and `grid-index` explicit.
  - Confirm chain metadata includes `variant`, `M`, `replicate`, and `chain_idx` so metrics can reconstruct groups.

## Safety
- Never modify `.npz` content.
- Never delete `.npz` files.
- Do not read notebooks unless explicitly requested.

## Example invocation
```text
Use execute-experiment-run-chains for <experiment>; resolve the run entrypoint
from instructions/experiments/<experiment>.md, do a dry-run shard 0/2,
and summarize assigned tasks and output directories.
```
