"""Compute ESS/MSJD metrics from generated polar-twist chains."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mess.algorithms.effective_sample_size import estimate_effective_sample_size
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_mcmc_comparison.naming import parse_chain_name


def _msjd_per_dim(samples: np.ndarray) -> np.ndarray:
    if samples.shape[0] < 2:
        return np.full(samples.shape[1], np.nan, dtype=float)
    jumps = np.diff(samples, axis=0)
    return np.mean(jumps * jumps, axis=0)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]

    rows: List[Dict[str, Any]] = []
    for chain_file in sorted(outdir.glob("chain_*.npz")):
        parsed = parse_chain_name(chain_file)
        if parsed is None:
            continue
        alg, m, p, rho = parsed

        with np.load(chain_file) as payload:
            chain = payload["chain"]
            acceptance = float(payload["acceptance"]) if "acceptance" in payload else float("nan")

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

        row = {
            "alg": alg,
            "M": m,
            "P": p,
            "rho": rho,
            "n_post_burn": int(samples.shape[0]),
            "ess_x1": float(ess_vec[0]) if ess_vec.shape[0] > 0 else float("nan"),
            "ess_x2": float(ess_vec[1]) if ess_vec.shape[0] > 1 else float("nan"),
            "ess_mean": float(np.nanmean(ess_vec)),
            "msjd_x1": float(msjd_vec[0]) if msjd_vec.shape[0] > 0 else float("nan"),
            "msjd_x2": float(msjd_vec[1]) if msjd_vec.shape[0] > 1 else float("nan"),
            "msjd_mean": float(np.nanmean(msjd_vec)),
            "acceptance": acceptance,
            "rejection": float(1.0 - acceptance) if np.isfinite(acceptance) else float("nan"),
            "path": str(chain_file.resolve()),
        }
        rows.append(row)

    out_path = ctx["reports_dir"] / "tables" / "metrics_summary.json"
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
