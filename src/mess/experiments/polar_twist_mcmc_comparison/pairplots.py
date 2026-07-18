"""Pairplot-style posterior scatter outputs for representative methods."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import (
    build_visual_data,
    load_chain,
    report_dirs,
    representative_method_specs,
)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "pairplots"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    vis = build_visual_data(cfg)
    x_true = vis["x_true"]
    specs = representative_method_specs(cfg)

    artifacts = []
    for alg, kwargs, label in specs:
        chain, _ = load_chain(cfg, dirs["estimations_dir"], alg, M=kwargs.get("M"), P=kwargs.get("P"), rho=kwargs.get("rho"))
        if chain is None or chain.shape[1] < 2:
            continue
        post = chain[int(cfg.burn_in) :: int(cfg.thin)]

        fig, ax = plt.subplots(figsize=(5.6, 5.2))
        ax.scatter(post[:, 0], post[:, 1], s=4, alpha=0.18, color="tab:blue")
        ax.scatter([x_true[0]], [x_true[1]], marker="*", s=120, color="tab:orange", edgecolor="black", label="x_true")
        ax.set_xlabel("x1")
        ax.set_ylabel("x2")
        ax.set_title(f"Posterior scatter: {label}")
        ax.legend(loc="best")

        suffix = label.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
        p = save_figure(fig, out_dir / f"pairplot_{suffix}.png", dpi=320)
        artifacts.append({"kind": "figure", "path": str(p.resolve()), "description": f"Posterior scatter for {label}."})

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nPairplots summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
