"""Report workflow for polar-twist warmup convergence experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.polar_twist_convergence.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_convergence.traceplots import run as run_traceplots


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    trace = run_traceplots(cfg)
    for item in trace.get("artifacts", []):
        registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "report_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of report workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable list of report workflow artifacts.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
