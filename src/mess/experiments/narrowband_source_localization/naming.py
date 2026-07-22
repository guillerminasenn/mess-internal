"""Chain naming and parsing for narrowband source-localization experiment."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def chain_path(
    outdir: Path,
    *,
    sampler: str,
    M: int,
    replicate: int,
    transition_variant: str = "",
    chain_idx: Optional[int] = None,
) -> Path:
    sampler_key = str(sampler)
    if sampler_key == "mess":
        if not transition_variant:
            raise ValueError("transition_variant is required for mess")
        return outdir / (
            f"chain_mess_{transition_variant}_M{int(M)}_rep{int(replicate):03d}.npz"
        )
    if sampler_key == "ep_ess":
        if chain_idx is None:
            raise ValueError("chain_idx is required for ep_ess")
        return outdir / (
            f"chain_ep_ess_M{int(M)}_rep{int(replicate):03d}_chain{int(chain_idx):03d}.npz"
        )
    if sampler_key == "mpcn":
        return outdir / f"chain_mpcn_P{int(M)}_rep{int(replicate):03d}.npz"
    raise ValueError(f"Unsupported sampler '{sampler}'")


def is_chain_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path) as data:
            _ = data["chain"]
        return True
    except (zipfile.BadZipFile, ValueError, KeyError):
        return False


def parse_chain_name(path: Path) -> Optional[Tuple[str, int, int, str, Optional[int]]]:
    stem = path.stem

    if stem.startswith("chain_mess_"):
        try:
            tail = stem.split("chain_mess_", 1)[1]
            variant, rem = tail.split("_M", 1)
            m_str, rep_str = rem.split("_rep", 1)
            return "mess", int(m_str), int(rep_str), variant, None
        except ValueError:
            return None

    if stem.startswith("chain_ep_ess_M"):
        try:
            tail = stem.split("chain_ep_ess_M", 1)[1]
            m_str, rem = tail.split("_rep", 1)
            rep_str, chain_str = rem.split("_chain", 1)
            return "ep_ess", int(m_str), int(rep_str), "uniform", int(chain_str)
        except ValueError:
            return None

    if stem.startswith("chain_mpcn_P"):
        try:
            tail = stem.split("chain_mpcn_P", 1)[1]
            p_str, rep_str = tail.split("_rep", 1)
            return "mpcn", int(p_str), int(rep_str), "proposal_count", None
        except ValueError:
            return None

    return None
