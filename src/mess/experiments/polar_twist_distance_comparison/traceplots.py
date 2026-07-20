"""Traceplot figures for transition-matrix variants."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_distance_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_distance_comparison.report_helpers import (
    load_chain,
    report_dirs,
    variant_specs,
)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "traceplots_pub"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    specs = variant_specs(cfg)
    artifacts = []
    trace_n = 30000

    for comp in (0, 1):
        fig, axes = plt.subplots(len(specs), 1, figsize=(12, 2.1 * max(1, len(specs))), sharex=True)
        if len(specs) == 1:
            axes = [axes]
        for row, spec in enumerate(specs):
            chain = load_chain(spec["path"])
            ax = axes[row]
            if chain is None or comp >= chain.shape[1]:
                ax.text(0.5, 0.5, "missing chain", transform=ax.transAxes, ha="center", va="center")
            else:
                s = chain[: min(trace_n, chain.shape[0]), comp]
                ax.plot(s, linewidth=0.8, color=spec["color"])
            ax.set_ylabel(spec["label"])
            if row == 0:
                ax.set_title(f"Transition-matrix traceplots for x{comp+1}")
            if row == len(specs) - 1:
                ax.set_xlabel("iteration")

        p = save_figure(fig, out_dir / f"traceplots_variant_comp{comp}.png", dpi=350)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"Traceplot stack by transition-matrix variant for x{comp+1}.",
            }
        )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nTraceplots summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
