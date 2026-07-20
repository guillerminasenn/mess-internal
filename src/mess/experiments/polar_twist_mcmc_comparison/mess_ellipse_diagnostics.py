"""Exact historical MESS ellipse playback plots from trace sidecars."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from mess.experiments.common.mess_ellipse_plotting import (
    plot_contiguous_overlay,
    plot_iteration_panels,
)
from mess.experiments.common.plotting_utils import apply_publication_style
from mess.experiments.polar_twist_mcmc_comparison.config import ExperimentConfig
from mess.experiments.polar_twist_mcmc_comparison.report_helpers import (
    build_visual_data,
    load_mess_ellipse_traces,
    report_dirs,
)


def _select_iterations(
    traces: Iterable[dict],
    start_iter: Optional[int],
    n_iters: Optional[int],
    explicit_iters: Optional[list[int]],
) -> list[dict]:
    traces = sorted(list(traces), key=lambda item: int(item["iteration"]))
    if explicit_iters:
        wanted = {int(v) for v in explicit_iters}
        return [item for item in traces if int(item["iteration"]) in wanted]
    if start_iter is not None and n_iters is not None and n_iters > 0:
        stop = int(start_iter) + int(n_iters)
        return [
            item
            for item in traces
            if int(start_iter) <= int(item["iteration"]) < stop
        ]
    return traces


def run(
    config: Optional[ExperimentConfig] = None,
    start_iter: Optional[int] = None,
    n_iters: Optional[int] = None,
    iterations: Optional[list[int]] = None,
) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "mess_ellipse_diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    problem = build_visual_data(cfg)["problem"]
    artifacts = []

    for m in cfg.M_list:
        traces, trace_path = load_mess_ellipse_traces(cfg, dirs["estimations_dir"], M=int(m))
        if not traces:
            continue
        traces = _select_iterations(traces, start_iter=start_iter, n_iters=n_iters, explicit_iters=iterations)
        if not traces:
            continue

        overlay_path = out_dir / f"mess_M{int(m)}_overlay_n{len(traces)}.png"
        p = plot_contiguous_overlay(
            traces=traces,
            problem=problem,
            out_path=overlay_path,
            title=f"MESS M={int(m)}: historical ellipse playback",
        )
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"Contiguous ellipse overlay using exact historical traces (M={int(m)}).",
            }
        )

        for trace_item in traces:
            iteration = int(trace_item["iteration"])
            panel_path = out_dir / f"mess_M{int(m)}_iter{iteration}_intervals.png"
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

        artifacts.append(
            {
                "kind": "diagnostic",
                "path": str(trace_path.resolve()),
                "description": f"Exact historical MESS trace sidecar consumed for M={int(m)}.",
            }
        )

    return {"artifacts": artifacts, "output_dir": str(out_dir.resolve())}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate historical MESS ellipse diagnostics.")
    parser.add_argument("--start-iter", type=int, default=None, help="Start iteration (inclusive) filter.")
    parser.add_argument("--n-iters", type=int, default=None, help="Number of contiguous iterations to include.")
    parser.add_argument(
        "--iters",
        type=str,
        default="",
        help="Comma-separated explicit iteration list (overrides start/n-iters).",
    )
    args = parser.parse_args()

    iters = None
    if args.iters.strip():
        iters = [int(v.strip()) for v in args.iters.split(",") if v.strip()]

    summary = run(start_iter=args.start_iter, n_iters=args.n_iters, iterations=iters)
    print("\nMESS ellipse diagnostics summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Artifacts: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
