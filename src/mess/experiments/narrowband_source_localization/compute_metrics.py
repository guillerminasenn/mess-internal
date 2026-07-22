"""Compute chain-level and replicate-level metrics for source localization."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from mess.algorithms.effective_sample_size import estimate_effective_sample_size
from mess.experiments.narrowband_source_localization.config import ExperimentConfig, build_context
from mess.experiments.narrowband_source_localization.naming import parse_chain_name
from mess.problems import build_narrowband_source_localization_problem


def _msjd(samples: np.ndarray) -> float:
    if samples.shape[0] < 2:
        return float("nan")
    jumps = np.diff(samples, axis=0)
    sq = np.sum(jumps * jumps, axis=1)
    return float(np.mean(sq))


def _chain_metrics(path: Path, cfg: ExperimentConfig, problem) -> Optional[Dict[str, Any]]:
    parsed = parse_chain_name(path)
    if parsed is None:
        return None
    sampler, m, replicate, transition_variant, chain_idx = parsed

    with np.load(path) as payload:
        chain = np.asarray(payload["chain"], dtype=float)
        subiters = np.asarray(payload.get("mess_subiters_per_iter", np.array([], dtype=float)), dtype=float)

    samples_z = chain[int(cfg.burn_in) :: int(cfg.thin)]
    if samples_z.shape[0] < 4:
        return None

    samples_q = problem.whitened_to_physical(samples_z)
    log_lik = problem.log_likelihood_batch(samples_z)

    ess_z = [float(estimate_effective_sample_size(samples_z[:, j], max_lag=int(cfg.max_lag))) for j in range(2)]
    ess_q = [float(estimate_effective_sample_size(samples_q[:, j], max_lag=int(cfg.max_lag))) for j in range(2)]
    ess_loglik = float(estimate_effective_sample_size(log_lik, max_lag=int(cfg.max_lag)))

    msjd_z = _msjd(samples_z)
    msjd_q = _msjd(samples_q)

    post_burn_subiters = subiters[int(cfg.burn_in) : int(cfg.n_iters)] if subiters.size >= int(cfg.n_iters) else np.array([], dtype=float)
    total_subiters = float(np.sum(post_burn_subiters)) if post_burn_subiters.size else float("nan")

    if sampler == "mess":
        lik_evals = total_subiters * float(m) if np.isfinite(total_subiters) else float("nan")
        parallel_steps = total_subiters
    elif sampler == "ep_ess":
        lik_evals = total_subiters if np.isfinite(total_subiters) else float("nan")
        parallel_steps = total_subiters
    else:
        lik_evals = float("nan")
        parallel_steps = float("nan")

    return {
        "sampler": sampler,
        "transition_variant": transition_variant,
        "M": int(m),
        "replicate": int(replicate),
        "chain_idx": int(chain_idx) if chain_idx is not None else None,
        "n_post_burn": int(samples_z.shape[0]),
        "ess_z1": ess_z[0],
        "ess_z2": ess_z[1],
        "ess_q1": ess_q[0],
        "ess_q2": ess_q[1],
        "ess_log_likelihood": ess_loglik,
        "msjd_z": msjd_z,
        "msjd_q": msjd_q,
        "total_subiters_post_burn": total_subiters,
        "lik_evals_post_burn": lik_evals,
        "parallel_lik_steps_post_burn": parallel_steps,
        "path": str(path.resolve()),
    }


def _aggregate_replicates(chain_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[Tuple[str, str, int, int], List[Dict[str, Any]]] = defaultdict(list)
    for row in chain_rows:
        key = (str(row["sampler"]), str(row["transition_variant"]), int(row["M"]), int(row["replicate"]))
        by_key[key].append(row)

    rep_rows: List[Dict[str, Any]] = []
    for (sampler, transition_variant, m, replicate), rows in sorted(by_key.items()):
        if sampler == "ep_ess":
            raw_ess_q1 = float(np.nansum([r["ess_q1"] for r in rows]))
            raw_ess_q2 = float(np.nansum([r["ess_q2"] for r in rows]))
            raw_ess_ll = float(np.nansum([r["ess_log_likelihood"] for r in rows]))
            energy_lik = float(np.nansum([r["lik_evals_post_burn"] for r in rows]))
            summed_steps = float(np.nansum([r["parallel_lik_steps_post_burn"] for r in rows]))
            parallel_steps = summed_steps / float(m)
        else:
            base = rows[0]
            raw_ess_q1 = float(base["ess_q1"])
            raw_ess_q2 = float(base["ess_q2"])
            raw_ess_ll = float(base["ess_log_likelihood"])
            energy_lik = float(base["lik_evals_post_burn"])
            parallel_steps = float(base["parallel_lik_steps_post_burn"])

        rep_rows.append(
            {
                "sampler": sampler,
                "transition_variant": transition_variant,
                "M": int(m),
                "replicate": int(replicate),
                "n_chains": int(len(rows)),
                "raw_ess_q1": raw_ess_q1,
                "raw_ess_q2": raw_ess_q2,
                "raw_ess_log_likelihood": raw_ess_ll,
                "ess_q1_per_energy_lik_eval": raw_ess_q1 / energy_lik if np.isfinite(energy_lik) and energy_lik > 0 else float("nan"),
                "ess_q2_per_energy_lik_eval": raw_ess_q2 / energy_lik if np.isfinite(energy_lik) and energy_lik > 0 else float("nan"),
                "ess_ll_per_energy_lik_eval": raw_ess_ll / energy_lik if np.isfinite(energy_lik) and energy_lik > 0 else float("nan"),
                "ess_q1_per_parallel_lik_step": raw_ess_q1 / parallel_steps if np.isfinite(parallel_steps) and parallel_steps > 0 else float("nan"),
                "ess_q2_per_parallel_lik_step": raw_ess_q2 / parallel_steps if np.isfinite(parallel_steps) and parallel_steps > 0 else float("nan"),
                "ess_ll_per_parallel_lik_step": raw_ess_ll / parallel_steps if np.isfinite(parallel_steps) and parallel_steps > 0 else float("nan"),
                "energy_lik_eval_denom": energy_lik,
                "parallel_lik_step_denom": parallel_steps,
            }
        )
    return rep_rows


def _aggregate_by_m(rep_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    by_key: Dict[Tuple[str, str, int], List[Dict[str, Any]]] = defaultdict(list)
    for row in rep_rows:
        by_key[(str(row["sampler"]), str(row["transition_variant"]), int(row["M"]))].append(row)

    def _mean_finite(values: List[float]) -> float:
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return float("nan")
        return float(np.mean(arr))

    for (sampler, transition_variant, m), rows in sorted(by_key.items()):
        out.append(
            {
                "aggregation": "by_m",
                "sampler": sampler,
                "transition_variant": transition_variant,
                "M": int(m),
                "replicate_count": int(len(rows)),
                "raw_ess_q1": _mean_finite([r["raw_ess_q1"] for r in rows]),
                "raw_ess_q2": _mean_finite([r["raw_ess_q2"] for r in rows]),
                "raw_ess_log_likelihood": _mean_finite([r["raw_ess_log_likelihood"] for r in rows]),
                "ess_q1_per_energy_lik_eval": _mean_finite([r["ess_q1_per_energy_lik_eval"] for r in rows]),
                "ess_q2_per_energy_lik_eval": _mean_finite([r["ess_q2_per_energy_lik_eval"] for r in rows]),
                "ess_ll_per_energy_lik_eval": _mean_finite([r["ess_ll_per_energy_lik_eval"] for r in rows]),
                "ess_q1_per_parallel_lik_step": _mean_finite([r["ess_q1_per_parallel_lik_step"] for r in rows]),
                "ess_q2_per_parallel_lik_step": _mean_finite([r["ess_q2_per_parallel_lik_step"] for r in rows]),
                "ess_ll_per_parallel_lik_step": _mean_finite([r["ess_ll_per_parallel_lik_step"] for r in rows]),
            }
        )
    return out


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]

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

    chain_rows: List[Dict[str, Any]] = []
    for chain_file in sorted(outdir.glob("chain_*.npz")):
        row = _chain_metrics(chain_file, cfg, problem)
        if row is not None:
            chain_rows.append(row)

    rep_rows = _aggregate_replicates(chain_rows)
    by_m_rows = _aggregate_by_m(rep_rows)

    tables_dir = outdir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    per_chain_path = tables_dir / "metrics_per_chain.json"
    per_rep_path = tables_dir / "metrics_per_replicate.json"
    summary_path = tables_dir / "metrics_summary.json"

    with open(per_chain_path, "w", encoding="utf-8") as handle:
        json.dump(chain_rows, handle, indent=2)
    with open(per_rep_path, "w", encoding="utf-8") as handle:
        json.dump(rep_rows, handle, indent=2)
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(by_m_rows, handle, indent=2)

    print(f"Metric rows (chain): {len(chain_rows)}")
    print(f"Metric rows (replicate): {len(rep_rows)}")
    print(f"Metric rows (summary): {len(by_m_rows)}")

    return {
        "report_path": str(summary_path.resolve()),
        "per_chain_path": str(per_chain_path.resolve()),
        "per_replicate_path": str(per_rep_path.resolve()),
        "rows": len(by_m_rows),
    }


def main() -> None:
    summary = run()
    print("\nMetrics summary:")
    print(f"- Report: {summary['report_path']}")
    print(f"- Per-chain: {summary['per_chain_path']}")
    print(f"- Per-replicate: {summary['per_replicate_path']}")
    print(f"- Rows: {summary['rows']}")


if __name__ == "__main__":
    main()
