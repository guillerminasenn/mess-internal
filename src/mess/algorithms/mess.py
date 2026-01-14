# MESS (M >= 1 proposals)

# algorithms/mess.py
import numpy as np

def mess_step(x, problem, rng, M=1):
    """Perform a MESS step.
    Parameters
    ----------
    x : np.ndarray
        Current state.
    problem : mess.problems.base.Problem
        Problem instance.
    rng : np.random.Generator
        Random number generator.
    M : int
        Number of proposals to generate.
    """
    # Center the current state and the auxiliary sample from the prior
    x_centered = x - problem.prior_mean()
    nu_centered = problem.sample_prior(rng) - problem.prior_mean() 

    # Sample the likelihood threshold
    logy = problem.log_likelihood(x) + np.log(rng.uniform())

    # Sample alpha, the angle corresponding to the current state
    alpha = rng.uniform(0, 2*np.pi)

    # Initialize the angle interval
    phi_min = 0
    phi_max = 2 * np.pi

    # Shrink interval until acceptance
    nr_intervals = 0
    while True:
        # Sample M angles
        phi_vector = rng.uniform(phi_min, phi_max, size=M)

        # Compute the proposals
        x_prop_vector = (
            problem.prior_mean()[:, np.newaxis]
            + np.cos(phi_vector - alpha) * x_centered[:, np.newaxis]
            + np.sin(phi_vector - alpha) * nu_centered[:, np.newaxis]
        )

        # Evaluate the likelihood for all proposals
        log_likelihoods = np.array([
            problem.log_likelihood(x_prop_vector[:, i])
            for i in range(M)
        ])

        # Compute A_i, the set of indexes of the candidate proposals
        A = np.where(log_likelihoods > logy)[0]

        # If there are valid proposals, select one and return
        if len(A) > 0:

            # Sample uniformly among the valid proposals
            i = rng.choice(A)
            return x_prop_vector[:, i], nr_intervals

        # Otherwise, shrink the angle interval
        phi_min = np.max(np.concatenate([np.array([phi_min]), phi_vector[np.where(phi_vector < alpha)]]))
        phi_max = np.min(np.concatenate([np.array([phi_max]), phi_vector[np.where(phi_vector >= alpha)]]))

        # Count the number of shrinking steps
        nr_intervals += 1