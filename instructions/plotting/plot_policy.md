# Plotting Policy

## General
- Use the spelling "mpCN" (not "mPCN") in titles and legends.
- Use LaTeX for symbols and indices: $\rho$, $x_1$, $x_2$.
- Prefer a single shared legend for multi-panel figures.
- Place legends outside the plotting area to avoid covering curves.
- For proposal-count color maps in observable grids, map colors per plot so the
  largest P in that plot is the lightest Viridis color.
- For independent pCN aggregates, use a distinct linestyle (for example, dotted for mean and
	dashed for max) and label them explicitly as "pCN indep".
- For norms in LaTeX titles/labels, use a single bar like $|A|$ (avoid double bars).
- In raw Python strings for LaTeX, use a single backslash (for example, r"$\varphi$", not r"$\\varphi$").

## ESS/MSJD Curves
- For dimension-sweep ESS/MSJD figures, use a two-panel layout: ESS (left) and MSJD (right), shared x-axis (`d`).
- Use the following style mapping in the current preferred implementation:
  - MESS: marker `o`, one curve per `M`, colors from the MESS colormap.
  - MH: marker `s`, dashed black line.
  - pCN: marker `D`, dotted red line.
  - mpCN: marker `^`, one curve per `P`, colors from the mpCN colormap.
- Generate both linear-scale and log-scale versions when reporting ESS/MSJD-vs-d summaries.
- Keep a single shared legend at figure level, centered above panels.

## Titles and Labels
- For per-parameter grids, use subplot titles as $x_1$ and $x_2$ only.
- Avoid redundant subplot titles when axis labels already indicate the metric.
- Keep figure-level titles short and consistent across notebooks.
- For ESS/MSJD dimension sweeps, use concise titles in the form `ESS vs dimension (...)` and `MSJD vs dimension (...)`.

## Trace Plots
- Use a fixed window of 30,000 iterations after burn-in for comparability.
- Use a horizontal shared legend above the subplot grid.

## MESS Ellipse Playback Plots
- Ellipse diagnostics for MESS must use full historical playback traces captured during the original chain run.
- Do not use approximate local replay for publication or parity diagnostics when exact historical playback is requested.
- Trace capture is controlled by experiment config and should target specific iterations to keep storage bounded.
- Historical playback outputs support two figure families:
  - contiguous-iteration ellipse overlays
  - interval-level panels with proposals, valid proposals, and accepted state
- Slice sections on the ellipse must be rendered in green.
- Interval arcs should use a distinct light-blue family, with interval boundary brackets visible.
- Nonvalid proposals should use red markers; valid proposals should use dark-green markers; accepted proposal should be a hollow square.
- Figure naming should include algorithm settings and iteration anchors (for example `mess_M50_iter200000_intervals.png`).
- Legends should remain outside dense panels whenever possible.
