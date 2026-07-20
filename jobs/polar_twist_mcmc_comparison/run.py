import argparse
import os
import sys
from pathlib import Path


def _resolve_repo_root() -> Path:
    env_root = os.environ.get("MULTIPROPOSAL_RUN_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _ensure_import_paths(repo_root: Path) -> None:
    workspace_root = repo_root.parent
    src_path = repo_root / "src"
    mcmc_src_path = workspace_root / "mcmc-internal" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(mcmc_src_path) not in sys.path and mcmc_src_path.exists():
        sys.path.insert(0, str(mcmc_src_path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run missing polar-twist chains via sharded workers.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Print tasks only, do not run.")
    parser.add_argument(
        "--capture-ellipse-traces",
        action="store_true",
        help="Capture exact MESS ellipse traces for selected iterations.",
    )
    parser.add_argument(
        "--ellipse-start-iter",
        type=int,
        default=None,
        help="Start iteration (inclusive) for contiguous ellipse trace capture.",
    )
    parser.add_argument(
        "--ellipse-count",
        type=int,
        default=None,
        help="Number of contiguous iterations to capture for ellipse traces.",
    )
    parser.add_argument(
        "--ellipse-iters",
        type=str,
        default="",
        help="Comma-separated explicit iteration list for ellipse trace capture.",
    )
    args = parser.parse_args()

    if args.grid_count < 1:
        raise ValueError("grid-count must be >= 1")
    if args.grid_index < 0 or args.grid_index >= args.grid_count:
        raise ValueError("grid-index must be in [0, grid-count)")

    repo_root = _resolve_repo_root()
    _ensure_import_paths(repo_root)

    from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
    from mess.experiments.polar_twist_mcmc_comparison.run_chains import run

    cfg = ExperimentConfig()

    if args.capture_ellipse_traces:
        cfg.capture_mess_ellipse_traces = True
    if args.ellipse_start_iter is not None:
        cfg.ellipse_trace_window_start = int(args.ellipse_start_iter)
    if args.ellipse_count is not None:
        cfg.ellipse_trace_window_length = int(args.ellipse_count)
    if args.ellipse_iters.strip():
        cfg.ellipse_trace_iters = [
            int(v.strip()) for v in args.ellipse_iters.split(",") if v.strip()
        ]

    summary = run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run, config=cfg)

    print("\nRun summary:")
    print(f"- Estimations dir: {summary['estimations_dir']}")
    print(f"- Reports dir: {summary['reports_dir']}")
    print(f"- Tasks assigned: {summary['assigned_tasks']} / missing total {summary['total_missing_tasks']}")
    for item in summary.get("artifacts", []):
        print(f"- [{item['kind']}] {item['path']}")
        print(f"  {item['description']}")


if __name__ == "__main__":
    main()
