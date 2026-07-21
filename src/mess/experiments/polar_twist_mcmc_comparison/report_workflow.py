"""Report workflow for polar-twist experiment stage 5."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_mcmc_comparison.ess_msjd_plots import run as run_ess_msjd
from mess.experiments.polar_twist_mcmc_comparison.mess_ess_vs_m_plots import run as run_mess_ess_vs_m
from mess.experiments.polar_twist_mcmc_comparison.mess_ellipse_diagnostics import (
    run as run_mess_ellipse_diagnostics,
)
from mess.experiments.polar_twist_mcmc_comparison.pairplots import run as run_pairplots
from mess.experiments.polar_twist_mcmc_comparison.panels import run as run_panels
from mess.experiments.polar_twist_mcmc_comparison.rejection_plots import run as run_rejection
from mess.experiments.polar_twist_mcmc_comparison.report_parity_checklist import run as run_checklist
from mess.experiments.polar_twist_mcmc_comparison.traceplots import run as run_traceplots
from mess.experiments.polar_twist_mcmc_comparison.visual_checks import run as run_visual_checks


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    visual = run_visual_checks(cfg)
    trace = run_traceplots(cfg)
    panels = run_panels(cfg)
    ess = run_ess_msjd(cfg)
    mess_vs_m = run_mess_ess_vs_m(cfg)
    ellipse = run_mess_ellipse_diagnostics(cfg)
    rej = run_rejection(cfg)
    pair = run_pairplots(cfg)

    for group in (visual, trace, panels, ess, mess_vs_m, ellipse, rej, pair):
        for item in group.get("artifacts", []):
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
