"""Metrics workflow for polar-twist convergence experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.polar_twist_convergence.compute_metrics import run as run_metrics
from mess.experiments.polar_twist_convergence.config import ExperimentConfig, build_context


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    metrics_summary = run_metrics(cfg)
    registry.add(
        path=Path(metrics_summary["report_path"]),
        kind="table",
        description="Source chain availability table for warmup convergence report.",
    )

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "metrics_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of metrics workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable metrics workflow artifact summary.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
