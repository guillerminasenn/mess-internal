# Experiment specification: narrowband wave-source localization

Date: 2026-07-21  
Status: implementation specification  
Proposed dataset/experiment ID: `narrowband_source_localization`

## 1. Context and scientific purpose

This experiment is part of the numerical assessment of Multiproposal Elliptical Slice Sampling (MESS). The existing experiments compare:

- MESS with (M) parallel proposals;
- ordinary Elliptical Slice Sampling (ESS), which is MESS with (M=1);
- MPCN((P)); and
- embarrassingly parallel ESS (EP-ESS), consisting of (M) independent ESS chains whose post-burn samples are pooled.

The polar-twist experiment indicates that (M=2) can reduce the number of interval-shrinking rounds and can improve some likelihood-evaluation-normalized metrics, but larger (M) has not produced a decisive improvement over EP-ESS. The next experiment must test a more specific mechanism:

> Can several proposals evaluated on the same ESS ellipse discover remote, disconnected valid slice components, and can distance-informed MESS turn those discoveries into physically large moves often enough to improve global exploration relative to both ESS and EP-ESS?

The target below is a real nonlinear inverse problem rather than a sign-symmetric mathematical construction. A narrowband wave contains phase only modulo (2\pi). With sparse sensors, distinct source locations can produce nearly the same relative sensor phases. These spatial aliases or grating lobes give several physically plausible source locations. A nonzero or shifted Gaussian prior can reweight these aliases but does not create them and does not remove the ambiguity unless the prior is made sufficiently informative to overwhelm the data.

The experiment is intended to test a plausible favorable case for MESS. It is not required to show that MESS beats EP-ESS. A negative result is scientifically useful if the geometry confirms that remote valid slice components exist but their total angular measure is too small, or if the gain from selecting remote proposals does not overcome EP-ESS's (M)-sample advantage.

Primary references: (do not try to read or parse)

- MESS: <https://arxiv.org/abs/2602.22358>
- Narrowband near-field phase model and ambiguity function: <https://arxiv.org/abs/2505.10053>
- Acoustic-array grating lobes and their dependence on spacing and frequency: <https://pmc.ncbi.nlm.nih.gov/articles/PMC3950370/>
- Multiproposal efficiency bounds and comparisons: <https://arxiv.org/abs/2410.23174>

## 2. Required implementation strategy

Implement the inverse problem as a new target/model module and add experiment workflows around the existing samplers. The model API must expose at least:

- prior sampling;
- transformation between whitened and physical coordinates;
- log likelihood and, when needed, log posterior;
- deterministic data generation from a stored seed;
- batched likelihood evaluation for MESS proposals;
- reference-grid evaluation in two dimensions; and
- metadata serialization sufficient to reproduce every dataset.

The MCMC state is the two-dimensional whitened source location only. Unknown complex source amplitude and emission phase are nuisance variables and must be integrated out analytically. Do not sample them in the baseline experiment.

## 3. Unknown and Gaussian prior

Let (q\in\mathbb R^2) be the physical source location. Use

\[
q = \mu_q + L_q z, \qquad z\sim N_2(0,I_2),
\]

where (L_qL_q^\top=C_q). The samplers operate on (z), so that the Gaussian reference measure is standard normal. The physical location is recovered deterministically from (z).

On an ESS or MESS update, draw (\nu\sim N_2(0,I_2)) and use the ellipse

\[
z(\theta)=z\cos\theta+\nu\sin\theta,
\qquad
q(\theta)=\mu_q+L_qz(\theta).
\]

This centered parameterization avoids incorrect handling of a nonzero prior mean.

## 4. Narrowband forward model

Let (s_j\in\mathbb R^2), (j=1,\ldots,J), be known sensor locations. For source location (q), define

\[
r_j(q)=\lVert q-s_j\rVert_2,
\qquad
k_\ell=\frac{2\pi f_\ell}{c},
\]

where (f_\ell) is frequency and (c) is propagation speed. The complex steering vector at frequency (f_\ell) is

\[
h_\ell(q)
=
\begin{bmatrix}
a_1(q)e^{-\mathrm i k_\ell r_1(q)} & \cdots &
a_J(q)e^{-\mathrm i k_\ell r_J(q)}
\end{bmatrix}^{\!\top}
\in\mathbb C^J.
\]

The baseline uses calibrated phase-only measurements,

\[
a_j(q)=1.
\]

