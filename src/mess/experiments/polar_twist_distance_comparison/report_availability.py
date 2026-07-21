"""Report expected versus available chain artifacts for distance-comparison runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mess.experiments.polar_twist_distance_comparison.config import (
    ExperimentConfig,
    build_context,
    resolve_uniform_chain_path,
)
from mess.experiments.polar_twist_distance_comparison.naming import chain_path, is_chain_readable
from mess.experiments.polar_twist_distance_comparison.tasks import build_expected_tasks


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]

    uniform_external = resolve_uniform_chain_path(cfg, repo_root=ctx["repo_root"])

    available: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    for task in build_expected_tasks(cfg):
        variant = str(task["variant"])
        m = int(task["M"])

        if variant == "uniform" and uniform_external and uniform_external.exists():
            item = {
                "variant": variant,
                "M": m,
                "source": "external",
                "path": str(uniform_external.resolve()),
            }
            available.append(item)
            continue

        path = chain_path(outdir, variant=variant, M=m)
        item = {
            "variant": variant,
            "M": m,
            "source": "local",
            "path": str(path.resolve()),
        }
        if is_chain_readable(path):
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

    report_path = ctx["estimations_dir"] / "diagnostics" / "chain_availability.json"
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
