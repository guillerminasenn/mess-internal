# README_context.md

# mess: Multiproposal Elliptical Slice Sampling

This repository implements **Elliptical Slice Sampling (ESS)** and its
generalization **MESS** for Bayesian inference with **Gaussian priors**
and non-Gaussian likelihoods.

The code accompanies a research paper and prioritizes:
- clarity over generality
- minimal abstractions
- faithful reproduction of reference examples
- fast experimentation

---

## Key Concepts

### ESS and MESS

- ESS corresponds to **MESS with M = 1**
- MESS uses **M proposals per iteration**
- All algorithms require:
  - sampling from a Gaussian prior
  - evaluation of the log-likelihood

---

## Design Principles

1. **Algorithms are model-agnostic**
   - ESS and MESS only require:
     - a method to sample from a Gaussian prior
     - a method to evaluate the log-likelihood

2. **Each problem constructs its own prior**
   - Mean and covariance depend on the model
   - Prior construction logic lives inside the problem class

3. **Gaussian priors only**
   - All problems inherit from `GaussianPriorProblem`
   - Gaussian sampling is done via Cholesky decomposition

4. **No geometry abstraction**
   - All problems live in Euclidean space
   - FFT / cyclic methods are intentionally excluded

---

## Repository Structure

### `src/mess/algorithms/`

Sampling algorithms only.

- `ess.py`
  - Standard ESS (M = 1)
- `mess.py`
  - Multiple-proposal ESS (M ≥ 1)
- `utils.py`
  - Angle sampling, bracket logic, helpers

---

### `src/mess/problems/`

Probabilistic models.

All problems:
- inherit from `GaussianPriorProblem`
- construct their own Gaussian prior
- implement `log_likelihood(x)`

Included problems:
- `gp_regression.py`
  - Gaussian process regression (Murray et al., Example 1)
- `logistic_regression.py`
  - Bayesian logistic regression (Example 2)
- `sbd.py`
  - Semi-blind deconvolution (Euclidean domain)

---

### `src/mess/kernels/`

Stationary covariance kernels.

- `stationary.py`
  - RBF kernel (p = 2)
  - Exponential kernel (p = 1)

Used by GP-style priors.

---

### `src/mess/data/`

Synthetic data generation only.

- Separate from inference
- Used to reproduce experiments and figures

---

### `examples/`

Runnable scripts demonstrating:
- data generation
- ESS/MESS usage
- diagnostics

---

## Typical Usage

```python
from mess.data.gp_regression import generate_data
from mess.problems.gp_regression import GaussianProcessRegression
from mess.algorithms.ess import ess_step

data = generate_data()
problem = GaussianProcessRegression(**data)

x = data["f_init"]
for _ in range(1000):
    x = ess_step(x, problem)
