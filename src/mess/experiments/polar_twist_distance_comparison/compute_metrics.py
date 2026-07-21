"""Compute ESS/MSJD metrics from distance-comparison chains."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mess.algorithms.effective_sample_size import estimate_effective_sample_size
from mess.experiments.polar_twist_distance_comparison.config import (
    ExperimentConfig,
    build_context,
    resolve_uniform_chain_path,
)
from mess.experiments.polar_twist_distance_comparison.naming import chain_path
from mess.experiments.polar_twist_distance_comparison.tasks import build_expected_tasks


def _msjd_per_dim(samples: np.ndarray) -> np.ndarray:
    if samples.shape[0] < 2:
        return np.full(samples.shape[1], np.nan, dtype=float)
    jumps = np.diff(samples, axis=0)
    return np.mean(jumps * jumps, axis=0)


def _mess_cost_metrics(payload, cfg: ExperimentConfig, m: int, ess_vec: np.ndarray) -> Dict[str, float]:
    unavailable = {
        "mess_cost_metrics_available": False,
        "mess_total_subiters_post_burn": float("nan"),
        "mess_avg_subiters_per_iter_post_burn": float("nan"),
        "mess_energy_lik_evals_post_burn": float("nan"),
        "mess_wallclock_lik_steps_post_burn": float("nan"),
        "ess_x1_per_energy_lik": float("nan"),
        "ess_x2_per_energy_lik": float("nan"),
        "ess_mean_per_energy_lik": float("nan"),
        "ess_x1_per_parallel_lik_step": float("nan"),
        "ess_x2_per_parallel_lik_step": float("nan"),
        "ess_mean_per_parallel_lik_step": float("nan"),
    }
    if "mess_subiters_per_iter" not in payload:
        return unavailable

    subiters = np.asarray(payload["mess_subiters_per_iter"], dtype=float)
    if subiters.ndim != 1 or subiters.size < int(cfg.n_iters):
        return unavailable

    post_burn_subiters = subiters[int(cfg.burn_in) : int(cfg.n_iters)]
    if post_burn_subiters.size == 0:
        return unavailable

    total_subiters = float(np.sum(post_burn_subiters))
    if not np.isfinite(total_subiters) or total_subiters <= 0.0:
        return unavailable

    wallclock_steps = total_subiters
    energy_lik_evals = total_subiters * float(m)
    return {
        "mess_cost_metrics_available": True,
        "mess_total_subiters_post_burn": total_subiters,
        "mess_avg_subiters_per_iter_post_burn": float(np.mean(post_burn_subiters)),
        "mess_energy_lik_evals_post_burn": energy_lik_evals,
        "mess_wallclock_lik_steps_post_burn": wallclock_steps,
        "ess_x1_per_energy_lik": float(ess_vec[0]) / energy_lik_evals if ess_vec.shape[0] > 0 else float("nan"),
        "ess_x2_per_energy_lik": float(ess_vec[1]) / energy_lik_evals if ess_vec.shape[0] > 1 else float("nan"),
        "ess_mean_per_energy_lik": float(np.nanmean(ess_vec)) / energy_lik_evals,
        "ess_x1_per_parallel_lik_step": float(ess_vec[0]) / wallclock_steps if ess_vec.shape[0] > 0 else float("nan"),
        "ess_x2_per_parallel_lik_step": float(ess_vec[1]) / wallclock_steps if ess_vec.shape[0] > 1 else float("nan"),
        "ess_mean_per_parallel_lik_step": float(np.nanmean(ess_vec)) / wallclock_steps,
    }


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]
    uniform_external = resolve_uniform_chain_path(cfg, repo_root=ctx["repo_root"])

    rows: List[Dict[str, Any]] = []
    for task in build_expected_tasks(cfg):
        variant = str(task["variant"])
        m = int(task["M"])

        if variant == "uniform" and uniform_external and uniform_external.exists():
            path = uniform_external
            source = "external"
        else:
            path = chain_path(outdir, variant=variant, M=m)
            source = "local"

        if not path.exists():
            continue

        with np.load(path) as payload:
            chain = payload["chain"]

        samples = chain[int(cfg.burn_in) :: int(cfg.thin)]
        if samples.shape[0] < 4:
            continue

        ess_vec = np.array(
            [
                float(estimate_effective_sample_size(samples[:, j], max_lag=int(cfg.max_lag)))
                for j in range(samples.shape[1])
            ],
            dtype=float,
        )
        msjd_vec = _msjd_per_dim(samples)
        with np.load(path) as payload:
            cost_metrics = _mess_cost_metrics(payload, cfg, m, ess_vec)

        row = {
            "variant": variant,
            "M": m,
            "source": source,
            "n_post_burn": int(samples.shape[0]),
            "ess_x1": float(ess_vec[0]) if ess_vec.shape[0] > 0 else float("nan"),
            "ess_x2": float(ess_vec[1]) if ess_vec.shape[0] > 1 else float("nan"),
            "ess_mean": float(np.nanmean(ess_vec)),
            "msjd_x1": float(msjd_vec[0]) if msjd_vec.shape[0] > 0 else float("nan"),
            "msjd_x2": float(msjd_vec[1]) if msjd_vec.shape[0] > 1 else float("nan"),
            "msjd_mean": float(np.nanmean(msjd_vec)),
            "path": str(path.resolve()),
        }
        row.update(cost_metrics)
        rows.append(row)

    out_path = ctx["estimations_dir"] / "tables" / "metrics_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    print(f"Metric rows: {len(rows)}")
    print(f"Metrics summary: {out_path}")
    return {"report_path": str(out_path.resolve()), "rows": len(rows)}


def main() -> None:
    summary = run()
    print("\nMetrics summary:")
    print(f"- Report: {summary['report_path']}")
    print(f"- Rows: {summary['rows']}")


if __name__ == "__main__":
    main()
