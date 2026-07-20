"""Chain naming and file-readability helpers for polar-twist distance comparison."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def chain_path(outdir: Path, *, variant: str, M: int) -> Path:
    key = str(variant).lower()
    if key == "uniform":
        return outdir / f"chain_mess_uniform_M{int(M)}.npz"
    if key == "lp_angular":
        return outdir / f"chain_mess_lp_angular_M{int(M)}.npz"
    if key == "lp_euclidean":
        return outdir / f"chain_mess_lp_euclidean_M{int(M)}.npz"
    raise ValueError(f"Unsupported variant '{variant}'")


def is_chain_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path) as data:
            _ = data["chain"]
        return True
    except (zipfile.BadZipFile, ValueError, KeyError):
        return False


def parse_chain_name(path: Path) -> Optional[Tuple[str, int]]:
    """Parse chain filename into (variant, M)."""
    stem = path.stem
    if stem.startswith("chain_mess_uniform_M"):
        try:
            m = int(stem.split("chain_mess_uniform_M", 1)[1])
            return "uniform", m
        except ValueError:
            return None
    if stem.startswith("chain_mess_lp_angular_M"):
        try:
            m = int(stem.split("chain_mess_lp_angular_M", 1)[1])
            return "lp_angular", m
        except ValueError:
            return None
    if stem.startswith("chain_mess_lp_euclidean_M"):
        try:
            m = int(stem.split("chain_mess_lp_euclidean_M", 1)[1])
            return "lp_euclidean", m
        except ValueError:
            return None
    return None
