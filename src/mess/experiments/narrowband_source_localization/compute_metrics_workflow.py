"""Metrics workflow for source-localization experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.narrowband_source_localization.compute_metrics import run as run_metrics
from mess.experiments.narrowband_source_localization.config import ExperimentConfig, build_context
from mess.experiments.narrowband_source_localization.report_availability import run as run_availability


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    avail_summary = run_availability(cfg)
    metrics_summary = run_metrics(cfg)

    registry.add(
        path=Path(avail_summary["report_path"]),
        kind="diagnostics",
        description="Availability report of expected vs present chain files.",
    )
    registry.add(
        path=Path(metrics_summary["report_path"]),
        kind="table",
        description="Aggregated ESS/MSJD summary with EP and MESS normalizations.",
    )
    registry.add(
        path=Path(metrics_summary["per_chain_path"]),
        kind="table",
        description="Per-chain metrics in whitened and physical coordinates.",
    )
    registry.add(
        path=Path(metrics_summary["per_replicate_path"]),
        kind="table",
        description="Per-replicate aggregated metrics for each sampler and M.",
    )

    manifest_json, manifest_md = registry.write(ctx["estimations_dir"] / "manifests", "metrics_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of metrics workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable metrics workflow artifact summary.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
