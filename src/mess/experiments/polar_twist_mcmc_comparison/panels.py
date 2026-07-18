"""Compact trace and histogram panel plots."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import (
    load_chain,
    report_dirs,
    representative_method_specs,
)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "trace_hist_panels"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    specs = representative_method_specs(cfg)
    artifacts = []

    for comp in (0, 1):
        fig = plt.figure(figsize=(16, 5.4))
        gs = fig.add_gridspec(1, 3, width_ratios=[1.4, 1.0, 1.4], wspace=0.25)
        ax_left = fig.add_subplot(gs[0, 0])
        ax_hist = fig.add_subplot(gs[0, 1])
        ax_right = fig.add_subplot(gs[0, 2])

        for idx, (alg, kwargs, label) in enumerate(specs):
            chain, _ = load_chain(cfg, dirs["estimations_dir"], alg, M=kwargs.get("M"), P=kwargs.get("P"), rho=kwargs.get("rho"))
            if chain is None or comp >= chain.shape[1]:
                continue
            post = chain[int(cfg.burn_in) :: int(cfg.thin), comp]
            color = plt.cm.tab10(idx % 10)
            if idx < 3:
                ax_left.plot(post[: min(20000, post.shape[0])], color=color, linewidth=0.7, label=label)
            else:
                ax_right.plot(post[: min(20000, post.shape[0])], color=color, linewidth=0.7, label=label)
            ax_hist.hist(post, bins=35, density=True, alpha=0.28, color=color)

        ax_left.set_title(f"Trace panel A (x{comp+1})")
        ax_right.set_title(f"Trace panel B (x{comp+1})")
        ax_hist.set_title("Posterior histogram")
        ax_left.set_xlabel("iteration")
        ax_right.set_xlabel("iteration")
        ax_hist.set_xlabel(f"x{comp+1}")
        ax_hist.set_ylabel("density")
        ax_left.legend(loc="upper right", fontsize=8)
        ax_right.legend(loc="upper right", fontsize=8)

        p = save_figure(fig, out_dir / f"trace_hist_comp{comp}.png", dpi=350)
        artifacts.append({"kind": "figure", "path": str(p.resolve()), "description": f"Trace/hist panel for x{comp+1}."})

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nPanel summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
