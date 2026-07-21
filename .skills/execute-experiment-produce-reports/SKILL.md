---
name: execute-experiment-produce-reports
description: Run the report-generation phase for an experiment by resolving report entrypoints from instructions/experiments; default is full report set unless a subset is requested.
---

# Execute Experiment: Produce Reports

Use this skill when the user asks for figures/checklists/reports from an experiment.

## Resolve target experiment
1. Determine `<experiment>` from the user request.
2. Read `instructions/experiments/<experiment>.md`.
3. Resolve package path as `<repo>.experiments.<experiment>`.
4. Resolve available report modules from the experiment spec.

## Default behavior
- If user does not request a subset: run full report workflow.
- If user requests a subset: run only the corresponding module entrypoints.

## Generic full-report command (default)
- `<activate_env_command> && python -m <repo>.experiments.<experiment>.report_workflow`

## Environment placeholder
- `<activate_env_command>` means the repository-specific environment activation command
  (for example `source .venv/bin/activate` or equivalent for the active workspace).

## Conditional execution (if/else)
- If `instructions/experiments/<experiment>.md` defines a `report_workflow` entrypoint:
  - Use it when no subset is requested.
- Else:
  - Run the report modules listed in the experiment spec one by one.

- If subset is requested:
  - Map requested subset names to module entrypoints listed in `instructions/experiments/<experiment>.md`.
  - Run only requested subsets.

- If `<experiment>` is `solute_transport_dim_sweep_shared_draws_pcn_mpcn`:
  - Full workflow:
    - `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_workflow`
  - Supported subsets:
    - `visual_checks` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.visual_checks`
    - `traceplots` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.traceplots`
    - `panels` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.panels`
    - `ess_msjd` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.ess_msjd_plots`
    - `pairplots` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.pairplots`
    - `parity_checklist` -> `python -m <repo>.experiments.solute_transport_dim_sweep_shared_draws_pcn_mpcn.report_parity_checklist`
- If `<experiment>` is `polar_twist_mcmc_comparison`:
  - Full workflow:
    - `python -m <repo>.experiments.polar_twist_mcmc_comparison.report_workflow`
  - Supported subsets:
    - `visual_checks` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.visual_checks`
    - `traceplots` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.traceplots`
    - `panels` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.panels`
    - `ess_msjd` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.ess_msjd_plots`
    - `rejection` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.rejection_plots`
    - `pairplots` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.pairplots`
    - `ellipse_diagnostics` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.mess_ellipse_diagnostics`
    - `mess_ess_vs_m` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.mess_ess_vs_m_plots`
    - `parity_checklist` -> `python -m <repo>.experiments.polar_twist_mcmc_comparison.report_parity_checklist`
- If `<experiment>` is `polar_twist_ep`:
  - Full workflow:
    - `python -m <repo>.experiments.polar_twist_ep.report_workflow`
  - Supported subsets:
    - `ess_msjd` -> `python -m <repo>.experiments.polar_twist_ep.ess_vs_m_plots`
    - `parity_checklist` -> `python -m <repo>.experiments.polar_twist_ep.report_parity_checklist`
- Else:
  - Use only report modules declared in `instructions/experiments/<experiment>.md`.

## Required precondition checks
- If any selected report module depends on metrics (for example ESS/MSJD plots):
  - Ensure required metrics tables exist first.
  - If missing, run the metrics workflow for `<experiment>` before report plotting.
- If `ellipse_diagnostics` is requested:
  - Ensure required MESS trace sidecars exist; otherwise ask user to re-run chain generation with trace capture enabled.
- If the request includes convergence-phase EP diagnostics for polar twist:
  - Run the `polar_twist_convergence` report workflow in addition to `polar_twist_ep` report workflow, because warmup trace/MSE outputs are owned by the convergence package.

## Related skill handoff
- If the user specifically requests MESS ellipse playback plots, prefer invoking `plot-ellipses`.

## Output checks
- Validate report outputs declared in `instructions/experiments/<experiment>.md`.
- For solute dim-sweep, expected checks include:
  - pairplots around 40 files for default grid.
  - ESS/MSJD folder with 8 files (mean/mean_log and component variants).

## Example invocation
```text
Use execute-experiment-produce-reports for <experiment>. If no subset is given,
run full report workflow. If subset is requested, run only those modules defined
for that experiment in instructions/experiments/<experiment>.md.
```
