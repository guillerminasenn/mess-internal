"""Configuration and deterministic run context for polar-twist warmup convergence plots."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    """Config for warmup convergence comparisons using existing chain artifacts."""

    # Source experiment roots.
    source_dataset_mcmc: str = "polar_twist_mcmc_comparison"
    source_dataset_distance: str = "polar_twist_distance_comparison"
    source_dataset_ep: str = "polar_twist_ep"
    source_data_id: str = "data_hf0d732d0900c"

    # Warmup and representative sweep selections.
    warmup_iters: int = 100
    rho_for_pcn_mpcn: float = 0.5
    p_list: List[int] = field(default_factory=lambda: [2, 5, 10, 20, 50])
    mess_uniform_m_list: List[int] = field(default_factory=lambda: [1, 2, 5, 10, 20, 50])
    mess_flavor_m_list: List[int] = field(default_factory=lambda: [5, 10, 20, 50])
    ep_m_list: List[int] = field(default_factory=lambda: [1, 2, 5, 10, 20, 50])
    ep_replicate_for_trace: int = 0
    include_ep: bool = True
    include_ess_proxy: bool = True

    # Run-layout labels.
    dataset: str = "polar_twist_convergence"
    algorithm: str = "polar_twist_convergence"
    sweep_mode: str = "fixed"

    def data_config(self) -> Dict[str, Any]:
        return {
            "source_data_id": self.source_data_id,
            "source_dataset_mcmc": self.source_dataset_mcmc,
            "source_dataset_distance": self.source_dataset_distance,
            "source_dataset_ep": self.source_dataset_ep,
        }

    def algorithm_config(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "warmup_iters": int(self.warmup_iters),
            "rho_for_pcn_mpcn": float(self.rho_for_pcn_mpcn),
            "p_list": [int(v) for v in self.p_list],
            "mess_uniform_m_list": [int(v) for v in self.mess_uniform_m_list],
            "mess_flavor_m_list": [int(v) for v in self.mess_flavor_m_list],
            "ep_m_list": [int(v) for v in self.ep_m_list],
            "ep_replicate_for_trace": int(self.ep_replicate_for_trace),
            "include_ep": bool(self.include_ep),
            "include_ess_proxy": bool(self.include_ess_proxy),
        }


def build_context(cfg: ExperimentConfig) -> Dict[str, Any]:
    """Build resolved paths and deterministic IDs for this experiment run."""
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


def source_roots(cfg: ExperimentConfig, *, repo_root: Path) -> Dict[str, Path]:
    """Resolve source reports/estimations roots for prior experiments."""
    mcmc_reports = repo_root / "reports" / cfg.source_dataset_mcmc / cfg.source_data_id / "sweep"
    dist_reports = repo_root / "reports" / cfg.source_dataset_distance / cfg.source_data_id / "fixed"
    ep_reports = repo_root / "reports" / cfg.source_dataset_ep
    mcmc_estimations = repo_root / "estimations" / cfg.source_dataset_mcmc / cfg.source_data_id / "sweep"
    dist_estimations = repo_root / "estimations" / cfg.source_dataset_distance / cfg.source_data_id / "fixed"
    ep_estimations = repo_root / "estimations" / cfg.source_dataset_ep
    return {
        "mcmc_reports": mcmc_reports,
        "dist_reports": dist_reports,
        "ep_reports": ep_reports,
        "mcmc_estimations": mcmc_estimations,
        "dist_estimations": dist_estimations,
        "ep_estimations": ep_estimations,
    }
