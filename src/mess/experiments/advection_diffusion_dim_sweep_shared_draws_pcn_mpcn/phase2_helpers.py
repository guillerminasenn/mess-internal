"""Shared data and chain access helpers for AD sweep phase-2 plotting modules."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
    build_context,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.naming import (
    chain_path,
    get_mh_proposal_std,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.problem_factory import (
    build_problem_for_dim,
    build_shared_draws,
    get_param_indices_for_dim,
)
from mess.problems.advection_diffusion import make_Astar_from_atrue, make_Astar_nn, make_omegas_power


def phase2_dirs(cfg: ExperimentConfig) -> Dict[str, Path]:
    ctx = build_context(cfg)
    fig_root = ctx["reports_dir"] / "figures"
    fig_root.mkdir(parents=True, exist_ok=True)
    return {
        "reports_dir": ctx["reports_dir"],
        "legacy_output_dir": ctx["legacy_output_dir"],
        "fig_root": fig_root,
        "manifests_dir": ctx["reports_dir"] / "manifests",
    }


def load_chain(cfg: ExperimentConfig, output_dir: Path, d: int, alg: str, M=None, P=None, rho=None):
    mh_std = get_mh_proposal_std(cfg)
    proposal_std = mh_std if alg == "mh" else None
    path = chain_path(cfg, output_dir, d, alg, M=M, proposal_std=proposal_std, P=P, rho=rho)
    if not path.exists():
        return None, path
    with np.load(path) as payload:
        return payload["chain"], path


def build_visual_data(cfg: ExperimentConfig, d: int) -> Dict[str, np.ndarray]:
    shared = build_shared_draws(cfg)
    problem, _, y, theta = build_problem_for_dim(cfg, d, shared)

    if cfg.a_mode == "nearest_neighbor":
        omegas = make_omegas_power(d, beta=cfg.alpha, c=2.0 ** (-cfg.gamma), offset=1.0)
        A_true = make_Astar_nn(d, omegas)
    else:
        param_idx = get_param_indices_for_dim(d, shared)
        a_true = shared["a_true"][param_idx]
        A_true = make_Astar_from_atrue(d, a_true)

    return {
        "A_true": A_true,
        "theta_true": theta,
        "y": y,
        "obs_indices": np.asarray(problem.obs_indices, dtype=int),
    }


def parameter_index_for_pair(dim: int, i: int, j: int) -> Optional[int]:
    if i < 0 or j < 0 or i >= dim or j >= dim or i == j:
        return None
    u = min(i, j)
    v = max(i, j)
    iju = np.triu_indices(dim, k=1)
    mask = (iju[0] == u) & (iju[1] == v)
    idx = np.nonzero(mask)[0]
    if idx.size == 0:
        return None
    return int(idx[0])
