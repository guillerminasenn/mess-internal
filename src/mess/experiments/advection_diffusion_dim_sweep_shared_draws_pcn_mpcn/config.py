"""Configuration and path setup for AD dim sweep phase scripts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from mess.experiments.common.run_layout import (
    build_run_layout,
    ensure_src_paths,
    resolve_repo_root,
    short_hash,
)


@dataclass
class ExperimentConfig:
    """Minimal configuration for phase-1 scripts."""

    seed_data: int = 0
    seed_mcmc: int = 0
    seed_algo: int = 202
    n_iters: int = 300000
    burn_in: int = 10000
    thin: int = 1
    max_lag: int = 1500

    d_list: List[int] = field(default_factory=lambda: [10, 20, 30, 40, 50])
    d_max: int = 100
    M_list: List[int] = field(default_factory=lambda: [1, 10, 50])
    P_list: List[int] = field(default_factory=lambda: [10, 50, 100])
    rho_algo: float = 0.5

    kappa: float = 0.02
    sigma: float = 0.5
    alpha: int = 3
    gamma: int = 2
    tau2: float = 2.0
    a_mode: str = "nearest_neighbor"
    use_prior_A: bool = True
    shared_draws_seed: int = 0

    obs_highest_freq: int = 6
    obs_bandwidth: int = 3
    obs_config: str = "central_modes"

    mh_proposal_cov: str = "prior"
    mh_proposal_isotropic_std: float = 0.000018
    mh_proposal_prior_std: float = 0.105

    dataset: str = "advection_diffusion_dim_sweep_shared_draws_pcn_mpcn"
    algorithm: str = "dim_sweep_shared_draws_pcn_mpcn"
    sweep_mode: str = "sweep"

    # Backward compatibility path used by notebook outputs.
    legacy_output_group: str = "AD_toy_dim_M_sweep_shared_draws"

    # External known chains that should not be recomputed.
    external_d: int = 10
    external_available: List[List[Any]] = field(
        default_factory=lambda: [
            ["mess", 10, 10],
            ["pcn", 10, None],
            ["mpcn", 10, 10],
            ["mpcn", 10, 100],
        ]
    )

    def data_config(self) -> Dict[str, Any]:
        return {
            "seed_data": self.seed_data,
            "kappa": self.kappa,
            "sigma": self.sigma,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "tau2": self.tau2,
            "a_mode": self.a_mode,
            "use_prior_A": self.use_prior_A,
            "shared_draws_seed": self.shared_draws_seed,
            "obs_highest_freq": self.obs_highest_freq,
            "obs_bandwidth": self.obs_bandwidth,
            "obs_config": self.obs_config,
            "d_max": self.d_max,
            "d_list": self.d_list,
        }

    def algorithm_config(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "n_iters": self.n_iters,
            "burn_in": self.burn_in,
            "thin": self.thin,
            "max_lag": self.max_lag,
            "M_list": self.M_list,
            "P_list": self.P_list,
            "rho_algo": self.rho_algo,
            "mh_proposal_cov": self.mh_proposal_cov,
            "mh_proposal_isotropic_std": self.mh_proposal_isotropic_std,
            "mh_proposal_prior_std": self.mh_proposal_prior_std,
        }

    def execution_config(self, grid_count: int, grid_index: int) -> Dict[str, Any]:
        return {
            "seed_mcmc": self.seed_mcmc,
            "seed_algo": self.seed_algo,
            "grid_count": int(grid_count),
            "grid_index": int(grid_index),
        }


def build_context(cfg: ExperimentConfig, grid_count: int = 1, grid_index: int = 0) -> Dict[str, Any]:
    """Build resolved paths and IDs for the current run."""
    if max(cfg.d_list) > cfg.d_max:
        raise ValueError("d_max must be >= max(d_list)")

    repo_root = resolve_repo_root()
    ensure_src_paths(repo_root)

    data_id = short_hash(cfg.data_config(), prefix="data_h")
    run_id = short_hash(cfg.algorithm_config(), prefix="run_h")
    layout = build_run_layout(repo_root, cfg.dataset, data_id, run_id, cfg.sweep_mode)

    # Legacy path used by the notebook naming convention.
    run_tag = (
        f"priorA{cfg.use_prior_A}_obs_{cfg.obs_config}_tau2{cfg.tau2}_sigma{cfg.sigma}_seed{cfg.seed_data}_"
        f"dmax{cfg.d_max}_Niters{cfg.n_iters}"
    )
    legacy_output_dir = repo_root / "estimations" / cfg.legacy_output_group / run_tag
    legacy_output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "dataset": cfg.dataset,
        "algorithm": cfg.algorithm,
        "data_id": data_id,
        "run_id": run_id,
        "data": cfg.data_config(),
        "algorithm_config": cfg.algorithm_config(),
        "execution": cfg.execution_config(grid_count=grid_count, grid_index=grid_index),
        "sweep": {"d_list": cfg.d_list, "M_list": cfg.M_list, "P_list": cfg.P_list},
        "paths": {
            "repo_root": str(repo_root),
            "estimations_dir": str(layout["estimations_dir"]),
            "reports_dir": str(layout["reports_dir"]),
            "legacy_output_dir": str(legacy_output_dir),
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
        "legacy_output_dir": legacy_output_dir,
        "payload": payload,
    }
