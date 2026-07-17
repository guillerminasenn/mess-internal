"""Phase-2 traceplot figures for notebook-11 parity."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.phase2_helpers import (
    load_chain,
    phase2_dirs,
)
from mess.experiments.common.plotting_utils import (
    apply_publication_style,
    color_maps_for_sweeps,
    save_figure,
)


def _series(chain: np.ndarray, component: int, trace_iters: int) -> np.ndarray:
    if component >= chain.shape[1]:
        return np.array([])
    end = min(trace_iters, chain.shape[0])
    return chain[:end, component]


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = phase2_dirs(cfg)
    out_dir = dirs["fig_root"] / "traceplots_pub"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    trace_iters = 10000
    plot_components = [0, 1, 8]
    plot_ms = [1, 50]
    plot_p = 50

    m_colors, p_colors = color_maps_for_sweeps(cfg.M_list, cfg.P_list)
    artifacts = []

    for comp in plot_components:
        fig, axes = plt.subplots(len(cfg.d_list), 1, figsize=(12, 2.2 * len(cfg.d_list)), sharex=True)
        if len(cfg.d_list) == 1:
            axes = [axes]

        for row, d in enumerate(cfg.d_list):
            ax = axes[row]
            lines: List[Tuple[str, np.ndarray, str]] = []

            for m in plot_ms:
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d, "mess", M=m)
                if chain is not None:
                    lines.append((f"MESS (M={m})", _series(chain, comp, trace_iters), m_colors.get(m, "tab:green")))

            chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d, "mh")
            if chain is not None:
                lines.append(("MH", _series(chain, comp, trace_iters), "black"))

            chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d, "pcn", rho=cfg.rho_algo)
            if chain is not None:
                lines.append(("pCN", _series(chain, comp, trace_iters), plt.cm.Reds(0.9)))

            chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d, "mpcn", P=plot_p, rho=cfg.rho_algo)
            if chain is not None:
                lines.append((f"mPCN (P={plot_p})", _series(chain, comp, trace_iters), p_colors.get(plot_p, plt.cm.OrRd(0.7))))

            for label, series, color in lines:
                if series.size == 0:
                    continue
                ax.plot(series, linewidth=0.6, label=label, color=color)

            ax.set_ylabel(f"d={d}")
            if row == 0:
                ax.set_title(f"Traceplots for component {comp}")
            if row == len(cfg.d_list) - 1:
                ax.set_xlabel("Iteration")
            if row == 0 and lines:
                ax.legend(loc="upper right", fontsize=9, ncol=4)

        file_path = save_figure(fig, out_dir / f"traceplots_comp{comp}.png", dpi=600)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(file_path.resolve()),
                "description": f"Traceplot grid for component {comp} across dimensions.",
            }
        )
        print(f"Saved {file_path}")

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nTraceplots summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
