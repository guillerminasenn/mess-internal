"""Diagnostics table for warmup convergence source availability."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from mess.experiments.polar_twist_convergence.config import ExperimentConfig
from mess.experiments.polar_twist_convergence.report_helpers import report_dirs, resolve_sources


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["reports_dir"] / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    source = resolve_sources(cfg)
    rows = []
    for spec in source["specs"]:
        rows.append(
            {
                "label": spec["label"],
                "group": spec["group"],
                "source": spec["source"],
                "found": spec["path"] is not None,
                "path": str(spec["path"]) if spec["path"] is not None else None,
            }
        )

    report_path = out_dir / "source_availability.json"
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "rows": rows,
                "found_count": sum(1 for row in rows if row["found"]),
                "total_count": len(rows),
            },
            handle,
            indent=2,
        )

    return {
        "report_path": str(Path(report_path).resolve()),
        "rows": len(rows),
    }


def main() -> None:
    summary = run()
    print("\nCompute-metrics summary:")
    print(f"- Table: {summary['report_path']}")
    print(f"- Rows: {summary['rows']}")


if __name__ == "__main__":
    main()
