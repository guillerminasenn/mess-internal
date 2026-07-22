"""Narrowband wave-source localization with marginalized complex amplitude."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple

import numpy as np

from .base import GaussianPriorProblem


def _complex_normal_scalar(rng: np.random.Generator, variance: float) -> complex:
    """Sample CN(0, variance) using the proper circular complex normal scaling."""
    if variance < 0.0:
        raise ValueError("variance must be nonnegative")
    if variance == 0.0:
        return 0.0 + 0.0j
    return np.sqrt(variance / 2.0) * (rng.standard_normal() + 1j * rng.standard_normal())


def _complex_normal_vector(rng: np.random.Generator, variance: float, size: int) -> np.ndarray:
    """Sample a vector from CN(0, variance * I)."""
    if variance < 0.0:
        raise ValueError("variance must be nonnegative")
    if size < 1:
        raise ValueError("size must be >= 1")
    if variance == 0.0:
        return np.zeros((size,), dtype=np.complex128)
    scale = np.sqrt(variance / 2.0)
    return scale * (rng.standard_normal(size) + 1j * rng.standard_normal(size))


def _as_2d_points(arr: np.ndarray) -> np.ndarray:
    """Normalize input points to shape (N, 2)."""
    pts = np.asarray(arr, dtype=float)
    if pts.ndim == 1:
        if pts.shape[0] != 2:
            raise ValueError(f"point must have shape (2,), got {pts.shape}")
        return pts.reshape(1, 2)
    if pts.ndim == 2 and pts.shape[1] == 2:
        return pts
    if pts.ndim == 2 and pts.shape[0] == 2:
        return pts.T
    raise ValueError(f"points must have shape (2,), (N,2), or (2,N), got {pts.shape}")


@dataclass(frozen=True)
class NarrowbandSourceLocalizationData:
    """Deterministic synthetic data bundle for narrowband source localization."""

    q_true: np.ndarray
    frequencies_hz: np.ndarray
    sensors_m: np.ndarray
    propagation_speed: float
    tau: np.ndarray
    sigma: np.ndarray
    y_obs: np.ndarray
    alpha_draws: np.ndarray
    epsilon_draws: np.ndarray
    amplitude_model: str
    gamma: float
    r_min: float
    data_seed: int
    config: Dict[str, Any]


class NarrowbandSourceLocalizationProblem(GaussianPriorProblem):
    """Whitened 2D localization target with marginalized complex source amplitude."""

    def __init__(
        self,
        *,
        y_obs: np.ndarray,
        sensors_m: np.ndarray,
        frequencies_hz: Iterable[float],
        propagation_speed: float,
        tau: Iterable[float],
        sigma: Iterable[float],
        prior_mean_m: Iterable[float],
        prior_cov_m: np.ndarray,
        amplitude_model: str = "phase_only",
        gamma: float = 1.0,
        r_min: float = 0.05,
    ):
        self.sensors_m = np.asarray(sensors_m, dtype=float)
        if self.sensors_m.ndim != 2 or self.sensors_m.shape[1] != 2:
            raise ValueError("sensors_m must have shape (J, 2)")
        self.sensor_count = int(self.sensors_m.shape[0])
        if self.sensor_count < 2:
            raise ValueError("at least two sensors are required")

        self.frequencies_hz = np.asarray(list(frequencies_hz), dtype=float)
        self.tau = np.asarray(list(tau), dtype=float)
        self.sigma = np.asarray(list(sigma), dtype=float)
        if self.frequencies_hz.ndim != 1 or self.frequencies_hz.size < 1:
            raise ValueError("frequencies_hz must be a non-empty 1D array")
        f_count = int(self.frequencies_hz.size)
        if self.tau.shape != (f_count,) or self.sigma.shape != (f_count,):
            raise ValueError("tau and sigma must match frequencies_hz length")
        if np.any(self.frequencies_hz <= 0.0):
            raise ValueError("frequencies_hz must be strictly positive")
        if np.any(self.tau < 0.0):
            raise ValueError("tau entries must be nonnegative")
        if np.any(self.sigma <= 0.0):
            raise ValueError("sigma entries must be strictly positive")

        self.propagation_speed = float(propagation_speed)
        if self.propagation_speed <= 0.0:
            raise ValueError("propagation_speed must be > 0")

        self.k = 2.0 * np.pi * self.frequencies_hz / self.propagation_speed

        model = str(amplitude_model).strip().lower()
        if model not in {"phase_only", "spherical_spreading"}:
            raise ValueError("amplitude_model must be 'phase_only' or 'spherical_spreading'")
        self.amplitude_model = model
        self.gamma = float(gamma)
        if self.gamma <= 0.0:
            raise ValueError("gamma must be > 0")
        self.r_min = float(r_min)
        if self.r_min <= 0.0:
            raise ValueError("r_min must be > 0")

        self.y_obs = np.asarray(y_obs, dtype=np.complex128)
        if self.y_obs.shape != (f_count, self.sensor_count):
            raise ValueError(
                "y_obs must have shape (F, J) matching frequencies and sensors, "
                f"got {self.y_obs.shape}"
            )

        prior_mean = np.asarray(list(prior_mean_m), dtype=float)
        prior_cov = np.asarray(prior_cov_m, dtype=float)
        if prior_mean.shape != (2,):
            raise ValueError("prior_mean_m must have shape (2,)")
        if prior_cov.shape != (2, 2):
            raise ValueError("prior_cov_m must have shape (2, 2)")

        self.mu_q = prior_mean.copy()
        self.cov_q = prior_cov.copy()
        self.L_q = np.linalg.cholesky(self.cov_q)
        self.L_q_inv = np.linalg.inv(self.L_q)

        # The sampled state is z ~ N(0, I2).
        super().__init__(np.zeros(2, dtype=float), np.eye(2, dtype=float))

    def whitened_to_physical(self, z: np.ndarray) -> np.ndarray:
        """Map whitened coordinates z to physical source location q."""
        z_pts = _as_2d_points(z)
        q = self.mu_q[None, :] + z_pts @ self.L_q.T
        return q[0] if np.asarray(z).ndim == 1 else q

    def physical_to_whitened(self, q: np.ndarray) -> np.ndarray:
        """Map physical coordinates q to whitened coordinates z."""
        q_pts = _as_2d_points(q)
        centered = q_pts - self.mu_q[None, :]
        z = centered @ self.L_q_inv.T
        return z[0] if np.asarray(q).ndim == 1 else z

    def _sensor_ranges(self, q_pts: np.ndarray) -> np.ndarray:
        diff = q_pts[:, None, :] - self.sensors_m[None, :, :]
        return np.linalg.norm(diff, axis=2)

    def _amplitude(self, ranges: np.ndarray) -> np.ndarray:
        if self.amplitude_model == "phase_only":
            return np.ones_like(ranges)
        denom = np.maximum(ranges, self.r_min)
        return 1.0 / np.power(denom, self.gamma)

    def steering_matrix(self, q: np.ndarray) -> np.ndarray:
        """Return steering vectors for points q with shape (N, F, J)."""
        q_pts = _as_2d_points(q)
        ranges = self._sensor_ranges(q_pts)  # (N, J)
        amp = self._amplitude(ranges)  # (N, J)
        phase = np.exp(-1j * self.k[None, :, None] * ranges[:, None, :])  # (N, F, J)
        return amp[:, None, :] * phase

    def log_likelihood_physical(self, q: np.ndarray) -> float:
        """Unnormalized marginalized complex-normal log likelihood at physical q."""
        q_pt = _as_2d_points(q)
        if q_pt.shape[0] != 1:
            raise ValueError("log_likelihood_physical expects a single point")
        h = self.steering_matrix(q_pt)[0]  # (F, J)

        total = 0.0
        for ell in range(h.shape[0]):
            h_ell = h[ell]
            y_ell = self.y_obs[ell]
            sigma2 = float(self.sigma[ell] ** 2)
            tau2 = float(self.tau[ell] ** 2)

            s = float(np.vdot(h_ell, h_ell).real)
            hy = np.vdot(h_ell, y_ell)
            y_norm2 = float(np.vdot(y_ell, y_ell).real)

            logdet = self.sensor_count * np.log(sigma2) + np.log1p((tau2 / sigma2) * s)
            quad = y_norm2 / sigma2
            if tau2 > 0.0:
                quad -= (tau2 * (np.abs(hy) ** 2)) / (sigma2 * (sigma2 + tau2 * s))
            total += logdet + quad

        return float(-total)

    def log_likelihood(self, z: np.ndarray) -> float:
        q = self.whitened_to_physical(np.asarray(z, dtype=float))
        return self.log_likelihood_physical(q)

    def log_likelihood_batch(self, z_batch: np.ndarray) -> np.ndarray:
        """Evaluate log likelihood for a batch of whitened states."""
        z_pts = _as_2d_points(z_batch)
        q_pts = self.whitened_to_physical(z_pts)
        out = np.empty((q_pts.shape[0],), dtype=float)
        for i in range(q_pts.shape[0]):
            out[i] = self.log_likelihood_physical(q_pts[i])
        return out

    def log_likelihood_dense_physical(self, q: np.ndarray) -> float:
        """Dense linear-algebra implementation used for validation tests."""
        q_pt = _as_2d_points(q)
        if q_pt.shape[0] != 1:
            raise ValueError("log_likelihood_dense_physical expects a single point")
        h = self.steering_matrix(q_pt)[0]

        total = 0.0
        eye = np.eye(self.sensor_count, dtype=np.complex128)
        for ell in range(h.shape[0]):
            h_ell = h[ell][:, None]  # (J, 1)
            sigma2 = float(self.sigma[ell] ** 2)
            tau2 = float(self.tau[ell] ** 2)
            K = sigma2 * eye + tau2 * (h_ell @ h_ell.conj().T)
            y_ell = self.y_obs[ell]
            sign, logdet = np.linalg.slogdet(K)
            if sign <= 0:
                raise RuntimeError("Covariance matrix is not positive definite")
            quad = np.vdot(y_ell, np.linalg.solve(K, y_ell)).real
            total += logdet + quad
        return float(-total)

    def phase_only_reduced_log_likelihood_physical(self, q: np.ndarray) -> float:
        """Location-dependent phase-only score from the closed-form reduction."""
        if self.amplitude_model != "phase_only":
            raise ValueError("phase_only_reduced_log_likelihood_physical requires phase_only mode")

        q_pt = _as_2d_points(q)
        if q_pt.shape[0] != 1:
            raise ValueError("phase_only_reduced_log_likelihood_physical expects a single point")

        h = self.steering_matrix(q_pt)[0]
        total = 0.0
        j_float = float(self.sensor_count)
        for ell in range(h.shape[0]):
            h_ell = h[ell]
            y_ell = self.y_obs[ell]
            tau2 = float(self.tau[ell] ** 2)
            sigma2 = float(self.sigma[ell] ** 2)
            hy2 = float(np.abs(np.vdot(h_ell, y_ell)) ** 2)
            denom = sigma2 * (sigma2 + j_float * tau2)
            if denom > 0.0:
                total += tau2 * hy2 / denom
        return float(total)

    def reference_grid_evaluation(
        self,
        reference_box_m: Tuple[float, float, float, float],
        grid_size: int,
    ) -> Dict[str, np.ndarray]:
        """Evaluate log-prior, log-likelihood, and log-posterior on a 2D grid."""
        if grid_size < 5:
            raise ValueError("grid_size must be >= 5")
        xmin, xmax, ymin, ymax = [float(v) for v in reference_box_m]
        if not (xmax > xmin and ymax > ymin):
            raise ValueError("reference_box_m must satisfy xmax>xmin and ymax>ymin")

        q1 = np.linspace(xmin, xmax, grid_size)
        q2 = np.linspace(ymin, ymax, grid_size)
        xx, yy = np.meshgrid(q1, q2, indexing="xy")
        q_flat = np.column_stack([xx.ravel(), yy.ravel()])
        z_flat = self.physical_to_whitened(q_flat)

        lp = -0.5 * np.sum(z_flat * z_flat, axis=1)
        ll = np.empty((q_flat.shape[0],), dtype=float)
        for i in range(q_flat.shape[0]):
            ll[i] = self.log_likelihood_physical(q_flat[i])
        post = lp + ll

        return {
            "q1": q1,
            "q2": q2,
            "Q1": xx,
            "Q2": yy,
            "log_prior": lp.reshape(grid_size, grid_size),
            "log_likelihood": ll.reshape(grid_size, grid_size),
            "log_posterior": post.reshape(grid_size, grid_size),
            "dx": np.array([(xmax - xmin) / (grid_size - 1)], dtype=float),
            "dy": np.array([(ymax - ymin) / (grid_size - 1)], dtype=float),
        }


def generate_narrowband_source_localization_data(
    *,
    sensors_m: np.ndarray,
    frequencies_hz: Iterable[float],
    propagation_speed: float,
    true_source_m: Iterable[float],
    tau: Iterable[float],
    sigma: Iterable[float],
    amplitude_model: str = "phase_only",
    gamma: float = 1.0,
    r_min: float = 0.05,
    data_seed: int = 20260721,
) -> NarrowbandSourceLocalizationData:
    """Generate deterministic synthetic complex sensor observations from a stored seed."""
    sensors = np.asarray(sensors_m, dtype=float)
    q_true = np.asarray(list(true_source_m), dtype=float)
    if q_true.shape != (2,):
        raise ValueError("true_source_m must have shape (2,)")

    rng = np.random.default_rng(int(data_seed))

    # Temporary prior placeholders are unused for data synthesis; set to standard shape.
    tmp = NarrowbandSourceLocalizationProblem(
        y_obs=np.zeros((len(list(frequencies_hz)), sensors.shape[0]), dtype=np.complex128),
        sensors_m=sensors,
        frequencies_hz=frequencies_hz,
        propagation_speed=propagation_speed,
        tau=tau,
        sigma=sigma,
        prior_mean_m=np.zeros(2, dtype=float),
        prior_cov_m=np.eye(2, dtype=float),
        amplitude_model=amplitude_model,
        gamma=gamma,
        r_min=r_min,
    )

    h_true = tmp.steering_matrix(q_true)[0]  # (F, J)
    f_count, j_count = h_true.shape

    alpha_draws = np.empty((f_count,), dtype=np.complex128)
    epsilon_draws = np.empty((f_count, j_count), dtype=np.complex128)
    y_obs = np.empty((f_count, j_count), dtype=np.complex128)

    for ell in range(f_count):
        tau2 = float(tmp.tau[ell] ** 2)
        sigma2 = float(tmp.sigma[ell] ** 2)
        alpha_ell = _complex_normal_scalar(rng, tau2)
        eps_ell = _complex_normal_vector(rng, sigma2, size=j_count)
        alpha_draws[ell] = alpha_ell
        epsilon_draws[ell, :] = eps_ell
        y_obs[ell, :] = alpha_ell * h_true[ell, :] + eps_ell

    cfg = {
        "model": "marginalized_complex_amplitude",
        "dimension": 2,
        "sensors_m": sensors.tolist(),
        "frequencies_hz": [float(v) for v in tmp.frequencies_hz],
        "propagation_speed": float(tmp.propagation_speed),
        "true_source_m": q_true.tolist(),
        "tau": [float(v) for v in tmp.tau],
        "sigma": [float(v) for v in tmp.sigma],
        "amplitude_model": tmp.amplitude_model,
        "gamma": float(tmp.gamma),
        "r_min": float(tmp.r_min),
        "data_seed": int(data_seed),
    }

    return NarrowbandSourceLocalizationData(
        q_true=q_true,
        frequencies_hz=tmp.frequencies_hz.copy(),
        sensors_m=sensors.copy(),
        propagation_speed=float(tmp.propagation_speed),
        tau=tmp.tau.copy(),
        sigma=tmp.sigma.copy(),
        y_obs=y_obs,
        alpha_draws=alpha_draws,
        epsilon_draws=epsilon_draws,
        amplitude_model=tmp.amplitude_model,
        gamma=float(tmp.gamma),
        r_min=float(tmp.r_min),
        data_seed=int(data_seed),
        config=cfg,
    )


def build_narrowband_source_localization_problem(
    *,
    sensors_m: np.ndarray,
    frequencies_hz: Iterable[float],
    propagation_speed: float,
    true_source_m: Iterable[float],
    tau: Iterable[float],
    sigma: Iterable[float],
    prior_mean_m: Iterable[float],
    prior_cov_m: np.ndarray,
    amplitude_model: str = "phase_only",
    gamma: float = 1.0,
    r_min: float = 0.05,
    data_seed: int = 20260721,
) -> tuple[NarrowbandSourceLocalizationProblem, NarrowbandSourceLocalizationData]:
    """Build deterministic data and the corresponding whitened localization problem."""
    data = generate_narrowband_source_localization_data(
        sensors_m=sensors_m,
        frequencies_hz=frequencies_hz,
        propagation_speed=propagation_speed,
        true_source_m=true_source_m,
        tau=tau,
        sigma=sigma,
        amplitude_model=amplitude_model,
        gamma=gamma,
        r_min=r_min,
        data_seed=data_seed,
    )
    problem = NarrowbandSourceLocalizationProblem(
        y_obs=data.y_obs,
        sensors_m=data.sensors_m,
        frequencies_hz=data.frequencies_hz,
        propagation_speed=data.propagation_speed,
        tau=data.tau,
        sigma=data.sigma,
        prior_mean_m=prior_mean_m,
        prior_cov_m=prior_cov_m,
        amplitude_model=amplitude_model,
        gamma=gamma,
        r_min=r_min,
    )
    return problem, data
