"""Configuration and deterministic run context for polar-twist MCMC comparison."""

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


def _rho_grid() -> List[float]:
    return [float(v) for v in np.arange(0.0, 1.0001, 0.025)]


@dataclass
class ExperimentConfig:
    """Stage-2 config surface for problem construction and deterministic IDs."""

    # Data-generation parameters (canonical notebook parity settings).
    alpha: float = 2.0
    sigma_noise: float = 1.0
    prior_std: float = 2.0
    prior_mean: List[float] = field(default_factory=lambda: [0.0, 0.0])
    prior_cov: List[List[float]] = field(
        default_factory=lambda: [[4.0, 1.2], [1.2, 2.0]]
    )
    weight_x: float = 1.0
    weight_y: float = 1.0
    data_seed: int = 202

    # Sweep and execution parameters.
    n_iters: int = 200000
    burn_in: int = 10000
    thin: int = 1
    max_lag: int = 1500
    seed_mcmc: int = 0
    seed_algo: int = 202

    P_list: List[int] = field(default_factory=lambda: [2, 5, 10, 20, 50])
    rho_list: List[float] = field(default_factory=_rho_grid)
    M_list: List[int] = field(default_factory=lambda: [1, 2, 5, 10, 20, 50])

    # MH and EP metadata (execution logic introduced in later stages).
    mh_target_acceptance: float = 0.234
    mh_tune_max_steps: int = 30
    mh_proposal_cov: str = "prior"
    mh_proposal_std: float = 0.2
    ep_replicates: int = 20

    # Run-layout labels.
    dataset: str = "polar_twist_mcmc_comparison"
    algorithm: str = "polar_twist_mcmc_comparison"
    sweep_mode: str = "sweep"

    def data_config(self) -> Dict[str, Any]:
        return {
            "model": "polar_twist",
            "alpha": self.alpha,
            "sigma_noise": self.sigma_noise,
            "prior_std": self.prior_std,
            "prior_mean": list(self.prior_mean),
            "prior_cov": [list(row) for row in self.prior_cov],
            "weight_x": self.weight_x,
            "weight_y": self.weight_y,
            "data_seed": int(self.data_seed),
        }

    def algorithm_config(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "n_iters": int(self.n_iters),
            "burn_in": int(self.burn_in),
            "thin": int(self.thin),
            "max_lag": int(self.max_lag),
            "seed_algo": int(self.seed_algo),
            "P_list": list(self.P_list),
            "rho_list": list(self.rho_list),
            "M_list": list(self.M_list),
            "mh_target_acceptance": float(self.mh_target_acceptance),
            "mh_tune_max_steps": int(self.mh_tune_max_steps),
            "mh_proposal_cov": self.mh_proposal_cov,
            "mh_proposal_std": float(self.mh_proposal_std),
            "ep_replicates": int(self.ep_replicates),
        }

    def execution_config(self, grid_count: int = 1, grid_index: int = 0) -> Dict[str, Any]:
        return {
            "seed_mcmc": int(self.seed_mcmc),
            "grid_count": int(grid_count),
            "grid_index": int(grid_index),
        }


def build_context(cfg: ExperimentConfig, grid_count: int = 1, grid_index: int = 0) -> Dict[str, Any]:
    """Build resolved paths and deterministic IDs for this experiment run."""
    if grid_count < 1:
        raise ValueError("grid_count must be >= 1")
    if grid_index < 0 or grid_index >= grid_count:
        raise ValueError("grid_index must be in [0, grid_count)")
    if len(cfg.prior_mean) != 2:
        raise ValueError("prior_mean must contain two entries")
    if len(cfg.prior_cov) != 2 or any(len(row) != 2 for row in cfg.prior_cov):
        raise ValueError("prior_cov must be a 2x2 matrix")

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
        "sweep": {
            "P_list": list(cfg.P_list),
            "rho_list": list(cfg.rho_list),
            "M_list": list(cfg.M_list),
        },
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
