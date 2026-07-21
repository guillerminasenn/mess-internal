"""Generate chains for polar-twist transition-matrix distance comparison."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mess.algorithms.mess import mess_step
from mess.experiments.polar_twist_distance_comparison.config import (
    ExperimentConfig,
    build_context,
    resolve_uniform_chain_path,
)
from mess.experiments.polar_twist_distance_comparison.naming import chain_path
from mess.experiments.polar_twist_distance_comparison.tasks import build_missing_task_list
from mess.problems import build_polar_twist_problem


def _save_chain(path: Path, chain: np.ndarray, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, chain=chain, **metadata)


def _variant_lp_config(variant: str) -> tuple[bool, str]:
    key = str(variant).lower()
    if key == "uniform":
        return False, "angular"
    if key == "lp_angular":
        return True, "angular"
    if key == "lp_euclidean":
        return True, "euclidean"
    raise ValueError(f"Unknown variant '{variant}'")


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    replace_existing_identical: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> Dict[str, Any]:
    """Run chain generation for one shard and return execution summary."""
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg, grid_count=grid_count, grid_index=grid_index)
    outdir: Path = ctx["estimations_dir"]

    uniform_external = resolve_uniform_chain_path(cfg, repo_root=ctx["repo_root"])
    has_external_uniform = uniform_external is not None and uniform_external.exists()

    tasks = build_missing_task_list(cfg, outdir, uniform_exists_external=has_external_uniform)
    my_tasks = tasks[grid_index::grid_count]

    summary = {
        "grid_count": int(grid_count),
        "grid_index": int(grid_index),
        "total_missing_tasks": len(tasks),
        "assigned_tasks": len(my_tasks),
        "dry_run": bool(dry_run),
        "replace_existing_identical": bool(replace_existing_identical),
        "estimations_dir": str(ctx["estimations_dir"]),
        "reports_dir": str(ctx["reports_dir"]),
        "uniform_external_chain": str(uniform_external.resolve()) if uniform_external else None,
        "artifacts": [],
    }

    print(f"Missing tasks total={len(tasks)}; assigned to this worker={len(my_tasks)}")
    if has_external_uniform:
        summary["artifacts"].append(
            {
                "kind": "reference",
                "path": str(uniform_external.resolve()),
                "description": "Existing uniform-transition MESS chain reused from polar_twist_mcmc_comparison.",
            }
        )

    if dry_run:
        for task in my_tasks:
            print(
                f"DRY_RUN variant={task['variant']:>12s} "
                f"M={str(task.get('M')):>4s} "
                f"refresh={bool(task.get('requires_refresh', False))}"
            )
        return summary

    problem, data = build_polar_twist_problem(
        alpha=cfg.alpha,
        sigma_noise=cfg.sigma_noise,
        prior_mean=np.asarray(cfg.prior_mean, dtype=float),
        prior_cov=np.asarray(cfg.prior_cov, dtype=float),
        weight_x=cfg.weight_x,
        weight_y=cfg.weight_y,
        data_seed=cfg.data_seed,
    )
    x0 = np.asarray(cfg.prior_mean, dtype=float)

    data_path = outdir / "data_and_latent.npz"
    if not data_path.exists():
        np.savez_compressed(data_path, y_obs=data.y_obs, x_true=data.x_true, theta_true=data.theta_true)
    summary["artifacts"].append(
        {
            "kind": "data",
            "path": str(data_path.resolve()),
            "description": "Observed data and latent truth used by all distance-comparison chains.",
        }
    )

    for task in my_tasks:
        variant = str(task["variant"])
        m = int(task["M"])

        if variant == "uniform" and has_external_uniform and not cfg.run_uniform_if_missing:
            continue

        out_path = chain_path(outdir, variant=variant, M=m)
        requires_refresh = bool(task.get("requires_refresh", False))
        should_replace = bool(replace_existing_identical and out_path.exists())
        if out_path.exists() and not (requires_refresh or should_replace):
            continue

        use_lp, distance_metric = _variant_lp_config(variant)
        rng = np.random.default_rng(cfg.seed_mcmc)
        chain = np.zeros((cfg.n_iters + 1, x0.shape[0]), dtype=float)
        mess_subiters_per_iter = np.zeros((cfg.n_iters,), dtype=int)
        chain[0] = x0.copy()
        x = x0.copy()

        t0 = time.perf_counter()
        for t in range(cfg.n_iters):
            x, nr_intervals, _ = mess_step(
                x,
                problem,
                rng,
                M=m,
                use_lp=use_lp,
                distance_metric=distance_metric,
                lam=float(cfg.lp_lam),
            )
            mess_subiters_per_iter[t] = int(nr_intervals) + 1
            chain[t + 1] = x
        runtime = time.perf_counter() - t0

        post = chain[:: cfg.thin]
        metadata = {
            "alg": "mess",
            "variant": variant,
            "transition_matrix": "uniform" if variant == "uniform" else "distance_informed",
            "distance_metric": None if variant == "uniform" else distance_metric,
            "use_lp": bool(use_lp),
            "lam": float(cfg.lp_lam),
            "M": m,
            "n_iters": cfg.n_iters,
            "burn_in": cfg.burn_in,
            "thin": cfg.thin,
            "seed_mcmc": cfg.seed_mcmc,
            "seed_data": cfg.data_seed,
            "runtime_sec": runtime,
            "mess_subiters_per_iter": mess_subiters_per_iter,
        }
        _save_chain(out_path, post, metadata)
        summary["artifacts"].append(
            {
                "kind": "chain",
                "path": str(out_path.resolve()),
                "description": f"MESS chain for variant={variant}, M={m}.",
            }
        )

    if any(str(v) == "uniform" for v in cfg.variant_list) and not has_external_uniform and not cfg.run_uniform_if_missing:
        print(
            "Uniform chain is requested but no existing external chain was found; "
            "set run_uniform_if_missing=True to generate it in this experiment output."
        )

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run polar-twist distance-comparison chains.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Print tasks only, do not run.")
    parser.add_argument(
        "--replace-existing-identical",
        action="store_true",
        help="Overwrite existing same-config chains in-place under the same run directory.",
    )
    args = parser.parse_args()

    summary = run(
        grid_count=args.grid_count,
        grid_index=args.grid_index,
        dry_run=args.dry_run,
        replace_existing_identical=args.replace_existing_identical,
    )

    print("\nRun summary:")
    print(f"- Estimations dir: {summary['estimations_dir']}")
    print(f"- Reports dir: {summary['reports_dir']}")
    print(f"- Tasks assigned: {summary['assigned_tasks']} / missing total {summary['total_missing_tasks']}")
    if summary.get("uniform_external_chain"):
        print(f"- Reused uniform chain: {summary['uniform_external_chain']}")


if __name__ == "__main__":
    main()
