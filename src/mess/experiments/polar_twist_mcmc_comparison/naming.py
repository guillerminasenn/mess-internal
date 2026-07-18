"""Chain naming and file-readability helpers for polar-twist MCMC comparison."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def rho_to_tag(rho: float) -> str:
    return f"{float(rho):.5f}".replace(".", "p")


def chain_path(
    outdir: Path,
    *,
    alg: str,
    M: Optional[int] = None,
    P: Optional[int] = None,
    rho: Optional[float] = None,
) -> Path:
    key = alg.lower()
    if key == "mess":
        return outdir / f"chain_mess_M{int(M)}.npz"
    if key == "mh":
        return outdir / "chain_mh.npz"
    if key == "pcn":
        return outdir / f"chain_pcn_rho{rho_to_tag(float(rho))}.npz"
    if key == "mpcn":
        return outdir / f"chain_mpcn_P{int(P)}_rho{rho_to_tag(float(rho))}.npz"
    raise ValueError(f"Unsupported algorithm '{alg}'")


def is_chain_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path) as data:
            _ = data["chain"]
        return True
    except (zipfile.BadZipFile, ValueError, KeyError):
        return False


def parse_chain_name(path: Path) -> Optional[Tuple[str, Optional[int], Optional[int], Optional[float]]]:
    """Parse chain filename into (alg, M, P, rho)."""
    stem = path.stem
    if stem == "chain_mh":
        return "mh", None, None, None

    if stem.startswith("chain_mess_M"):
        try:
            m = int(stem.split("chain_mess_M", 1)[1])
            return "mess", m, None, None
        except ValueError:
            return None

    if stem.startswith("chain_pcn_rho"):
        try:
            rho_str = stem.split("chain_pcn_rho", 1)[1].replace("p", ".")
            return "pcn", None, None, float(rho_str)
        except ValueError:
            return None

    if stem.startswith("chain_mpcn_P"):
        try:
            right = stem.split("chain_mpcn_P", 1)[1]
            p_str, rho_part = right.split("_rho", 1)
            rho = float(rho_part.replace("p", "."))
            return "mpcn", None, int(p_str), rho
        except ValueError:
            return None

    return None
