"""Report workflow for polar-twist EP experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.polar_twist_ep.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_ep.ess_vs_m_plots import run as run_ess_vs_m
from mess.experiments.polar_twist_ep.report_parity_checklist import run as run_checklist


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    ess = run_ess_vs_m(cfg)
    for item in ess.get("artifacts", []):
        registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    checklist = run_checklist(cfg)
    registry.add(
        path=Path(checklist["markdown_path"]),
        kind="checklist",
        description=f"Report parity checklist markdown ({checklist['passed']}/{checklist['total']} passed).",
    )
    registry.add(
        path=Path(checklist["json_path"]),
        kind="checklist",
        description="Report parity checklist machine-readable JSON.",
    )

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "report_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of report workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable list of report workflow artifacts.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
