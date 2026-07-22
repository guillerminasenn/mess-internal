"""Report helper utilities for narrowband source-localization experiment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from mess.experiments.narrowband_source_localization.config import ExperimentConfig, build_context


def report_dirs(cfg: ExperimentConfig) -> Dict[str, Path]:
    ctx = build_context(cfg)
    reports_dir = Path(ctx["reports_dir"])
    return {
        "estimations_dir": Path(ctx["estimations_dir"]),
        "reports_dir": reports_dir,
        "fig_root": reports_dir / "figures",
    }


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
