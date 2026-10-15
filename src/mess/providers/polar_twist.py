"""Structural provider for the existing polar-twist inverse problem."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from mess.problems.base import GaussianPriorProblem
from mess.problems.polar_twist import PolarTwistToy, f_polar_twist


def _model_values(model: Mapping[str, object]) -> dict[str, Any]:
    required = ("alpha", "sigma_noise", "prior_mean", "prior_cov")
    missing = [name for name in required if name not in model]
    if missing:
        raise ValueError(f"Missing polar-twist model settings: {', '.join(missing)}")
    allowed = set(required) | {"weight_x", "weight_y"}
    unknown = set(model) - allowed
    if unknown:
        raise ValueError(f"Unknown polar-twist model settings: {sorted(map(str, unknown))}")
    values = dict(model)
    values.setdefault("weight_x", 1.0)
    values.setdefault("weight_y", 1.0)
    for name in ("alpha", "sigma_noise", "weight_x", "weight_y"):
        if isinstance(values[name], bool):
            raise ValueError(f"{name} must be a finite number")
        try:
            number = float(values[name])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a finite number") from exc
        if not np.isfinite(number):
            raise ValueError(f"{name} must be a finite number")
        values[name] = number
    if values["sigma_noise"] <= 0:
        raise ValueError("sigma_noise must be greater than zero")
    mean = np.asarray(values["prior_mean"], dtype=float)
    covariance = np.asarray(values["prior_cov"], dtype=float)
    if mean.shape != (2,) or covariance.shape != (2, 2):
        raise ValueError("prior_mean and prior_cov must have shapes (2,) and (2, 2)")
    if not np.isfinite(mean).all() or not np.isfinite(covariance).all():
        raise ValueError("prior_mean and prior_cov must contain finite values")
    if not np.allclose(covariance, covariance.T):
        raise ValueError("prior_cov must be symmetric")
    np.linalg.cholesky(covariance)
    values["prior_mean"] = mean
    values["prior_cov"] = covariance
    return values


class PolarTwistRuntime:
    """Expose existing Gaussian-prior operations plus the model's forward map."""

    def __init__(self, problem: PolarTwistToy):
        self._problem = problem

    @property
    def dim(self) -> int:
        return self._problem.dim

    @property
    def L(self) -> np.ndarray:
        return self._problem.L

    def log_posterior(self, parameters: np.ndarray) -> float:
        return self._problem.log_posterior(parameters)

    def log_prior(self, parameters: np.ndarray) -> float:
        return self._problem.log_prior(parameters)

    def log_likelihood(self, parameters: np.ndarray) -> float:
        return self._problem.log_likelihood(parameters)

    def prior_mean(self) -> np.ndarray:
        return self._problem.prior_mean()

    def sample_prior(self, rng: Any) -> np.ndarray:
        return self._problem.sample_prior(rng)

    def forward(self, parameters: np.ndarray) -> np.ndarray:
        return f_polar_twist(
            parameters,
            alpha=self._problem.alpha,
            weight_x=self._problem.weight_x,
            weight_y=self._problem.weight_y,
        )


