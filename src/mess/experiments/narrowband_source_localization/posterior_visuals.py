"""Posterior and likelihood visualization figures for source localization."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.narrowband_source_localization.config import ExperimentConfig
from mess.experiments.narrowband_source_localization.report_helpers import report_dirs
from mess.problems import build_narrowband_source_localization_problem


def _load_chain(path: Path, burn_in: int, thin: int) -> Optional[np.ndarray]:
    if not path.exists():
        return None
    with np.load(path) as payload:
        chain = np.asarray(payload["chain"], dtype=float)
    return chain[int(burn_in) :: int(thin)]


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "posterior_geometry"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    problem, data = build_narrowband_source_localization_problem(
        sensors_m=np.asarray(cfg.sensors_m, dtype=float),
        frequencies_hz=cfg.frequencies_hz,
        propagation_speed=float(cfg.propagation_speed),
        true_source_m=cfg.true_source_m,
        tau=cfg.tau,
        sigma=cfg.sigma,
        prior_mean_m=cfg.prior_mean_m,
        prior_cov_m=cfg.prior_cov_m(),
        amplitude_model=cfg.amplitude_model,
        gamma=float(cfg.amplitude_gamma),
        r_min=float(cfg.r_min),
        data_seed=int(cfg.data_seed),
    )

    grid = problem.reference_grid_evaluation(
        reference_box_m=tuple(float(v) for v in cfg.reference_box_m),
        grid_size=int(cfg.reference_grid_size),
    )
    q1 = np.asarray(grid["q1"], dtype=float)
    q2 = np.asarray(grid["q2"], dtype=float)
    Q1 = np.asarray(grid["Q1"], dtype=float)
    Q2 = np.asarray(grid["Q2"], dtype=float)
    ll = np.asarray(grid["log_likelihood"], dtype=float)
    lpst = np.asarray(grid["log_posterior"], dtype=float)

    posterior = np.exp(lpst - np.max(lpst))

    artifacts = []

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), constrained_layout=True)

    c1 = axes[0].contourf(Q1, Q2, ll, levels=40, cmap="viridis")
    axes[0].contour(Q1, Q2, ll, levels=12, colors="white", linewidths=0.55, alpha=0.7)
    axes[0].scatter(data.sensors_m[:, 0], data.sensors_m[:, 1], marker="^", s=55, color="tab:red", label="sensors")
    axes[0].scatter([data.q_true[0]], [data.q_true[1]], marker="*", s=130, color="gold", edgecolor="black", label="true source")
    axes[0].set_title("Log-likelihood in physical space q")
    axes[0].set_xlabel("q1")
    axes[0].set_ylabel("q2")
    axes[0].legend(loc="best")
    fig.colorbar(c1, ax=axes[0], fraction=0.047, pad=0.04)

    c2 = axes[1].contourf(Q1, Q2, posterior, levels=40, cmap="magma")
    axes[1].contour(Q1, Q2, posterior, levels=12, colors="white", linewidths=0.55, alpha=0.7)
    axes[1].scatter(data.sensors_m[:, 0], data.sensors_m[:, 1], marker="^", s=55, color="tab:red")
    axes[1].scatter([data.q_true[0]], [data.q_true[1]], marker="*", s=130, color="gold", edgecolor="black")
    axes[1].set_title("Unnormalized posterior density in q")
    axes[1].set_xlabel("q1")
    axes[1].set_ylabel("q2")
    fig.colorbar(c2, ax=axes[1], fraction=0.047, pad=0.04)

    p = save_figure(fig, out_dir / "likelihood_and_posterior_contours_q.png", dpi=340)
    artifacts.append(
        {
            "kind": "figure",
            "path": str(p.resolve()),
            "description": "Likelihood and posterior contour maps in 2D physical source space.",
        }
    )

    est = dirs["estimations_dir"]
    m_target = int(max(cfg.M_list))
    mess_chain = _load_chain(est / f"chain_mess_uniform_M{m_target}_rep000.npz", cfg.burn_in, cfg.thin)
    ep_chain = _load_chain(est / f"chain_ep_ess_M{m_target}_rep000_chain000.npz", cfg.burn_in, cfg.thin)
    mpcn_chain = _load_chain(est / f"chain_mpcn_P{m_target}_rep000.npz", cfg.burn_in, cfg.thin)

    if mess_chain is not None and ep_chain is not None and mpcn_chain is not None:
        mess_q = problem.whitened_to_physical(mess_chain)
        ep_q = problem.whitened_to_physical(ep_chain)
        mpcn_q = problem.whitened_to_physical(mpcn_chain)

        fig2, axes2 = plt.subplots(2, 2, figsize=(10.8, 8.6), constrained_layout=True)

        bins = 45
        axes2[0, 0].hist(mess_q[:, 0], bins=bins, density=True, alpha=0.55, label="MESS", color="tab:blue")
        axes2[0, 0].hist(ep_q[:, 0], bins=bins, density=True, alpha=0.45, label="EP-ESS chain 0", color="tab:orange")
        axes2[0, 0].hist(mpcn_q[:, 0], bins=bins, density=True, alpha=0.40, label="MPCN", color="tab:green")
        axes2[0, 0].set_title("Posterior marginal q1")
        axes2[0, 0].set_xlabel("q1")
        axes2[0, 0].legend(loc="best", fontsize=8)

        axes2[0, 1].hist(mess_q[:, 1], bins=bins, density=True, alpha=0.55, label="MESS", color="tab:blue")
        axes2[0, 1].hist(ep_q[:, 1], bins=bins, density=True, alpha=0.45, label="EP-ESS chain 0", color="tab:orange")
        axes2[0, 1].hist(mpcn_q[:, 1], bins=bins, density=True, alpha=0.40, label="MPCN", color="tab:green")
        axes2[0, 1].set_title("Posterior marginal q2")
        axes2[0, 1].set_xlabel("q2")

        axes2[1, 0].scatter(mess_q[:, 0], mess_q[:, 1], s=4, alpha=0.14, color="tab:blue", label="MESS")
        axes2[1, 0].scatter(ep_q[:, 0], ep_q[:, 1], s=4, alpha=0.14, color="tab:orange", label="EP-ESS chain 0")
        axes2[1, 0].scatter(mpcn_q[:, 0], mpcn_q[:, 1], s=4, alpha=0.14, color="tab:green", label="MPCN")
        axes2[1, 0].scatter([data.q_true[0]], [data.q_true[1]], marker="*", s=130, color="gold", edgecolor="black", label="true")
        axes2[1, 0].set_title(f"Posterior pair scatter (M={m_target}, rep=0)")
        axes2[1, 0].set_xlabel("q1")
        axes2[1, 0].set_ylabel("q2")
        axes2[1, 0].legend(loc="best", fontsize=8)

        axes2[1, 1].contourf(Q1, Q2, posterior, levels=30, cmap="Greys", alpha=0.6)
        axes2[1, 1].scatter(mess_q[:, 0], mess_q[:, 1], s=3, alpha=0.10, color="tab:blue", label="MESS")
        axes2[1, 1].scatter([data.q_true[0]], [data.q_true[1]], marker="*", s=130, color="gold", edgecolor="black")
        axes2[1, 1].set_title("MESS samples over posterior contours")
        axes2[1, 1].set_xlabel("q1")
        axes2[1, 1].set_ylabel("q2")
        axes2[1, 1].legend(loc="best", fontsize=8)

        p2 = save_figure(fig2, out_dir / "posterior_histograms_and_pairplot_q.png", dpi=340)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p2.resolve()),
                "description": "Posterior marginals and pairplot-style scatter for representative chains.",
            }
        )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nPosterior-visual report summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
