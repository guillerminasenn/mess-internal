"""Report workflow: generate figures and report checklist artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots import (
    run as run_ess_msjd_plots,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.pairplots import (
    run as run_pairplots,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.panels import (
    run as run_panels,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_parity_checklist import (
    run as run_report_checklist,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.traceplots import (
    run as run_traceplots,
)
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.visual_checks import (
    run as run_visual_checks,
)
from mess.experiments.common.artifacts import ArtifactRegistry


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    visual = run_visual_checks(cfg)
    trace = run_traceplots(cfg)
    panels = run_panels(cfg)
    ess = run_ess_msjd_plots(cfg)
    pair = run_pairplots(cfg)

    for group in (visual, trace, panels, ess, pair):
        for item in group.get("artifacts", []):
            registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    checklist = run_report_checklist(cfg)
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
