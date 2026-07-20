"""Run phase for polar-twist convergence experiment (reuses existing chains)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mess.experiments.polar_twist_convergence.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_convergence.report_helpers import write_source_summary


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> Dict[str, Any]:
    """Run chain stage as a no-op, materializing source-chain diagnostics only."""
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    summary_path = write_source_summary(cfg)

    summary = {
        "grid_count": int(grid_count),
        "grid_index": int(grid_index),
        "total_missing_tasks": 0,
        "assigned_tasks": 0,
        "dry_run": bool(dry_run),
        "estimations_dir": str(ctx["estimations_dir"]),
        "reports_dir": str(ctx["reports_dir"]),
        "artifacts": [
            {
                "kind": "diagnostics",
                "path": str(summary_path.resolve()),
                "description": "Source chain availability summary for reused runs.",
            }
        ],
    }
    print("No chain generation required: reusing existing polar-twist chain files.")
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run chain stage for polar-twist convergence (reuse mode).")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Show staged summary only.")
    args = parser.parse_args()

    summary = run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run)
    print("\nRun summary:")
    print(f"- Estimations dir: {summary['estimations_dir']}")
    print(f"- Reports dir: {summary['reports_dir']}")
    print(f"- Tasks assigned: {summary['assigned_tasks']} / missing total {summary['total_missing_tasks']}")


if __name__ == "__main__":
    main()
