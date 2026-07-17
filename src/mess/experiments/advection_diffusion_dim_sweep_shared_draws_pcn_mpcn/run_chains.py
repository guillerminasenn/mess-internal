"""Generate chains for AD dim sweep while preserving existing job behavior."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mess.algorithms.mess import mess_step
from mess.algorithms.mh import mh_chain
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.naming import (
    get_mh_proposal_std,
    is_chain_readable,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.problem_factory import (
    build_problem_for_dim,
    build_shared_draws,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.tasks import (
    build_missing_task_list,
)


def _save_chain(path: Path, chain: np.ndarray, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, chain=chain, **metadata)


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> Dict[str, Any]:
    """Run chain generation for one shard and return execution summary."""
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg, grid_count=grid_count, grid_index=grid_index)
    outdir: Path = ctx["legacy_output_dir"]

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
        "legacy_output_dir": str(outdir),
        "artifacts": [],
    }

    print(f"Missing tasks total={len(tasks)}; assigned to this worker={len(my_tasks)}")
    if dry_run:
        for task in my_tasks:
            alg = task["alg"]
            d = task["d"]
            M = task.get("M")
            P = task.get("P")
            print(f"DRY_RUN {alg:4s} d={d:3d} M={str(M):>3s} P={str(P):>3s}")
        return summary

    # Import mcmc-internal samplers after context setup inserted external src path.
    from multiproposal.algorithms.mpcn import mpcn_chain
    from multiproposal.algorithms.pcn import pcn_chain

    shared_draws = build_shared_draws(cfg)
    problem_cache = {}

    d0 = cfg.d_list[0]
    problem0, x00, y0, theta0 = build_problem_for_dim(cfg, d0, shared_draws)
    _ = problem0, x00
    data_path = outdir / "data_and_latent.npz"
    np.savez_compressed(data_path, y=y0, u_true=theta0)
    summary["artifacts"].append({
        "kind": "data",
        "path": str(data_path.resolve()),
        "description": "Observed data and latent truth used by all chains.",
    })

    logs = []
    mh_std = get_mh_proposal_std(cfg)
    for task in my_tasks:
        d_cur = task["d"]
        if d_cur not in problem_cache:
            problem_cache[d_cur] = build_problem_for_dim(cfg, d_cur, shared_draws)
        problem_cur, x0_cur, _, _ = problem_cache[d_cur]
        out_path = Path(task["path"])
        alg = task["alg"]

        if is_chain_readable(out_path):
            continue

        if alg == "mess":
            M = task["M"]
            rng = np.random.default_rng(cfg.seed_mcmc)
            chain = np.zeros((cfg.n_iters + 1, x0_cur.shape[0]))
            chain[0] = x0_cur.copy()
            x = x0_cur.copy()
            t0 = time.perf_counter()
            for t in range(cfg.n_iters):
                x, _, _ = mess_step(x, problem_cur, rng, M=M, use_lp=False)
                chain[t + 1] = x
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "mess",
                "M": M,
                "d": d_cur,
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_mcmc": cfg.seed_mcmc,
                "seed_data": cfg.seed_data,
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append({"alg": "mess", "d": d_cur, "M": M, "P": None, "runtime_sec": runtime, "path": str(out_path.resolve()), "n_samples": int(post.shape[0])})
        elif alg == "mh":
            rng = np.random.default_rng(cfg.seed_mcmc)
            t0 = time.perf_counter()
            chain, acc = mh_chain(
                x0_cur,
                problem_cur,
                rng,
                cfg.n_iters,
                proposal_std=mh_std,
                proposal_cov=cfg.mh_proposal_cov,
            )
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "mh",
                "d": d_cur,
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_mcmc": cfg.seed_mcmc,
                "seed_data": cfg.seed_data,
                "proposal_std": float(mh_std),
                "proposal_cov": cfg.mh_proposal_cov,
                "acceptance": float(acc),
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append({"alg": "mh", "d": d_cur, "M": None, "P": None, "runtime_sec": runtime, "path": str(out_path.resolve()), "n_samples": int(post.shape[0])})
        elif alg == "pcn":
            rho = task["rho"]
            rng = np.random.default_rng(cfg.seed_algo)
            t0 = time.perf_counter()
            chain = pcn_chain(x0_cur, problem_cur, rng, cfg.n_iters, rho=rho)
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "pcn",
                "d": d_cur,
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_algo": cfg.seed_algo,
                "seed_data": cfg.seed_data,
                "rho": float(rho),
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append({"alg": "pcn", "d": d_cur, "M": None, "P": None, "runtime_sec": runtime, "path": str(out_path.resolve()), "n_samples": int(post.shape[0])})
        elif alg == "mpcn":
            P = task["P"]
            rho = task["rho"]
            rng = np.random.default_rng(cfg.seed_algo)
            t0 = time.perf_counter()
            chain = mpcn_chain(x0_cur, problem_cur, rng, cfg.n_iters, rho=rho, n_props=P)
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "mpcn",
                "d": d_cur,
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_algo": cfg.seed_algo,
                "seed_data": cfg.seed_data,
                "P": int(P),
                "rho": float(rho),
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append({"alg": "mpcn", "d": d_cur, "M": None, "P": P, "runtime_sec": runtime, "path": str(out_path.resolve()), "n_samples": int(post.shape[0])})

    runs_path = outdir / f"worker_{grid_index}_runs.json"
    with open(runs_path, "w", encoding="utf-8") as handle:
        json.dump(logs, handle, indent=2)
    summary["artifacts"].append({
        "kind": "metadata",
        "path": str(runs_path.resolve()),
        "description": "Per-task runtimes and chain metadata for this worker.",
    })
    summary["artifacts"].extend(
        {
            "kind": "chain",
            "path": item["path"],
            "description": f"{item['alg']} chain for d={item['d']}, M={item['M']}, P={item['P']}",
        }
        for item in logs
    )

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run missing AD toy chains for notebook-11 migration.")
    parser.add_argument("--grid-count", type=int, default=1, help="Total number of workers.")
    parser.add_argument("--grid-index", type=int, default=0, help="This worker index in [0, grid-count).")
    parser.add_argument("--dry-run", action="store_true", help="Print tasks only, do not run.")
    args = parser.parse_args()

    if args.grid_count < 1:
        raise ValueError("grid-count must be >= 1")
    if args.grid_index < 0 or args.grid_index >= args.grid_count:
        raise ValueError("grid-index must be in [0, grid-count)")

    summary = run(grid_count=args.grid_count, grid_index=args.grid_index, dry_run=args.dry_run)
    print("\nPhase 1 chain runner summary:")
    print(f"- Estimations dir: {summary['estimations_dir']}")
    print(f"- Reports dir: {summary['reports_dir']}")
    print(f"- Legacy output dir: {summary['legacy_output_dir']}")
    print(f"- Tasks assigned: {summary['assigned_tasks']} / missing total {summary['total_missing_tasks']}")
    for item in summary.get("artifacts", []):
        print(f"- [{item['kind']}] {item['path']}")
        print(f"  {item['description']}")


if __name__ == "__main__":
    main()
