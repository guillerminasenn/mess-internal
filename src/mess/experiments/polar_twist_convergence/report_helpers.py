"""Shared helpers for polar-twist convergence report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from mess.experiments.polar_twist_convergence.config import ExperimentConfig, build_context, source_roots


def report_dirs(cfg: ExperimentConfig) -> Dict[str, Path]:
    ctx = build_context(cfg)
    fig_root = ctx["reports_dir"] / "figures"
    return {
        "reports_dir": ctx["reports_dir"],
        "estimations_dir": ctx["estimations_dir"],
        "fig_root": fig_root,
        "manifests_dir": ctx["reports_dir"] / "manifests",
        "repo_root": Path(ctx["repo_root"]),
    }


def _run_candidates(root: Path) -> List[str]:
    if not root.exists():
        return []
    runs = [p for p in root.glob("run_h*") if p.is_dir()]
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in runs]


def _first_existing_path(candidates: List[Path]) -> Optional[Path]:
    for path in candidates:
        if path.exists():
            return path
    return None


def resolve_sources(cfg: ExperimentConfig) -> Dict[str, object]:
    dirs = report_dirs(cfg)
    roots = source_roots(cfg, repo_root=dirs["repo_root"])

    mcmc_runs = _run_candidates(roots["mcmc_reports"])
    dist_runs = _run_candidates(roots["dist_reports"])
    if not mcmc_runs:
        raise FileNotFoundError(f"No source runs found under {roots['mcmc_reports']}")
    if not dist_runs:
        raise FileNotFoundError(f"No source runs found under {roots['dist_reports']}")

    mcmc_rho_tag = f"{float(cfg.rho_for_pcn_mpcn):.5f}".replace(".", "p")

    specs: List[dict] = []
    specs.append({
        "label": "MH",
        "group": "mh",
        "source": "mcmc",
        "kind": "mh",
        "candidates": [roots["mcmc_estimations"] / run / "chain_mh.npz" for run in mcmc_runs],
    })
    specs.append({
        "label": f"pCN (rho={float(cfg.rho_for_pcn_mpcn):.3f})",
        "group": "pcn",
        "source": "mcmc",
        "kind": "pcn",
        "candidates": [
            roots["mcmc_estimations"] / run / f"chain_pcn_rho{mcmc_rho_tag}.npz" for run in mcmc_runs
        ],
    })

    for p in cfg.p_list:
        specs.append({
            "label": f"mPCN (P={int(p)}, rho={float(cfg.rho_for_pcn_mpcn):.3f})",
            "group": "mpcn",
            "source": "mcmc",
            "kind": "mpcn",
            "candidates": [
                roots["mcmc_estimations"] / run / f"chain_mpcn_P{int(p)}_rho{mcmc_rho_tag}.npz" for run in mcmc_runs
            ],
        })

    for m in cfg.mess_uniform_m_list:
        specs.append({
            "label": f"MESS uniform (M={int(m)})",
            "group": "mess_uniform",
            "source": "mcmc",
            "kind": "mess_uniform",
            "candidates": [roots["mcmc_estimations"] / run / f"chain_mess_M{int(m)}.npz" for run in mcmc_runs],
        })

    if cfg.include_ess_proxy:
        specs.append({
            "label": "ESS proxy (MESS M=1)",
            "group": "ess",
            "source": "mcmc",
            "kind": "ess_proxy",
            "candidates": [roots["mcmc_estimations"] / run / "chain_mess_M1.npz" for run in mcmc_runs],
        })

    for m in cfg.mess_flavor_m_list:
        specs.append({
            "label": f"MESS angular (M={int(m)})",
            "group": "mess_angular",
            "source": "distance",
            "kind": "mess_angular",
            "candidates": [
                roots["dist_estimations"] / run / f"chain_mess_lp_angular_M{int(m)}.npz" for run in dist_runs
            ],
        })
        specs.append({
            "label": f"MESS euclidean (M={int(m)})",
            "group": "mess_euclidean",
            "source": "distance",
            "kind": "mess_euclidean",
            "candidates": [
                roots["dist_estimations"] / run / f"chain_mess_lp_euclidean_M{int(m)}.npz" for run in dist_runs
            ],
        })

    resolved_specs: List[dict] = []
    for spec in specs:
        resolved = _first_existing_path(spec["candidates"])
        item = dict(spec)
        item["path"] = resolved
        resolved_specs.append(item)

    return {
        "specs": resolved_specs,
        "roots": {k: str(v) for k, v in roots.items()},
        "mcmc_runs": mcmc_runs,
        "distance_runs": dist_runs,
    }


def load_chain(path: Optional[Path]) -> Optional[np.ndarray]:
    if path is None or (not path.exists()):
        return None
    with np.load(path) as payload:
        return np.asarray(payload["chain"], dtype=float)


def write_source_summary(cfg: ExperimentConfig) -> Path:
    dirs = report_dirs(cfg)
    summary = resolve_sources(cfg)
    out_path = dirs["estimations_dir"] / "diagnostics" / "source_chain_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for spec in summary["specs"]:
        rows.append(
            {
                "label": spec["label"],
                "group": spec["group"],
                "source": spec["source"],
                "kind": spec["kind"],
                "path": str(spec["path"]) if spec["path"] is not None else None,
                "found": spec["path"] is not None,
            }
        )

    payload = {
        "roots": summary["roots"],
        "mcmc_runs": summary["mcmc_runs"],
        "distance_runs": summary["distance_runs"],
        "spec_count": len(rows),
        "found_count": sum(1 for row in rows if row["found"]),
        "rows": rows,
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return out_path
