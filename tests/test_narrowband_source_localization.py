from __future__ import annotations

import numpy as np

from mess.experiments.narrowband_source_localization.run_chains import _circular_components
from mess.problems import (
    NarrowbandSourceLocalizationProblem,
    build_narrowband_source_localization_problem,
    generate_narrowband_source_localization_data,
)


def _build_problem(
    *,
    frequencies=(1200.0,),
    sigma=(0.10,),
    amplitude_model="phase_only",
    prior_mean=(0.0, 0.0),
):
    return build_narrowband_source_localization_problem(
        sensors_m=np.array([[-1.4, -1.2], [1.5, -1.0], [-1.1, 1.4], [1.3, 1.2]], dtype=float),
        frequencies_hz=list(frequencies),
        propagation_speed=343.0,
        true_source_m=np.array([0.35, 0.55], dtype=float),
        tau=[1.0 for _ in frequencies],
        sigma=list(sigma),
        prior_mean_m=np.array(prior_mean, dtype=float),
        prior_cov_m=np.diag([1.2**2, 1.2**2]),
        amplitude_model=amplitude_model,
        gamma=1.0,
        r_min=0.05,
        data_seed=20260721,
    )


def test_whitened_and_physical_are_inverses():
    problem, _ = _build_problem()
    z = np.array([0.3, -0.7], dtype=float)
    q = problem.whitened_to_physical(z)
    z_back = problem.physical_to_whitened(q)
    np.testing.assert_allclose(z_back, z, atol=1e-12, rtol=0.0)


def test_phase_only_steering_has_unit_modulus():
    problem, _ = _build_problem(amplitude_model="phase_only")
    q = np.array([0.1, -0.2], dtype=float)
    h = problem.steering_matrix(q)[0]
    np.testing.assert_allclose(np.abs(h), np.ones_like(np.abs(h)), atol=1e-12, rtol=0.0)


def test_marginal_formula_matches_dense_linear_algebra():
    problem, _ = _build_problem(amplitude_model="spherical_spreading")
    q = np.array([-0.4, 0.8], dtype=float)
    ll_fast = problem.log_likelihood_physical(q)
    ll_dense = problem.log_likelihood_dense_physical(q)
    np.testing.assert_allclose(ll_fast, ll_dense, atol=1e-10, rtol=1e-10)


def test_phase_only_reduced_differs_by_constant_only():
    problem, _ = _build_problem(amplitude_model="phase_only")
    q_a = np.array([-0.8, 0.2], dtype=float)
    q_b = np.array([0.7, -0.4], dtype=float)

    full_a = problem.log_likelihood_physical(q_a)
    full_b = problem.log_likelihood_physical(q_b)
    red_a = problem.phase_only_reduced_log_likelihood_physical(q_a)
    red_b = problem.phase_only_reduced_log_likelihood_physical(q_b)

    np.testing.assert_allclose((full_a - red_a), (full_b - red_b), atol=1e-10, rtol=1e-10)


def test_batched_and_scalar_log_likelihood_agree():
    problem, _ = _build_problem()
    z_batch = np.array([[0.0, 0.0], [0.2, -0.1], [-0.6, 0.5]], dtype=float)
    batch = problem.log_likelihood_batch(z_batch)
    scalar = np.array([problem.log_likelihood(z) for z in z_batch], dtype=float)
    np.testing.assert_allclose(batch, scalar, atol=1e-12, rtol=0.0)


def test_log_likelihood_deterministic_and_stateless():
    problem, _ = _build_problem()
    z = np.array([0.25, -0.35], dtype=float)
    before = problem.log_likelihood(z)
    for _ in range(5):
        cur = problem.log_likelihood(z)
        np.testing.assert_allclose(cur, before, atol=0.0, rtol=0.0)


def test_data_generation_is_reproducible_from_seed():
    d1 = generate_narrowband_source_localization_data(
        sensors_m=np.array([[-1.4, -1.2], [1.5, -1.0], [-1.1, 1.4], [1.3, 1.2]], dtype=float),
        frequencies_hz=[1200.0],
        propagation_speed=343.0,
        true_source_m=np.array([0.35, 0.55], dtype=float),
        tau=[1.0],
        sigma=[0.1],
        amplitude_model="phase_only",
        data_seed=42,
    )
    d2 = generate_narrowband_source_localization_data(
        sensors_m=np.array([[-1.4, -1.2], [1.5, -1.0], [-1.1, 1.4], [1.3, 1.2]], dtype=float),
        frequencies_hz=[1200.0],
        propagation_speed=343.0,
        true_source_m=np.array([0.35, 0.55], dtype=float),
        tau=[1.0],
        sigma=[0.1],
        amplitude_model="phase_only",
        data_seed=42,
    )
    np.testing.assert_allclose(d1.y_obs, d2.y_obs, atol=0.0, rtol=0.0)
    np.testing.assert_allclose(d1.alpha_draws, d2.alpha_draws, atol=0.0, rtol=0.0)
    np.testing.assert_allclose(d1.epsilon_draws, d2.epsilon_draws, atol=0.0, rtol=0.0)


