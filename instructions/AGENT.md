# AGENT Policy

This file defines always-on behavior for agents working in this repository.

## Core quality rules
- Implement reproducible experiments and deterministic run layouts.
- Keep code precise, concise, and as simple as possible without sacrificing correctness.
- Keep problem definitions in `src/<repo>/problems`; experiment code must import/instantiate problems from there.
- Execute experiment workflows from script/job entrypoints under `src/<repo>/experiments/` and `jobs/`.
- Treat notebooks as references only unless the user explicitly requests notebook execution.

## Plans
- When following staged plans for experiment work, apply strict phase separation:
	1) implement scripts/modules,
	2) run chains,
	3) compute metrics,
	4) produce plots/reports.
- Do not implement and execute in the same stage unless the user explicitly requests combined execution.
- Prefer separate skill invocations for each phase so users can approve transitions between stages.

## Always-on hard constraints
1. Do not read any file under `notebooks/` unless the user explicitly requests a specific notebook.
2. Do not modify `.npz` chain contents.
3. Do not delete `.npz` files.
4. `.npz` files may only be renamed/moved when necessary for naming consistency.
5. Keep the `src/<repo>/problems` design: experiments must construct/import problem objects from `src/<repo>/problems`.
6. Any instruction updates must be reflected in affected instruction files.
7. If a user request contradicts existing instructions, ask for user confirmation before applying the contradictory change.
8. After implementing repository changes, create a git commit and push to the remote.

## Instructions maintenance protocol
- Treat `instructions/` as the source of operational policy.
- When a user updates policy/design, update every affected instruction document in the same workstream.
- Keep experiment-specific replication docs under `instructions/experiments/`.
- Keep run/outputs/parallel/checkpoint policy under `instructions/run/`.
- Keep diagnostics and plotting policies under `instructions/diagnostics/` and `instructions/plotting/`.
- Keep experiment implementation guidance script-first: define run, metrics, and report workflows in experiment/job modules, not notebook pipelines.
- After applying changes, commit and push so repository history stays up to date.

## Run and diagnostics policy references
- `instructions/run/outputs.md`
- `instructions/run/jobs.md`
- `instructions/run/parallelization.md`
- `instructions/run/checkpoints.md`
- `instructions/diagnostics/diagnostics.md`
- `instructions/plotting/plot_policy.md`

## Skills
- Use repository skills under `.skills/` when the user asks to run those workflows.