class PolarTwistProvider:
    """Build the existing problem from resolved model and observed-data values."""

    def describe(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "problem_id": "polar_twist",
            "label": "Polar twist",
            "provider_version": "1.0",
            "parameters": [{
                "name": "x",
                "dims": ["parameter"],
                "shape": [2],
                "coordinates": {"parameter": ["x1", "x2"]},
            }],
            "observations": [{
                "name": "y_obs",
                "dims": ["observation"],
                "shape": [2],
                "coordinates": {"observation": ["y1", "y2"]},
            }],
            "capabilities": [
                "log_density", "log_prior", "log_likelihood", "sample_prior",
                "gaussian_prior", "forward",
            ],
            "model_schema": {
                "alpha": {"type": "number"},
                "sigma_noise": {"type": "number", "exclusiveMinimum": 0},
                "prior_mean": {"type": "array", "minItems": 2, "maxItems": 2},
                "prior_cov": {"type": "array", "shape": [2, 2]},
                "weight_x": {"type": "number", "default": 1.0},
                "weight_y": {"type": "number", "default": 1.0},
            },
            "data_schema": {
                "y_obs": {"type": "array", "minItems": 2, "maxItems": 2},
            },
        }

    def build(
        self, model: Mapping[str, object], data: Mapping[str, object],
    ) -> PolarTwistRuntime:
        values = _model_values(model)
        unknown_data = set(data) - {"y_obs"}
        if unknown_data:
            raise ValueError(f"Unknown polar-twist data fields: {sorted(map(str, unknown_data))}")
        if "y_obs" not in data:
            raise ValueError("Polar-twist data requires y_obs")
        observations = np.asarray(data["y_obs"], dtype=float)
        if observations.shape != (2,) or not np.isfinite(observations).all():
            raise ValueError("y_obs must contain two finite values")
        problem = PolarTwistToy(
            y_obs=observations,
            sigma_noise=float(values["sigma_noise"]),
            alpha=float(values["alpha"]),
            prior_mean=np.asarray(values["prior_mean"], dtype=float),
            prior_cov=np.asarray(values["prior_cov"], dtype=float),
            weight_x=float(values["weight_x"]),
            weight_y=float(values["weight_y"]),
        )
        return PolarTwistRuntime(problem)

    def simulate(self, model: Mapping[str, object], rng: Any) -> dict[str, np.ndarray]:
        values = _model_values(model)
        truth = rng.multivariate_normal(values["prior_mean"], values["prior_cov"])
        forward = f_polar_twist(
            truth,
            alpha=float(values["alpha"]),
            weight_x=float(values["weight_x"]),
            weight_y=float(values["weight_y"]),
        )
        observations = forward + rng.normal(0.0, float(values["sigma_noise"]), size=2)
        return {"x_true": truth, "theta_true": forward, "y_obs": observations}

    def sample_prior(self, model: Mapping[str, object], rng: Any) -> np.ndarray:
        values = _model_values(model)
        prior = GaussianPriorProblem(
            np.asarray(values["prior_mean"], dtype=float),
            np.asarray(values["prior_cov"], dtype=float),
        )
        return prior.sample_prior(rng)

    def prior_predictive(
        self, model: Mapping[str, object], rng: Any, samples: int,
    ) -> dict[str, np.ndarray]:
        if isinstance(samples, bool) or not isinstance(samples, int) or samples < 1:
            raise ValueError("samples must be a positive integer")
        values = _model_values(model)
        parameters = np.stack([self.sample_prior(model, rng) for _ in range(samples)])
        forward = np.stack([
            f_polar_twist(
                parameter,
                alpha=float(values["alpha"]),
                weight_x=float(values["weight_x"]),
                weight_y=float(values["weight_y"]),
            )
            for parameter in parameters
        ])
        observations = forward + rng.normal(
            0.0, float(values["sigma_noise"]), size=forward.shape
        )
        return {"parameters": parameters, "forward": forward, "observations": observations}

    def reference(
        self,
        model: Mapping[str, object],
        data: Mapping[str, object],
        config: Mapping[str, object],
    ) -> dict[str, object]:
        grid_size = config.get("grid_size", 201)
        if isinstance(grid_size, bool) or not isinstance(grid_size, int) or grid_size < 3:
            raise ValueError("grid_size must be an integer greater than or equal to 3")

        values = _model_values(model)
        mean = np.asarray(values["prior_mean"], dtype=float)
        covariance = np.asarray(values["prior_cov"], dtype=float)
        standard_deviation = np.sqrt(np.diag(covariance))
        bounds = config.get("bounds")
        if bounds is None:
            bounds = tuple(
                (float(center - 5.0 * scale), float(center + 5.0 * scale))
                for center, scale in zip(mean, standard_deviation)
            )
        if (
            not isinstance(bounds, (list, tuple)) or len(bounds) != 2
            or any(not isinstance(pair, (list, tuple)) or len(pair) != 2 for pair in bounds)
        ):
            raise ValueError("bounds must contain one (minimum, maximum) pair per parameter")
        limits = tuple((float(pair[0]), float(pair[1])) for pair in bounds)
        if any(not np.isfinite(low + high) or low >= high for low, high in limits):
            raise ValueError("Each reference bound must be finite and increasing")

        runtime = self.build(model, data)
        axes = tuple(np.linspace(low, high, grid_size) for low, high in limits)
        x1, x2 = np.meshgrid(*axes, indexing="ij")
        log_density = np.empty((grid_size, grid_size), dtype=float)
        for row in range(grid_size):
            for column in range(grid_size):
                log_density[row, column] = runtime.log_posterior(
                    np.array([x1[row, column], x2[row, column]])
                )
        weights = np.exp(log_density - np.max(log_density))
        cell_area = float((axes[0][1] - axes[0][0]) * (axes[1][1] - axes[1][0]))
        normalizer = float(weights.sum() * cell_area)
        density = weights / normalizer
        boundary_weights = (
            weights[0, :].sum() + weights[-1, :].sum()
            + weights[1:-1, 0].sum() + weights[1:-1, -1].sum()
        )
        return {
            "x1": axes[0],
            "x2": axes[1],
            "density": density,
            "accuracy": {
                "method": "finite-domain uniform grid",
                "grid_size": grid_size,
                "bounds": [list(pair) for pair in limits],
                "grid_spacing": [float(axis[1] - axis[0]) for axis in axes],
                "boundary_weight_fraction": float(boundary_weights / weights.sum()),
                "normalization": "trapezoid-free rectangular grid sum",
            },
        }


provider = PolarTwistProvider()