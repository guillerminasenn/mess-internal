"""Shared data draws and per-dimension problem construction for solute-transport dim sweep."""

from __future__ import annotations

import numpy as np

from mess.problems.solute_transport import (
    SoluteTransportToy,
    make_Astar_from_atrue,
    make_Astar_nn,
    make_omegas_power,
    params_from_skew,
    prior_diag_from_powerlaw,
    solve_theta,
)


def get_obs_indices(dim_value: int, highest_freq: int, bandwidth: int) -> np.ndarray:
    highest_freq = min(highest_freq, dim_value)
    bandwidth = min(bandwidth, dim_value)
    start = max(0, highest_freq - bandwidth + 1)
    return np.arange(start, highest_freq + 1, dtype=int)


def get_param_indices_for_dim(dim: int, shared_draws: dict) -> np.ndarray:
    cache = shared_draws.setdefault("param_indices_cache", {})
    if dim not in cache:
        iju = shared_draws["param_iju"]
        mask = (iju[0] < dim) & (iju[1] < dim)
        cache[dim] = np.nonzero(mask)[0]
    return cache[dim]


def build_shared_draws(cfg) -> dict:
    rng = np.random.default_rng(cfg.shared_draws_seed)
    m_max = cfg.d_max * (cfg.d_max - 1) // 2
    prior_diag_max = prior_diag_from_powerlaw(
        cfg.d_max,
        alpha=cfg.alpha,
        gamma=cfg.gamma,
        tau2=cfg.tau2,
        offset=1.0,
    )
    if cfg.a_mode == "nearest_neighbor":
        omegas = make_omegas_power(cfg.d_max, beta=cfg.alpha, c=2.0 ** (-cfg.gamma), offset=1.0)
        a_true_max = params_from_skew(make_Astar_nn(cfg.d_max, omegas))
    elif cfg.a_mode == "prior":
        z_prior = rng.standard_normal(m_max)
        a_true_max = z_prior * np.sqrt(prior_diag_max)
    else:
        raise ValueError("a_mode must be 'nearest_neighbor' or 'prior'")

    g_max = np.zeros(cfg.d_max, dtype=float)
    g_max[0] = 1.0
    theta_true_max = solve_theta(cfg.d_max, a_true_max, g_max, cfg.kappa)
    noise_max = rng.standard_normal(cfg.d_max)
    z_init = rng.standard_normal(m_max)
    a_init_max = z_init * np.sqrt(prior_diag_max)
    return {
        "param_iju": np.triu_indices(cfg.d_max, k=1),
        "param_indices_cache": {},
        "prior_diag": prior_diag_max,
        "a_true": a_true_max,
        "g": g_max,
        "theta_true": theta_true_max,
        "noise": noise_max,
        "a_init": a_init_max,
    }


def build_problem_for_dim(cfg, dim: int, shared_draws: dict):
    obs_indices = get_obs_indices(dim, cfg.obs_highest_freq, cfg.obs_bandwidth)
    param_idx = get_param_indices_for_dim(dim, shared_draws)
    prior_diag = shared_draws["prior_diag"][param_idx]
    g = shared_draws["g"][:dim]

    a_true = shared_draws["a_true"][param_idx]
    theta_true = shared_draws["theta_true"][:dim]

    noise = shared_draws["noise"][:dim]
    y = theta_true[obs_indices] + cfg.sigma * noise[obs_indices]
    a_init = shared_draws["a_init"][param_idx]
    problem = SoluteTransportToy(
        dim=dim,
        kappa=cfg.kappa,
        sigma=cfg.sigma,
        y=y,
        obs_indices=obs_indices,
        g=g,
        prior_diag=prior_diag,
    )
    return problem, a_init, y, theta_true


def build_visual_data(cfg, d: int):
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
