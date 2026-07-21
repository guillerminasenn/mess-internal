"""Running-MSE convergence diagnostics for MESS versus EP-ESS branches."""

from __future__ import annotations

from typing import Callable, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from mess.experiments.common.plotting_utils import apply_publication_style, save_figure
from mess.experiments.polar_twist_convergence.config import ExperimentConfig
from mess.experiments.polar_twist_convergence.report_helpers import load_ep_grouped_chains, report_dirs


Observable = Callable[[np.ndarray], np.ndarray]


def _running_mean(series: np.ndarray) -> np.ndarray:
    csum = np.cumsum(series, axis=0)
    denom = np.arange(1, series.shape[0] + 1, dtype=float).reshape(-1, 1)
    return csum / denom


def _ep_group_running_mean(chains: list[np.ndarray], observable: Observable, n: int) -> Optional[np.ndarray]:
    if not chains:
        return None
    n0 = min(n, min(arr.shape[0] for arr in chains))
    if n0 <= 1:
        return None
    values = np.stack([observable(arr[:n0]) for arr in chains], axis=0)
    # EP estimator is average across independent chains at each iteration.
    mean_per_iter = np.mean(values, axis=0)
    return _running_mean(mean_per_iter.reshape(-1, 1)).reshape(-1)


def _single_running_mean(chain: np.ndarray, observable: Observable, n: int) -> Optional[np.ndarray]:
    n0 = min(n, chain.shape[0])
    if n0 <= 1:
        return None
    values = observable(chain[:n0]).reshape(-1, 1)
    return _running_mean(values).reshape(-1)


def _target_from_largest_m(
    grouped: Dict[tuple[str, int, int], list[np.ndarray]],
    cfg: ExperimentConfig,
    observable: Observable,
) -> float:
    m_star = int(max(cfg.ep_m_list))
    vals = []
    for (variant, m, _rep), chains in grouped.items():
        if int(m) != m_star:
            continue
        for chain in chains:
            post = chain[int(cfg.warmup_iters) :]
            if post.shape[0] == 0:
                continue
            vals.append(observable(post))
    if not vals:
        return float("nan")
    flat = np.concatenate([np.asarray(v, dtype=float).reshape(-1) for v in vals])
    return float(np.nanmean(flat))


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    cfg = config or ExperimentConfig()
    dirs = report_dirs(cfg)
    out_dir = dirs["fig_root"] / "warmup_mse"
    out_dir.mkdir(parents=True, exist_ok=True)
    apply_publication_style()

    grouped = load_ep_grouped_chains(cfg)
    warmup_n = max(2, int(cfg.warmup_iters))

    observables: Dict[str, Observable] = {
        "x1": lambda samples: samples[:, 0],
        "x2": lambda samples: samples[:, 1],
    }

    artifacts = []
    for obs_name, obs_fn in observables.items():
        target = _target_from_largest_m(grouped, cfg, obs_fn)

        fig, ax = plt.subplots(1, 1, figsize=(12.5, 4.8), constrained_layout=True)
        for m in sorted(int(v) for v in cfg.ep_m_list):
            mess_curves = []
            ep_curves = []
            reps = sorted({int(rep) for (variant, mm, rep) in grouped.keys() if int(mm) == int(m) and variant in {"mess", "ep_ess"}})
            for rep in reps:
                mess = grouped.get(("mess", int(m), rep), [])
                ep = grouped.get(("ep_ess", int(m), rep), [])

                if mess:
                    curve = _single_running_mean(mess[0], obs_fn, warmup_n)
                    if curve is not None:
                        mess_curves.append(curve)
                curve_ep = _ep_group_running_mean(ep, obs_fn, warmup_n)
                if curve_ep is not None:
                    ep_curves.append(curve_ep)

            if mess_curves:
                n = min(c.shape[0] for c in mess_curves)
                arr = np.stack([c[:n] for c in mess_curves], axis=0)
                mse = np.mean((arr - target) ** 2, axis=0)
                ax.plot(np.arange(1, n + 1), mse, linewidth=1.2, label=f"MESS M={m}")

            if ep_curves:
                n = min(c.shape[0] for c in ep_curves)
                arr = np.stack([c[:n] for c in ep_curves], axis=0)
                mse = np.mean((arr - target) ** 2, axis=0)
                ax.plot(np.arange(1, n + 1), mse, linewidth=1.2, linestyle="--", label=f"EP-ESS M={m}")

        ax.set_title(f"Running MSE during warmup for observable {obs_name}")
        ax.set_xlabel("iteration")
        ax.set_ylabel("running MSE")
        ax.grid(alpha=0.2)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper right", ncol=2, frameon=False, fontsize=8)

        p = save_figure(fig, out_dir / f"running_mse_{obs_name}.png", dpi=350)
        artifacts.append(
            {
                "kind": "figure",
                "path": str(p.resolve()),
                "description": f"Warmup running-MSE comparison for observable {obs_name}.",
            }
        )

    return {
        "artifacts": artifacts,
        "output_dir": str(out_dir.resolve()),
    }


def main() -> None:
    summary = run()
    print("\nConvergence MSE summary:")
    print(f"- Output dir: {summary['output_dir']}")
    print(f"- Figures: {len(summary['artifacts'])}")


if __name__ == "__main__":
    main()
