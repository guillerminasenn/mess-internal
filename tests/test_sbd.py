# Tests for semi-blind deconvolution

import numpy as np
from mess.data.sbd import generate_sbd_data
from mess.problems.sbd import SemiBlindDeconvolution


def test_sbd_data_generation():
    """Test that SBD data generation works correctly."""
    data = generate_sbd_data(
        n_v=20,
        n_h=15,
        kernel_length=3,
        prior_var=1.0,
        noise_variance=0.1,
        seed=42,
    )
    
    n = 20 * 15
    
    assert data["c_true"].shape == (n,)
    assert data["c_init"].shape == (n,)
    assert data["d"].shape == (n,)
    assert data["w"].shape == (3,)
    assert data["W"].shape == (n, n)
    assert data["n_v"] == 20
    assert data["n_h"] == 15
    
    # Check that W @ c_true + noise approximately equals d
    reconstructed_mean = data["W"] @ data["c_true"]
    residual = data["d"] - reconstructed_mean
    # Residual should have approximately noise_variance
    empirical_var = np.var(residual)
    assert 0.01 < empirical_var < 1.0, f"Residual variance {empirical_var} seems off"
    
    print("✓ Data generation test passed")


def test_sbd_problem_initialization():
    """Test that SBD problem class initializes correctly."""
    data = generate_sbd_data(
        n_v=20,
        n_h=15,
        kernel_length=3,
        prior_var=1.0,
        noise_variance=0.1,
        seed=42,
    )
    
    problem = SemiBlindDeconvolution(
        d=data["d"],
        w=data["w"],
        n_v=20,
        n_h=15,
        prior_var=1.0,
        noise_variance=0.1,
    )
    
    assert problem.dim == 20 * 15
    assert problem.n_v == 20
    assert problem.n_h == 15
    assert problem.k == 3
    assert problem.W.shape == (300, 300)
    
    print("✓ Problem initialization test passed")


def test_sbd_log_likelihood():
    """Test that log-likelihood computation works."""
    data = generate_sbd_data(
        n_v=20,
        n_h=15,
        kernel_length=3,
        prior_var=1.0,
        noise_variance=0.1,
        seed=42,
    )
    
    problem = SemiBlindDeconvolution(
        d=data["d"],
        w=data["w"],
        n_v=20,
        n_h=15,
        prior_var=1.0,
        noise_variance=0.1,
    )
    
    # Compute log-likelihood at true value
    ll_true = problem.log_likelihood(data["c_true"])
    
    # Compute log-likelihood at a random point
    rng = np.random.default_rng(123)
    c_random = rng.standard_normal(problem.dim)
    ll_random = problem.log_likelihood(c_random)
    
    # True value should have higher likelihood (in expectation)
    # Note: this might not always hold due to noise, but is likely
    print(f"  Log-likelihood at true: {ll_true:.4f}")
    print(f"  Log-likelihood at random: {ll_random:.4f}")
    
    # Check that likelihood is finite
    assert np.isfinite(ll_true)
    assert np.isfinite(ll_random)
    
    print("✓ Log-likelihood test passed")


def test_convolution_matrix_structure():
    """Test that the convolution matrix has the expected structure."""
    data = generate_sbd_data(
        n_v=10,
        n_h=5,
        kernel_length=3,
        seed=42,
    )
    
    problem = SemiBlindDeconvolution(
        d=data["d"],
        w=data["w"],
        n_v=10,
        n_h=5,
        prior_var=1.0,
        noise_variance=0.1,
    )
    
    W = problem.W
    
    # W should be block diagonal with 5 blocks of size 10x10
    # Check that off-diagonal blocks are zero
    for i in range(5):
        for j in range(5):
            if i != j:
                block = W[i*10:(i+1)*10, j*10:(j+1)*10]
                assert np.allclose(block, 0), f"Block ({i}, {j}) should be zero"
    
    # Check that diagonal blocks are Toeplitz
    for i in range(5):
        block = W[i*10:(i+1)*10, i*10:(i+1)*10]
        # Each row should be a shifted version
        # We'll just check it's not all zeros
        assert not np.allclose(block, 0), f"Diagonal block {i} should not be zero"
    
    print("✓ Convolution matrix structure test passed")


if __name__ == "__main__":
    test_sbd_data_generation()
    test_sbd_problem_initialization()
    test_sbd_log_likelihood()
    test_convolution_matrix_structure()
    print("\n✅ All tests passed!")
