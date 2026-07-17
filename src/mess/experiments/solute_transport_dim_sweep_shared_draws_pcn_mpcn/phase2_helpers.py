"""Deprecated compatibility wrapper: use report_helpers instead."""

from __future__ import annotations

from mess.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_helpers import (
    build_visual_data,
    load_chain,
    parameter_index_for_pair,
    report_dirs,
)


def phase2_dirs(cfg):
    return report_dirs(cfg)