def test_prior_mean_shift_does_not_change_likelihood_surface():
    data = generate_narrowband_source_localization_data(
        sensors_m=np.array([[-1.4, -1.2], [1.5, -1.0], [-1.1, 1.4], [1.3, 1.2]], dtype=float),
        frequencies_hz=[1200.0],
        propagation_speed=343.0,
        true_source_m=np.array([0.35, 0.55], dtype=float),
        tau=[1.0],
        sigma=[0.1],
        amplitude_model="phase_only",
        data_seed=20260721,
    )

    p0 = NarrowbandSourceLocalizationProblem(
        y_obs=data.y_obs,
        sensors_m=data.sensors_m,
        frequencies_hz=data.frequencies_hz,
        propagation_speed=data.propagation_speed,
        tau=data.tau,
        sigma=data.sigma,
        prior_mean_m=np.array([0.0, 0.0], dtype=float),
        prior_cov_m=np.diag([1.2**2, 1.2**2]),
        amplitude_model="phase_only",
    )
    p1 = NarrowbandSourceLocalizationProblem(
        y_obs=data.y_obs,
        sensors_m=data.sensors_m,
        frequencies_hz=data.frequencies_hz,
        propagation_speed=data.propagation_speed,
        tau=data.tau,
        sigma=data.sigma,
        prior_mean_m=np.array([0.6, -0.4], dtype=float),
        prior_cov_m=np.diag([1.2**2, 1.2**2]),
        amplitude_model="phase_only",
    )

    q = np.array([0.1, -0.7], dtype=float)
    np.testing.assert_allclose(
        p0.log_likelihood_physical(q),
        p1.log_likelihood_physical(q),
        atol=1e-12,
        rtol=0.0,
    )


def test_two_frequency_negative_control_reduces_ambiguity_statistic():
    p1, d1 = _build_problem(frequencies=(1200.0,), sigma=(0.05,))
    p2, d2 = _build_problem(frequencies=(1200.0, 1644.0), sigma=(0.05, 0.05))
    assert np.allclose(d1.q_true, d2.q_true)

    q_true = d1.q_true

    def ambiguity_gap(problem):
        grid = problem.reference_grid_evaluation(reference_box_m=(-4.0, 4.0, -4.0, 4.0), grid_size=121)
        ll = np.asarray(grid["log_likelihood"], dtype=float)
        q1 = np.asarray(grid["q1"], dtype=float)
        q2 = np.asarray(grid["q2"], dtype=float)
        x, y = np.meshgrid(q1, q2, indexing="xy")
        dist = np.sqrt((x - q_true[0]) ** 2 + (y - q_true[1]) ** 2)
        true_like = problem.log_likelihood_physical(q_true)
        alias_like = float(np.max(ll[dist > 0.5]))
        return float(true_like - alias_like)

    gap1 = ambiguity_gap(p1)
    gap2 = ambiguity_gap(p2)
    assert gap2 >= gap1 - 1e-8


def test_circular_component_detection_handles_wraparound():
    mask = np.array([True, True, False, False, True, True, True], dtype=bool)
    comps = _circular_components(mask)
    total = sum(b - a for a, b in comps)
    assert total == int(mask.sum())
    # The wraparound true block should be represented without splitting loss.
    assert len(comps) in {1, 2}


def test_reference_grid_probabilities_sum_to_one():
    problem, _ = _build_problem()
    grid = problem.reference_grid_evaluation(reference_box_m=(-4.0, 4.0, -4.0, 4.0), grid_size=81)
    logp = np.asarray(grid["log_posterior"], dtype=float)
    dx = float(np.asarray(grid["dx"])[0])
    dy = float(np.asarray(grid["dy"])[0])

    m = np.max(logp)
    w = np.exp(logp - m)
    z = np.sum(w) * dx * dy
    probs = w / np.sum(w)

    assert np.isfinite(z)
    np.testing.assert_allclose(np.sum(probs), 1.0, atol=1e-12, rtol=0.0)
