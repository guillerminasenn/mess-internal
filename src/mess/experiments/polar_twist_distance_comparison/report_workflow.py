"""Report workflow for polar-twist distance comparison."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.artifacts import ArtifactRegistry
from mess.experiments.common.plotting_utils import apply_publication_style
from mess.experiments.polar_twist_distance_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_distance_comparison.ess_msjd_plots import run as run_ess_msjd
from mess.experiments.polar_twist_distance_comparison.panels import run as run_panels
from mess.experiments.polar_twist_distance_comparison.traceplots import run as run_traceplots


def _load_json(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run(config: Optional[ExperimentConfig] = None) -> None:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    registry = ArtifactRegistry()

    tables_dir = ctx["reports_dir"] / "tables"
    fig_dir = ctx["reports_dir"] / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = tables_dir / "metrics_summary.json"
    runtime_path = tables_dir / "runtime_summary.json"
    if not metrics_path.exists() or not runtime_path.exists():
        raise FileNotFoundError(
            "Missing metrics/runtime tables. Run compute_metrics_workflow before report_workflow."
        )

    metrics_rows = _load_json(metrics_path)
    runtime_rows = _load_json(runtime_path)

    runtime_by_variant = {str(row["variant"]): float(row.get("runtime_sec", np.nan)) for row in runtime_rows}

    # Keep publication order stable even if a subset of variants is present.
    preferred_order = ["uniform", "lp_angular", "lp_euclidean"]
    variants_present = [v for v in preferred_order if any(str(r.get("variant")) == v for r in metrics_rows)]

    ess_vals = []
    msjd_vals = []
    runtime_vals = []
    for variant in variants_present:
        row = next(r for r in metrics_rows if str(r.get("variant")) == variant)
        ess_vals.append(float(row.get("ess_mean", np.nan)))
        msjd_vals.append(float(row.get("msjd_mean", np.nan)))
        runtime_vals.append(float(runtime_by_variant.get(variant, np.nan)))

    apply_publication_style()
    x = np.arange(len(variants_present))

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    axes[0].bar(x, ess_vals)
    axes[0].set_title("ESS mean")
    axes[1].bar(x, msjd_vals)
    axes[1].set_title("MSJD mean")
    axes[2].bar(x, runtime_vals)
    axes[2].set_title("Runtime (sec)")

    labels = [v.replace("lp_", "").replace("_", " ") for v in variants_present]
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.grid(alpha=0.2, axis="y")

    fig.suptitle(f"Polar-twist MESS transition matrix comparison (M={int(cfg.M)})")
    fig_path = fig_dir / "distance_comparison_summary.png"
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    summary_md = ctx["reports_dir"] / "distance_comparison_summary.md"
    lines = [
        "# Polar-Twist Distance Comparison Summary",
        "",
        f"M: {int(cfg.M)}",
        "",
        "| Variant | ESS mean | MSJD mean | Runtime (sec) |",
        "|---|---:|---:|---:|",
    ]
    for variant, ess, msjd, rt in zip(variants_present, ess_vals, msjd_vals, runtime_vals):
        lines.append(f"| {variant} | {ess:.4f} | {msjd:.4f} | {rt:.4f} |")

    with open(summary_md, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    trace = run_traceplots(cfg)
    panels = run_panels(cfg)
    ess = run_ess_msjd(cfg)
    for group in (trace, panels, ess):
        for item in group.get("artifacts", []):
            registry.add(path=Path(item["path"]), kind=item["kind"], description=item["description"])

    registry.add(path=metrics_path, kind="table", description="ESS/MSJD summary table used for report.")
    registry.add(path=runtime_path, kind="table", description="Runtime summary table used for report.")
    registry.add(path=fig_path, kind="figure", description="Side-by-side ESS/MSJD/runtime comparison bar plot.")
    registry.add(path=summary_md, kind="report", description="Markdown summary table for transition-matrix comparison.")

    manifest_json, manifest_md = registry.write(ctx["reports_dir"] / "manifests", "report_workflow_artifacts")
    registry.add(manifest_json, "manifest", "Machine-readable list of report workflow artifacts.")
    registry.add(manifest_md, "manifest", "Human-readable list of report workflow artifacts.")
    registry.print_summary()


def main() -> None:
    run()


if __name__ == "__main__":
    main()
