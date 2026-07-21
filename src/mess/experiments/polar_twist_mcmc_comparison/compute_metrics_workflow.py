"""Metrics workflow for polar-twist experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.polar_twist_mcmc_comparison.benchmark_runtime import run as run_benchmark
from mess.experiments.polar_twist_mcmc_comparison.compute_metrics import run as run_metrics
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_mcmc_comparison.report_availability import run as run_availability


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    avail_summary = run_availability(cfg)
    runtime_summary = run_benchmark(cfg)
    metrics_summary = run_metrics(cfg)

    registry.add(
        path=Path(avail_summary["report_path"]),
        kind="diagnostics",
        description="Availability report of expected vs present chain files.",
    )
    registry.add(
        path=Path(runtime_summary["report_path"]),
        kind="table",
        description="Runtime and acceptance summary from chain metadata.",
    )
    registry.add(
        path=Path(metrics_summary["report_path"]),
        kind="table",
        description="ESS/MSJD summary with per-parameter and mean diagnostics.",
    )

    manifest_json, manifest_md = registry.write(ctx["estimations_dir"] / "manifests", "metrics_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of metrics workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable metrics workflow artifact summary.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
