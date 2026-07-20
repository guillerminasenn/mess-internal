"""Checklist of expected report artifacts for polar-twist workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from mess.experiments.common.checklist import write_checklist
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import report_dirs


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    fig_root: Path = dirs["fig_root"]
    manifests_dir: Path = dirs["manifests_dir"]

    checks = [
        {
            "name": "visual_check_data_points",
            "expected_path": str((fig_root / "visual_checks" / "visual_check_data_points.png").resolve()),
            "exists": (fig_root / "visual_checks" / "visual_check_data_points.png").exists(),
            "description": "Observed/latent data sanity visual.",
        },
        {
            "name": "traceplots_comp0",
            "expected_path": str((fig_root / "traceplots_pub" / "traceplots_comp0.png").resolve()),
            "exists": (fig_root / "traceplots_pub" / "traceplots_comp0.png").exists(),
            "description": "Traceplot stack for x1.",
        },
        {
            "name": "traceplots_comp1",
            "expected_path": str((fig_root / "traceplots_pub" / "traceplots_comp1.png").resolve()),
            "exists": (fig_root / "traceplots_pub" / "traceplots_comp1.png").exists(),
            "description": "Traceplot stack for x2.",
        },
        {
            "name": "panel_comp0",
            "expected_path": str((fig_root / "trace_hist_panels" / "trace_hist_comp0.png").resolve()),
            "exists": (fig_root / "trace_hist_panels" / "trace_hist_comp0.png").exists(),
            "description": "Trace/hist panel for x1.",
        },
        {
            "name": "ess_msjd_vs_rho_mean",
            "expected_path": str((fig_root / "ess_msjd_vs_rho" / "ess_msjd_vs_rho_mean.png").resolve()),
            "exists": (fig_root / "ess_msjd_vs_rho" / "ess_msjd_vs_rho_mean.png").exists(),
            "description": "ESS/MSJD rho summary plot (mean).",
        },
        {
            "name": "rejection_vs_rho",
            "expected_path": str((fig_root / "rejection" / "rejection_vs_rho.png").resolve()),
            "exists": (fig_root / "rejection" / "rejection_vs_rho.png").exists(),
            "description": "Rejection-vs-rho plot.",
        },
        {
            "name": "pairplots_directory",
            "expected_path": str((fig_root / "pairplots").resolve()),
            "exists": (fig_root / "pairplots").exists(),
            "description": "Pairplot output directory exists.",
        },
        {
            "name": "mess_ellipse_diagnostics_directory",
            "expected_path": str((fig_root / "mess_ellipse_diagnostics").resolve()),
            "exists": (fig_root / "mess_ellipse_diagnostics").exists(),
            "description": "MESS ellipse diagnostics output directory exists (if traces were captured).",
        },
    ]

    md_path = manifests_dir / "report_parity_checklist.md"
    json_path = manifests_dir / "report_parity_checklist.json"
    summary = write_checklist(
        checks=checks,
        markdown_path=md_path,
        json_path=json_path,
        title="Polar-Twist Report Artifact Parity Checklist",
    )

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
