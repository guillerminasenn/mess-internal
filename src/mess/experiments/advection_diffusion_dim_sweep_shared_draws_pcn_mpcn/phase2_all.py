"""Deprecated compatibility wrapper for old phase-2 report entrypoint."""

from __future__ import annotations

from typing import Optional

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import (
    ExperimentConfig,
)
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.report_workflow import (
    run as run_report_workflow,
)


def run(config: Optional[ExperimentConfig] = None) -> None:
    print("[deprecated] phase2_all.run -> report_workflow.run")
    run_report_workflow(config=config)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
