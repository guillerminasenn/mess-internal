"""Configuration and deterministic run context for polar-twist EP-vs-MESS experiment."""

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
    # Polar-twist model configuration.
    alpha: float = 2.0
    sigma_noise: float = 1.0
    prior_mean: List[float] = field(default_factory=lambda: [0.0, 0.0])
    prior_cov: List[List[float]] = field(default_factory=lambda: [[4.0, 1.2], [1.2, 2.0]])
    weight_x: float = 1.0
    weight_y: float = 1.0
    data_seed: int = 202

    # EP experiment parameters.
    M_list: List[int] = field(default_factory=_default_m_list)
    replicates: int = 20
    n_iters: int = 20000
    burn_in: int = 1000
    thin: int = 1
    max_lag: int = 1500
    seed_starts: int = 202
    seed_mcmc: int = 0
    warmup_iters: int = 1000

    # Run-layout labels.
    dataset: str = "polar_twist_ep"
    algorithm: str = "polar_twist_ep"
    sweep_mode: str = "fixed"

    def data_config(self) -> Dict[str, Any]:
        return {
            "model": "polar_twist",
            "alpha": float(self.alpha),
            "sigma_noise": float(self.sigma_noise),
            "prior_mean": [float(v) for v in self.prior_mean],
            "prior_cov": [[float(v) for v in row] for row in self.prior_cov],
            "weight_x": float(self.weight_x),
            "weight_y": float(self.weight_y),
            "data_seed": int(self.data_seed),
        }

    def algorithm_config(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "M_list": [int(v) for v in self.M_list],
            "replicates": int(self.replicates),
            "n_iters": int(self.n_iters),
            "burn_in": int(self.burn_in),
            "thin": int(self.thin),
            "max_lag": int(self.max_lag),
            "seed_starts": int(self.seed_starts),
            "seed_mcmc": int(self.seed_mcmc),
            "warmup_iters": int(self.warmup_iters),
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

    if len(cfg.prior_mean) != 2:
        raise ValueError("prior_mean must contain two entries")
    if len(cfg.prior_cov) != 2 or any(len(row) != 2 for row in cfg.prior_cov):
        raise ValueError("prior_cov must be a 2x2 matrix")
    if cfg.burn_in < 0 or cfg.burn_in >= cfg.n_iters:
        raise ValueError("burn_in must satisfy 0 <= burn_in < n_iters")
    if not cfg.M_list:
        raise ValueError("M_list cannot be empty")

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


def sample_start_points(cfg: ExperimentConfig, dim: int) -> Dict[str, np.ndarray]:
    """Generate deterministic starts for MESS and EP-ESS, aligning first EP chain per replicate."""
    rng = np.random.default_rng(int(cfg.seed_starts))
    prior_mean = np.asarray(cfg.prior_mean, dtype=float)
    prior_cov = np.asarray(cfg.prior_cov, dtype=float)

    b = int(cfg.replicates)
    max_m = int(max(cfg.M_list))

    mess_starts = rng.multivariate_normal(prior_mean, prior_cov, size=b)
    ep_starts = rng.multivariate_normal(prior_mean, prior_cov, size=(b, max_m))
    ep_starts[:, 0, :] = mess_starts

    return {
        "mess_starts": np.asarray(mess_starts, dtype=float).reshape(b, dim),
        "ep_starts": np.asarray(ep_starts, dtype=float).reshape(b, max_m, dim),
    }
