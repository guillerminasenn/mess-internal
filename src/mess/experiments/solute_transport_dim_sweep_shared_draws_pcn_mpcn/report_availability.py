"""Report chain availability for AD dim sweep phase-1 outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.naming import (
    chain_path,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.tasks import (
    build_expected_tasks,
    should_skip_external,
)


def _expected_tasks(cfg: ExperimentConfig) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    for task in build_expected_tasks(cfg):
        if should_skip_external(cfg, task):
            continue
        tasks.append(task)
    return tasks


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["legacy_output_dir"]

    available: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    for task in _expected_tasks(cfg):
        path = chain_path(
            cfg,
            outdir,
            task["d"],
            task["alg"],
            M=task.get("M"),
            proposal_std=task.get("proposal_std"),
            P=task.get("P"),
            rho=task.get("rho"),
        )
        item = {
            "alg": task["alg"],
            "d": task["d"],
            "M": task.get("M"),
            "P": task.get("P"),
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
        "legacy_output_dir": str(outdir.resolve()),
    }

    report_path = ctx["legacy_output_dir"] / "diagnostics" / "chain_availability.json"
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
