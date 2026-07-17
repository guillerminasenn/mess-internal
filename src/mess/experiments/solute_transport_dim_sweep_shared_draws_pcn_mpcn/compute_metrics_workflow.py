"""Metrics workflow: availability, runtime summary, and ESS/MSJD summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.benchmark_runtime import (
    run as run_benchmark,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.compute_metrics import (
    run as run_metrics,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_availability import (
    run as run_availability,
)
from mess.experiments.common.artifacts import ArtifactRegistry


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
        description="Runtime benchmark summary from chain metadata.",
    )
    registry.add(
        path=Path(metrics_summary["report_path"]),
        kind="table",
        description="ESS and MSJD diagnostics summary across chains.",
    )

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "metrics_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of metrics workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable metrics workflow artifact summary.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
