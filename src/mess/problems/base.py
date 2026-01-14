# GaussianPriorProblem

# problems/base.py
import numpy as np

class GaussianPriorProblem:
    def __init__(self, mu, cov):
        self.mu = mu
        self.dim = len(mu)
        self.L = np.linalg.cholesky(cov)

    def sample_prior(self, rng):
        z = rng.standard_normal(self.dim)
        return self.mu + self.L @ z

    def prior_mean(self):
        return self.mu
