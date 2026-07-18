"""Visual sanity checks for polar-twist data and posterior geometry."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import build_visual_data, report_dirs
from mess.problems.polar_twist import f_polar_twist


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "visual_checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    vis = build_visual_data(cfg)
    x_true = vis["x_true"]
    y_obs = vis["y_obs"]

    artifacts = []

    fig, ax = plt.subplots(figsize=(6.5, 5.6))
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(2.0 * np.cos(t), 2.0 * np.sin(t), linestyle="--", linewidth=1.0, color="gray", alpha=0.6, label="radius 2")
    ax.scatter([x_true[0]], [x_true[1]], s=80, color="tab:blue", label="x_true")
    ax.scatter([y_obs[0]], [y_obs[1]], s=80, color="tab:orange", label="y_obs")
    ax.set_xlabel("x1 / y1")
    ax.set_ylabel("x2 / y2")
    ax.set_title("Polar-twist data sanity check")
    ax.legend(loc="best")
    p1 = save_figure(fig, out_dir / "visual_check_data_points.png", dpi=400)
    artifacts.append({"kind": "figure", "path": str(p1.resolve()), "description": "Observed and latent points in state/observation space."})

    # Coarse posterior log-density heatmap for visual shape checking.
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    grid = np.linspace(-8.0, 8.0, 161)
    xx, yy = np.meshgrid(grid, grid)
    zz = np.zeros_like(xx)
    problem = vis["problem"]
    for i in range(xx.shape[0]):
        pts = np.column_stack([xx[i], yy[i]])
        zz[i] = [problem.log_posterior(p) for p in pts]
    c = ax.contourf(xx, yy, zz, levels=25, cmap="viridis")
    ax.scatter([x_true[0]], [x_true[1]], s=30, color="white", edgecolor="black", label="x_true")
    ax.set_title("Log-posterior contour (coarse)")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.legend(loc="upper right")
    fig.colorbar(c, ax=ax, fraction=0.045, pad=0.03)
    p2 = save_figure(fig, out_dir / "visual_check_logposterior_contour.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p2.resolve()), "description": "Coarse contour map of posterior log-density."})

    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    radii = np.linspace(0.0, 8.0, 200)
    norm_fx = []
    for r in radii:
        x = np.array([r / np.sqrt(2.0), r / np.sqrt(2.0)])
        fx = f_polar_twist(x, alpha=cfg.alpha, weight_x=cfg.weight_x, weight_y=cfg.weight_y)
        norm_fx.append(np.linalg.norm(fx))
    ax.plot(radii, norm_fx, color="tab:green", linewidth=1.5)
    ax.set_xlabel("radius ||x||")
    ax.set_ylabel("||f(x)||")
    ax.set_title("Forward map norm along diagonal ray")
    p3 = save_figure(fig, out_dir / "visual_check_forward_norm.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p3.resolve()), "description": "Forward-map magnitude diagnostic."})

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nVisual checks summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
