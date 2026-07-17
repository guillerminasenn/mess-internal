"""Report parity checklist for expected report artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.report_helpers import report_dirs
from mess.experiments.common.checklist import write_checklist


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    fig_root: Path = dirs["fig_root"]
    manifests_dir: Path = dirs["manifests_dir"]

    d0 = cfg.d_list[0]
    checks = [
        {
            "name": "visual_check_A_theta_y",
            "expected_path": str((fig_root / "visual_checks" / "visual_check_A_theta_y.png").resolve()),
            "exists": (fig_root / "visual_checks" / "visual_check_A_theta_y.png").exists(),
            "description": "Main multi-d visual check panel.",
        },
        {
            "name": "visual_check_A_theta_y_columnwise",
            "expected_path": str((fig_root / "visual_checks" / "visual_check_A_theta_y_columnwise.png").resolve()),
            "exists": (fig_root / "visual_checks" / "visual_check_A_theta_y_columnwise.png").exists(),
            "description": "Columnwise visual check panel.",
        },
        {
            "name": f"visual_check_A_d{d0}",
            "expected_path": str((fig_root / "visual_checks" / f"visual_check_A_d{d0}.png").resolve()),
            "exists": (fig_root / "visual_checks" / f"visual_check_A_d{d0}.png").exists(),
            "description": "Single-d A matrix visual check.",
        },
        {
            "name": f"visual_check_theta_y_d{d0}",
            "expected_path": str((fig_root / "visual_checks" / f"visual_check_theta_y_d{d0}.png").resolve()),
            "exists": (fig_root / "visual_checks" / f"visual_check_theta_y_d{d0}.png").exists(),
            "description": "Single-d theta/y visual check.",
        },
        {
            "name": "traceplots_comp0",
            "expected_path": str((fig_root / "traceplots_pub" / "traceplots_comp0.png").resolve()),
            "exists": (fig_root / "traceplots_pub" / "traceplots_comp0.png").exists(),
            "description": "Traceplot grid for component 0.",
        },
        {
            "name": "traceplots_comp1",
            "expected_path": str((fig_root / "traceplots_pub" / "traceplots_comp1.png").resolve()),
            "exists": (fig_root / "traceplots_pub" / "traceplots_comp1.png").exists(),
            "description": "Traceplot grid for component 1.",
        },
        {
            "name": "trace_hist_panel_comp0",
            "expected_path": str((fig_root / "trace_hist_panels" / f"trace_hist_d{d0}_comp0.png").resolve()),
            "exists": (fig_root / "trace_hist_panels" / f"trace_hist_d{d0}_comp0.png").exists(),
            "description": "Trace/hist panel for component 0.",
        },
        {
            "name": "ess_msjd_vs_d_mean",
            "expected_path": str((fig_root / "ess_msjd_vs_d" / "ess_msjd_vs_d_mean.png").resolve()),
            "exists": (fig_root / "ess_msjd_vs_d" / "ess_msjd_vs_d_mean.png").exists(),
            "description": "ESS/MSJD summary plot (linear scale).",
        },
        {
            "name": "ess_msjd_vs_d_mean_log",
            "expected_path": str((fig_root / "ess_msjd_vs_d" / "ess_msjd_vs_d_mean_log.png").resolve()),
            "exists": (fig_root / "ess_msjd_vs_d" / "ess_msjd_vs_d_mean_log.png").exists(),
            "description": "ESS/MSJD summary plot (log scale).",
        },
        {
            "name": "pairplots_directory",
            "expected_path": str((fig_root / "pairplots").resolve()),
            "exists": (fig_root / "pairplots").exists(),
            "description": "Pairplot output directory exists.",
        },
    ]

    md_path = manifests_dir / "report_parity_checklist.md"
    json_path = manifests_dir / "report_parity_checklist.json"
    summary = write_checklist(
        checks=checks,
        markdown_path=md_path,
        json_path=json_path,
        title="Report Artifact Parity Checklist",
    )

    print(f"Saved report checklist markdown: {md_path}")
    print(f"Saved report checklist JSON: {json_path}")

    return {
        "checks": checks,
        "markdown_path": str(md_path.resolve()),
        "json_path": str(json_path.resolve()),
        "passed": summary["passed"],
        "total": summary["total"],
    }


def main() -> None:
    summary = run()
    print("\nReport parity checklist summary:")
    print(f"- Passed: {summary['passed']}/{summary['total']}")
    print(f"- Markdown: {summary['markdown_path']}")
    print(f"- JSON: {summary['json_path']}")


if __name__ == "__main__":
    main()