This represents data for which sensor gains and gross propagation loss have been normalized. Add the following sensitivity model without making it the default:

\[
a_j(q)=\frac{1}{\max\{r_j(q),r_{\min}\}^{\gamma}},
\qquad \gamma\in\{1/2,1\}.
\]

The positive floor (r_{\min}) prevents a numerical singularity if a proposed location approaches a sensor.

At each frequency, the observed complex sensor vector satisfies

\[
y_\ell=\alpha_\ell h_\ell(q)+\varepsilon_\ell,
\]

with

\[
\alpha_\ell\sim\mathcal{CN}(0,\tau_\ell^2),
\qquad
\varepsilon_\ell\sim\mathcal{CN}(0,\sigma_\ell^2I_J),
\]

independently across frequencies. The scalar (\alpha_\ell) absorbs unknown source strength and absolute emission phase. This is essential: the localization ambiguity must come from relative propagation phases, not from assuming that the absolute phase emitted by a passive source is known.

Use the proper complex-normal convention

\[
p(w)=\frac{1}{\pi^J\det K}
\exp\!\left(-w^*K^{-1}w\right),
\qquad w\sim\mathcal{CN}(0,K).
\]

## 5. Marginal likelihood after eliminating source amplitude and phase

Integrating out (\alpha_\ell) gives

\[
y_\ell\mid q
\sim
\mathcal{CN}\!\left(0,K_\ell(q)\right),
\qquad
K_\ell(q)
=
\sigma_\ell^2I_J
+\tau_\ell^2h_\ell(q)h_\ell(q)^*.
\]

Therefore, up to a constant independent of (q),

\[
\log L(q)
=
-\sum_{\ell=1}^{F}
\left\{
\log\det K_\ell(q)
+y_\ell^*K_\ell(q)^{-1}y_\ell
\right\}.
\]

Do not form or invert the (J\times J) matrices in the baseline implementation. Let

\[
s_\ell(q)=h_\ell(q)^*h_\ell(q).
\]

The matrix determinant lemma and Sherman--Morrison formula give

\[
\log\det K_\ell(q)
=
J\log\sigma_\ell^2
+\log\!\left(
1+\frac{\tau_\ell^2}{\sigma_\ell^2}s_\ell(q)
\right),
\]

and

\[
y_\ell^*K_\ell(q)^{-1}y_\ell
=
\frac{\lVert y_\ell\rVert_2^2}{\sigma_\ell^2}
-
\frac{
\tau_\ell^2\left|h_\ell(q)^*y_\ell\right|^2
}{
\sigma_\ell^2
\left(\sigma_\ell^2+\tau_\ell^2s_\ell(q)\right)
}.
\]

For the phase-only model, (s_\ell(q)=J), so the log-determinant is constant. The location-dependent likelihood is then proportional to a sensor-coherence score,

\[
\log L(q)
=
\mathrm{constant}
+
\sum_{\ell=1}^{F}
\frac{
\tau_\ell^2\left|h_\ell(q)^*y_\ell\right|^2
}{
\sigma_\ell^2
\left(\sigma_\ell^2+J\tau_\ell^2\right)
}.
\]

Implement the general marginal expression and test that it reduces numerically to this phase-only expression.

The posterior sampled by MESS/ESS is

\[
\pi(z\mid y)
\propto
\exp\!\left(-\frac12z^\top z\right)
L(\mu_q+L_qz).
\]

## 6. Why this likelihood can create remote valid slice components

At one frequency, relative sensor phases depend on path-length differences modulo the wavelength (\lambda=c/f):

