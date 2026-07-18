"""ESS/MSJD reporting plots for polar-twist comparisons."""

from __future__ import annotations

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import load_metrics_rows, report_dirs, row_matches


def _rho_series(rows, alg: str, metric: str, P: Optional[int] = None):
    out = {}
    for r in rows:
        if not row_matches(r, alg=alg, P=P):
            continue
        if r.get("rho") is None:
            continue
        out[float(r["rho"])] = float(r.get(metric, np.nan))
    return out


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "ess_msjd_vs_rho"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    rows, _ = load_metrics_rows(cfg)
    artifacts = []

    plot_specs = [
        ("ess_mean", "msjd_mean", "mean"),
        ("ess_x1", "msjd_x1", "x1"),
        ("ess_x2", "msjd_x2", "x2"),
    ]

    for ess_key, msjd_key, suffix in plot_specs:
        fig, axes = plt.subplots(1, 2, figsize=(14.2, 5.2), sharex=True)
        ax_e, ax_m = axes

        pcn_s = _rho_series(rows, alg="pcn", metric=ess_key)
        ax_e.plot(sorted(pcn_s.keys()), [pcn_s[k] for k in sorted(pcn_s.keys())], color="tab:red", label="pCN")
        pcn_s = _rho_series(rows, alg="pcn", metric=msjd_key)
        ax_m.plot(sorted(pcn_s.keys()), [pcn_s[k] for k in sorted(pcn_s.keys())], color="tab:red", label="pCN")

        for p in cfg.P_list:
            mpcn_e = _rho_series(rows, alg="mpcn", P=p, metric=ess_key)
            mpcn_m = _rho_series(rows, alg="mpcn", P=p, metric=msjd_key)
            x = sorted(mpcn_e.keys())
            if not x:
                continue
            ax_e.plot(x, [mpcn_e[k] for k in x], linewidth=1.0, label=f"mPCN P={p}")
            ax_m.plot(x, [mpcn_m[k] for k in x], linewidth=1.0, label=f"mPCN P={p}")

        # Horizontal references for MH and MESS
        mh = next((r for r in rows if row_matches(r, alg="mh")), None)
        if mh is not None:
            ax_e.axhline(float(mh.get(ess_key, np.nan)), color="black", linestyle="--", label="MH")
            ax_m.axhline(float(mh.get(msjd_key, np.nan)), color="black", linestyle="--", label="MH")
        for m in cfg.M_list:
            r = next((x for x in rows if row_matches(x, alg="mess", M=m)), None)
            if r is None:
                continue
            ax_e.axhline(float(r.get(ess_key, np.nan)), linestyle=":", linewidth=0.9, label=f"MESS M={m}")
            ax_m.axhline(float(r.get(msjd_key, np.nan)), linestyle=":", linewidth=0.9, label=f"MESS M={m}")

        ax_e.set_title(f"ESS vs rho ({suffix})")
        ax_m.set_title(f"MSJD vs rho ({suffix})")
        ax_e.set_xlabel("rho")
        ax_m.set_xlabel("rho")
        ax_e.set_ylabel("ESS")
        ax_m.set_ylabel("MSJD")
        handles, labels = ax_e.get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=4, frameon=False)
        fig.tight_layout(rect=(0, 0, 1, 0.94))

        p = save_figure(fig, out_dir / f"ess_msjd_vs_rho_{suffix}.png", dpi=350)
        artifacts.append({"kind": "figure", "path": str(p.resolve()), "description": f"ESS/MSJD vs rho for {suffix}."})

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nESS/MSJD report summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
