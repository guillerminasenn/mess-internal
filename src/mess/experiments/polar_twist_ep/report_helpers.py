"""Shared helpers for polar-twist EP reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from mess.experiments.polar_twist_ep.config import ExperimentConfig, build_context


def report_dirs(cfg: ExperimentConfig) -> Dict[str, Path]:
    ctx = build_context(cfg)
    fig_root = ctx["reports_dir"] / "figures"
    return {
        "reports_dir": ctx["reports_dir"],
        "estimations_dir": ctx["estimations_dir"],
        "fig_root": fig_root,
        "manifests_dir": ctx["reports_dir"] / "manifests",
    }


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
