"""Deprecated compatibility wrapper: use report_parity_checklist instead."""

from __future__ import annotations

from typing import Dict, Optional

from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.config import ExperimentConfig
from mess.experiments.advection_diffusion_dim_sweep_shared_draws_pcn_mpcn.report_parity_checklist import (
    run as run_report_parity_checklist,
)


def run(config: Optional[ExperimentConfig] = None) -> Dict[str, object]:
    print("[deprecated] phase2_parity_checklist.run -> report_parity_checklist.run")
    return run_report_parity_checklist(config=config)


def main() -> None:
    summary = run()
    print("\nDeprecated phase-2 parity checklist summary:")
    print(f"- Passed: {summary['passed']}/{summary['total']}")
    print(f"- Markdown: {summary['markdown_path']}")
    print(f"- JSON: {summary['json_path']}")


if __name__ == "__main__":
    main()
