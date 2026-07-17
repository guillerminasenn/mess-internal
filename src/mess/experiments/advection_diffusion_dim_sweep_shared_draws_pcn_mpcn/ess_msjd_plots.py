"""Phase-2 ESS/MSJD plotting for notebook-11 parity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.algorithms.effective_sample_size import estimate_effective_sample_size
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.compute_metrics import (
    run as run_compute_metrics,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.report_helpers import (
    load_chain,
    parameter_index_for_pair,
    report_dirs,
)
from mess.experiments.common.plotting_utils import apply_publication_style, color_maps_for_sweeps, save_figure


COMPONENT_SPECS = [
    ("a_01", 0, 1, 1.0),
    ("a_12", 1, 2, 1.0),
    # a_21 shares the same underlying sampled parameter as a_12 but with opposite sign.
    ("a_21", 2, 1, -1.0),
]


def _collect_by_key(rows, key_name):
    values = {}
    for row in rows:
        key = row.get(key_name)
        if key is None:
            continue
        d = int(row["d"])
        values.setdefault(key, {})[d] = row
    return values


def _msjd_1d(series: np.ndarray) -> float:
    if series.shape[0] < 2:
        return float("nan")
    jumps = np.diff(series)
    return float(np.mean(jumps * jumps))


def _safe_float(value) -> float:
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _component_metrics_for_row(
    row: dict,
    cfg: ExperimentConfig,
    output_dir: Path,
    cache: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    existing = {}
    has_all_existing = True
    for name, _, _, _ in COMPONENT_SPECS:
        e_key = f"ess_{name}"
        m_key = f"msjd_{name}"
        existing[e_key] = _safe_float(row.get(e_key))
        existing[m_key] = _safe_float(row.get(m_key))
        if np.isnan(existing[e_key]) or np.isnan(existing[m_key]):
            has_all_existing = False

    existing["ess_subset_mean"] = _safe_float(row.get("ess_subset_mean"))
    existing["msjd_subset_mean"] = _safe_float(row.get("msjd_subset_mean"))
    if has_all_existing and not np.isnan(existing["ess_subset_mean"]) and not np.isnan(existing["msjd_subset_mean"]):
        return existing

    alg = str(row.get("alg"))
    d = int(row["d"])
    M = row.get("M")
    P = row.get("P")
    cache_key = f"{alg}|{d}|{M}|{P}"
    if cache_key in cache:
        return cache[cache_key]

    chain = None
    path_str = row.get("path")
    if path_str:
        path = Path(path_str)
        if path.exists() and path.is_file():
            try:
                with np.load(path) as payload:
                    chain = payload["chain"]
            except Exception:
                chain = None

    if chain is None:
        chain, _ = load_chain(cfg, output_dir, d, alg, M=M, P=P, rho=cfg.rho_algo)
    if chain is None:
        return existing

    samples = chain[int(cfg.burn_in) :: int(cfg.thin)]
    if samples.shape[0] < 4:
        return existing

    result = {}
    ess_vals = []
    msjd_vals = []
    for name, i, j, sign in COMPONENT_SPECS:
        idx = parameter_index_for_pair(d, i, j)
        e_key = f"ess_{name}"
        m_key = f"msjd_{name}"
        if idx is None or idx >= samples.shape[1]:
            result[e_key] = float("nan")
            result[m_key] = float("nan")
            continue
        series = sign * samples[:, idx]
        ess_value = float(estimate_effective_sample_size(series, max_lag=int(cfg.max_lag)))
        msjd_value = _msjd_1d(series)
        result[e_key] = ess_value
        result[m_key] = msjd_value
        if np.isfinite(ess_value):
            ess_vals.append(ess_value)
        if np.isfinite(msjd_value):
            msjd_vals.append(msjd_value)

    result["ess_subset_mean"] = float(np.mean(ess_vals)) if ess_vals else float("nan")
    result["msjd_subset_mean"] = float(np.mean(msjd_vals)) if msjd_vals else float("nan")
    cache[cache_key] = result
    return result


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "ess_msjd_vs_d"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    metrics_path = dirs["reports_dir"] / "tables" / "metrics_summary.json"
    if not metrics_path.exists():
        print(f"Metrics summary not found, generating it via compute_metrics: {metrics_path}")
        run_compute_metrics(cfg)
    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing metrics summary after regeneration attempt: {metrics_path}")

    with open(metrics_path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)

    derived_cache: Dict[str, Dict[str, float]] = {}
    for row in rows:
        row.update(_component_metrics_for_row(row, cfg, dirs["legacy_output_dir"], derived_cache))

    mess_rows = [r for r in rows if r.get("alg") == "mess"]
    mh_rows = [r for r in rows if r.get("alg") == "mh"]
    pcn_rows = [r for r in rows if r.get("alg") == "pcn"]
    mpcn_rows = [r for r in rows if r.get("alg") == "mpcn"]

    mess_by_m = _collect_by_key(mess_rows, "M")
    mpcn_by_p = _collect_by_key(mpcn_rows, "P")
    m_colors, p_colors = color_maps_for_sweeps(cfg.M_list, cfg.P_list)

    def _series_from(by_key, key_value, metric_key):
        return [_safe_float(by_key.get(key_value, {}).get(d, {}).get(metric_key)) for d in cfg.d_list]

    def _series_from_rows(base_rows, metric_key):
        by_d = {int(r["d"]): _safe_float(r.get(metric_key)) for r in base_rows}
        return [by_d.get(d, np.nan) for d in cfg.d_list]

    def make_plot(
        filename: str,
        ess_key: str,
        msjd_key: str,
        ess_title: str,
        msjd_title: str,
        yscale: Optional[str] = None,
    ):
        fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.6), sharex=True)
        ax_ess, ax_msjd = axes

        for m in cfg.M_list:
            vals_ess = _series_from(mess_by_m, m, ess_key)
            vals_msjd = _series_from(mess_by_m, m, msjd_key)
            ax_ess.plot(cfg.d_list, vals_ess, marker="o", color=m_colors.get(m), label=f"MESS M={m}")
            ax_msjd.plot(cfg.d_list, vals_msjd, marker="o", color=m_colors.get(m), label=f"MESS M={m}")

        ax_ess.plot(cfg.d_list, _series_from_rows(mh_rows, ess_key), marker="s", linestyle="--", color="black", label="MH")
        ax_msjd.plot(cfg.d_list, _series_from_rows(mh_rows, msjd_key), marker="s", linestyle="--", color="black", label="MH")

        ax_ess.plot(cfg.d_list, _series_from_rows(pcn_rows, ess_key), marker="D", linestyle=":", color=plt.cm.Reds(0.9), label="pCN")
        ax_msjd.plot(cfg.d_list, _series_from_rows(pcn_rows, msjd_key), marker="D", linestyle=":", color=plt.cm.Reds(0.9), label="pCN")

        for p in cfg.P_list:
            vals_ess = _series_from(mpcn_by_p, p, ess_key)
            vals_msjd = _series_from(mpcn_by_p, p, msjd_key)
            ax_ess.plot(cfg.d_list, vals_ess, marker="^", color=p_colors.get(p), label=f"mPCN P={p}")
            ax_msjd.plot(cfg.d_list, vals_msjd, marker="^", color=p_colors.get(p), label=f"mPCN P={p}")

        if yscale is not None:
            ax_ess.set_yscale(yscale)
            ax_msjd.set_yscale(yscale)

        ax_ess.set_title(ess_title)
        ax_msjd.set_title(msjd_title)
        ax_ess.set_xlabel("d")
        ax_msjd.set_xlabel("d")
        ax_ess.set_ylabel("ESS")
        ax_msjd.set_ylabel("MSJD")

        handles, labels = ax_ess.get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.1), ncol=4, frameon=False)
        fig.tight_layout(rect=(0, 0, 1, 0.9))
        return save_figure(fig, out_dir / filename, dpi=300)

    artifacts = []

    plot_specs = [
        {
            "suffix": "mean",
            "ess_key": "ess_subset_mean",
            "msjd_key": "msjd_subset_mean",
            "subtitle": "average over subset components a_01, a_12, a_21",
        },
        {
            "suffix": "a_01",
            "ess_key": "ess_a_01",
            "msjd_key": "msjd_a_01",
            "subtitle": "raw component a_01",
        },
        {
            "suffix": "a_12",
            "ess_key": "ess_a_12",
            "msjd_key": "msjd_a_12",
            "subtitle": "raw component a_12",
        },
        {
            "suffix": "a_21",
            "ess_key": "ess_a_21",
            "msjd_key": "msjd_a_21",
            "subtitle": "raw component a_21",
        },
    ]

    for spec in plot_specs:
        linear_name = f"ess_msjd_vs_d_{spec['suffix']}.png"
        log_name = f"ess_msjd_vs_d_{spec['suffix']}_log.png"
        ess_title = f"ESS vs dimension ({spec['subtitle']})"
        msjd_title = f"MSJD vs dimension ({spec['subtitle']})"

        p_linear = make_plot(
            linear_name,
            ess_key=spec["ess_key"],
            msjd_key=spec["msjd_key"],
            ess_title=ess_title,
            msjd_title=msjd_title,
            yscale=None,
        )
        p_log = make_plot(
            log_name,
            ess_key=spec["ess_key"],
            msjd_key=spec["msjd_key"],
            ess_title=ess_title,
            msjd_title=msjd_title,
            yscale="log",
        )
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p_linear.resolve()),
                "description": f"ESS/MSJD vs dimension ({spec['subtitle']}, linear scale).",
            }
        )
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p_log.resolve()),
                "description": f"ESS/MSJD vs dimension ({spec['subtitle']}, log scale).",
            }
        )

    for item in artifacts:
        print(f"Saved {item['path']}")

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nESS/MSJD plot summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
