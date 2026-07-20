"""Shared helpers for polar-twist distance-comparison report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from mess.experiments.polar_twist_distance_comparison.config import (
    ExperimentConfig,
    build_context,
    resolve_uniform_chain_path,
)
from mess.experiments.polar_twist_distance_comparison.naming import chain_path


def report_dirs(cfg: ExperimentConfig) -> Dict[str, Path]:
    ctx = build_context(cfg)
    fig_root = ctx["reports_dir"] / "figures"
    fig_root.mkdir(parents=True, exist_ok=True)
    return {
        "reports_dir": ctx["reports_dir"],
        "estimations_dir": ctx["estimations_dir"],
        "fig_root": fig_root,
        "manifests_dir": ctx["reports_dir"] / "manifests",
        "repo_root": Path(ctx["repo_root"]),
    }


def variant_specs(cfg: ExperimentConfig) -> List[dict]:
    specs: List[dict] = []
    dirs = report_dirs(cfg)
    outdir = dirs["estimations_dir"]

    include_uniform = "uniform" in {str(v) for v in cfg.variant_list}
    uniform_external = resolve_uniform_chain_path(cfg, repo_root=dirs["repo_root"])
    if include_uniform and uniform_external and uniform_external.exists():
        specs.append(
            {
                "variant": "uniform",
                "label": "MESS (uniform)",
                "color": "tab:blue",
                "path": uniform_external,
                "source": "external",
            }
        )

    style_map = {
        "lp_angular": ("MESS LP (angular)", "tab:orange"),
        "lp_euclidean": ("MESS LP (euclidean)", "tab:green"),
    }
    for key in ("lp_angular", "lp_euclidean"):
        if key not in {str(v) for v in cfg.variant_list}:
            continue
        label, color = style_map[key]
        specs.append(
            {
                "variant": key,
                "label": label,
                "color": color,
                "path": chain_path(outdir, variant=key, M=int(cfg.M)),
                "source": "local",
            }
        )

    return specs


def load_chain(path: Path) -> Optional[np.ndarray]:
    if not path.exists():
        return None
    with np.load(path) as payload:
        return np.asarray(payload["chain"], dtype=float)


def load_metrics_rows(cfg: ExperimentConfig):
    dirs = report_dirs(cfg)
    path = dirs["reports_dir"] / "tables" / "metrics_summary.json"
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle), path


def load_runtime_rows(cfg: ExperimentConfig):
    dirs = report_dirs(cfg)
    path = dirs["reports_dir"] / "tables" / "runtime_summary.json"
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle), path
