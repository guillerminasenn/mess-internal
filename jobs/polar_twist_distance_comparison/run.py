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


def _parse_variants(raw: str):
    if not raw.strip():
        return None
    return [v.strip() for v in raw.split(",") if v.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run missing polar-twist distance-comparison chains via sharded workers.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Print tasks only, do not run.")
    parser.add_argument(
        "--variants",
        type=str,
        default="",
        help="Comma-separated variants from: uniform,lp_angular,lp_euclidean.",
    )
    parser.add_argument(
        "--run-uniform-if-missing",
        action="store_true",
        help="Generate uniform chain locally if no reusable chain is found.",
    )
    args = parser.parse_args()

    if args.grid_count < 1:
        raise ValueError("grid-count must be >= 1")
    if args.grid_index < 0 or args.grid_index >= args.grid_count:
        raise ValueError("grid-index must be in [0, grid-count)")

    repo_root = _resolve_repo_root()
    _ensure_import_paths(repo_root)

    from mess.experiments.polar_twist_distance_comparison.config import ExperimentConfig
    from mess.experiments.polar_twist_distance_comparison.run_chains import run

    cfg = ExperimentConfig()
    selected = _parse_variants(args.variants)
    if selected is not None:
        cfg.variant_list = selected
    if args.run_uniform_if_missing:
        cfg.run_uniform_if_missing = True

    summary = run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run, config=cfg)

    print("\nRun summary:")
    print(f"- Estimations dir: {summary['estimations_dir']}")
    print(f"- Reports dir: {summary['reports_dir']}")
    print(f"- Tasks assigned: {summary['assigned_tasks']} / missing total {summary['total_missing_tasks']}")
    if summary.get("uniform_external_chain"):
        print(f"- Reused uniform chain: {summary['uniform_external_chain']}")
    for item in summary.get("artifacts", []):
        print(f"- [{item['kind']}] {item['path']}")
        print(f"  {item['description']}")


if __name__ == "__main__":
    main()
