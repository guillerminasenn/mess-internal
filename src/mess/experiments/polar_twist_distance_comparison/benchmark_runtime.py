"""Aggregate runtime summaries from generated distance-comparison chain files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mess.experiments.polar_twist_distance_comparison.config import (
    ExperimentConfig,
    build_context,
    resolve_uniform_chain_path,
)
from mess.experiments.polar_twist_distance_comparison.naming import chain_path
from mess.experiments.polar_twist_distance_comparison.tasks import build_expected_tasks


def _safe_scalar(payload, key: str) -> float:
    if key not in payload:
        return float("nan")
    value = payload[key]
    arr = np.asarray(value).reshape(-1)
    if arr.size == 0:
        return float("nan")
    return float(arr[0])


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
            runtime_sec = _safe_scalar(payload, "runtime_sec")

        rows.append(
            {
                "variant": variant,
                "M": m,
                "source": source,
                "runtime_sec": runtime_sec,
                "path": str(path.resolve()),
            }
        )

    out_path = ctx["estimations_dir"] / "tables" / "runtime_summary.json"
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
