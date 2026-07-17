"""Compute phase-1 diagnostics (ESS/MSJD) from generated chains."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.naming import parse_chain_name
from mess.algorithms.effective_sample_size import estimate_effective_sample_size


def _mean_squared_jump_distance(samples: np.ndarray) -> float:
    if samples.shape[0] < 2:
        return float("nan")
    jumps = np.diff(samples, axis=0)
    sq = np.sum(jumps * jumps, axis=1)
    return float(np.mean(sq))


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["legacy_output_dir"]

    rows = []
    for chain_path in sorted(outdir.glob("chain_*.npz")):
        parsed = parse_chain_name(chain_path)
        if parsed is None:
            continue
        alg, d, M, P = parsed
        chain = np.load(chain_path)["chain"]
        samples = chain[int(cfg.burn_in) :: int(cfg.thin)]
        if samples.shape[0] < 4:
            continue

        ess_dims = []
        for j in range(samples.shape[1]):
            ess_dims.append(float(estimate_effective_sample_size(samples[:, j], max_lag=int(cfg.max_lag))))
        ess_mean = float(np.mean(ess_dims))
        msjd = _mean_squared_jump_distance(samples)

        rows.append(
            {
                "alg": alg,
                "d": d,
                "M": M,
                "P": P,
                "n_post_burn": int(samples.shape[0]),
                "ess_mean": ess_mean,
                "msjd": msjd,
                "path": str(chain_path.resolve()),
            }
        )

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
