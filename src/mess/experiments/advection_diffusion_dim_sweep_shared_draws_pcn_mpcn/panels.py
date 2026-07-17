"""Phase-2 trace/hist panel plots for notebook-11 parity."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_helpers import (
    load_chain,
    phase2_dirs,
)
from mess.experiments.common.plotting_utils import apply_publication_style, color_maps_for_sweeps, save_figure


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = phase2_dirs(cfg)
    out_dir = dirs["fig_root"] / "trace_hist_panels"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    d_cur = cfg.d_list[0]
    components = [0, 1]
    trace_iters = 30000
    hist_bins = 30
    m_colors, p_colors = color_maps_for_sweeps(cfg.M_list, cfg.P_list)

    artifacts = []
    for comp in components:
        fig = plt.figure(figsize=(16, 5.2))
        gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.0, 1.2], wspace=0.22)
        ax_left = fig.add_subplot(gs[0, 0])
        ax_hist = fig.add_subplot(gs[0, 1])
        ax_right = fig.add_subplot(gs[0, 2])

        left_specs = [("mh", None, "MH", "black"), ("mess", 1, "MESS (M=1)", m_colors.get(1, "tab:green")), ("mess", 10, "MESS (M=10)", m_colors.get(10, "tab:olive")), ("mess", 50, "MESS (M=50)", m_colors.get(50, "tab:cyan"))]
        right_specs = [("pcn", None, "pCN", plt.cm.Reds(0.9)), ("mpcn", 10, "mPCN (P=10)", p_colors.get(10, plt.cm.Reds(0.9))), ("mpcn", 50, "mPCN (P=50)", p_colors.get(50, plt.cm.Reds(0.65))), ("mpcn", 100, "mPCN (P=100)", p_colors.get(100, plt.cm.Reds(0.4)))]

        all_series = []

        for alg, param, label, color in left_specs:
            if alg == "mh":
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "mh")
            else:
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "mess", M=param)
            if chain is None or comp >= chain.shape[1]:
                continue
            series = chain[cfg.burn_in : min(chain.shape[0], cfg.burn_in + trace_iters), comp]
            ax_left.plot(series, linewidth=0.6, color=color, label=label)
            ax_hist.hist(chain[cfg.burn_in :, comp], bins=hist_bins, density=True, alpha=0.28, color=color)
            all_series.append(series)

        for alg, param, label, color in right_specs:
            if alg == "pcn":
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "pcn", rho=cfg.rho_algo)
            else:
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "mpcn", P=param, rho=cfg.rho_algo)
            if chain is None or comp >= chain.shape[1]:
                continue
            series = chain[cfg.burn_in : min(chain.shape[0], cfg.burn_in + trace_iters), comp]
            ax_right.plot(series, linewidth=0.6, color=color, label=label)
            ax_hist.hist(chain[cfg.burn_in :, comp], bins=hist_bins, density=True, alpha=0.28, color=color)
            all_series.append(series)

        if all_series:
            low = min(float(np.min(s)) for s in all_series if s.size > 0)
            high = max(float(np.max(s)) for s in all_series if s.size > 0)
            pad = 0.05 * (high - low if high > low else 1.0)
            ax_left.set_ylim(low - pad, high + pad)
            ax_right.set_ylim(low - pad, high + pad)

        ax_left.set_title(f"MESS/MH traces (d={d_cur}, comp={comp})")
        ax_right.set_title(f"pCN/mPCN traces (d={d_cur}, comp={comp})")
        ax_hist.set_title("Posterior histogram")
        ax_left.set_xlabel("Iteration")
        ax_right.set_xlabel("Iteration")
        ax_hist.set_xlabel("Value")
        ax_hist.set_ylabel("Density")
        ax_left.legend(loc="upper right", fontsize=8)
        ax_right.legend(loc="upper right", fontsize=8)

        file_path = save_figure(fig, out_dir / f"trace_hist_d{d_cur}_comp{comp}.png", dpi=600)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(file_path.resolve()),
                "description": f"Trace/hist panel for d={d_cur}, component={comp}.",
            }
        )
        print(f"Saved {file_path}")

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nTrace/hist panel summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
