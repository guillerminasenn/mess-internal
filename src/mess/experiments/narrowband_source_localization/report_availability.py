"""Availability checks for expected chain artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from mess.experiments.narrowband_source_localization.config import ExperimentConfig, build_context
from mess.experiments.narrowband_source_localization.naming import chain_path, is_chain_readable
from mess.experiments.narrowband_source_localization.tasks import build_expected_tasks


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]

    rows = []
    missing = 0
    for task in build_expected_tasks(cfg):
        path = chain_path(
            outdir,
            sampler=str(task["sampler"]),
            M=int(task["M"]),
            replicate=int(task["replicate"]),
            transition_variant=str(task.get("transition_variant", "")),
            chain_idx=task.get("chain_idx"),
        )
        present = is_chain_readable(path)
        if not present:
            missing += 1
        rows.append(
            {
                "sampler": str(task["sampler"]),
                "transition_variant": str(task.get("transition_variant", "")),
                "M": int(task["M"]),
                "replicate": int(task["replicate"]),
                "chain_idx": int(task["chain_idx"]) if task.get("chain_idx") is not None else None,
                "present": bool(present),
                "path": str(path.resolve()),
            }
        )

    report = {
        "total_expected": int(len(rows)),
        "total_missing": int(missing),
        "total_present": int(len(rows) - missing),
        "rows": rows,
    }

    out_path = outdir / "diagnostics" / "availability_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Availability expected={len(rows)} present={len(rows) - missing} missing={missing}")
    return {
        "report_path": str(out_path.resolve()),
        "total_expected": int(len(rows)),
        "total_missing": int(missing),
    }


def main() -> None:
    summary = run()
    print("\nAvailability summary:")
    print(f"- Report: {summary['report_path']}")
    print(f"- Missing: {summary['total_missing']} / {summary['total_expected']}")


if __name__ == "__main__":
    main()
