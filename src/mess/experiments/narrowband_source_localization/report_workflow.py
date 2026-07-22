"""Report workflow for source-localization experiment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.narrowband_source_localization.config import ExperimentConfig, build_context
from mess.experiments.narrowband_source_localization.ess_vs_m_plots import run as run_ess_vs_m
from mess.experiments.narrowband_source_localization.posterior_visuals import run as run_posterior_visuals


def _render_summary_markdown(metrics_summary_path: Path) -> str:
    if not metrics_summary_path.exists():
        return "# Source-localization report\n\nNo metrics summary was found.\n"

    with open(metrics_summary_path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)

    lines = [
        "# Source-localization report",
        "",
        "This report summarizes aggregated ESS normalizations by sampler and M.",
        "",
        "| sampler | transition | M | ess_q1_per_energy | ess_q2_per_energy | ess_q1_per_parallel_step | ess_q2_per_parallel_step |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| "
            + f"{row.get('sampler', '')} | {row.get('transition_variant', '')} | {int(row.get('M', 0))} | "
            + f"{float(row.get('ess_q1_per_energy_lik_eval', float('nan'))):.6g} | "
            + f"{float(row.get('ess_q2_per_energy_lik_eval', float('nan'))):.6g} | "
            + f"{float(row.get('ess_q1_per_parallel_lik_step', float('nan'))):.6g} | "
            + f"{float(row.get('ess_q2_per_parallel_lik_step', float('nan'))):.6g} |"
        )

    lines.append("")
    lines.append("The full machine-readable metrics are stored in estimations tables.")
    lines.append("")
    return "\n".join(lines)


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    ess = run_ess_vs_m(cfg)
    for item in ess.get("artifacts", []):
        registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    vis = run_posterior_visuals(cfg)
    for item in vis.get("artifacts", []):
        registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    metrics_summary_path = ctx["estimations_dir"] / "tables" / "metrics_summary.json"
    report_text = _render_summary_markdown(metrics_summary_path)

    reports_dir = ctx["reports_dir"]
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_md_path = reports_dir / "summary.md"
    report_md_path.write_text(report_text, encoding="utf-8")

    registry.add(report_md_path, "report", "Compact markdown summary for source-localization metrics.")

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "report_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of report workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable list of report workflow artifacts.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
