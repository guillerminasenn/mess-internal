"""ESS/MSJD comparison panels for transition-matrix variants."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_distance_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_distance_comparison.report_helpers import (
    load_metrics_rows,
    load_runtime_rows,
    report_dirs,
    variant_specs,
)


def _row_by_variant(rows):
    return {str(r.get("variant")): r for r in rows}


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "ess_msjd_variant_panels"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    metrics_rows, _ = load_metrics_rows(cfg)
    runtime_rows, _ = load_runtime_rows(cfg)
    metrics_by_variant = _row_by_variant(metrics_rows)
    runtime_by_variant = _row_by_variant(runtime_rows)
    specs = variant_specs(cfg)

    variants = [s["variant"] for s in specs if s["variant"] in metrics_by_variant]
    labels = [next(s["label"] for s in specs if s["variant"] == v) for v in variants]
    x = np.arange(len(variants))

    ess_mean = [float(metrics_by_variant[v].get("ess_mean", np.nan)) for v in variants]
    ess_x1 = [float(metrics_by_variant[v].get("ess_x1", np.nan)) for v in variants]
    ess_x2 = [float(metrics_by_variant[v].get("ess_x2", np.nan)) for v in variants]

    msjd_mean = [float(metrics_by_variant[v].get("msjd_mean", np.nan)) for v in variants]
    msjd_x1 = [float(metrics_by_variant[v].get("msjd_x1", np.nan)) for v in variants]
    msjd_x2 = [float(metrics_by_variant[v].get("msjd_x2", np.nan)) for v in variants]

    runtime = [float(runtime_by_variant.get(v, {}).get("runtime_sec", np.nan)) for v in variants]

    artifacts = []

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    axes[0].bar(x, ess_mean)
    axes[1].bar(x, msjd_mean)
    axes[0].set_title("ESS mean by variant")
    axes[1].set_title("MSJD mean by variant")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.grid(alpha=0.2, axis="y")
    p = save_figure(fig, out_dir / "ess_msjd_mean_variant.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p.resolve()), "description": "Mean ESS/MSJD by transition-matrix variant."})

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    axes[0, 0].bar(x, ess_x1)
    axes[0, 1].bar(x, ess_x2)
    axes[1, 0].bar(x, msjd_x1)
    axes[1, 1].bar(x, msjd_x2)
    axes[0, 0].set_title("ESS x1")
    axes[0, 1].set_title("ESS x2")
    axes[1, 0].set_title("MSJD x1")
    axes[1, 1].set_title("MSJD x2")
    for ax in axes.ravel():
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.grid(alpha=0.2, axis="y")
    p = save_figure(fig, out_dir / "ess_msjd_components_variant.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p.resolve()), "description": "Component-wise ESS/MSJD by transition-matrix variant."})

    fig, ax = plt.subplots(1, 1, figsize=(6.6, 4.2), constrained_layout=True)
    ax.bar(x, runtime)
    ax.set_title("Runtime by variant")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("seconds")
    ax.grid(alpha=0.2, axis="y")
    p = save_figure(fig, out_dir / "runtime_variant.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p.resolve()), "description": "Runtime by transition-matrix variant."})

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nESS/MSJD variant-panel summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
