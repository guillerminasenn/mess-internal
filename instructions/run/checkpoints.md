# Checkpoint and Progress Policy

## Long-run checkpointing
- Write partial chains at a fixed interval (for example every 10,000 iterations).
- Store partial chains next to final chains with `_partial` suffix.

## Progress sidecars
- Write progress JSON sidecars containing at least:
  - `completed_iters`
  - `total_iters`
  - `timestamp`
- For independent chains, keep one progress sidecar per chain file.

## Diagnostics sidecars
- Store per-chain diagnostics and metrics in a diagnostics subfolder under the run directory (for example `diagnostics/independent_chains/`).

## Hashing rule
- Checkpoint/progress settings are execution metadata and should not be included in `run_id`.
