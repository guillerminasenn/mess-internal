"""Generate chains for polar-twist EP-vs-MESS experiment."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mess.algorithms.mess import mess_step
from mess.experiments.polar_twist_ep.config import ExperimentConfig, build_context, sample_start_points
from mess.experiments.polar_twist_ep.tasks import build_missing_task_list
from mess.problems import build_polar_twist_problem


def _save_chain(path: Path, chain: np.ndarray, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, chain=chain, **metadata)


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg, grid_count=grid_count, grid_index=grid_index)
    outdir: Path = ctx["estimations_dir"]

    tasks = build_missing_task_list(cfg, outdir)
    my_tasks = tasks[grid_index::grid_count]

    summary = {
        "grid_count": int(grid_count),
        "grid_index": int(grid_index),
        "total_missing_tasks": len(tasks),
        "assigned_tasks": len(my_tasks),
        "dry_run": bool(dry_run),
        "estimations_dir": str(ctx["estimations_dir"]),
        "reports_dir": str(ctx["reports_dir"]),
        "artifacts": [],
    }

    print(f"Missing tasks total={len(tasks)}; assigned to this worker={len(my_tasks)}")
    if dry_run:
        for task in my_tasks:
            print(
                f"DRY_RUN variant={task['variant']:6s} M={int(task['M']):3d} "
                f"rep={int(task['replicate']):03d} chain={str(task.get('chain_idx')):>4s}"
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
    dim = int(np.asarray(cfg.prior_mean, dtype=float).shape[0])
    starts = sample_start_points(cfg, dim=dim)

    starts_path = outdir / "diagnostics" / "start_points.npz"
    starts_path.parent.mkdir(parents=True, exist_ok=True)
    if not starts_path.exists():
        np.savez_compressed(
            starts_path,
            mess_starts=starts["mess_starts"],
            ep_starts=starts["ep_starts"],
            M_list=np.asarray(sorted(int(v) for v in cfg.M_list), dtype=int),
            replicates=int(cfg.replicates),
        )

    data_path = outdir / "data_and_latent.npz"
    if not data_path.exists():
        np.savez_compressed(data_path, y_obs=data.y_obs, x_true=data.x_true, theta_true=data.theta_true)

    summary["artifacts"].append(
        {
            "kind": "data",
            "path": str(data_path.resolve()),
            "description": "Observed data and latent truth used by all chains.",
        }
    )
    summary["artifacts"].append(
        {
            "kind": "diagnostics",
            "path": str(starts_path.resolve()),
            "description": "Deterministic MESS and EP start points.",
        }
    )

    logs = []
    base_seed = int(cfg.seed_mcmc)
    for task in my_tasks:
        out_path = Path(str(task["path"]))
        variant = str(task["variant"])
        m = int(task["M"])
        replicate = int(task["replicate"])
        chain_idx = task.get("chain_idx")

        if out_path.exists():
            continue

        if variant == "mess":
            x0 = starts["mess_starts"][replicate].copy()
            algo_m = int(m)
            chain_seed = base_seed + 100000 * m + replicate
        elif variant == "ep_ess":
            idx = int(chain_idx)
            x0 = starts["ep_starts"][replicate, idx].copy()
            algo_m = 1
            chain_seed = base_seed + 200000 * m + 1000 * replicate + idx
        else:
            raise ValueError(f"Unsupported variant '{variant}'")

        rng = np.random.default_rng(chain_seed)
        chain = np.zeros((cfg.n_iters + 1, x0.shape[0]), dtype=float)
        mess_subiters_per_iter = np.zeros((cfg.n_iters,), dtype=int)
        chain[0] = x0.copy()
        x = x0.copy()

        t0 = time.perf_counter()
        for t in range(cfg.n_iters):
            x, nr_intervals, _ = mess_step(x, problem, rng, M=algo_m, use_lp=False)
            mess_subiters_per_iter[t] = int(nr_intervals) + 1
            chain[t + 1] = x
        runtime = time.perf_counter() - t0

        post = chain[:: cfg.thin]
        metadata = {
            "variant": variant,
            "algorithm": "mess" if variant == "mess" else "ess",
            "M": int(m),
            "replicate": int(replicate),
            "chain_idx": int(chain_idx) if chain_idx is not None else -1,
            "n_iters": int(cfg.n_iters),
            "burn_in": int(cfg.burn_in),
            "thin": int(cfg.thin),
            "seed_data": int(cfg.data_seed),
            "seed_starts": int(cfg.seed_starts),
            "seed_mcmc": int(chain_seed),
            "runtime_sec": float(runtime),
            "mess_subiters_per_iter": mess_subiters_per_iter,
        }
        _save_chain(out_path, post, metadata)

        logs.append(
            {
                "variant": variant,
                "M": int(m),
                "replicate": int(replicate),
                "chain_idx": int(chain_idx) if chain_idx is not None else None,
                "runtime_sec": float(runtime),
                "path": str(out_path.resolve()),
                "n_samples": int(post.shape[0]),
            }
        )

    runs_path = outdir / f"worker_{grid_index}_runs.json"
    with open(runs_path, "w", encoding="utf-8") as handle:
        json.dump(logs, handle, indent=2)
    summary["artifacts"].append(
        {
            "kind": "metadata",
            "path": str(runs_path.resolve()),
            "description": "Per-task runtimes and chain metadata for this worker.",
        }
    )
    summary["artifacts"].extend(
        {
            "kind": "chain",
            "path": item["path"],
            "description": (
                f"{item['variant']} chain for M={item['M']}, replicate={item['replicate']}, "
                f"chain_idx={item['chain_idx']}"
            ),
        }
        for item in logs
    )

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run missing polar-twist EP chains for one worker shard.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Print assigned tasks only, do not run.")
    args = parser.parse_args()

    if args.grid_count < 1:
        raise ValueError("grid-count must be >= 1")
    if args.grid_index < 0 or args.grid_index >= args.grid_count:
        raise ValueError("grid-index must be in [0, grid-count)")

    summary = run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run)
    print("\nRun summary:")
    print(f"- Estimations dir: {summary['estimations_dir']}")
    print(f"- Reports dir: {summary['reports_dir']}")
    print(f"- Tasks assigned: {summary['assigned_tasks']} / missing total {summary['total_missing_tasks']}")


if __name__ == "__main__":
    main()
