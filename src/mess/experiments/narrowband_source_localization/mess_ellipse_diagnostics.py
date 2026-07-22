"""MESS ellipse diagnostics for narrowband source localization via deterministic replay."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np

from mess.algorithms.mess import mess_step
from mess.experiments.common.mess_ellipse_plotting import plot_contiguous_overlay, plot_iteration_panels
from mess.experiments.common.plotting_utils import apply_publication_style
from mess.experiments.narrowband_source_localization.config import ExperimentConfig, build_context, sample_start_points
from mess.problems import build_narrowband_source_localization_problem


def _transition_lp_config(variant: str) -> tuple[bool, str]:
    key = str(variant).strip().lower()
    if key == "uniform":
        return False, "angular"
    if key == "euclidean_informed":
        return True, "euclidean"
    if key == "angular_informed":
        return True, "angular"
    raise ValueError(f"Unknown transition variant '{variant}'")


def _select_trace_window(start_iter: int, n_iters: int) -> set[int]:
    if start_iter < 1:
        raise ValueError("start_iter must be >= 1")
    if n_iters < 1:
        raise ValueError("n_iters must be >= 1")
    return set(range(int(start_iter), int(start_iter + n_iters)))


def run(
    config: Optional[ExperimentConfig] = None,
    *,
    start_iter: int = 200,
    n_iters: int = 3,
    replicate: int = 0,
    variant: str = "uniform",
    m_list: Optional[list[int]] = None,
) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    out_dir = Path(ctx["reports_dir"]) / "figures" / "mess_ellipse_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    problem, _ = build_narrowband_source_localization_problem(
        sensors_m=np.asarray(cfg.sensors_m, dtype=float),
        frequencies_hz=cfg.frequencies_hz,
        propagation_speed=float(cfg.propagation_speed),
        true_source_m=cfg.true_source_m,
        tau=cfg.tau,
        sigma=cfg.sigma,
        prior_mean_m=cfg.prior_mean_m,
        prior_cov_m=cfg.prior_cov_m(),
        amplitude_model=cfg.amplitude_model,
        gamma=float(cfg.amplitude_gamma),
        r_min=float(cfg.r_min),
        data_seed=int(cfg.data_seed),
    )
    starts = sample_start_points(cfg)

    sel = _select_trace_window(start_iter=start_iter, n_iters=n_iters)
    max_iter = max(sel)

    m_values = sorted(int(v) for v in (m_list if m_list is not None else cfg.M_list))
    use_lp, distance_metric = _transition_lp_config(variant)

    artifacts = []
    for m in m_values:
        x = starts["mess_starts"][int(replicate)].copy()
        seed = int(cfg.seed_mcmc) + 100000 * int(m) + 1000 * int(replicate) + (0 if variant == "uniform" else 10)
        rng = np.random.default_rng(seed)

        traces = []
        for t in range(1, max_iter + 1):
            x, _, _, trace = mess_step(
                x,
                problem,
                rng,
                M=int(m),
                use_lp=use_lp,
                distance_metric=distance_metric,
                return_trace=True,
            )
            if t in sel:
                trace_item = dict(trace)
                trace_item["iteration"] = int(t)
                traces.append(trace_item)

        if not traces:
            continue

        overlay_path = out_dir / f"mess_{variant}_M{int(m)}_rep{int(replicate):03d}_overlay_{start_iter}_{start_iter+n_iters-1}.png"
        p = plot_contiguous_overlay(
            traces=traces,
            problem=problem,
            out_path=overlay_path,
            title=f"MESS {variant} M={int(m)} rep={int(replicate)}: ellipse playback",
        )
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"Contiguous replayed ellipse overlay for M={int(m)}, variant={variant}, rep={int(replicate)}.",
            }
        )

        for trace_item in traces:
            iteration = int(trace_item["iteration"])
            panel_path = out_dir / f"mess_{variant}_M{int(m)}_rep{int(replicate):03d}_iter{iteration}_intervals.png"
            p = plot_iteration_panels(
                trace_item=trace_item,
                problem=problem,
                out_path=panel_path,
                title_prefix=f"Iteration {iteration}",
            )
            artifacts.append(
                {
                    "kind": "figure",
                    "path": str(p.resolve()),
                    "description": f"Interval-level ellipse playback for M={int(m)}, iteration={iteration}.",
                }
            )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate MESS ellipse diagnostics for source localization.")
    parser.add_argument("--start-iter", type=int, default=200, help="First iteration to visualize (1-based).")
    parser.add_argument("--n-iters", type=int, default=3, help="Number of contiguous iterations to visualize.")
    parser.add_argument("--replicate", type=int, default=0, help="Replicate index to replay.")
    parser.add_argument("--variant", type=str, default="uniform", help="Transition variant.")
    parser.add_argument("--M-list", type=str, default="", help="Optional comma-separated M list override.")
    args = parser.parse_args()

    m_list = None
    if args.M_list.strip():
        m_list = [int(v.strip()) for v in args.M_list.split(",") if v.strip()]

    summary = run(
        start_iter=int(args.start_iter),
        n_iters=int(args.n_iters),
        replicate=int(args.replicate),
        variant=str(args.variant),
        m_list=m_list,
    )
    print("\nMESS ellipse diagnostics summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Artifacts: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
