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
- `run_workflow.py`: run-phase orchestrator that writes run manifests and artifact summaries.
- `compute_metrics_workflow.py`: metrics-phase orchestrator that writes diagnostics/tables/manifests.
- `report_workflow.py`: report-phase orchestrator for figures/tables/checklists.
- `report_availability.py`: checks expected vs available chain artifacts.
- `*_plots.py` / `visual_checks.py`: report figure generation modules.

## Script-first execution model
- Experiment runs should be launched from job wrappers under `jobs/<experiment>/`.
- Notebook-driven experiment execution is not the default path; notebooks may be used only for reference or explicit user-requested checks.
- Job wrappers should remain thin: parse CLI flags, build/override config, and call experiment workflow entrypoints.

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

Path symmetry requirement:
- For a given `dataset`, `data_id`, `sweep|fixed`, and `run_id`, write computational artifacts under the matching `estimations/` subtree and reporting artifacts under the matching `reports/` subtree.
- Keep config snapshots and manifests in both phases as needed so runs can be reproduced and audited from either root.
- Path symmetry does not require eager creation of `reports/.../<run_id>/`; materialize report run directories only when significant report artifacts are emitted (figures or `tables/*.tex`).

`data_id` should encode only stable data-generation settings.
`run_id` should encode algorithm/statistical settings.

Within each run:
- `estimations/`: chains, diagnostics payloads, metrics payloads, config snapshots.
- `reports/`: figures, tables, manifests, parity/checklist outputs.
- If a stage emits only non-significant JSON diagnostics/tables and no figures/LaTeX tables, keep those outputs under `estimations/` to avoid empty report runs.

## Interaction with `jobs/`
Job wrappers should live under:
- `jobs/<experiment>/run.py`

Wrapper responsibilities:
- parse CLI args (grid sharding, dry-run flags)
- build/override experiment config
- call `src/<repo>/experiments/<experiment_name>/run_chains.py` and/or workflow orchestrators

## Portability rules for template reuse
- Resolve repository root from environment override or `pyproject.toml` walk-up.
- Keep all paths repository-relative; do not hardcode machine-specific absolute paths.
- Keep naming deterministic and hash-based for reproducibility and cache safety.
