"""Compact trace/histogram panels for transition-matrix variants."""

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
    out_dir = dirs["fig_root"] / "trace_hist_panels"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    specs = variant_specs(cfg)
    artifacts = []

    for comp in (0, 1):
        fig = plt.figure(figsize=(14, 4.8))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.6, 1.0], wspace=0.25)
        ax_trace = fig.add_subplot(gs[0, 0])
        ax_hist = fig.add_subplot(gs[0, 1])

        for spec in specs:
            chain = load_chain(spec["path"])
            if chain is None or comp >= chain.shape[1]:
                continue
            post = chain[int(cfg.burn_in) :: int(cfg.thin), comp]
            ax_trace.plot(post[: min(20000, post.shape[0])], color=spec["color"], linewidth=0.8, label=spec["label"])
            ax_hist.hist(post, bins=35, density=True, alpha=0.26, color=spec["color"], label=spec["label"])

        ax_trace.set_title(f"Trace panel (x{comp+1})")
        ax_hist.set_title(f"Posterior histogram (x{comp+1})")
        ax_trace.set_xlabel("iteration")
        ax_trace.set_ylabel(f"x{comp+1}")
        ax_hist.set_xlabel(f"x{comp+1}")
        ax_hist.set_ylabel("density")
        ax_trace.legend(loc="upper right", fontsize=9)
        ax_hist.legend(loc="upper right", fontsize=9)

        p = save_figure(fig, out_dir / f"trace_hist_variant_comp{comp}.png", dpi=350)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"Trace/hist panel by transition-matrix variant for x{comp+1}.",
            }
        )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nPanel summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
