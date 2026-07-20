"""Generate chains for polar-twist MCMC comparison."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mess.algorithms.mess import mess_step
from mess.experiments.common.mess_ellipse_plotting import (
    plot_contiguous_overlay,
    plot_iteration_panels,
    trace_to_jsonable,
)
from mess.algorithms.mh import mh_chain
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_mcmc_comparison.tasks import build_missing_task_list
from mess.problems import build_polar_twist_problem


def _save_chain(path: Path, chain: np.ndarray, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, chain=chain, **metadata)


def _selected_trace_iters(cfg: ExperimentConfig) -> list[int]:
    selected = set(int(v) for v in cfg.ellipse_trace_iters if int(v) > 0)
    if int(cfg.ellipse_trace_window_length) > 0:
        start = max(1, int(cfg.ellipse_trace_window_start))
        stop = start + int(cfg.ellipse_trace_window_length)
        selected.update(range(start, stop))
    selected = sorted(v for v in selected if v <= int(cfg.n_iters))
    return selected


def run(
    grid_count: int = 1,
    grid_index: int = 0,
    dry_run: bool = False,
    config: Optional[ExperimentConfig] = None,
) -> Dict[str, Any]:
    """Run chain generation for one shard and return execution summary."""
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
                f"DRY_RUN {task['alg']:4s} "
                f"M={str(task.get('M')):>4s} "
                f"P={str(task.get('P')):>4s} "
                f"rho={str(task.get('rho')):>8s}"
            )
        return summary

    # Import mcmc-internal samplers after context setup has ensured path injection.
    from multiproposal.algorithms.mpcn import mpcn_chain
    from multiproposal.algorithms.pcn import pcn_chain

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
            "description": "Observed data and latent truth used by all chains.",
        }
    )

    logs = []
    for task in my_tasks:
        out_path = Path(str(task["path"]))
        alg = str(task["alg"]) 
        if out_path.exists():
            continue

        if alg == "mess":
            m = int(task["M"])
            rng = np.random.default_rng(cfg.seed_mcmc)
            chain = np.zeros((cfg.n_iters + 1, x0.shape[0]), dtype=float)
            chain[0] = x0.copy()
            x = x0.copy()
            trace_iters = _selected_trace_iters(cfg) if cfg.capture_mess_ellipse_traces else []
            trace_iter_set = set(trace_iters)
            traces_payload = []
            t0 = time.perf_counter()
            for t in range(cfg.n_iters):
                iter_no = t + 1
                if iter_no in trace_iter_set:
                    x, _, _, trace = mess_step(
                        x,
                        problem,
                        rng,
                        M=m,
                        use_lp=False,
                        return_trace=True,
                    )
                    traces_payload.append(
                        {
                            "iteration": iter_no,
                            "trace": trace_to_jsonable(trace),
                        }
                    )
                else:
                    x, _, _ = mess_step(x, problem, rng, M=m, use_lp=False)
                chain[t + 1] = x
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "mess",
                "M": m,
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_mcmc": cfg.seed_mcmc,
                "seed_data": cfg.data_seed,
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)

            if traces_payload:
                trace_path = out_path.with_name(out_path.stem + "_ellipse_traces.json")
                trace_doc = {
                    "alg": "mess",
                    "M": m,
                    "seed_mcmc": int(cfg.seed_mcmc),
                    "n_iters": int(cfg.n_iters),
                    "capture_mode": {
                        "iters": [int(v) for v in cfg.ellipse_trace_iters],
                        "window_start": int(cfg.ellipse_trace_window_start),
                        "window_length": int(cfg.ellipse_trace_window_length),
                    },
                    "trace_count": len(traces_payload),
                    "traces": traces_payload,
                }
                with open(trace_path, "w", encoding="utf-8") as handle:
                    json.dump(trace_doc, handle, indent=2)
                logs.append(
                    {
                        "alg": "mess",
                        "M": m,
                        "P": None,
                        "rho": None,
                        "runtime_sec": runtime,
                        "path": str(out_path.resolve()),
                        "trace_path": str(trace_path.resolve()),
                        "n_samples": int(post.shape[0]),
                    }
                )

                if cfg.ellipse_plot_enable_in_run:
                    trace_sorted = sorted(traces_payload, key=lambda item: int(item["iteration"]))
                    fig_dir = outdir / "mess_ellipse_figures"
                    fig_dir.mkdir(parents=True, exist_ok=True)
                    overlay_path = fig_dir / f"mess_M{m}_overlay_n{len(trace_sorted)}.png"
                    overlay_traces = [
                        {"iteration": int(item["iteration"]), **item["trace"]}
                        for item in trace_sorted
                    ]
                    plot_contiguous_overlay(
                        traces=overlay_traces,
                        problem=problem,
                        out_path=overlay_path,
                        title=f"MESS M={m}: contiguous ellipse replay",
                    )
                    logs[-1]["trace_overlay_path"] = str(overlay_path.resolve())

                    for item in trace_sorted:
                        it = int(item["iteration"])
                        panel_path = fig_dir / f"mess_M{m}_iter{it}_intervals.png"
                        plot_iteration_panels(
                            trace_item=item["trace"],
                            problem=problem,
                            out_path=panel_path,
                            title_prefix=f"Iteration {it}",
                        )
                    logs[-1]["trace_panel_dir"] = str(fig_dir.resolve())
            else:
                logs.append(
                    {
                        "alg": "mess",
                        "M": m,
                        "P": None,
                        "rho": None,
                        "runtime_sec": runtime,
                        "path": str(out_path.resolve()),
                        "n_samples": int(post.shape[0]),
                    }
                )
        elif alg == "mh":
            rng = np.random.default_rng(cfg.seed_mcmc)
            t0 = time.perf_counter()
            chain, acc = mh_chain(
                x0,
                problem,
                rng,
                cfg.n_iters,
                proposal_std=cfg.mh_proposal_std,
                proposal_cov=cfg.mh_proposal_cov,
            )
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "mh",
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_mcmc": cfg.seed_mcmc,
                "seed_data": cfg.data_seed,
                "proposal_std": float(cfg.mh_proposal_std),
                "proposal_cov": cfg.mh_proposal_cov,
                "acceptance": float(acc),
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append(
                {
                    "alg": "mh",
                    "M": None,
                    "P": None,
                    "rho": None,
                    "runtime_sec": runtime,
                    "path": str(out_path.resolve()),
                    "n_samples": int(post.shape[0]),
                    "acceptance": float(acc),
                }
            )
        elif alg == "pcn":
            rho = float(task["rho"])
            rng = np.random.default_rng(cfg.seed_algo)
            t0 = time.perf_counter()
            chain = pcn_chain(x0, problem, rng, cfg.n_iters, rho=rho)
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "pcn",
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_algo": cfg.seed_algo,
                "seed_data": cfg.data_seed,
                "rho": rho,
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append(
                {
                    "alg": "pcn",
                    "M": None,
                    "P": None,
                    "rho": rho,
                    "runtime_sec": runtime,
                    "path": str(out_path.resolve()),
                    "n_samples": int(post.shape[0]),
                }
            )
        elif alg == "mpcn":
            p = int(task["P"])
            rho = float(task["rho"])
            rng = np.random.default_rng(cfg.seed_algo)
            t0 = time.perf_counter()
            chain = mpcn_chain(x0, problem, rng, cfg.n_iters, rho=rho, n_props=p)
            runtime = time.perf_counter() - t0
            post = chain[:: cfg.thin]
            metadata = {
                "alg": "mpcn",
                "n_iters": cfg.n_iters,
                "burn_in": cfg.burn_in,
                "thin": cfg.thin,
                "seed_algo": cfg.seed_algo,
                "seed_data": cfg.data_seed,
                "P": p,
                "rho": rho,
                "runtime_sec": runtime,
            }
            _save_chain(out_path, post, metadata)
            logs.append(
                {
                    "alg": "mpcn",
                    "M": None,
                    "P": p,
                    "rho": rho,
                    "runtime_sec": runtime,
                    "path": str(out_path.resolve()),
                    "n_samples": int(post.shape[0]),
                }
            )
        else:
            raise ValueError(f"Unsupported algorithm '{alg}'")

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
                f"{item['alg']} chain for M={item['M']}, P={item['P']}, rho={item['rho']}"
            ),
        }
        for item in logs
    )
    summary["artifacts"].extend(
        {
            "kind": "diagnostic",
            "path": item["trace_path"],
            "description": f"Exact MESS ellipse playback traces for M={item['M']}",
        }
        for item in logs
        if item.get("trace_path")
    )
    summary["artifacts"].extend(
        {
            "kind": "figure",
            "path": item["trace_overlay_path"],
            "description": f"Run-phase contiguous MESS ellipse overlay for M={item['M']}",
        }
        for item in logs
        if item.get("trace_overlay_path")
    )

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run missing polar-twist chains for one worker shard.")
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
