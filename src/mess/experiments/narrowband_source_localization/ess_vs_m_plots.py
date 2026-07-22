"""ESS-vs-M figures for narrowband source-localization experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.narrowband_source_localization.config import ExperimentConfig
from mess.experiments.narrowband_source_localization.report_helpers import load_json, report_dirs


def _rows(rows, sampler: str, variant: str, m_list):
    selected = [
        r
        for r in rows
        if str(r.get("sampler")) == sampler and str(r.get("transition_variant")) == variant
    ]
    by_m = {int(r["M"]): r for r in selected}
    out = []
    for m in sorted(int(v) for v in m_list):
        if m in by_m:
            out.append(by_m[m])
    return out


def _series(rows, key):
    return np.asarray([float(r.get(key, np.nan)) for r in rows], dtype=float)


def _plot_two_curve_three_panel(
    left_rows,
    right_rows,
    left_label,
    right_label,
    key_q1,
    key_q2,
    key_ll,
    title,
    y_label,
    out_path: Path,
):
    m_vals = np.asarray([int(r["M"]) for r in left_rows], dtype=int)

    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.2), sharex=True, constrained_layout=True)
    for ax, key, subtitle in zip(
        axes,
        (key_q1, key_q2, key_ll),
        (r"$q_1$", r"$q_2$", r"$\log L(z_t)=\log p(y\mid z_t)$"),
    ):
        ax.plot(m_vals, _series(left_rows, key), marker="o", linewidth=1.5, color="tab:blue", label=left_label)
        ax.plot(m_vals, _series(right_rows, key), marker="s", linewidth=1.5, color="tab:orange", label=right_label)
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
    out_dir = dirs["fig_root"] / "ess_msjd_vs_M"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    rows = load_json(dirs["estimations_dir"] / "tables" / "metrics_summary.json")
    mess_rows = _rows(rows, "mess", "uniform", cfg.M_list)
    ep_rows = _rows(rows, "ep_ess", "uniform", cfg.M_list)

    artifacts = []
    if not mess_rows or not ep_rows:
        return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}

    raw_path = _plot_two_curve_three_panel(
        mess_rows,
        ep_rows,
        left_label="MESS",
        right_label="EP-ESS",
        key_q1="raw_ess_q1",
        key_q2="raw_ess_q2",
        key_ll="raw_ess_log_likelihood",
        title="Average raw ESS vs M: MESS vs EP-ESS",
        y_label="Average raw ESS",
        out_path=out_dir / "mess_vs_ep_raw_ess_vs_M.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(raw_path.resolve()),
            "description": "Average raw ESS vs M comparing MESS and EP-ESS (q1, q2, logL).",
        }
    )

    parallel_path = _plot_two_curve_three_panel(
        mess_rows,
        ep_rows,
        left_label="MESS",
        right_label="EP-ESS",
        key_q1="ess_q1_per_parallel_lik_step",
        key_q2="ess_q2_per_parallel_lik_step",
        key_ll="ess_ll_per_parallel_lik_step",
        title="Average ESS per parallel likelihood step vs M",
        y_label="Average ESS / parallel likelihood step",
        out_path=out_dir / "mess_vs_ep_ess_per_parallel_step_vs_M.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(parallel_path.resolve()),
            "description": "Average ESS per parallel likelihood step vs M comparing MESS and EP-ESS.",
        }
    )

    energy_path = _plot_two_curve_three_panel(
        mess_rows,
        ep_rows,
        left_label="MESS",
        right_label="EP-ESS",
        key_q1="ess_q1_per_energy_lik_eval",
        key_q2="ess_q2_per_energy_lik_eval",
        key_ll="ess_ll_per_energy_lik_eval",
        title="Average ESS per total likelihood evaluation vs M",
        y_label="Average ESS / likelihood evaluation",
        out_path=out_dir / "mess_vs_ep_ess_per_lik_eval_vs_M.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(energy_path.resolve()),
            "description": "Average ESS per likelihood evaluation vs M comparing MESS and EP-ESS.",
        }
    )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nESS-vs-M report summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Artifacts: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
