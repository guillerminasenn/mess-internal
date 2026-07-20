"""Warmup traceplot figures for polar-twist convergence comparisons."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_convergence.config import ExperimentConfig
from mess.experiments.polar_twist_convergence.report_helpers import load_chain, report_dirs, resolve_sources


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "warmup_traceplots"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    source = resolve_sources(cfg)
    specs = source["specs"]
    artifacts = []
    warmup_n = max(1, int(cfg.warmup_iters))

    for comp in (0, 1):
        fig, axes = plt.subplots(len(specs), 1, figsize=(13, 1.6 * max(1, len(specs))), sharex=True)
        if len(specs) == 1:
            axes = [axes]

        for row, spec in enumerate(specs):
            ax = axes[row]
            chain = load_chain(spec["path"])
            if chain is None or comp >= chain.shape[1]:
                ax.text(0.5, 0.5, "missing chain", transform=ax.transAxes, ha="center", va="center")
            else:
                segment = chain[: min(warmup_n, chain.shape[0]), comp]
                ax.plot(segment, linewidth=0.8)
            ax.set_ylabel(spec["label"], fontsize=8)
            if row == 0:
                ax.set_title(f"Warmup convergence traceplots for x{comp + 1} (first {warmup_n} iterations)")
            if row == len(specs) - 1:
                ax.set_xlabel("iteration")

        p = save_figure(fig, out_dir / f"traceplots_warmup_x{comp + 1}.png", dpi=350)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"Warmup traceplot stack for x{comp + 1}.",
            }
        )

    return {
        "artifacts": artifacts,
        "output_dir": str(out_dir.resolve()),
        "method_count": len(specs),
        "warmup_iters": warmup_n,
    }


def main() -> None:
    summary = run()
    print("\nTraceplots summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")
    print(f"- Methods: {summary['method_count']}")


if __name__ == "__main__":
    main()
