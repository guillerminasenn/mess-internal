"""Task list construction and missing-chain detection helpers."""

from __future__ import annotations

from pathlib import Path

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.naming import (
    chain_path,
    get_mh_proposal_std,
    is_chain_readable,
)


def should_skip_external(cfg, task: dict) -> bool:
    if task["d"] != cfg.external_d:
        return False
    ext_set = {tuple(x) for x in cfg.external_available}
    if task["alg"] == "mess":
        return ("mess", task["d"], task["M"]) in ext_set
    if task["alg"] == "pcn":
        return ("pcn", task["d"], None) in ext_set
    if task["alg"] == "mpcn":
        return ("mpcn", task["d"], task["P"]) in ext_set
    return False


def build_expected_tasks(cfg):
    tasks = []
    mh_std = get_mh_proposal_std(cfg)
    for d_idx, d_cur in enumerate(cfg.d_list):
        for M in cfg.M_list:
            tasks.append({"alg": "mess", "d": d_cur, "d_idx": d_idx, "M": M})
        tasks.append({"alg": "mh", "d": d_cur, "d_idx": d_idx, "proposal_std": mh_std})
        tasks.append({"alg": "pcn", "d": d_cur, "d_idx": d_idx, "rho": cfg.rho_algo})
        for P in cfg.P_list:
            tasks.append({"alg": "mpcn", "d": d_cur, "d_idx": d_idx, "P": P, "rho": cfg.rho_algo})
    return tasks


def build_missing_task_list(cfg, outdir: Path):
    missing = []
    for task in build_expected_tasks(cfg):
        if should_skip_external(cfg, task):
            continue
        path = chain_path(
            cfg,
            outdir,
            task["d"],
            task["alg"],
            M=task.get("M"),
            proposal_std=task.get("proposal_std"),
            P=task.get("P"),
            rho=task.get("rho"),
        )
        task["path"] = str(path)
        if is_chain_readable(path):
            continue
        missing.append(task)
    return missing
