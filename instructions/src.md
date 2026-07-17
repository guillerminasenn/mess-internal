# Source Layout Template (`src/<repo>`)

This document defines the recommended source layout for experiments in this repository and can be reused as a template in other repositories.

## Core structure
- `src/<repo>/problems/`: canonical definitions of Bayesian inverse problems (forward model, prior, likelihood, helper transforms).
- `src/<repo>/experiments/common/`: shared experiment infrastructure (run layout, artifact manifests, plotting/checklist helpers, path resolution).
- `src/<repo>/experiments/<experiment_name>/`: experiment-specific orchestration, metrics, and plotting/report scripts.

## Design rule: problem/experiment separation
- Problem definitions must live in `src/<repo>/problems/`.
- Experiment modules must import and instantiate problem objects from `src/<repo>/problems/`.
- Do not duplicate problem model definitions inside experiment scripts.

## Standard experiment package shape
Recommended files under `src/<repo>/experiments/<experiment_name>/`:
- `config.py`: dataclass + payload builders for data config, algorithm config, execution config.
- `run_chains.py`: chain generation/orchestration entrypoint.
- `compute_metrics.py`: post-chain metric computation.
- `report_availability.py`: checks expected vs available chain artifacts.
- `phase*_all.py`: optional phase orchestrators for grouped workflows.
- `*_plots.py` / `visual_checks.py`: report figure generation modules.

## Interaction with `problems/`
Typical pattern:
1. Build deterministic data/shared draws from config.
2. Select dimension/observation/parameter subsets for a run slice.
3. Construct problem object from `src/<repo>/problems/*`.
4. Pass that problem object to algorithm runners.

## Interaction with `estimations/` and `reports/`
Use deterministic run layout:
- `estimations/<dataset>/<data_id>/<sweep|fixed>/<run_id>/...`
- `reports/<dataset>/<data_id>/<sweep|fixed>/<run_id>/...`

`data_id` should encode only stable data-generation settings.
`run_id` should encode algorithm/statistical settings.

Within each run:
- `estimations/`: chains, diagnostics payloads, metrics payloads, config snapshots.
- `reports/`: figures, tables, manifests, parity/checklist outputs.

## Interaction with `jobs/`
Job wrappers should live under:
- `jobs/<dataset>/<run_id>_data_<data_id>/run.py`

Wrapper responsibilities:
- parse CLI args (grid sharding, dry-run flags)
- build/override experiment config
- call `src/<repo>/experiments/<experiment_name>/run_chains.py` (or orchestrator)

## Portability rules for template reuse
- Resolve repository root from environment override or `pyproject.toml` walk-up.
- Keep all paths repository-relative; do not hardcode machine-specific absolute paths.
- Keep naming deterministic and hash-based for reproducibility and cache safety.
