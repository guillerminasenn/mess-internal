"""Report expected versus available chain artifacts for polar-twist EP runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mess.experiments.polar_twist_ep.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_ep.naming import chain_path
from mess.experiments.polar_twist_ep.tasks import build_expected_tasks


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]

    available: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    for task in build_expected_tasks(cfg):
        path = chain_path(
            outdir,
            variant=str(task["variant"]),
            M=int(task["M"]),
            replicate=int(task["replicate"]),
            chain_idx=task.get("chain_idx"),
        )
        item = {
            "variant": task["variant"],
            "M": int(task["M"]),
            "replicate": int(task["replicate"]),
            "chain_idx": task.get("chain_idx"),
            "path": str(path.resolve()),
        }
        if path.exists():
            available.append(item)
        else:
            missing.append(item)

    report = {
        "available": available,
        "missing": missing,
        "available_count": len(available),
        "missing_count": len(missing),
        "estimations_dir": str(outdir.resolve()),
    }

    report_path = outdir / "diagnostics" / "chain_availability.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Available chains: {len(available)}")
    print(f"Missing chains: {len(missing)}")
    print(f"Availability report: {report_path}")

    return {
        "report_path": str(report_path.resolve()),
        "available_count": len(available),
        "missing_count": len(missing),
    }


def main() -> None:
    summary = run()
    print("\nAvailability summary:")
    print(f"- Report: {summary['report_path']}")
    print(f"- Available: {summary['available_count']}")
    print(f"- Missing: {summary['missing_count']}")


if __name__ == "__main__":
    main()
