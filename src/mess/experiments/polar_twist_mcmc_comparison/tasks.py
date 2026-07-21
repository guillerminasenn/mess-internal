"""Task-grid construction and missing-chain detection for polar-twist runs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

from mess.experiments.polar_twist_mcmc_comparison.naming import chain_path, is_chain_readable


def build_expected_tasks(cfg) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for m in cfg.M_list:
        tasks.append({"alg": "mess", "M": int(m)})

    tasks.append({"alg": "mh"})

    for rho in cfg.rho_list:
        tasks.append({"alg": "pcn", "rho": float(rho)})

    for p in cfg.P_list:
        for rho in cfg.rho_list:
            tasks.append({"alg": "mpcn", "P": int(p), "rho": float(rho)})

    return tasks


def build_missing_task_list(cfg, outdir: Path) -> List[Dict[str, object]]:
    missing: List[Dict[str, object]] = []
    for task in build_expected_tasks(cfg):
        path = chain_path(
            outdir,
            alg=str(task["alg"]),
            M=task.get("M"),
            P=task.get("P"),
            rho=task.get("rho"),
        )
        item = dict(task)
        item["path"] = str(path)
        if is_chain_readable(path):
            # Re-enqueue MESS chains that predate sub-iteration instrumentation.
            if str(task["alg"]) == "mess":
                try:
                    with np.load(path) as payload:
                        has_steps = "mess_subiters_per_iter" in payload
                    if not has_steps:
                        item["requires_refresh"] = True
                        missing.append(item)
                except Exception:
                    item["requires_refresh"] = True
                    missing.append(item)
            continue
        missing.append(item)
    return missing
