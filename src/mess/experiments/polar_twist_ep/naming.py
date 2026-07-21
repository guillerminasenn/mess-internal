"""Chain naming and file-readability helpers for polar-twist EP experiment."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def chain_path(
    outdir: Path,
    *,
    variant: str,
    M: int,
    replicate: int,
    chain_idx: Optional[int] = None,
) -> Path:
    key = str(variant)
    if key == "mess":
        return outdir / f"chain_mess_M{int(M)}_rep{int(replicate):03d}.npz"
    if key == "ep_ess":
        if chain_idx is None:
            raise ValueError("chain_idx is required for ep_ess")
        return outdir / (
            f"chain_ep_ess_M{int(M)}_rep{int(replicate):03d}_chain{int(chain_idx):03d}.npz"
        )
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


def parse_chain_name(path: Path) -> Optional[Tuple[str, int, int, Optional[int]]]:
    stem = path.stem
    if stem.startswith("chain_mess_M"):
        try:
            tail = stem.split("chain_mess_M", 1)[1]
            m_str, rep_str = tail.split("_rep", 1)
            return "mess", int(m_str), int(rep_str), None
        except ValueError:
            return None

    if stem.startswith("chain_ep_ess_M"):
        try:
            tail = stem.split("chain_ep_ess_M", 1)[1]
            m_str, rem = tail.split("_rep", 1)
            rep_str, chain_str = rem.split("_chain", 1)
            return "ep_ess", int(m_str), int(rep_str), int(chain_str)
        except ValueError:
            return None

    return None
