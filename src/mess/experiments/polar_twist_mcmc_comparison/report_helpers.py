"""Shared helpers for polar-twist report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from mess.experiments.common.mess_ellipse_plotting import trace_from_jsonable
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_mcmc_comparison.naming import chain_path
from mess.problems import build_polar_twist_problem


def report_dirs(cfg: ExperimentConfig) -> Dict[str, Path]:
    ctx = build_context(cfg)
    fig_root = ctx["reports_dir"] / "figures"
    return {
        "reports_dir": ctx["reports_dir"],
        "estimations_dir": ctx["estimations_dir"],
        "fig_root": fig_root,
        "manifests_dir": ctx["reports_dir"] / "manifests",
    }


def load_chain(cfg: ExperimentConfig, estimations_dir: Path, alg: str, M=None, P=None, rho=None):
    path = chain_path(estimations_dir, alg=alg, M=M, P=P, rho=rho)
    if not path.exists():
        return None, path
    with np.load(path) as payload:
        return payload["chain"], path


def load_mess_ellipse_traces(cfg: ExperimentConfig, estimations_dir: Path, M: int):
    chain_file = chain_path(estimations_dir, alg="mess", M=M)
    trace_file = chain_file.with_name(chain_file.stem + "_ellipse_traces.json")
    if not trace_file.exists():
        sweep_root = estimations_dir.parent
        candidates = sorted(
            sweep_root.glob(f"run_h*/{chain_file.stem}_ellipse_traces.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            trace_file = candidates[0]
    if not trace_file.exists():
        return [], trace_file
    with open(trace_file, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    traces = []
    for item in payload.get("traces", []):
        traces.append(
            {
                "iteration": int(item["iteration"]),
                **trace_from_jsonable(item["trace"]),
            }
        )
    traces.sort(key=lambda t: int(t["iteration"]))
    return traces, trace_file


def load_metrics_rows(cfg: ExperimentConfig):
    dirs = report_dirs(cfg)
    path = dirs["estimations_dir"] / "tables" / "metrics_summary.json"
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle), path


def load_runtime_rows(cfg: ExperimentConfig):
    dirs = report_dirs(cfg)
    path = dirs["estimations_dir"] / "tables" / "runtime_summary.json"
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle), path


def build_visual_data(cfg: ExperimentConfig):
    problem, data = build_polar_twist_problem(
        alpha=cfg.alpha,
        sigma_noise=cfg.sigma_noise,
        prior_mean=np.asarray(cfg.prior_mean, dtype=float),
        prior_cov=np.asarray(cfg.prior_cov, dtype=float),
        weight_x=cfg.weight_x,
        weight_y=cfg.weight_y,
        data_seed=cfg.data_seed,
    )
    return {
        "problem": problem,
        "x_true": data.x_true,
        "theta_true": data.theta_true,
        "y_obs": data.y_obs,
        "config": data.config,
    }


def representative_method_specs(cfg: ExperimentConfig):
    return [
        ("mess", {"M": 1}, "MESS (M=1)"),
        ("mess", {"M": 50}, "MESS (M=50)"),
        ("mh", {}, "MH"),
        ("pcn", {"rho": 0.5}, "pCN (rho=0.5)"),
        ("mpcn", {"P": 50, "rho": 0.5}, "mPCN (P=50, rho=0.5)"),
    ]


def row_matches(row: dict, alg: str, M: Optional[int] = None, P: Optional[int] = None, rho: Optional[float] = None) -> bool:
    if str(row.get("alg")) != alg:
        return False
    if M is not None and int(row.get("M", -1)) != int(M):
        return False
    if P is not None and int(row.get("P", -1)) != int(P):
        return False
    if rho is not None:
        rr = row.get("rho")
        if rr is None:
            return False
        if not np.isclose(float(rr), float(rho)):
            return False
    return True
