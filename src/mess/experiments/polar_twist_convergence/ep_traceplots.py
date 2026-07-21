"""Warmup traceplots comparing MESS and EP-ESS branches from polar_twist_ep chains."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_convergence.config import ExperimentConfig
from mess.experiments.polar_twist_convergence.report_helpers import load_ep_grouped_chains, report_dirs


def _ep_group_mean(chains):
    if not chains:
        return None
    n = min(arr.shape[0] for arr in chains)
    if n <= 0:
        return None
    stack = np.stack([arr[:n] for arr in chains], axis=0)
    return np.mean(stack, axis=0)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "warmup_traceplots"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    grouped = load_ep_grouped_chains(cfg)
    warmup_n = max(1, int(cfg.warmup_iters))
    rep = int(cfg.ep_replicate_for_trace)
    artifacts = []

    for comp in (0, 1):
        fig, ax = plt.subplots(1, 1, figsize=(12.5, 4.6), constrained_layout=True)
        for m in sorted(int(v) for v in cfg.ep_m_list):
            mess = grouped.get(("mess", int(m), rep), [])
            ep = grouped.get(("ep_ess", int(m), rep), [])

            if mess:
                series = mess[0][:warmup_n, comp]
                ax.plot(series, linewidth=1.0, alpha=0.9, label=f"MESS M={m}")

            ep_mean = _ep_group_mean(ep)
            if ep_mean is not None and comp < ep_mean.shape[1]:
                ax.plot(
                    ep_mean[:warmup_n, comp],
                    linewidth=1.0,
                    alpha=0.9,
                    linestyle="--",
                    label=f"EP-ESS M={m}",
                )

        ax.set_title(f"Warmup traceplots from EP experiment for x{comp + 1} (replicate {rep})")
        ax.set_xlabel("iteration")
        ax.set_ylabel(f"x{comp + 1}")
        ax.grid(alpha=0.2)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper right", ncol=2, frameon=False, fontsize=8)

        p = save_figure(fig, out_dir / f"traceplots_ep_warmup_x{comp + 1}.png", dpi=350)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"EP-source warmup traceplot comparison for x{comp + 1}.",
            }
        )

    return {
        "artifacts": artifacts,
        "output_dir": str(out_dir.resolve()),
        "warmup_iters": warmup_n,
    }


def main() -> None:
    summary = run()
    print("\nEP warmup traceplots summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
