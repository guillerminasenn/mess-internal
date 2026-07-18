"""Rejection-rate visualizations for polar-twist experiment."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import load_metrics_rows, report_dirs, row_matches


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "rejection"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    rows, _ = load_metrics_rows(cfg)
    artifacts = []

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    pcn_rows = [r for r in rows if row_matches(r, alg="pcn") and r.get("rho") is not None]
    pcn_rows.sort(key=lambda r: float(r["rho"]))
    if pcn_rows:
        ax.plot([float(r["rho"]) for r in pcn_rows], [float(r.get("rejection", np.nan)) for r in pcn_rows], label="pCN", color="tab:red")

    for p in cfg.P_list:
        rr = [r for r in rows if row_matches(r, alg="mpcn", P=p) and r.get("rho") is not None]
        rr.sort(key=lambda r: float(r["rho"]))
        if rr:
            ax.plot([float(r["rho"]) for r in rr], [float(r.get("rejection", np.nan)) for r in rr], label=f"mPCN P={p}")

    ax.set_title("Rejection rate vs rho")
    ax.set_xlabel("rho")
    ax.set_ylabel("rejection")
    ax.set_ylim(0.0, 1.0)
    ax.legend(loc="best", fontsize=8)
    p1 = save_figure(fig, out_dir / "rejection_vs_rho.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p1.resolve()), "description": "Rejection curves across rho for pCN/mPCN."})

    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    labels = []
    vals = []
    mh = next((r for r in rows if row_matches(r, alg="mh")), None)
    if mh is not None:
        labels.append("MH")
        vals.append(float(mh.get("rejection", np.nan)))
    for m in cfg.M_list:
        r = next((x for x in rows if row_matches(x, alg="mess", M=m)), None)
        if r is None:
            continue
        labels.append(f"MESS {m}")
        vals.append(float(r.get("rejection", np.nan)))
    ax.bar(labels, vals, color=plt.cm.Blues(np.linspace(0.4, 0.9, max(1, len(vals)))))
    ax.set_title("Rejection by method (MH/MESS)")
    ax.set_ylabel("rejection")
    ax.set_ylim(0.0, 1.0)
    ax.tick_params(axis="x", rotation=35)
    p2 = save_figure(fig, out_dir / "rejection_mh_mess.png", dpi=350)
    artifacts.append({"kind": "figure", "path": str(p2.resolve()), "description": "Rejection bars for MH and MESS sweep."})

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nRejection plot summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
