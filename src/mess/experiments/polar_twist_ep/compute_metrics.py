"""Compute chain-level and replicate-level ESS/MSJD metrics for polar-twist EP experiment."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from mess.algorithms.effective_sample_size import estimate_effective_sample_size
from mess.experiments.polar_twist_ep.config import ExperimentConfig, build_context
from mess.experiments.polar_twist_ep.naming import parse_chain_name


def _msjd_per_dim(samples: np.ndarray) -> np.ndarray:
    if samples.shape[0] < 2:
        return np.full(samples.shape[1], np.nan, dtype=float)
    jumps = np.diff(samples, axis=0)
    return np.mean(jumps * jumps, axis=0)


def _chain_metrics(path: Path, cfg: ExperimentConfig) -> Optional[Dict[str, Any]]:
    parsed = parse_chain_name(path)
    if parsed is None:
        return None
    variant, m, replicate, chain_idx = parsed

    with np.load(path) as payload:
        chain = np.asarray(payload["chain"], dtype=float)
        subiters = np.asarray(payload.get("mess_subiters_per_iter", np.array([], dtype=float)), dtype=float)

    samples = chain[int(cfg.burn_in) :: int(cfg.thin)]
    if samples.shape[0] < 4:
        return None

    ess_vec = np.array(
        [float(estimate_effective_sample_size(samples[:, j], max_lag=int(cfg.max_lag))) for j in range(samples.shape[1])],
        dtype=float,
    )
    msjd_vec = _msjd_per_dim(samples)

    post_burn_subiters = subiters[int(cfg.burn_in) : int(cfg.n_iters)] if subiters.size >= int(cfg.n_iters) else np.array([], dtype=float)
    total_subiters = float(np.sum(post_burn_subiters)) if post_burn_subiters.size else float("nan")
    batch_m = int(m) if variant == "mess" else 1
    lik_evals = total_subiters * float(batch_m) if np.isfinite(total_subiters) else float("nan")

    return {
        "variant": variant,
        "M": int(m),
        "replicate": int(replicate),
        "chain_idx": int(chain_idx) if chain_idx is not None else None,
        "n_post_burn": int(samples.shape[0]),
        "ess_x1": float(ess_vec[0]) if ess_vec.shape[0] > 0 else float("nan"),
        "ess_x2": float(ess_vec[1]) if ess_vec.shape[0] > 1 else float("nan"),
        "ess_mean": float(np.nanmean(ess_vec)),
        "msjd_x1": float(msjd_vec[0]) if msjd_vec.shape[0] > 0 else float("nan"),
        "msjd_x2": float(msjd_vec[1]) if msjd_vec.shape[0] > 1 else float("nan"),
        "msjd_mean": float(np.nanmean(msjd_vec)),
        "total_subiters_post_burn": total_subiters,
        "lik_evals_post_burn": lik_evals,
        "path": str(path.resolve()),
    }


def _aggregate_replicates(chain_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[Tuple[str, int, int], List[Dict[str, Any]]] = defaultdict(list)
    for row in chain_rows:
        by_key[(str(row["variant"]), int(row["M"]), int(row["replicate"]))].append(row)

    rep_rows: List[Dict[str, Any]] = []
    for (variant, m, replicate), rows in sorted(by_key.items()):
        if variant == "mess":
            base = rows[0]
            raw_x1 = float(base["ess_x1"])
            raw_x2 = float(base["ess_x2"])
            raw_mean = float(base["ess_mean"])
            energy_denom = float(base.get("lik_evals_post_burn", float("nan")))
            parallel_denom = float(base.get("total_subiters_post_burn", float("nan")))
        else:
            raw_x1 = float(np.nansum([float(r["ess_x1"]) for r in rows]))
            raw_x2 = float(np.nansum([float(r["ess_x2"]) for r in rows]))
            raw_mean = float(np.nansum([float(r["ess_mean"]) for r in rows]))
            energy_denom = float(np.nansum([float(r.get("lik_evals_post_burn", float("nan"))) for r in rows]))
            summed_parallel_steps = float(np.nansum([float(r.get("total_subiters_post_burn", float("nan"))) for r in rows]))
            parallel_denom = summed_parallel_steps / float(m)

        rep_rows.append(
            {
                "variant": variant,
                "M": int(m),
                "replicate": int(replicate),
                "n_chains": int(len(rows)),
                "raw_ess_x1": raw_x1,
                "raw_ess_x2": raw_x2,
                "raw_ess_mean": raw_mean,
                "ess_x1_per_energy_lik_eval": raw_x1 / energy_denom if np.isfinite(energy_denom) and energy_denom > 0 else float("nan"),
                "ess_x2_per_energy_lik_eval": raw_x2 / energy_denom if np.isfinite(energy_denom) and energy_denom > 0 else float("nan"),
                "ess_mean_per_energy_lik_eval": raw_mean / energy_denom if np.isfinite(energy_denom) and energy_denom > 0 else float("nan"),
                "ess_x1_per_parallel_lik_step": raw_x1 / parallel_denom if np.isfinite(parallel_denom) and parallel_denom > 0 else float("nan"),
                "ess_x2_per_parallel_lik_step": raw_x2 / parallel_denom if np.isfinite(parallel_denom) and parallel_denom > 0 else float("nan"),
                "ess_mean_per_parallel_lik_step": raw_mean / parallel_denom if np.isfinite(parallel_denom) and parallel_denom > 0 else float("nan"),
                "energy_lik_eval_denom": energy_denom,
                "parallel_lik_step_denom": parallel_denom,
            }
        )
    return rep_rows


def _aggregate_by_m(rep_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    by_key: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    for row in rep_rows:
        by_key[(str(row["variant"]), int(row["M"]))].append(row)

    for (variant, m), rows in sorted(by_key.items()):
        out.append(
            {
                "aggregation": "by_m",
                "variant": variant,
                "M": int(m),
                "replicate_count": int(len(rows)),
                "raw_ess_x1": float(np.nanmean([float(r["raw_ess_x1"]) for r in rows])),
                "raw_ess_x2": float(np.nanmean([float(r["raw_ess_x2"]) for r in rows])),
                "raw_ess_mean": float(np.nanmean([float(r["raw_ess_mean"]) for r in rows])),
                "ess_x1_per_energy_lik_eval": float(np.nanmean([float(r["ess_x1_per_energy_lik_eval"]) for r in rows])),
                "ess_x2_per_energy_lik_eval": float(np.nanmean([float(r["ess_x2_per_energy_lik_eval"]) for r in rows])),
                "ess_mean_per_energy_lik_eval": float(np.nanmean([float(r["ess_mean_per_energy_lik_eval"]) for r in rows])),
                "ess_x1_per_parallel_lik_step": float(np.nanmean([float(r["ess_x1_per_parallel_lik_step"]) for r in rows])),
                "ess_x2_per_parallel_lik_step": float(np.nanmean([float(r["ess_x2_per_parallel_lik_step"]) for r in rows])),
                "ess_mean_per_parallel_lik_step": float(np.nanmean([float(r["ess_mean_per_parallel_lik_step"]) for r in rows])),
            }
        )
    return out


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, Any]:
    cfg = config or ExperimentConfig()
    ctx = build_context(cfg)
    outdir: Path = ctx["estimations_dir"]

    chain_rows: List[Dict[str, Any]] = []
    for chain_file in sorted(outdir.glob("chain_*.npz")):
        row = _chain_metrics(chain_file, cfg)
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
    print(f"Metrics summary: {summary_path}")

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
