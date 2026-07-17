"""Shared chain naming and parsing helpers for AD dim sweep experiments."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


def rho_to_tag(rho: float) -> str:
    return f"{rho:.5f}".replace(".", "p")


def get_mh_proposal_std(cfg) -> float:
    return cfg.mh_proposal_prior_std if cfg.mh_proposal_cov == "prior" else cfg.mh_proposal_isotropic_std


def chain_path(
    cfg,
    outdir: Path,
    d: int,
    alg: str,
    M=None,
    proposal_std=None,
    P=None,
    rho=None,
) -> Path:
    alg_key = alg.lower()
    if alg_key == "mh":
        if proposal_std is None:
            return outdir / f"chain_d{d}_mh_sigma2unknown.npz"
        sigma_tag = f"{proposal_std:.6g}"
        cov_tag = "" if cfg.mh_proposal_cov in (None, "isotropic") else f"_cov{cfg.mh_proposal_cov}"
        return outdir / f"chain_d{d}_mh_sigma2{sigma_tag}{cov_tag}.npz"
    if alg_key == "pcn":
        rho_tag = rho_to_tag(rho if rho is not None else cfg.rho_algo)
        return outdir / f"chain_d{d}_pcn_rho{rho_tag}.npz"
    if alg_key == "mpcn":
        rho_tag = rho_to_tag(rho if rho is not None else cfg.rho_algo)
        return outdir / f"chain_d{d}_mpcn_P{P}_rho{rho_tag}.npz"
    return outdir / f"chain_d{d}_{alg_key}_M{M}.npz"


def parse_chain_name(path: Path) -> Optional[Tuple[str, int, Optional[int], Optional[int]]]:
    name = path.stem
    if not name.startswith("chain_d"):
        return None
    rest = name[len("chain_d") :]
    if "_mh_" in rest:
        d_str = rest.split("_mh_")[0]
        return "mh", int(d_str), None, None
    if "_pcn_" in rest:
        d_str = rest.split("_pcn_")[0]
        return "pcn", int(d_str), None, None
    if "_mpcn_" in rest:
        d_str, tail = rest.split("_mpcn_", 1)
        p_part = tail.split("_", 1)[0]
        return "mpcn", int(d_str), None, int(p_part[1:])
    if "_mess_" in rest:
        d_str, tail = rest.split("_mess_", 1)
        m_part = tail.split("_", 1)[0]
        return "mess", int(d_str), int(m_part[1:]), None
    return None


def is_chain_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with np.load(path) as data:
            _ = data["chain"]
        return True
    except (zipfile.BadZipFile, ValueError, KeyError):
        return False
