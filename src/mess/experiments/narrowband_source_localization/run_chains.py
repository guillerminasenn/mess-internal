"""Generate chains for narrowband source-localization experiment."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mess.algorithms.mess import mess_step
from mess.experiments.narrowband_source_localization.config import (
    ExperimentConfig,
    build_context,
    sample_start_points,
)
from mess.experiments.narrowband_source_localization.tasks import build_missing_task_list
from mess.problems import build_narrowband_source_localization_problem


def _save_chain(path: Path, chain: np.ndarray, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, chain=chain, **metadata)


def _transition_lp_config(variant: str) -> tuple[bool, str]:
    key = str(variant).strip().lower()
    if key == "uniform":
        return False, "angular"
    if key == "euclidean_informed":
        return True, "euclidean"
    if key == "angular_informed":
        return True, "angular"
    raise ValueError(f"Unknown transition variant '{variant}'")


def _circular_components(mask: np.ndarray) -> List[tuple[int, int]]:
    """Connected components on a circular boolean mask over [0, 2pi)."""
    if mask.ndim != 1:
        raise ValueError("mask must be 1D")
    n = int(mask.size)
    if n == 0 or not np.any(mask):
        return []

    # Rotate so the sequence starts at a False location if possible.
    if np.all(mask):
        return [(0, n)]

    start = int(np.where(~mask)[0][0])
    rolled = np.roll(mask, -start)

    comps: List[tuple[int, int]] = []
    i = 0
    while i < n:
        if not rolled[i]:
            i += 1
            continue
        j = i
        while j < n and rolled[j]:
            j += 1
        a = (i + start) % n
        b = (j + start) % n
        if a < b:
            comps.append((a, b))
        else:
            # Component wraps around 2pi.
            comps.append((a, n))
            if b > 0:
                comps.append((0, b))
        i = j

    # Merge adjacent entries created by a wrap-around split.
    comps = sorted(comps, key=lambda t: (t[0], t[1]))
    merged: List[tuple[int, int]] = []
    for a, b in comps:
        if not merged:
            merged.append((a, b))
            continue
        pa, pb = merged[-1]
        if a <= pb:
            merged[-1] = (pa, max(pb, b))
        else:
            merged.append((a, b))
    return merged


def _slice_geometry_summary(problem, trace: dict, angle_grid_size: int) -> Dict[str, Any]:
    """Compute disconnected-slice geometry diagnostics for one MESS ellipse."""
    x = np.asarray(trace["x"], dtype=float)
    x_centered = np.asarray(trace["x_centered"], dtype=float)
    nu_centered = np.asarray(trace["nu_centered"], dtype=float)
    alpha = float(trace["alpha"])
    logy = float(trace["logy"])

    phi = np.linspace(0.0, 2.0 * np.pi, int(angle_grid_size), endpoint=False)
    z_grid = (
        problem.prior_mean()[:, None]
        + np.cos(phi - alpha)[None, :] * x_centered[:, None]
        + np.sin(phi - alpha)[None, :] * nu_centered[:, None]
    ).T

    ll = problem.log_likelihood_batch(z_grid)
    valid = ll >= logy
    components = _circular_components(valid)

    widths = []
    physical_jumps = []
    whitened_jumps = []
    q0 = problem.whitened_to_physical(x)
    for a, b in components:
        w = (b - a) / float(phi.size) * 2.0 * np.pi
        widths.append(float(w))
        z_comp = z_grid[a:b, :]
        q_comp = problem.whitened_to_physical(z_comp)
        whitened_jumps.append(float(np.max(np.linalg.norm(z_comp - x[None, :], axis=1))))
        physical_jumps.append(float(np.max(np.linalg.norm(q_comp - q0[None, :], axis=1))))

    zero_idx = int(np.floor((alpha / (2.0 * np.pi)) * phi.size)) % phi.size
    zero_comp_idx = None
    for idx, (a, b) in enumerate(components):
        if a <= zero_idx < b:
            zero_comp_idx = idx
            break

    remote_width = 0.0
    if components:
        for idx, w in enumerate(widths):
            if zero_comp_idx is None or idx != zero_comp_idx:
                remote_width += w

    return {
        "component_count": int(len(components)),
        "component_widths": widths,
        "zero_component_index": int(zero_comp_idx) if zero_comp_idx is not None else None,
        "remote_total_width": float(remote_width),
        "max_physical_jump_per_component": physical_jumps,
        "max_whitened_jump_per_component": whitened_jumps,
        "has_remote_component": bool(remote_width > 0.0),
    }


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
                f"DRY_RUN sampler={task['sampler']:6s} M={int(task['M']):3d} "
                f"rep={int(task['replicate']):03d} variant={str(task['transition_variant']):>18s} "
                f"chain={str(task.get('chain_idx')):>4s}"
            )
        return summary

    # Import mcmc-internal sampler lazily after context setup has inserted cross-repo paths.
    from multiproposal.algorithms.mpcn import mpcn_chain

    problem, data = build_narrowband_source_localization_problem(
        sensors_m=np.asarray(cfg.sensors_m, dtype=float),
        frequencies_hz=cfg.frequencies_hz,
        propagation_speed=float(cfg.propagation_speed),
        true_source_m=cfg.true_source_m,
        tau=cfg.tau,
        sigma=cfg.sigma,
        prior_mean_m=cfg.prior_mean_m,
        prior_cov_m=cfg.prior_cov_m(),
        amplitude_model=cfg.amplitude_model,
        gamma=float(cfg.amplitude_gamma),
        r_min=float(cfg.r_min),
        data_seed=int(cfg.data_seed),
    )
    starts = sample_start_points(cfg)

    starts_path = outdir / "diagnostics" / "start_points.npz"
    starts_path.parent.mkdir(parents=True, exist_ok=True)
    if not starts_path.exists():
        np.savez_compressed(
            starts_path,
            mess_starts=starts["mess_starts"],
            ep_starts=starts["ep_starts"],
            mpcn_starts=starts["mpcn_starts"],
            M_list=np.asarray(sorted(int(v) for v in cfg.M_list), dtype=int),
            replicates=int(cfg.replicates),
        )

    data_path = outdir / "data_and_latent.npz"
    if not data_path.exists():
        np.savez_compressed(
            data_path,
            y_obs=data.y_obs,
            q_true=data.q_true,
            alpha_draws=data.alpha_draws,
            epsilon_draws=data.epsilon_draws,
            sensors_m=data.sensors_m,
            frequencies_hz=data.frequencies_hz,
            tau=data.tau,
            sigma=data.sigma,
        )

    manifest_path = outdir / "data_manifest.json"
    if not manifest_path.exists():
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(data.config, handle, indent=2)

    summary["artifacts"].append(
        {
            "kind": "data",
            "path": str(data_path.resolve()),
            "description": "Observed complex data and latent random draws shared by all samplers.",
        }
    )
    summary["artifacts"].append(
        {
            "kind": "metadata",
            "path": str(manifest_path.resolve()),
            "description": "Dataset manifest for deterministic regeneration.",
        }
    )
    summary["artifacts"].append(
        {
            "kind": "diagnostics",
            "path": str(starts_path.resolve()),
            "description": "Deterministic start points for MESS, EP-ESS, and MPCN.",
        }
    )

    logs = []
    geometry_rows: List[Dict[str, Any]] = []

    variant_to_offset = {
        "uniform": 0,
        "euclidean_informed": 1,
        "angular_informed": 2,
    }

    for task in my_tasks:
        out_path = Path(str(task["path"]))
        sampler = str(task["sampler"])
        m = int(task["M"])
        replicate = int(task["replicate"])
        transition_variant = str(task.get("transition_variant", ""))
        chain_idx = task.get("chain_idx")

        if out_path.exists():
            continue

        if sampler == "mess":
            use_lp, distance_metric = _transition_lp_config(transition_variant)
            x0 = starts["mess_starts"][replicate].copy()
            chain_seed = int(cfg.seed_mcmc) + 100000 * m + 1000 * replicate + 10 * variant_to_offset[transition_variant]
            rng = np.random.default_rng(chain_seed)

            chain = np.zeros((cfg.n_iters + 1, x0.shape[0]), dtype=float)
            mess_subiters_per_iter = np.zeros((cfg.n_iters,), dtype=int)
            chain[0] = x0.copy()
            x = x0.copy()

            t0 = time.perf_counter()
            for t in range(cfg.n_iters):
                capture_trace = (
                    replicate < int(cfg.geometry_diag_replicates)
                    and t < int(cfg.geometry_diag_max_iters)
                )
                if capture_trace:
                    x, nr_intervals, _, trace = mess_step(
                        x,
                        problem,
                        rng,
                        M=m,
                        use_lp=use_lp,
                        distance_metric=distance_metric,
                        return_trace=True,
                    )
                    geom = _slice_geometry_summary(problem, trace, angle_grid_size=int(cfg.geometry_angle_grid_size))
                    geom.update(
                        {
                            "sampler": sampler,
                            "transition_variant": transition_variant,
                            "M": int(m),
                            "replicate": int(replicate),
                            "iteration": int(t),
                            "subiters": int(nr_intervals) + 1,
                        }
                    )
                    geometry_rows.append(geom)
                else:
                    x, nr_intervals, _ = mess_step(
                        x,
                        problem,
                        rng,
                        M=m,
                        use_lp=use_lp,
                        distance_metric=distance_metric,
                    )

                mess_subiters_per_iter[t] = int(nr_intervals) + 1
                chain[t + 1] = x
            runtime = time.perf_counter() - t0

            post = chain[:: cfg.thin]
            metadata = {
                "sampler": "mess",
                "transition_variant": transition_variant,
                "M": int(m),
                "replicate": int(replicate),
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

        elif sampler == "ep_ess":
            idx = int(chain_idx)
            x0 = starts["ep_starts"][replicate, idx].copy()
            if m == 1 and idx == 0:
                # Ensure M=1 EP-ESS is path-coupled to MESS-uniform for exact contract checks.
                chain_seed = int(cfg.seed_mcmc) + 100000 * m + 1000 * replicate
            else:
                chain_seed = int(cfg.seed_mcmc) + 200000 * m + 1000 * replicate + idx
            rng = np.random.default_rng(chain_seed)

            chain = np.zeros((cfg.n_iters + 1, x0.shape[0]), dtype=float)
            mess_subiters_per_iter = np.zeros((cfg.n_iters,), dtype=int)
            chain[0] = x0.copy()
            x = x0.copy()

            t0 = time.perf_counter()
            for t in range(cfg.n_iters):
                x, nr_intervals, _ = mess_step(x, problem, rng, M=1, use_lp=False)
                mess_subiters_per_iter[t] = int(nr_intervals) + 1
                chain[t + 1] = x
            runtime = time.perf_counter() - t0

            post = chain[:: cfg.thin]
            metadata = {
                "sampler": "ep_ess",
                "transition_variant": "uniform",
                "M": int(m),
                "replicate": int(replicate),
                "chain_idx": idx,
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

        elif sampler == "mpcn":
            x0 = starts["mpcn_starts"][replicate].copy()
            chain_seed = int(cfg.seed_algo) + 300000 * m + replicate
            rng = np.random.default_rng(chain_seed)
            t0 = time.perf_counter()
            chain = mpcn_chain(x0, problem, rng, cfg.n_iters, rho=float(cfg.mpcn_rho), n_props=int(m))
            runtime = time.perf_counter() - t0

            post = chain[:: cfg.thin]
            metadata = {
                "sampler": "mpcn",
                "transition_variant": "proposal_count",
                "M": int(m),
                "P": int(m),
                "replicate": int(replicate),
                "n_iters": int(cfg.n_iters),
                "burn_in": int(cfg.burn_in),
                "thin": int(cfg.thin),
                "seed_data": int(cfg.data_seed),
                "seed_starts": int(cfg.seed_starts),
                "seed_algo": int(chain_seed),
                "rho": float(cfg.mpcn_rho),
                "runtime_sec": float(runtime),
            }
            _save_chain(out_path, post, metadata)

        else:
            raise ValueError(f"Unknown sampler '{sampler}'")

        logs.append(
            {
                "sampler": sampler,
                "transition_variant": transition_variant,
                "M": int(m),
                "replicate": int(replicate),
                "chain_idx": int(chain_idx) if chain_idx is not None else None,
                "path": str(out_path.resolve()),
                "n_samples": int(post.shape[0]),
                "runtime_sec": float(runtime),
            }
        )

    runs_path = outdir / f"worker_{grid_index}_runs.json"
    with open(runs_path, "w", encoding="utf-8") as handle:
        json.dump(logs, handle, indent=2)
    summary["artifacts"].append(
        {
            "kind": "metadata",
            "path": str(runs_path.resolve()),
            "description": "Per-task runtime and chain metadata for this worker.",
        }
    )

    if geometry_rows:
        geometry_path = outdir / f"geometry_worker_{grid_index}.json"
        with open(geometry_path, "w", encoding="utf-8") as handle:
            json.dump(geometry_rows, handle, indent=2)
        summary["artifacts"].append(
            {
                "kind": "diagnostics",
                "path": str(geometry_path.resolve()),
                "description": "Per-iteration slice-geometry diagnostics from traced MESS ellipses.",
            }
        )

    summary["artifacts"].extend(
        {
            "kind": "chain",
            "path": item["path"],
            "description": (
                f"{item['sampler']} chain for transition={item['transition_variant']}, "
                f"M={item['M']}, replicate={item['replicate']}, chain_idx={item['chain_idx']}"
            ),
        }
        for item in logs
    )

    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run narrowband source-localization chains for one worker shard.")
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
