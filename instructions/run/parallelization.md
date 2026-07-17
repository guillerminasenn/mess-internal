# Parallelization Policy

## Principle
Parallelization is an execution concern, not a statistical configuration concern.

## Hashing rule
- Do not include execution-only parameters in `run_id` unless they alter statistical output.
- If an execution setting changes RNG/statistical behavior, treat it as an algorithmic variant.

## Backend selection
- Use threads when problem objects are not picklable.
- Use processes only when problem + inputs are serializable and process overhead is justified.

## Determinism
- Prefer deterministic collection order of worker outputs.
- Use independent RNG streams (for example `SeedSequence` spawning) for worker-level randomness.

## Proposal-level parallelization
- Keep vectorized/single-process proposal generation as default where practical.
- If enabling proposal-level parallelization, document it explicitly as a variant when it changes RNG stream behavior.

## Recommended mpCN setup
- Prefer chunked process-based likelihood evaluation.
- Keep proposal generation in main process unless benchmark evidence justifies otherwise.
- Record `backend`, `n_jobs`, and chunk parameters in run configuration metadata.
