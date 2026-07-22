"""Task-grid construction and missing-chain detection for source localization."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from mess.experiments.narrowband_source_localization.naming import chain_path, is_chain_readable


def build_expected_tasks(cfg) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    for m in sorted(int(v) for v in cfg.M_list):
        for rep in range(int(cfg.replicates)):
            for variant in cfg.transition_variants:
                tasks.append(
                    {
                        "sampler": "mess",
                        "M": int(m),
                        "replicate": int(rep),
                        "transition_variant": str(variant),
                        "chain_idx": None,
                    }
                )
        for rep in range(int(cfg.replicates)):
            for chain_idx in range(int(m)):
                tasks.append(
                    {
                        "sampler": "ep_ess",
                        "M": int(m),
                        "replicate": int(rep),
                        "transition_variant": "uniform",
                        "chain_idx": int(chain_idx),
                    }
                )
        for rep in range(int(cfg.replicates)):
            tasks.append(
                {
                    "sampler": "mpcn",
                    "M": int(m),
                    "replicate": int(rep),
                    "transition_variant": "proposal_count",
                    "chain_idx": None,
                }
            )
    return tasks


def build_missing_task_list(cfg, outdir: Path) -> List[Dict[str, object]]:
    missing: List[Dict[str, object]] = []
    for task in build_expected_tasks(cfg):
        path = chain_path(
            outdir,
            sampler=str(task["sampler"]),
            M=int(task["M"]),
            replicate=int(task["replicate"]),
            transition_variant=str(task.get("transition_variant", "")),
            chain_idx=task.get("chain_idx"),
        )
        item = dict(task)
        item["path"] = str(path)
        if is_chain_readable(path):
            continue
        missing.append(item)
    return missing
