"""Orchestrate phase-1 execution and print artifact summary."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.benchmark_runtime import (
    run as run_benchmark,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.compute_metrics import (
    run as run_metrics,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.report_availability import (
    run as run_availability,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.run_chains import (
    run as run_chains,
)
from mess.experiments.common.artifacts import ArtifactRegistry


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg, grid_count=grid_count, grid_index=grid_index)
    registry = ArtifactRegistry()

    chain_summary = run_chains(
        grid_count=grid_count,
        grid_index=grid_index,
        dry_run=dry_run,
        config=cfg,
    )
    for item in chain_summary.get("artifacts", []):
        registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    if not dry_run:
        avail_summary = run_availability(cfg)
        runtime_summary = run_benchmark(cfg)
        metrics_summary = run_metrics(cfg)

        registry.add(
            path=Path(avail_summary["report_path"]),
            kind="diagnostics",
            description="Availability report of expected vs present chain files.",
        )
        registry.add(
            path=Path(runtime_summary["report_path"]),
            kind="table",
            description="Runtime benchmark summary from chain metadata.",
        )
        registry.add(
            path=Path(metrics_summary["report_path"]),
            kind="table",
            description="ESS and MSJD diagnostics summary across chains.",
        )

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "phase1_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of generated artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable artifact summary.")
    registry.print_summary()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run full phase-1 AD dim sweep script pipeline.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Run only task selection without chain execution.")
    args = parser.parse_args()
    run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
