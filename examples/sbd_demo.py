# Demo for semi-blind deconvolution

import numpy as np
import matplotlib.pyplot as plt
from mess.data.sbd import generate_sbd_data
from mess.problems.sbd import SemiBlindDeconvolution
from mess.algorithms.ess import elliptical_slice_sampling
from mess.algorithms.mess import manifold_elliptical_slice_sampling


def run_sbd_demo(
    n_v=50,
    n_h=50,
    kernel_length=5,
    prior_var=1.0,
    noise_variance=0.1,
    n_samples=1000,
    seed=0,
):
    """
    Run a demo comparing ESS and MESS on semi-blind deconvolution.
    
    Parameters
    ----------
    n_v : int
        Number of rows in the image lattice.
    n_h : int
        Number of columns in the image lattice.
    kernel_length : int
        Length of the blur kernel.
    prior_var : float
        Prior variance for image pixels.
    noise_variance : float
        Observation noise variance.
    n_samples : int
        Number of MCMC samples to generate.
    seed : int
        Random seed.
    """
    print("=" * 70)
    print("Semi-Blind Deconvolution Demo")
    print("=" * 70)
    
    # Generate data
    print(f"\nGenerating synthetic data...")
    print(f"  Image size: {n_v} x {n_h} = {n_v * n_h} pixels")
    print(f"  Kernel length: {kernel_length}")
    print(f"  Prior variance: {prior_var}")
    print(f"  Noise variance: {noise_variance}")
    
    data = generate_sbd_data(
        n_v=n_v,
        n_h=n_h,
        kernel_length=kernel_length,
        prior_var=prior_var,
        noise_variance=noise_variance,
        seed=seed,
    )
    
    # Create problem instance
    problem = SemiBlindDeconvolution(
        d=data["d"],
        w=data["w"],
        n_v=n_v,
        n_h=n_h,
        prior_var=prior_var,
        noise_variance=noise_variance,
    )
    
    print(f"\nProblem setup complete.")
    print(f"  Dimension: {problem.dim}")
    
    # Run ESS
    print(f"\n{'=' * 70}")
    print(f"Running Elliptical Slice Sampling (ESS)...")
    print(f"{'=' * 70}")
    
    rng_ess = np.random.default_rng(seed)
    samples_ess = elliptical_slice_sampling(
        problem=problem,
        initial_state=data["c_init"],
        n_samples=n_samples,
        rng=rng_ess,
        verbose=True,
    )
    
    # Run MESS (if available)
    print(f"\n{'=' * 70}")
    print(f"Running Manifold Elliptical Slice Sampling (MESS)...")
    print(f"{'=' * 70}")
    
    # For MESS, we may need to specify the manifold dimension m
    # Typically m << n for efficiency
    m = min(50, problem.dim // 2)
    
    rng_mess = np.random.default_rng(seed + 1)
    samples_mess = manifold_elliptical_slice_sampling(
        problem=problem,
        initial_state=data["c_init"],
        n_samples=n_samples,
        m=m,
        rng=rng_mess,
        verbose=True,
    )
    
    # Compute statistics
    print(f"\n{'=' * 70}")
    print(f"Results Summary")
    print(f"{'=' * 70}")
    
    # Posterior means
    c_true = data["c_true"]
    c_mean_ess = np.mean(samples_ess, axis=0)
    c_mean_mess = np.mean(samples_mess, axis=0)
    
    # Reconstruction errors (RMSE)
    rmse_ess = np.sqrt(np.mean((c_mean_ess - c_true) ** 2))
    rmse_mess = np.sqrt(np.mean((c_mean_mess - c_true) ** 2))
    
    print(f"\nReconstruction RMSE:")
    print(f"  ESS:  {rmse_ess:.6f}")
    print(f"  MESS: {rmse_mess:.6f}")
    
    # Visualize results
    visualize_results(
        c_true=c_true,
        d=data["d"],
        c_mean_ess=c_mean_ess,
        c_mean_mess=c_mean_mess,
        n_v=n_v,
        n_h=n_h,
        kernel=data["w"],
    )
    
    return {
        "samples_ess": samples_ess,
        "samples_mess": samples_mess,
        "data": data,
        "problem": problem,
    }


def visualize_results(c_true, d, c_mean_ess, c_mean_mess, n_v, n_h, kernel):
    """Visualize true image, observations, and reconstructions."""
    
    # Reshape vectors to 2D images
    img_true = c_true.reshape(n_v, n_h)
    img_obs = d.reshape(n_v, n_h)
    img_ess = c_mean_ess.reshape(n_v, n_h)
    img_mess = c_mean_mess.reshape(n_v, n_h)
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # True image
    im0 = axes[0, 0].imshow(img_true, cmap='gray', aspect='auto')
    axes[0, 0].set_title('True Image', fontsize=12, fontweight='bold')
    axes[0, 0].axis('off')
    plt.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04)
    
    # Observed (blurred + noisy)
    im1 = axes[0, 1].imshow(img_obs, cmap='gray', aspect='auto')
    axes[0, 1].set_title('Observed (Blurred + Noisy)', fontsize=12, fontweight='bold')
    axes[0, 1].axis('off')
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)
    
    # Blur kernel
    axes[0, 2].plot(kernel, 'o-', linewidth=2, markersize=6)
    axes[0, 2].set_title('Blur Kernel', fontsize=12, fontweight='bold')
    axes[0, 2].set_xlabel('Index')
    axes[0, 2].set_ylabel('Value')
    axes[0, 2].grid(True, alpha=0.3)
    
    # ESS reconstruction
    im2 = axes[1, 0].imshow(img_ess, cmap='gray', aspect='auto')
    axes[1, 0].set_title('ESS Reconstruction', fontsize=12, fontweight='bold')
    axes[1, 0].axis('off')
    plt.colorbar(im2, ax=axes[1, 0], fraction=0.046, pad=0.04)
    
    # MESS reconstruction
    im3 = axes[1, 1].imshow(img_mess, cmap='gray', aspect='auto')
    axes[1, 1].set_title('MESS Reconstruction', fontsize=12, fontweight='bold')
    axes[1, 1].axis('off')
    plt.colorbar(im3, ax=axes[1, 1], fraction=0.046, pad=0.04)
    
    # Difference map (ESS vs MESS)
    diff = np.abs(img_ess - img_mess)
    im4 = axes[1, 2].imshow(diff, cmap='hot', aspect='auto')
    axes[1, 2].set_title('|ESS - MESS|', fontsize=12, fontweight='bold')
    axes[1, 2].axis('off')
    plt.colorbar(im4, ax=axes[1, 2], fraction=0.046, pad=0.04)
    
    plt.tight_layout()
    plt.savefig('sbd_demo_results.png', dpi=150, bbox_inches='tight')
    print(f"\nFigure saved as 'sbd_demo_results.png'")
    plt.show()


if __name__ == "__main__":
    # Run demo with default parameters
    results = run_sbd_demo(
        n_v=50,
        n_h=50,
        kernel_length=5,
        prior_var=1.0,
        noise_variance=0.1,
        n_samples=1000,
        seed=42,
    )
