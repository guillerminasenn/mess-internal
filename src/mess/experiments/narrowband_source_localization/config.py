"""Configuration and deterministic run context for narrowband source localization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np

from mess.experiments.common.run_layout import (
    build_run_layout,
    ensure_src_paths,
    resolve_repo_root,
    short_hash,
)


def _default_m_list() -> List[int]:
    return [1, 2, 5, 10, 20, 50]


@dataclass
class ExperimentConfig:
    # Baseline data/model configuration.
    propagation_speed: float = 343.0
    frequencies_hz: List[float] = field(default_factory=lambda: [1200.0])
    sensors_m: List[List[float]] = field(
        default_factory=lambda: [
            [-1.4, -1.2],
            [1.5, -1.0],
            [-1.1, 1.4],
            [1.3, 1.2],
        ]
    )
    true_source_m: List[float] = field(default_factory=lambda: [0.35, 0.55])
    prior_mean_m: List[float] = field(default_factory=lambda: [0.0, 0.0])
    prior_sd_m: List[float] = field(default_factory=lambda: [1.2, 1.2])
    amplitude_model: str = "phase_only"
    amplitude_gamma: float = 1.0
    r_min: float = 0.05
    tau: List[float] = field(default_factory=lambda: [1.0])
    sigma: List[float] = field(default_factory=lambda: [0.10])
    data_seed: int = 20260721

    # Reference-grid baseline.
    reference_box_m: List[float] = field(default_factory=lambda: [-4.0, 4.0, -4.0, 4.0])
    reference_grid_size: int = 301

    # Pilot values to preregister geometry-only candidate scans.
    pilot_frequencies_hz: List[float] = field(default_factory=lambda: [600.0, 900.0, 1200.0])
    pilot_sigma_values: List[float] = field(default_factory=lambda: [0.05, 0.10, 0.20])

    # Sampler configuration.
    M_list: List[int] = field(default_factory=_default_m_list)
    transition_variants: List[str] = field(default_factory=lambda: ["uniform", "euclidean_informed"])
    replicates: int = 20
    n_iters: int = 20000
    burn_in: int = 1000
    thin: int = 1
    max_lag: int = 1500
    seed_starts: int = 20260721
    seed_mcmc: int = 0
    seed_algo: int = 7
    mpcn_rho: float = 0.8

    # Diagnostic slice geometry settings.
    geometry_diag_replicates: int = 3
    geometry_diag_max_iters: int = 300
    geometry_angle_grid_size: int = 1440

    # Run-layout labels.
    dataset: str = "narrowband_source_localization"
    algorithm: str = "narrowband_source_localization"
    sweep_mode: str = "fixed"

    def prior_cov_m(self) -> np.ndarray:
        sd = np.asarray(self.prior_sd_m, dtype=float)
        if sd.shape != (2,):
            raise ValueError("prior_sd_m must have shape (2,)")
        return np.diag(sd * sd)

    def data_config(self) -> Dict[str, Any]:
        return {
            "model": "marginalized_complex_amplitude",
            "dimension": 2,
            "propagation_speed": float(self.propagation_speed),
            "frequencies_hz": [float(v) for v in self.frequencies_hz],
            "sensors_m": [[float(v) for v in row] for row in self.sensors_m],
            "true_source_m": [float(v) for v in self.true_source_m],
            "prior_mean_m": [float(v) for v in self.prior_mean_m],
            "prior_sd_m": [float(v) for v in self.prior_sd_m],
            "amplitude_model": str(self.amplitude_model),
            "amplitude_gamma": float(self.amplitude_gamma),
            "r_min": float(self.r_min),
            "tau": [float(v) for v in self.tau],
            "sigma": [float(v) for v in self.sigma],
            "data_seed": int(self.data_seed),
            "reference_box_m": [float(v) for v in self.reference_box_m],
            "reference_grid_size": int(self.reference_grid_size),
        }

    def algorithm_config(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "M_list": [int(v) for v in self.M_list],
            "transition_variants": [str(v) for v in self.transition_variants],
            "replicates": int(self.replicates),
            "n_iters": int(self.n_iters),
            "burn_in": int(self.burn_in),
            "thin": int(self.thin),
            "max_lag": int(self.max_lag),
            "seed_starts": int(self.seed_starts),
            "seed_mcmc": int(self.seed_mcmc),
            "seed_algo": int(self.seed_algo),
            "mpcn_rho": float(self.mpcn_rho),
            "geometry_diag_replicates": int(self.geometry_diag_replicates),
            "geometry_diag_max_iters": int(self.geometry_diag_max_iters),
            "geometry_angle_grid_size": int(self.geometry_angle_grid_size),
        }

    def execution_config(self, grid_count: int = 1, grid_index: int = 0) -> Dict[str, Any]:
        return {
            "grid_count": int(grid_count),
            "grid_index": int(grid_index),
        }


def build_context(cfg: ExperimentConfig, grid_count: int = 1, grid_index: int = 0) -> Dict[str, Any]:
    if grid_count < 1:
        raise ValueError("grid_count must be >= 1")
    if grid_index < 0 or grid_index >= grid_count:
        raise ValueError("grid_index must be in [0, grid_count)")

    if not cfg.M_list:
        raise ValueError("M_list cannot be empty")
    if not cfg.transition_variants:
        raise ValueError("transition_variants cannot be empty")
    if cfg.burn_in < 0 or cfg.burn_in >= cfg.n_iters:
        raise ValueError("burn_in must satisfy 0 <= burn_in < n_iters")

    repo_root = resolve_repo_root()
    ensure_src_paths(repo_root)

    data_id = short_hash(cfg.data_config(), prefix="data_h")
    run_id = short_hash(cfg.algorithm_config(), prefix="run_h")
    layout = build_run_layout(repo_root, cfg.dataset, data_id, run_id, cfg.sweep_mode)

    payload = {
        "dataset": cfg.dataset,
        "algorithm": cfg.algorithm,
        "data_id": data_id,
        "run_id": run_id,
        "data": cfg.data_config(),
        "algorithm_config": cfg.algorithm_config(),
        "execution": cfg.execution_config(grid_count=grid_count, grid_index=grid_index),
        "paths": {
            "repo_root": str(repo_root),
            "estimations_dir": str(layout["estimations_dir"]),
            "reports_dir": str(layout["reports_dir"]),
        },
    }

    config_path = layout["estimations_dir"] / "config.json"
    if not config_path.exists():
        import json

        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    return {
        "config": cfg,
        "repo_root": repo_root,
        "data_id": data_id,
        "run_id": run_id,
        "estimations_dir": layout["estimations_dir"],
        "reports_dir": layout["reports_dir"],
        "payload": payload,
    }


def sample_start_points(cfg: ExperimentConfig) -> Dict[str, np.ndarray]:
    """Deterministic starts for MESS/EP/MPCN with EP first-chain alignment."""
    rng = np.random.default_rng(int(cfg.seed_starts))

    prior_mean = np.asarray(cfg.prior_mean_m, dtype=float)
    prior_cov = cfg.prior_cov_m()
    b = int(cfg.replicates)
    max_m = int(max(cfg.M_list))

    q_mess = rng.multivariate_normal(prior_mean, prior_cov, size=b)
    z_mess = (q_mess - prior_mean[None, :]) / np.asarray(cfg.prior_sd_m, dtype=float)[None, :]

    q_ep = rng.multivariate_normal(prior_mean, prior_cov, size=(b, max_m))
    z_ep = (q_ep - prior_mean[None, None, :]) / np.asarray(cfg.prior_sd_m, dtype=float)[None, None, :]
    z_ep[:, 0, :] = z_mess

    q_mpcn = rng.multivariate_normal(prior_mean, prior_cov, size=b)
    z_mpcn = (q_mpcn - prior_mean[None, :]) / np.asarray(cfg.prior_sd_m, dtype=float)[None, :]

    return {
        "mess_starts": np.asarray(z_mess, dtype=float),
        "ep_starts": np.asarray(z_ep, dtype=float),
        "mpcn_starts": np.asarray(z_mpcn, dtype=float),
    }
