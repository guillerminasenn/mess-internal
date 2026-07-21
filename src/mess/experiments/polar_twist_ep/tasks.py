"""Task-grid construction and missing-chain detection for polar-twist EP experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from mess.experiments.polar_twist_ep.naming import chain_path, is_chain_readable


def build_expected_tasks(cfg) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for m in sorted(int(v) for v in cfg.M_list):
        for rep in range(int(cfg.replicates)):
            tasks.append({"variant": "mess", "M": int(m), "replicate": int(rep), "chain_idx": None})
        for rep in range(int(cfg.replicates)):
            for chain_idx in range(int(m)):
                tasks.append(
                    {
                        "variant": "ep_ess",
                        "M": int(m),
                        "replicate": int(rep),
                        "chain_idx": int(chain_idx),
                    }
                )
    return tasks


def build_missing_task_list(cfg, outdir: Path) -> List[Dict[str, object]]:
    missing: List[Dict[str, object]] = []
    for task in build_expected_tasks(cfg):
        path = chain_path(
            outdir,
            variant=str(task["variant"]),
            M=int(task["M"]),
            replicate=int(task["replicate"]),
            chain_idx=task.get("chain_idx"),
        )
        item = dict(task)
        item["path"] = str(path)
        if is_chain_readable(path):
            continue
        missing.append(item)
    return missing
