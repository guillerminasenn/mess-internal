"""Checklist of expected report artifacts for polar-twist EP workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from mess.experiments.common.checklist import write_checklist
from mess.experiments.polar_twist_ep.config import ExperimentConfig
from mess.experiments.polar_twist_ep.report_helpers import report_dirs


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    fig_root: Path = dirs["fig_root"]
    manifests_dir: Path = dirs["manifests_dir"]

    checks = [
        {
            "name": "mess_ess_vs_m_raw",
            "expected_path": str((fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_raw.png").resolve()),
            "exists": (fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_raw.png").exists(),
            "description": "Average raw ESS-vs-M plot comparing MESS and EP-ESS.",
        },
        {
            "name": "mess_ess_vs_m_per_parallel_lik_step",
            "expected_path": str((fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_per_parallel_lik_step.png").resolve()),
            "exists": (fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_per_parallel_lik_step.png").exists(),
            "description": "Average ESS per parallel likelihood step vs M comparing MESS and EP-ESS.",
        },
        {
            "name": "mess_ess_vs_m_per_energy_lik_eval",
            "expected_path": str((fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_per_energy_lik_eval.png").resolve()),
            "exists": (fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_per_energy_lik_eval.png").exists(),
            "description": "Average ESS per energy likelihood eval vs M comparing MESS and EP-ESS.",
        },
        {
            "name": "mess_ess_vs_m_availability",
            "expected_path": str((fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_availability.json").resolve()),
            "exists": (fig_root / "ess_msjd_vs_rho" / "mess_ess_vs_M_availability.json").exists(),
            "description": "Availability status JSON for MESS vs EP-ESS ESS-vs-M plotting.",
        },
    ]

    md_path = manifests_dir / "report_parity_checklist.md"
    json_path = manifests_dir / "report_parity_checklist.json"
    summary = write_checklist(
        checks=checks,
        markdown_path=md_path,
        json_path=json_path,
        title="Polar-Twist EP Report Artifact Parity Checklist",
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
