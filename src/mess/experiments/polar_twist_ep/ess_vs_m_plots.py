"""EP-ESS versus MESS ESS-vs-M figures, including normalized variants."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_ep.config import ExperimentConfig
from mess.experiments.polar_twist_ep.report_helpers import load_json, report_dirs


def _rows_by_variant(rows, variant: str, m_list):
    selected = [r for r in rows if str(r.get("variant")) == variant]
    by_m = {int(r["M"]): r for r in selected}
    out = []
    for m in sorted(int(v) for v in m_list):
        if m in by_m:
            out.append(by_m[m])
    return out


def _series(rows, key):
    return np.asarray([float(r.get(key, np.nan)) for r in rows], dtype=float)


def _plot_two_curve_three_panel(
    mess_rows,
    ep_rows,
    key_x1,
    key_x2,
    key_mean,
    title,
    y_label,
    out_path: Path,
):
    m_vals = np.asarray([int(r["M"]) for r in mess_rows], dtype=int)

    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.2), sharex=True, constrained_layout=True)
    for ax, key, subtitle in zip(
        axes,
        (key_x1, key_x2, key_mean),
        (r"$x_1$", r"$x_2$", "mean"),
    ):
        ax.plot(m_vals, _series(mess_rows, key), marker="o", linewidth=1.5, color="tab:blue", label="MESS")
        ax.plot(m_vals, _series(ep_rows, key), marker="s", linewidth=1.5, color="tab:orange", label="EP-ESS")
        ax.set_title(subtitle)
        ax.set_xlabel("M")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel(y_label)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=2, frameon=False)
    fig.suptitle(title)
    return save_figure(fig, out_path, dpi=350)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "ess_msjd_vs_rho"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    rows = load_json(dirs["estimations_dir"] / "tables" / "metrics_summary.json")
    mess_rows = _rows_by_variant(rows, "mess", cfg.M_list)
    ep_rows = _rows_by_variant(rows, "ep_ess", cfg.M_list)
    artifacts = []

    if not mess_rows or not ep_rows:
        return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}

    raw_path = _plot_two_curve_three_panel(
        mess_rows,
        ep_rows,
        key_x1="raw_ess_x1",
        key_x2="raw_ess_x2",
        key_mean="raw_ess_mean",
        title="Average raw ESS vs M: MESS vs EP-ESS",
        y_label="Average raw ESS",
        out_path=out_dir / "mess_ess_vs_M_raw.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(raw_path.resolve()),
            "description": "Average raw ESS vs M comparing MESS and EP-ESS (x1, x2, mean).",
        }
    )

    p_path = _plot_two_curve_three_panel(
        mess_rows,
        ep_rows,
        key_x1="ess_x1_per_parallel_lik_step",
        key_x2="ess_x2_per_parallel_lik_step",
        key_mean="ess_mean_per_parallel_lik_step",
        title="Average ESS per parallel likelihood step vs M",
        y_label="Average ESS / parallel likelihood step",
        out_path=out_dir / "mess_ess_vs_M_per_parallel_lik_step.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(p_path.resolve()),
            "description": "Average ESS per parallel likelihood step vs M comparing MESS and EP-ESS.",
        }
    )

    e_path = _plot_two_curve_three_panel(
        mess_rows,
        ep_rows,
        key_x1="ess_x1_per_energy_lik_eval",
        key_x2="ess_x2_per_energy_lik_eval",
        key_mean="ess_mean_per_energy_lik_eval",
        title="Average ESS per energy likelihood evaluation vs M",
        y_label="Average ESS / likelihood evaluation",
        out_path=out_dir / "mess_ess_vs_M_per_energy_lik_eval.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(e_path.resolve()),
            "description": "Average ESS per energy likelihood evaluation vs M comparing MESS and EP-ESS.",
        }
    )

    availability_path = out_dir / "mess_ess_vs_M_availability.json"
    with open(availability_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "has_mess": bool(mess_rows),
                "has_ep_ess": bool(ep_rows),
                "m_values_mess": [int(r["M"]) for r in mess_rows],
                "m_values_ep_ess": [int(r["M"]) for r in ep_rows],
            },
            handle,
            indent=2,
        )
    artifacts.append(
        {
            "kind": "metadata",
            "path": str(availability_path.resolve()),
            "description": "Availability status for MESS vs EP-ESS ESS-vs-M plots.",
        }
    )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nEP ESS-vs-M report summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Artifacts: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
