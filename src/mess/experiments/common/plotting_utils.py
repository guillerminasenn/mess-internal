"""Reusable plotting helpers for experiment migration scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np


def apply_publication_style() -> None:
    """Apply a lightweight publication style shared across migrated scripts."""
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 11,
        }
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_figure(fig: plt.Figure, path: Path, dpi: int = 300) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path


def color_maps_for_sweeps(M_list: Iterable[int], P_list: Iterable[int]) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    m_vals = list(M_list)
    p_vals = list(P_list)

    m_ordered = sorted(m_vals)
    p_ordered = sorted(p_vals)
    m_scale = np.linspace(0.9, 0.35, max(len(m_ordered), 1))
    p_scale = np.linspace(0.9, 0.35, max(len(p_ordered), 1))
    m_colors = plt.cm.Greens(m_scale)
    p_colors = plt.cm.Reds(p_scale)
    return (
        {m: m_colors[i] for i, m in enumerate(m_ordered)},
        {p: p_colors[i] for i, p in enumerate(p_ordered)},
    )


def upper_tri_component_labels(dim: int, indices: List[int]) -> List[str]:
    labels: List[str] = []
    for idx in indices:
        count = 0
        found = False
        for i in range(dim):
            for j in range(i + 1, dim):
                if count == idx:
                    labels.append(f"a_{{{i}{j}}}")
                    found = True
                    break
                count += 1
            if found:
                break
        if not found:
            labels.append(f"param_{idx}")
    return labels
