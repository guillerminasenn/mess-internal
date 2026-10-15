import unittest

import numpy as np

from mess.providers.polar_twist import provider


class PolarTwistProviderTests(unittest.TestCase):
    def setUp(self):
        self.model = {
            "alpha": 5.0,
            "sigma_noise": 0.2,
            "prior_mean": [0.0, 0.0],
            "prior_cov": [[1.0, 0.0], [0.0, 1.0]],
        }
        self.data = {"y_obs": [0.5, -0.2]}

    def test_metadata_and_runtime_match_existing_gaussian_sampler_contract(self):
        metadata = provider.describe()
        self.assertEqual(metadata["problem_id"], "polar_twist")
        self.assertEqual(metadata["parameters"][0]["coordinates"]["parameter"], ["x1", "x2"])
        runtime = provider.build(self.model, self.data)
        self.assertEqual(runtime.dim, 2)
        np.testing.assert_array_equal(runtime.L, np.eye(2))
        for operation in (
            runtime.log_posterior, runtime.log_prior, runtime.log_likelihood,
            runtime.prior_mean, runtime.sample_prior, runtime.forward,
        ):
            self.assertTrue(callable(operation))

    def test_simulation_and_prior_sampling_use_supplied_rng(self):
        first = provider.simulate(self.model, np.random.default_rng(22))
        second = provider.simulate(self.model, np.random.default_rng(22))
        for name in first:
            np.testing.assert_array_equal(first[name], second[name])

        runtime = provider.build(self.model, self.data)
        first_draw = runtime.sample_prior(np.random.default_rng(33))
        second_draw = runtime.sample_prior(np.random.default_rng(33))
        np.testing.assert_array_equal(first_draw, second_draw)

        first_predictive = provider.prior_predictive(
            self.model, np.random.default_rng(44), samples=12
        )
        second_predictive = provider.prior_predictive(
            self.model, np.random.default_rng(44), samples=12
        )
        for name in first_predictive:
            np.testing.assert_array_equal(first_predictive[name], second_predictive[name])
        self.assertEqual(first_predictive["parameters"].shape, (12, 2))
        self.assertEqual(first_predictive["observations"].shape, (12, 2))

    def test_reference_is_normalized_and_reports_grid_limits(self):
        result = provider.reference(self.model, self.data, {"grid_size": 41})
        density = result["density"]
        accuracy = result["accuracy"]
        self.assertEqual(density.shape, (41, 41))
        integral = density.sum() * np.prod(accuracy["grid_spacing"])
        self.assertAlmostEqual(float(integral), 1.0)
        self.assertIn("boundary_weight_fraction", accuracy)
        self.assertEqual(accuracy["method"], "finite-domain uniform grid")

    def test_invalid_reference_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            provider.reference(self.model, self.data, {"grid_size": 2})
        with self.assertRaises(ValueError):
            provider.reference(self.model, self.data, {"bounds": [[1, -1], [-1, 1]]})

    def test_invalid_or_unknown_problem_settings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown polar-twist model"):
            provider.build({**self.model, "typo": 1}, self.data)
        with self.assertRaisesRegex(ValueError, "finite number"):
            provider.build({**self.model, "alpha": float("nan")}, self.data)
        with self.assertRaisesRegex(ValueError, "Unknown polar-twist data"):
            provider.build(self.model, {**self.data, "unexpected": 1})


if __name__ == "__main__":
    unittest.main()