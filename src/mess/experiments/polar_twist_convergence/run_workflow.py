"""Run workflow for polar-twist convergence (reuse existing chains)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.polar_twist_convergence.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_convergence.run_chains import run as run_chains


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    chain_summary = run_chains(
        grid_count=grid_count,
        grid_index=grid_index,
        dry_run=dry_run,
        config=cfg,
    )
    for item in chain_summary.get("artifacts", []):
        registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "run_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of run workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable run workflow artifact summary.")
    registry.print_summary()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run workflow for polar-twist convergence experiment.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Run task selection only, without chain execution.")
    args = parser.parse_args()

    run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
