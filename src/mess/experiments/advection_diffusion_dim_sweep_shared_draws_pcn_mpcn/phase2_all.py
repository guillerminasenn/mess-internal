"""Orchestrate phase-2 plotting pipeline and parity checklist."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots import (
    run as run_ess_msjd_plots,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.pairplots import (
    run as run_pairplots,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.panels import (
    run as run_panels,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_parity_checklist import (
    run as run_parity_checklist,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.traceplots import (
    run as run_traceplots,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.visual_checks import (
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

    parity = run_parity_checklist(cfg)
    registry.add(
        path=Path(parity["markdown_path"]),
        kind="checklist",
        description=f"Notebook parity checklist markdown ({parity['passed']}/{parity['total']} passed).",
    )
    registry.add(
        path=Path(parity["json_path"]),
        kind="checklist",
        description="Notebook parity checklist machine-readable JSON.",
    )

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "phase2_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of phase-2 artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable list of phase-2 artifacts.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
