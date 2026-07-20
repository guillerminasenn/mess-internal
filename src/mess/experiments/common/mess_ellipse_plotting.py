"""Reusable MESS ellipse plotting helpers for exact playback traces."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import save_figure


def build_plane_basis(x_centered: np.ndarray, nu_centered: np.ndarray):
    x_norm = float(np.linalg.norm(x_centered))
    if x_norm == 0.0:
        raise ValueError("Current state has zero norm; cannot define ellipse plane.")
    u = x_centered / x_norm
    nu_parallel = float(np.dot(u, nu_centered))
    v_perp = nu_centered - nu_parallel * u
    v_perp_norm = float(np.linalg.norm(v_perp))
    if v_perp_norm == 0.0:
        basis = np.zeros_like(u)
        basis[0] = 1.0
        if abs(float(np.dot(basis, u))) > 0.9 and basis.shape[0] > 1:
            basis[1] = 1.0
            basis[0] = 0.0
        v_perp = basis - np.dot(basis, u) * u
        v_perp_norm = float(np.linalg.norm(v_perp))
    return x_norm, nu_parallel, v_perp_norm


def ellipse_coords(
    phi: np.ndarray,
    alpha_val: float,
    x_norm: float,
    nu_parallel: float,
    nu_perp_norm: float,
):
    delta = phi - alpha_val
    x_coord = x_norm * np.cos(delta) + nu_parallel * np.sin(delta)
    y_coord = nu_perp_norm * np.sin(delta)
    return x_coord, y_coord


def _plot_slice_segment(
    ax: plt.Axes,
    phi_grid: np.ndarray,
    mask: np.ndarray,
    alpha_val: float,
    x_norm: float,
    nu_parallel: float,
    nu_perp_norm: float,
    color: str = "green",
    alpha: float = 0.7,
    linewidth: float = 5.0,
) -> None:
    mask = np.asarray(mask, dtype=bool)
    if mask[0] and mask[-1]:
        phi_ext = np.concatenate([phi_grid, phi_grid[1:] + 2 * np.pi])
        mask_ext = np.concatenate([mask, mask[1:]])
        xs, ys = ellipse_coords(phi_ext, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        xs = xs.copy()
        ys = ys.copy()
        xs[~mask_ext] = np.nan
        ys[~mask_ext] = np.nan
        ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)
        return
    xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    xs = xs.copy()
    ys = ys.copy()
    xs[~mask] = np.nan
    ys[~mask] = np.nan
    ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)


def _draw_interval_arc(
    ax: plt.Axes,
    phi_min: float,
    phi_max: float,
    alpha_val: float,
    x_norm: float,
    nu_parallel: float,
    nu_perp_norm: float,
    color: str = "lightskyblue",
    linewidth: float = 3.0,
    alpha: float = 0.35,
) -> None:
    if phi_min <= phi_max:
        phi_arc = np.linspace(phi_min, phi_max, 200)
    else:
        phi_arc = np.concatenate([
            np.linspace(phi_min, 2 * np.pi, 150),
            np.linspace(0.0, phi_max, 150),
        ])
    xs, ys = ellipse_coords(phi_arc, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)


def _draw_interval_brackets(
    ax: plt.Axes,
    phi_min: float,
    phi_max: float,
    alpha_val: float,
    x_norm: float,
    nu_parallel: float,
    nu_perp_norm: float,
    bracket_len: float,
    color: str = "tab:blue",
) -> None:
    for phi in (phi_min, phi_max):
        x0, y0 = ellipse_coords(np.asarray([phi]), alpha_val, x_norm, nu_parallel, nu_perp_norm)
        x0 = float(x0[0])
        y0 = float(y0[0])
        delta = phi - alpha_val
        dx = -x_norm * np.sin(delta) + nu_parallel * np.cos(delta)
        dy = nu_perp_norm * np.cos(delta)
        normal = np.array([-dy, dx], dtype=float)
        norm_len = float(np.linalg.norm(normal))
        if norm_len == 0.0:
            continue
        normal /= norm_len
        x1 = x0 - 0.5 * bracket_len * normal[0]
        y1 = y0 - 0.5 * bracket_len * normal[1]
        x2 = x0 + 0.5 * bracket_len * normal[0]
        y2 = y0 + 0.5 * bracket_len * normal[1]
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=1.6)


def _base_limits(phi_grid: np.ndarray, alpha: float, x_norm: float, nu_parallel: float, nu_perp_norm: float):
    xs, ys = ellipse_coords(phi_grid, alpha, x_norm, nu_parallel, nu_perp_norm)
    pad = 0.08
    return (
        (float(xs.min()) * (1 + pad), float(xs.max()) * (1 + pad)),
        (float(ys.min()) * (1 + pad), float(ys.max()) * (1 + pad)),
        0.05 * max(float(xs.max() - xs.min()), float(ys.max() - ys.min())),
    )


def _slice_mask(trace_item: dict, problem, phi_grid: np.ndarray) -> np.ndarray:
    alpha_val = float(trace_item["alpha"])
    x_centered = np.asarray(trace_item["x_centered"], dtype=float)
    nu_centered = np.asarray(trace_item["nu_centered"], dtype=float)
    prior_mean = np.asarray(problem.prior_mean(), dtype=float)
    ellipse_props = (
        prior_mean[:, np.newaxis]
        + np.cos(phi_grid - alpha_val) * x_centered[:, np.newaxis]
        + np.sin(phi_grid - alpha_val) * nu_centered[:, np.newaxis]
    )
    log_likes_grid = np.array([problem.log_likelihood(ellipse_props[:, i]) for i in range(phi_grid.size)])
    return log_likes_grid > float(trace_item["logy"])


def plot_iteration_panels(trace_item: dict, problem, out_path: Path, title_prefix: str) -> Path:
    x_centered = np.asarray(trace_item["x_centered"], dtype=float)
    nu_centered = np.asarray(trace_item["nu_centered"], dtype=float)
    alpha_val = float(trace_item["alpha"])
    intervals = trace_item["intervals"]
    accepted_phi = float(trace_item["accepted_phi"])
    accepted_interval_idx = int(trace_item["accepted_interval_index"])

    x_norm, nu_parallel, nu_perp_norm = build_plane_basis(x_centered, nu_centered)
    phi_grid = np.linspace(0.0, 2 * np.pi, 600)
    slice_mask = _slice_mask(trace_item, problem, phi_grid)
    xlim, ylim, bracket_len = _base_limits(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)

    n_panels = 1 + len(intervals)
    n_cols = 3
    n_rows = int(np.ceil(n_panels / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(13, 4 * n_rows), constrained_layout=True)
    axes = np.array(axes).reshape(-1)

    ax = axes[0]
    xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    ax.plot(xs, ys, color="black", linewidth=1.2)
    _plot_slice_segment(ax, phi_grid, slice_mask, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    _draw_interval_arc(ax, 0.0, 2 * np.pi, alpha_val, x_norm, nu_parallel, nu_perp_norm)
    _draw_interval_brackets(ax, 0.0, 2 * np.pi, alpha_val, x_norm, nu_parallel, nu_perp_norm, bracket_len)
    ax.set_title(f"{title_prefix}: full bracket")

    for idx, interval in enumerate(intervals, start=1):
        ax = axes[idx]
        ax.plot(xs, ys, color="black", linewidth=1.2)
        _plot_slice_segment(ax, phi_grid, slice_mask, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        _draw_interval_arc(
            ax,
            float(interval["phi_min"]),
            float(interval["phi_max"]),
            alpha_val,
            x_norm,
            nu_parallel,
            nu_perp_norm,
        )
        _draw_interval_brackets(
            ax,
            float(interval["phi_min"]),
            float(interval["phi_max"]),
            alpha_val,
            x_norm,
            nu_parallel,
            nu_perp_norm,
            bracket_len,
        )
        phi_vector = np.asarray(interval["phi_vector"], dtype=float)
        px, py = ellipse_coords(phi_vector, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        ax.scatter(px, py, color="tab:red", s=30)

        valid_indices = np.asarray(interval["valid_indices"], dtype=int)
        if valid_indices.size > 0:
            vphi = phi_vector[valid_indices]
            vx, vy = ellipse_coords(vphi, alpha_val, x_norm, nu_parallel, nu_perp_norm)
            ax.scatter(vx, vy, color="darkgreen", s=34)

        if idx - 1 == accepted_interval_idx:
            axa, aya = ellipse_coords(np.asarray([accepted_phi]), alpha_val, x_norm, nu_parallel, nu_perp_norm)
            ax.scatter([float(axa[0])], [float(aya[0])], s=150, marker="s", facecolors="none", edgecolors="black")
            ax.set_title(f"Interval {idx}: accepted")
        else:
            ax.set_title(f"Interval {idx}")

    for ax in axes[:n_panels]:
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel("Plane coord 1")
        ax.set_ylabel("Plane coord 2")

    for ax in axes[n_panels:]:
        ax.axis("off")

    return save_figure(fig, out_path, dpi=300)


def plot_contiguous_overlay(traces: Iterable[dict], problem, out_path: Path, title: str) -> Path:
    traces = list(traces)
    if not traces:
        raise ValueError("At least one trace is required for contiguous overlay.")

    fig, ax = plt.subplots(figsize=(7.5, 6.6))
    colors = plt.cm.tab20(np.linspace(0.05, 0.95, len(traces)))
    for idx, trace_item in enumerate(traces):
        alpha_val = float(trace_item["alpha"])
        x_centered = np.asarray(trace_item["x_centered"], dtype=float)
        nu_centered = np.asarray(trace_item["nu_centered"], dtype=float)
        x_norm, nu_parallel, nu_perp_norm = build_plane_basis(x_centered, nu_centered)
        phi_grid = np.linspace(0.0, 2 * np.pi, 600)
        slice_mask = _slice_mask(trace_item, problem, phi_grid)
        xs, ys = ellipse_coords(phi_grid, alpha_val, x_norm, nu_parallel, nu_perp_norm)
        ax.plot(xs, ys, linewidth=1.0, color=colors[idx], alpha=0.55, label=f"iter {trace_item['iteration']}")
        _plot_slice_segment(
            ax,
            phi_grid,
            slice_mask,
            alpha_val,
            x_norm,
            nu_parallel,
            nu_perp_norm,
            alpha=0.5,
            linewidth=4.0,
        )

    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title)
    ax.set_xlabel("Plane coord 1")
    ax.set_ylabel("Plane coord 2")
    ax.legend(loc="best", fontsize=8)
    return save_figure(fig, out_path, dpi=300)


def trace_to_jsonable(trace: dict) -> Dict[str, object]:
    out: Dict[str, object] = {
        "x": np.asarray(trace["x"], dtype=float).tolist(),
        "x_centered": np.asarray(trace["x_centered"], dtype=float).tolist(),
        "nu_centered": np.asarray(trace["nu_centered"], dtype=float).tolist(),
        "alpha": float(trace["alpha"]),
        "logy": float(trace["logy"]),
        "accepted_phi": float(trace["accepted_phi"]),
        "accepted_interval_index": int(trace["accepted_interval_index"]),
        "accepted_index": int(trace["accepted_index"]),
        "intervals": [],
    }
    for interval in trace["intervals"]:
        out["intervals"].append(
            {
                "phi_min": float(interval["phi_min"]),
                "phi_max": float(interval["phi_max"]),
                "phi_vector": np.asarray(interval["phi_vector"], dtype=float).tolist(),
                "log_likelihoods": np.asarray(interval["log_likelihoods"], dtype=float).tolist(),
                "valid_indices": np.asarray(interval["valid_indices"], dtype=int).tolist(),
                "accepted_index": None
                if interval.get("accepted_index") is None
                else int(interval["accepted_index"]),
            }
        )
    return out


def trace_from_jsonable(trace: dict) -> dict:
    out = {
        "x": np.asarray(trace["x"], dtype=float),
        "x_centered": np.asarray(trace["x_centered"], dtype=float),
        "nu_centered": np.asarray(trace["nu_centered"], dtype=float),
        "alpha": float(trace["alpha"]),
        "logy": float(trace["logy"]),
        "accepted_phi": float(trace["accepted_phi"]),
        "accepted_interval_index": int(trace["accepted_interval_index"]),
        "accepted_index": int(trace["accepted_index"]),
        "intervals": [],
    }
    for interval in trace["intervals"]:
        out["intervals"].append(
            {
                "phi_min": float(interval["phi_min"]),
                "phi_max": float(interval["phi_max"]),
                "phi_vector": np.asarray(interval["phi_vector"], dtype=float),
                "log_likelihoods": np.asarray(interval["log_likelihoods"], dtype=float),
                "valid_indices": np.asarray(interval["valid_indices"], dtype=int),
                "accepted_index": None
                if interval.get("accepted_index") is None
                else int(interval["accepted_index"]),
            }
        )
    return out
