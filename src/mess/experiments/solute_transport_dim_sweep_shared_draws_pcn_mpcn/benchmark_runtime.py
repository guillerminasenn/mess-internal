"""Aggregate runtime benchmarks from chain files."""

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
        payload = np.load(chain_path)
        runtime_sec = float(payload["runtime_sec"]) if "runtime_sec" in payload else float("nan")
        rows.append({
            "alg": alg,
            "d": d,
            "M": M,
            "P": P,
            "runtime_sec": runtime_sec,
            "path": str(chain_path.resolve()),
        })

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
