"""Phase-2 pairplot generation for notebook-11 parity."""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_helpers import (
    load_chain,
    parameter_index_for_pair,
    report_dirs,
)
from mess.plotting.diagnostics import make_hist_grid_comps


def _selected_components_for_dim(dim: int):
    pairs = [(0, 1), (0, 2), (2, 1)]
    labels = {
        (0, 1): "$a_{01}$",
        (0, 2): "$a_{02}$",
        (2, 1): "$a_{21}$",
    }
    comps = []
    label_map = {}
    for i, j in pairs:
        idx = parameter_index_for_pair(dim, i, j)
        if idx is None:
            continue
        if idx in comps:
            continue
        comps.append(idx)
        label_map[idx] = labels[(i, j)]
    return comps, label_map


def _robust_radius(samples, comp_list):
    subset = samples[:, comp_list]
    lo = np.quantile(subset, 0.01, axis=0)
    hi = np.quantile(subset, 0.99, axis=0)
    span = np.max(np.abs(np.concatenate([lo, hi])))
    return max(1e-3, 1.1 * float(span))


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "pairplots"
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = []
    n_missing = 0

    for d_cur in cfg.d_list:
        comp_list, label_map = _selected_components_for_dim(d_cur)
        if len(comp_list) < 2:
            continue

        specs = []
        for m in cfg.M_list:
            specs.append(("mess", m, f"alg_mess_d{d_cur}_M{m}"))
        specs.append(("mh", None, f"alg_mh_d{d_cur}"))
        specs.append(("pcn", None, f"alg_pcn_d{d_cur}"))
        for p in cfg.P_list:
            specs.append(("mpcn", p, f"alg_mpcn_d{d_cur}_P{p}"))

        for alg, param, tag in specs:
            if alg == "mess":
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "mess", M=param)
                hist_label = f"MESS (M={param}), d={d_cur}"
            elif alg == "mh":
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "mh")
                hist_label = f"MH d={d_cur}"
            elif alg == "pcn":
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "pcn", rho=cfg.rho_algo)
                hist_label = f"pCN d={d_cur}"
            else:
                chain, _ = load_chain(cfg, dirs["legacy_output_dir"], d_cur, "mpcn", P=param, rho=cfg.rho_algo)
                hist_label = f"mPCN (P={param}), d={d_cur}"

            if chain is None or chain.size == 0:
                n_missing += 1
                continue

            post = chain[cfg.burn_in :: cfg.thin]
            comp_list_valid = [c for c in comp_list if c < post.shape[1]]
            if len(comp_list_valid) < 2:
                n_missing += 1
                continue

            radius = _robust_radius(post, comp_list_valid)
            dr = max(2.0 * radius / 100.0, 1e-3)
            filename = out_dir / f"pairplot_{tag}_a01_a02_a21.png"
            make_hist_grid_comps(
                R=radius,
                dr=dr,
                samples=post,
                comp_list=comp_list_valid,
                save_path=filename,
                hide_plot=True,
                title=hist_label,
                label_map=label_map,
            )
            artifacts.append(
                {
                    "kind": "figure",
                    "path": str(filename.resolve()),
                    "description": f"Pairplot for {hist_label}.",
                }
            )
            print(f"Saved {filename}")

    print(f"Pairplots saved: {len(artifacts)}. Skipped (missing chains): {n_missing}.")
    return {"artifacts": artifacts, "missing": n_missing, "output_dir": str(out_dir.resolve())}


def main() -> None:
    summary = run()
    print("\nPairplots summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")
    print(f"- Missing inputs: {summary['missing']}")


if __name__ == "__main__":
    main()
