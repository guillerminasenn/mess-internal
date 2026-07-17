# Diagnostics Policy

This document defines diagnostics that apply across experiments and algorithms, including MESS, ESS, MH, pCN, mpCN, and future methods.

## Pointwise error diagnostics (MAE/MSE/RMSE)

For a scalar quantity of interest $z$ (parameter component, observable, or summary statistic) with reference value $z^*$:

1. Choose comparison windows (for example, fixed sample counts for bar plots and progressive windows for time-series plots).
2. For each chain and each window length $n$, compute:
   - MAE: $\frac{1}{n}\sum_{t=1}^n |z_t-z^*|$
   - MSE: $\frac{1}{n}\sum_{t=1}^n (z_t-z^*)^2$
   - RMSE: $\sqrt{\mathrm{MSE}}$
3. Aggregate across chains within each algorithm variant (mean by default unless explicitly overridden).

If comparing thinned and unthinned variants, align effective sample counts before comparison.

## Running observable MSE

For chain $\{X_t\}_{t=1}^T$ and observable $\varphi$:

$$\bar{\varphi}_t = \frac{1}{t}\sum_{s=1}^t \varphi(X_s).$$

For embarrassingly parallel (EP) groups with $P$ chains:

$$\tilde{\varphi}_t^{\mathrm{EP}} = \frac{1}{P}\sum_{p=1}^P \varphi(X_{t,p}), \qquad
\bar{\varphi}_t^{\mathrm{EP}} = \frac{1}{t}\sum_{s=1}^t \tilde{\varphi}_s^{\mathrm{EP}}.$$

Given reference target $\mu_\varphi$ (typically from long-run posterior means), running MSE is:

$$\mathrm{MSE}_t = \frac{1}{K}\sum_{k=1}^K \left(\bar{\varphi}_t^{(k)} - \mu_\varphi\right)^2.$$

Observable sets are experiment-specific but must be documented in the relevant experiment instruction file.

## ESS and MSJD diagnostics

### ESS
- Compute ESS per scalar component/observable.
- Report aggregation explicitly (for example mean ESS across components, sum ESS across independent chains, or min ESS as a conservative bound).

### MSJD
- For samples $x_t$, define jump vectors $\Delta_t = x_{t+1}-x_t$.
- MSJD per chain is mean squared jump norm over available iterations.
- For independent-chain groups, report explicit aggregation (mean and optionally max across chains).

## Independent-chain and EP diagnostics

When diagnostics are computed from independent chains:

1. Load indexed chain set for the target algorithm/configuration.
2. Apply burn-in and thinning policy consistently.
3. Compute per-chain diagnostics.
4. Aggregate diagnostics according to the experiment definition.

Store aggregation outputs in diagnostics payloads with clear field names and documented semantics.

## Comparison fairness requirements

- Match effective sample budgets when comparing algorithms.
- Document burn-in, thinning stride, and chain-count aggregation.
- Keep diagnostic formulas fixed across compared methods.
- Distinguish algorithmic variants from execution variants when interpreting diagnostic differences.

## Solute-transport note

High-dimensional observable summaries used historically in solute-transport experiments are a valid instance of this general policy, not a special-case policy limited to one algorithm family.
