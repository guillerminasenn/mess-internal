"""Phase-2 visual check plots for notebook-11 parity."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.report_helpers import (
    build_visual_data,
    report_dirs,
)
from mess.experiments.common.plotting_utils import apply_publication_style, save_figure


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "visual_checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    per_dim = {d: build_visual_data(cfg, d) for d in cfg.d_list}
    artifacts = []

    fig, axes = plt.subplots(len(cfg.d_list), 3, figsize=(12, 2.8 * len(cfg.d_list)))
    if len(cfg.d_list) == 1:
        axes = np.array([axes])
    for row, d in enumerate(cfg.d_list):
        data = per_dim[d]
        im = axes[row, 0].imshow(data["A_true"], cmap="coolwarm")
        axes[row, 0].set_title(f"A (d={d})")
        plt.colorbar(im, ax=axes[row, 0], fraction=0.04, pad=0.02)

        axes[row, 1].plot(data["theta_true"], color="tab:blue")
        axes[row, 1].set_title("theta_true")

        obs_idx = data["obs_indices"]
        axes[row, 2].plot(data["theta_true"], color="tab:blue", alpha=0.75, linewidth=1.0)
        axes[row, 2].scatter(obs_idx, data["y"], s=18, color="tab:orange", zorder=3)
        axes[row, 2].set_title("observed y")

    p1 = save_figure(fig, out_dir / "visual_check_A_theta_y.png", dpi=600)
    artifacts.append({"kind": "figure", "path": str(p1.resolve()), "description": "Per-dimension A/theta/y visual check panel."})

    fig, axes = plt.subplots(3, len(cfg.d_list), figsize=(3.8 * len(cfg.d_list), 9))
    for col, d in enumerate(cfg.d_list):
        data = per_dim[d]
        axes[0, col].imshow(data["A_true"], cmap="coolwarm")
        axes[0, col].set_title(f"d={d}")
        axes[1, col].plot(data["theta_true"], color="tab:blue")
        axes[2, col].plot(data["theta_true"], color="tab:blue", alpha=0.75, linewidth=1.0)
        axes[2, col].scatter(data["obs_indices"], data["y"], s=18, color="tab:orange", zorder=3)
    axes[0, 0].set_ylabel("A")
    axes[1, 0].set_ylabel("theta")
    axes[2, 0].set_ylabel("y")
    p2 = save_figure(fig, out_dir / "visual_check_A_theta_y_columnwise.png", dpi=600)
    artifacts.append({"kind": "figure", "path": str(p2.resolve()), "description": "Columnwise A/theta/y visual check panel."})

    d0 = cfg.d_list[0]
    d0_data = per_dim[d0]

    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    im = ax.imshow(d0_data["A_true"], cmap="coolwarm")
    ax.set_title(f"A (d={d0})")
    plt.colorbar(im, ax=ax)
    p3 = save_figure(fig, out_dir / f"visual_check_A_d{d0}.png", dpi=600)
    artifacts.append({"kind": "figure", "path": str(p3.resolve()), "description": f"Single-dimension A matrix check for d={d0}."})

    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    ax.plot(d0_data["theta_true"], label="theta_true", color="tab:blue")
    ax.scatter(d0_data["obs_indices"], d0_data["y"], label="y", color="tab:orange", s=18)
    ax.legend(loc="best")
    ax.set_title(f"theta and y (d={d0})")
    p4 = save_figure(fig, out_dir / f"visual_check_theta_y_d{d0}.png", dpi=600)
    artifacts.append({"kind": "figure", "path": str(p4.resolve()), "description": f"Single-dimension theta/y check for d={d0}."})

    for item in artifacts:
        print(f"Saved {item['path']}")

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nVisual checks summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