\[
k\bigl(r_j(q)-r_{j'}(q)\bigr)
\equiv
k\bigl(r_j(q')-r_{j'}(q')\bigr)
\pmod{2\pi}.
\]

Equivalently, different locations can satisfy

\[
\bigl(r_j(q)-r_{j'}(q)\bigr)
-
\bigl(r_j(q')-r_{j'}(q')\bigr)
\approx m_{jj'}\lambda,
\qquad m_{jj'}\in\mathbb Z.
\]

Sparse arrays and sensor separations larger than (\lambda/2) can therefore produce spatial aliases. On an ESS ellipse, define the random angular slice

\[
S(z,\nu,u)
=
\left\{
\theta\in[0,2\pi):
\log L(q(\theta))
\ge
\log L(q)+\log u
\right\},
\qquad u\sim\mathrm{Uniform}(0,1).
\]

The desired geometry is that (S) has a component containing (0) and one or more separated components whose physical locations (q(\theta)) are far from the current source location. MESS receives several chances to discover these components before bracket shrinking deletes them. When several valid candidates are present, the existing Euclidean-informed transition can favor a large physical displacement.

Multimodality alone is not sufficient. The implementation must measure the angular slice geometry directly.

## 7. Baseline data configuration

Use SI units and store all values in the dataset manifest.

```yaml
model: marginalized_complex_amplitude
dimension: 2
propagation_speed: 343.0
frequencies_hz: [1200.0]
sensors_m:
  - [-1.4, -1.2]
  - [ 1.5, -1.0]
  - [-1.1,  1.4]
  - [ 1.3,  1.2]
true_source_m: [0.35, 0.55]
prior_mean_m: [0.0, 0.0]
prior_sd_m: [1.2, 1.2]
amplitude_model: phase_only
tau: [1.0]
sigma: [0.10]
data_seed: 20260721
reference_box_m: [-4.0, 4.0, -4.0, 4.0]
reference_grid_size: 1601
```

Generate (\alpha_\ell) and (\varepsilon_\ell) once from the stated seed and store them with the observations. Do not regenerate data separately for different samplers or values of (M).

The proposed configuration is a starting point, not a guarantee of suitable geometry. Before running the sampler comparison, perform a deterministic geometry-only pilot over

\[
f\in\{600,900,1200\}\ \mathrm{Hz},
\qquad
\sigma\in\{0.05,0.10,0.20\}.
\]

Choose and freeze one primary configuration using only the reference posterior and slice-geometry criteria below. Do not use MESS, ESS, EP-ESS, ESS values, MSJD values, or runtime to select the configuration. Record all pilot configurations and the selection rule to prevent sampler-dependent tuning.

Prefer a configuration satisfying all of the following:

1. At least four separated posterior basins lie inside the reference box.
2. At least three basins have posterior mass above (2\%).
3. The largest basin has posterior mass below (70\%).
4. The median distance between the dominant basin centers exceeds (0.5) prior standard deviations.
5. In a prior-predictive sample of at least 500 ellipses started from reference-posterior draws, at least (10\%) of slices have a remote valid component separated from the zero component.

If no configuration meets all criteria, report that fact and choose the configuration maximizing the fraction in item 5 subject to items 1--3. This choice is still made without examining sampler performance.

## 8. Required ablations

Implement these model ablations:

1. **Frequency / wavelength:** use the registered primary frequency and at least one lower frequency.
2. **Noise / sharpness:** use the registered (\sigma), one larger value, and one smaller value when the reference grid can still resolve the modes.
3. **Number of frequencies:** compare one frequency with two noncommensurate frequencies. Use a second frequency such as (f_2=1.37f_1). The second frequency should reduce phase ambiguity and acts as a negative control.
4. **Amplitude model:** compare `phase_only` with spherical spreading after the primary experiment.
5. **Prior mean:** shift (\mu_q) moderately while keeping (C_q) fixed. Verify that likelihood aliases persist although posterior weights change.

The primary claims must use the preregistered single-frequency phase-only setting. Ablations explain the mechanism and must not replace an unfavorable primary result.

## 9. Sampler comparison

Use the same (M) grid as the existing EP experiment unless repository-wide settings require a shared alternative:

\[
M\in\{1,2,5,10,20,50\}.
\]

For each (M) and replicate (b=1,\ldots,B):

- run one MESS((M)) chain;
- run one EP-ESS replicate containing (M) independent ESS chains;
- retain the existing start-point contract in which the first EP chain shares its start with the corresponding MESS chain; and
- run MPCN((P)) under the repository's existing (P\)-to-(M) comparison convention.

Default run settings:

```yaml
B: 20
n_iters: 20000
burn_in: 1000
M: [1, 2, 5, 10, 20, 50]
transition_variants:
  - uniform
  - euclidean_informed
```

Add these diagnostic transition ablations when the existing transition API permits them without changing the invariance contract:

- prior-whitened distance in (z)-space;
- physical Euclidean distance in (q)-space;
- symmetrized informed matrix (P_{\mathrm{sym}}=(P+P^\top)/2).

Do not introduce a hand-designed cyclic transition in this experiment. The purpose is to test the existing informed MESS mechanism.

## 10. Fair-comparison and cost rules

Retain the EP aggregation contract used by `polar_twist_ep`:

- EP raw ESS for a scalar observable is the sum of ESS values across its (M) independent chains.
- MESS raw ESS is the ESS of its single chain.
- EP likelihood energy is the sum of likelihood evaluations over all (M) chains.
- MESS likelihood energy is (M) times its number of parallel interval rounds when every round evaluates (M) proposals.
- Report ideal parallel likelihood steps and measured wall-clock time separately.

Also report LP construction/solve time separately from likelihood time. This likelihood is intentionally cheap, so total runtime can be dominated by informed-transition overhead. Likelihood-evaluation counts are a hardware-neutral work proxy, not a literal measurement of electrical energy.

Do not claim that one method produces more "independent samples" solely from a single component-wise ESS number.

## 11. Reference posterior and mode partition

Because the sampled unknown is two-dimensional, construct a numerical reference posterior on a dense grid over the registered box.

1. Evaluate log prior, log likelihood, and log posterior.
2. Normalize with log-sum-exp including the grid-cell area.
3. Verify that omitted posterior mass outside the box is negligible using a larger, coarser grid and prior-tail bounds.
4. Identify local maxima and modal basins using a deterministic watershed or steepest-ascent assignment.
5. Merge numerically duplicated maxima using fixed distance and saddle-height criteria.
6. Store basin labels, basin masses, centers, and adjacency/saddle information.

The basin definition and merge thresholds must be frozen before examining sampler comparisons. Validate grid results by repeating at higher resolution for the registered primary configuration.

Reference expectations must include:

\[
\mathbb E_\pi[q_1],\quad
\mathbb E_\pi[q_2],\quad
\mathbb E_\pi[q_1^2],\quad
\mathbb E_\pi[q_2^2],\quad
\mathbb E_\pi[\log L(q)],
\]

and every modal-basin probability (\pi(B_k)) above a registered minimum mass.

## 12. Metrics

### 12.1 Local and observable-specific metrics

Compute ESS and integrated autocorrelation diagnostics for:

- (q_1,q_2);
- (q_1^2,q_2^2);
- radius and polar angle relative to the prior mean;
- log likelihood;
- selected posterior-predictive complex phases; and
- every modal-basin indicator (1\{q\in B_k\}) with non-negligible reference mass.

Compute MSJD in both physical and whitened coordinates:

\[
\operatorname{MSJD}_{q}
=
\frac1{T-1}\sum_{t=1}^{T-1}
\lVert q_{t+1}-q_t\rVert_2^2,
\]

\[
\operatorname{MSJD}_{z}
=
\frac1{T-1}\sum_{t=1}^{T-1}
\lVert z_{t+1}-z_t\rVert_2^2.
\]

### 12.2 Global exploration metrics

ESS can be misleading when a chain remains inside one mode. The primary global metrics are:

- replicate MSE of posterior expectations against the reference grid;
- total-variation error in the vector of modal occupation probabilities;
- number of distinct basins visited;
- inter-basin transition count;
- first-passage time from the starting basin to any other major basin;
- round-trip times between registered distant basins;
- maximum duration trapped in one basin; and
- between-chain rank-normalized (\widehat R) and bulk/tail ESS where applicable.

For EP-ESS, compute each replicate's modal occupation from all (M) pooled chains. Preserve chain identities when calculating within-chain transitions and first-passage times.

### 12.3 Estimator-level comparison with EP-ESS

For every reference-known observable (g), compute the replicate estimator

\[
\widehat\mu_g^{(b)}
=
\frac1{N_b}\sum_{i=1}^{N_b}g(q_i^{(b)})
\]

and the empirical MSE across replicates,

\[
\operatorname{MSE}(g)
=
\frac1B\sum_{b=1}^{B}
\left(\widehat\mu_g^{(b)}-\mathbb E_\pi[g]\right)^2.
\]

Report raw, per ideal parallel likelihood step, per total likelihood evaluation, and per measured wall-clock second. This is the most direct comparison of MESS's one-state-per-iteration estimator with EP-ESS's pooled estimator.

## 13. Slice-geometry instrumentation

For a registered diagnostic subset of iterations and replicates, evaluate the likelihood on a dense angular grid before any shrinking. This instrumentation must not affect the chain.

For each diagnostic ellipse and slice threshold, store:

- number of connected angular slice components;
- angular width of every component;
- width of the component containing (0);
- total angular measure outside the zero component;
- maximum physical and whitened displacement attainable in each component;
- whether remote components correspond to different reference-posterior basins;
- whether a remote component is removed by the first rejected batch;
- whether a terminal MESS batch contains both local and remote valid proposals;
- which candidate is selected under uniform and informed transitions; and
- selected angular, whitened, and physical jump distances.

Use circular connected-component logic so components crossing (0=2\pi) are not split incorrectly.

The main mechanism plots must show:

1. probability of discovering a remote component before the first shrink versus (M);
2. probability that the terminal batch contains candidates from multiple posterior basins versus (M);
3. probability of selecting a different basin conditional on such a batch, by transition variant;
4. distribution of remote-component angular measure;
5. inter-basin transition rate versus (M); and
6. MSE of modal occupation versus parallel work and total likelihood work.

## 14. Required plots and tables

Produce at least:

- sensor geometry, true source, and reference posterior contours;
- reference modal-basin map and basin masses;
- representative ESS ellipses over the posterior with valid angular segments identified;
- representative likelihood-versus-angle plots showing disconnected slices;
- trace plots colored by modal basin;
- mode-transition matrices for each sampler and (M);
- ESS/MSJD versus (M), with all existing normalizations;
- mode-occupation error and estimator MSE versus (M);
- first-passage and round-trip summaries;
- slice-geometry mechanism plots from Section 13; and
- a runtime table separating likelihood, transition-matrix, synchronization, and total time.

Every result table must carry the dataset hash, data seed, start seed, sampler seed, (M), transition variant, iteration count, burn-in, and code version.

## 15. Tests

Add unit and integration tests covering all of the following:

1. Whitened-to-physical and physical-to-whitened transformations are inverses.
2. (h_\ell(q)) has the expected shape and unit modulus in phase-only mode.
3. The general complex-normal marginal log likelihood agrees with direct dense linear algebra.
4. The Sherman--Morrison implementation agrees with the dense calculation over random locations.
5. The phase-only simplified expression differs from the general expression only by a location-independent constant.
6. Batched and scalar likelihood evaluations agree.
7. Likelihood evaluation is deterministic and does not mutate state.
8. Data generation is exactly reproducible from the manifest and seed.
9. Changing the prior mean does not change the likelihood surface.
10. Adding a well-separated second frequency reduces the registered ambiguity statistic in the negative-control dataset.
11. Circular angular-component detection handles a component crossing (0=2\pi).
12. Reference-grid probabilities sum to one within numerical tolerance.
13. The (M=1) MESS branch agrees with the repository's ESS contract.
14. EP aggregation and likelihood-cost normalization agree with the existing `polar_twist_ep` implementation.
15. Diagnostic angular-grid evaluation leaves sampler trajectories unchanged for fixed seeds.

## 16. Interpretation rules

The strongest supported claim depends on the results:

- If MESS improves remote-component discovery and inter-basin movement over ESS but not estimator MSE over EP-ESS, conclude that MESS improves a single trajectory's global exploration but does not overcome independent replication at the tested costs.
- If MESS improves finite-time modal-occupation MSE over EP-ESS, identify whether the gain comes from faster initial escape, informed remote selection, or stationary transition behavior.
- If symmetrizing the informed transition removes the gain, report evidence that nonreversible tie resolution or circulation contributed; do not infer this from nonsymmetry alone.
- If full Euclidean and prior-whitened distances differ, attribute the change to the chosen geometry of the informed transition.
- If component-wise ESS improves while modal-occupation error does not, do not describe the method as globally better mixed.
- If larger (M) discovers remote components more often but still loses to EP-ESS, report the one-sample-per-iteration limitation directly.

## 17. Completion criteria

The task is complete only when:

1. the model, marginal likelihood, deterministic dataset, and reference posterior are implemented and tested;
2. the primary configuration is selected without sampler-dependent tuning and recorded in a manifest;
3. MESS, ESS, MPCN, and EP-ESS run through the existing workflow;
4. local, global, and estimator-level metrics are produced;
5. slice geometry is measured directly rather than inferred from posterior multimodality;
6. all cost normalizations and measured runtime are reported;
7. the two-frequency ambiguity-resolving negative control is included; and
8. conclusions distinguish single-chain exploration, stationary efficiency, finite-time convergence, total likelihood work, and wall-clock performance.
