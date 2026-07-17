"""Deprecated compatibility wrapper for old phase-1 workflow entrypoint."""

from __future__ import annotations

from typing import Optional

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.run_workflow import (
    run as run_workflow,
)


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> None:
    print("[deprecated] phase1_all.run -> run_workflow.run")
    run_workflow(
        grid_count=grid_count,
        grid_index=grid_index,
        dry_run=dry_run,
        config=config,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Deprecated: use run_workflow module instead.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Run only task selection without chain execution.")
    args = parser.parse_args()
    run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
