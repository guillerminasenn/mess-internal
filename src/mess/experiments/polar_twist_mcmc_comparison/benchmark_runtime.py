"""Aggregate runtime and acceptance summaries from generated chain files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_mcmc_comparison.naming import parse_chain_name


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
            runtime_sec = float(payload["runtime_sec"]) if "runtime_sec" in payload else float("nan")
            acceptance = float(payload["acceptance"]) if "acceptance" in payload else float("nan")

        rows.append(
            {
                "alg": alg,
                "M": m,
                "P": p,
                "rho": rho,
                "runtime_sec": runtime_sec,
                "acceptance": acceptance,
                "rejection": float(1.0 - acceptance) if np.isfinite(acceptance) else float("nan"),
                "path": str(chain_file.resolve()),
            }
        )

    out_path = ctx["reports_dir"] / "tables" / "runtime_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)

    print(f"Runtime entries: {len(rows)}")
    print(f"Runtime summary: {out_path}")
    return {"report_path": str(out_path.resolve()), "rows": len(rows)}


def main() -> None:
    summary = run()
    print("\nRuntime benchmark summary:")
    print(f"- Report: {summary['report_path']}")
    print(f"- Rows: {summary['rows']}")


if __name__ == "__main__":
    main()
