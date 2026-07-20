"""Exact historical MESS ellipse playback plots from trace sidecars."""

from __future__ import annotations

from typing import Dict, Optional

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


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
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
    summary = run()
    print("\nMESS ellipse diagnostics summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Artifacts: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
