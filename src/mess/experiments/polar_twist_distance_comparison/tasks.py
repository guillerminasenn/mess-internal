"""Task-grid construction and missing-chain detection for distance-comparison runs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from mess.experiments.polar_twist_distance_comparison.naming import chain_path, is_chain_readable


def build_expected_tasks(cfg) -> List[Dict[str, object]]:
    return [{"variant": str(v), "M": int(cfg.M)} for v in cfg.variant_list]


def build_missing_task_list(cfg, outdir: Path, uniform_exists_external: bool = False) -> List[Dict[str, object]]:
    missing: List[Dict[str, object]] = []
    for task in build_expected_tasks(cfg):
        variant = str(task["variant"])
        if variant == "uniform" and uniform_exists_external:
            continue

        path = chain_path(outdir, variant=variant, M=int(task["M"]))
        item = dict(task)
        item["path"] = str(path)
        if is_chain_readable(path):
            continue
        missing.append(item)
    return missing
