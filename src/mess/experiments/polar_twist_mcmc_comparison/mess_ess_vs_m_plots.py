"""MESS-only ESS-vs-M figures, including cost-normalized variants."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import load_metrics_rows, report_dirs, row_matches


def _mess_rows_by_m(rows, m_list):
    out = []
    for m in sorted(int(v) for v in m_list):
        row = next((r for r in rows if row_matches(r, alg="mess", M=m)), None)
        if row is not None:
            out.append(row)
    return out


def _series(rows, key):
    return np.asarray([float(r.get(key, np.nan)) for r in rows], dtype=float)


def _plot_three_panel(rows, key_x1, key_x2, key_mean, title, y_label, out_path: Path):
    m_vals = np.asarray([int(r["M"]) for r in rows], dtype=int)
    y1 = _series(rows, key_x1)
    y2 = _series(rows, key_x2)
    ym = _series(rows, key_mean)

    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.2), sharex=True, constrained_layout=True)
    for ax, yy, subtitle in zip(
        axes,
        (y1, y2, ym),
        (r"$x_1$", r"$x_2$", "mean"),
    ):
        ax.plot(m_vals, yy, marker="o", linewidth=1.4, color="tab:blue")
        ax.set_title(subtitle)
        ax.set_xlabel("M")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel(y_label)
    fig.suptitle(title)
    return save_figure(fig, out_path, dpi=350)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "ess_msjd_vs_rho"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    rows, _ = load_metrics_rows(cfg)
    mess_rows = _mess_rows_by_m(rows, cfg.M_list)
    artifacts = []

    if not mess_rows:
        return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}

    raw_path = _plot_three_panel(
        mess_rows,
        key_x1="ess_x1",
        key_x2="ess_x2",
        key_mean="ess_mean",
        title="MESS ESS vs M",
        y_label="ESS",
        out_path=out_dir / "mess_ess_vs_M_raw.png",
    )
    artifacts.append(
        {
            "kind": "figure",
            "path": str(raw_path.resolve()),
            "description": "MESS-only raw ESS vs M (x1, x2, mean).",
        }
    )

    energy_ok = np.all(np.isfinite(_series(mess_rows, "ess_mean_per_energy_lik")))
    wallclock_ok = np.all(np.isfinite(_series(mess_rows, "ess_mean_per_parallel_lik_step")))

    if energy_ok:
        p = _plot_three_panel(
            mess_rows,
            key_x1="ess_x1_per_energy_lik",
            key_x2="ess_x2_per_energy_lik",
            key_mean="ess_mean_per_energy_lik",
            title="MESS ESS per likelihood evaluation (energy cost) vs M",
            y_label="ESS / likelihood evaluation",
            out_path=out_dir / "mess_ess_vs_M_per_energy_lik_eval.png",
        )
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": "MESS-only ESS per energy likelihood evaluation vs M (x1, x2, mean).",
            }
        )

    if wallclock_ok:
        p = _plot_three_panel(
            mess_rows,
            key_x1="ess_x1_per_parallel_lik_step",
            key_x2="ess_x2_per_parallel_lik_step",
            key_mean="ess_mean_per_parallel_lik_step",
            title="MESS ESS per parallel likelihood step vs M",
            y_label="ESS / parallel likelihood step",
            out_path=out_dir / "mess_ess_vs_M_per_parallel_lik_step.png",
        )
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": "MESS-only ESS per parallel likelihood step vs M (x1, x2, mean).",
            }
        )

    availability = {
        "energy_normalization_available": bool(energy_ok),
        "parallel_step_normalization_available": bool(wallclock_ok),
        "reason_if_unavailable": (
            "missing mess_subiters_per_iter in one or more MESS chain artifacts"
            if not (energy_ok and wallclock_ok)
            else "all required normalized metrics available"
        ),
    }
    availability_path = out_dir / "mess_ess_vs_M_availability.json"
    with open(availability_path, "w", encoding="utf-8") as handle:
        json.dump(availability, handle, indent=2)
    artifacts.append(
        {
            "kind": "metadata",
            "path": str(availability_path.resolve()),
            "description": "Availability status for normalized MESS ESS-vs-M plots.",
        }
    )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nMESS ESS-vs-M report summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Artifacts: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
