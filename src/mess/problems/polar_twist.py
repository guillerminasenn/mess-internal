"""Polar-twist 2D toy inverse problem with Gaussian prior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np

from .base import GaussianPriorProblem


def f_polar_twist(x: np.ndarray, alpha: float, weight_x: float = 1.0, weight_y: float = 1.0) -> np.ndarray:
    """Compute the polar-twist forward map f(x)."""
    x = np.asarray(x, dtype=float)
    if x.shape != (2,):
        raise ValueError(f"x must have shape (2,), got {x.shape}")

    x1, x2 = x
    radius = float(np.sqrt(x1**2 + x2**2))
    comp1 = x1 * np.cos(alpha * weight_x * radius) - x2 * np.sin(alpha * weight_y * radius)
    comp2 = x1 * np.sin(alpha * weight_x * radius) + x2 * np.cos(alpha * weight_y * radius)
    return np.array([comp1, comp2], dtype=float)


def log_likelihood_polar_twist(
    x: np.ndarray,
    y_obs: np.ndarray,
    sigma_noise: float,
    alpha: float,
    weight_x: float = 1.0,
    weight_y: float = 1.0,
) -> float:
    """Unnormalized Gaussian log-likelihood for the polar-twist map."""
    y_obs = np.asarray(y_obs, dtype=float)
    if y_obs.shape != (2,):
        raise ValueError(f"y_obs must have shape (2,), got {y_obs.shape}")
    if sigma_noise <= 0:
        raise ValueError("sigma_noise must be > 0")

    residual = f_polar_twist(x, alpha=alpha, weight_x=weight_x, weight_y=weight_y) - y_obs
    return float(-0.5 * np.dot(residual, residual) / (sigma_noise**2))


@dataclass(frozen=True)
class PolarTwistData:
    """Deterministic synthetic data bundle for the polar-twist toy model."""

    x_true: np.ndarray
    theta_true: np.ndarray
    y_obs: np.ndarray
    config: Dict[str, Any]


def generate_polar_twist_data(
    *,
    alpha: float,
    sigma_noise: float,
    prior_mean: np.ndarray,
    prior_cov: np.ndarray,
    weight_x: float = 1.0,
    weight_y: float = 1.0,
    data_seed: int = 202,
) -> PolarTwistData:
    """Generate synthetic (x_true, y_obs) with deterministic RNG seed."""
    prior_mean = np.asarray(prior_mean, dtype=float)
    prior_cov = np.asarray(prior_cov, dtype=float)

    if prior_mean.shape != (2,):
        raise ValueError(f"prior_mean must have shape (2,), got {prior_mean.shape}")
    if prior_cov.shape != (2, 2):
        raise ValueError(f"prior_cov must have shape (2, 2), got {prior_cov.shape}")
    if sigma_noise <= 0:
        raise ValueError("sigma_noise must be > 0")

    rng = np.random.default_rng(int(data_seed))
    x_true = rng.multivariate_normal(prior_mean, prior_cov)
    theta_true = f_polar_twist(x_true, alpha=alpha, weight_x=weight_x, weight_y=weight_y)
    y_obs = theta_true + rng.normal(0.0, sigma_noise, size=theta_true.shape)

    cfg = {
        "model": "polar_twist",
        "alpha": float(alpha),
        "weight_x": float(weight_x),
        "weight_y": float(weight_y),
        "sigma_noise": float(sigma_noise),
        "prior_cov": prior_cov.tolist(),
        "prior_mean": prior_mean.tolist(),
        "data_seed": int(data_seed),
    }
    return PolarTwistData(
        x_true=np.asarray(x_true, dtype=float),
        theta_true=np.asarray(theta_true, dtype=float),
        y_obs=np.asarray(y_obs, dtype=float),
        config=cfg,
    )


class PolarTwistToy(GaussianPriorProblem):
    """2D Gaussian-prior problem with polar-twist likelihood."""

    def __init__(
        self,
        *,
        y_obs: np.ndarray,
        sigma_noise: float,
        alpha: float,
        prior_mean: np.ndarray,
        prior_cov: np.ndarray,
        weight_x: float = 1.0,
        weight_y: float = 1.0,
    ):
        prior_mean = np.asarray(prior_mean, dtype=float)
        prior_cov = np.asarray(prior_cov, dtype=float)
        y_obs = np.asarray(y_obs, dtype=float)

        if prior_mean.shape != (2,):
            raise ValueError(f"prior_mean must have shape (2,), got {prior_mean.shape}")
        if prior_cov.shape != (2, 2):
            raise ValueError(f"prior_cov must have shape (2, 2), got {prior_cov.shape}")
        if y_obs.shape != (2,):
            raise ValueError(f"y_obs must have shape (2,), got {y_obs.shape}")
        if sigma_noise <= 0:
            raise ValueError("sigma_noise must be > 0")

        self.y_obs = y_obs
        self.sigma_noise = float(sigma_noise)
        self.alpha = float(alpha)
        self.weight_x = float(weight_x)
        self.weight_y = float(weight_y)

        super().__init__(prior_mean, prior_cov)

    def log_likelihood(self, x: np.ndarray) -> float:
        return log_likelihood_polar_twist(
            x,
            y_obs=self.y_obs,
            sigma_noise=self.sigma_noise,
            alpha=self.alpha,
            weight_x=self.weight_x,
            weight_y=self.weight_y,
        )


def build_polar_twist_problem(
    *,
    alpha: float,
    sigma_noise: float,
    prior_mean: np.ndarray,
    prior_cov: np.ndarray,
    weight_x: float = 1.0,
    weight_y: float = 1.0,
    data_seed: int = 202,
) -> tuple[PolarTwistToy, PolarTwistData]:
    """Build deterministic synthetic data and the corresponding problem object."""
    data = generate_polar_twist_data(
        alpha=alpha,
        sigma_noise=sigma_noise,
        prior_mean=prior_mean,
        prior_cov=prior_cov,
        weight_x=weight_x,
        weight_y=weight_y,
        data_seed=data_seed,
    )
    problem = PolarTwistToy(
        y_obs=data.y_obs,
        sigma_noise=sigma_noise,
        alpha=alpha,
        prior_mean=prior_mean,
        prior_cov=prior_cov,
        weight_x=weight_x,
        weight_y=weight_y,
    )
    return problem, data
