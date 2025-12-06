import numpy as np
from .strategies import Strategy, NoiseType
from .noise_models import compute_bias, compute_discard_rate, compute_sampling_sigma

def evaluate_point(R, gamma, strategy: Strategy, fci_energy, noise_type: NoiseType = NoiseType.AMPLITUDE_DAMPING, num_bootstraps=50):
    """
    Evaluate a single (R, gamma, strategy) point using the Phenomenological Model.
    Returns a dictionary of statistics.
    """
    
    # 1. Compute deterministic bias
    # Bias depends on strategy, gamma, noise_type, and depth (fixed at 9)
    bias = compute_bias(strategy, gamma, noise_type, depth=9)
    
    # Hybrid region-dependent variation (from spec)
    if strategy == Strategy.HYBRID:
        if 0.74 <= R <= 1.0:
            bias *= 0.8
        else:
            bias *= 1.1

    # 2. Compute discard rate
    discard_rate = compute_discard_rate(strategy, gamma, noise_type)
    
    # 3. Compute sampling noise sigma
    # N_physical = 10000 (fixed shot budget)
    sigma = compute_sampling_sigma(discard_rate, N_physical=10000)
    
    # 4. Bootstrap sampling
    # We generate 'num_bootstraps' estimates of the energy
    # E_est = E_FCI + bias + Normal(0, sigma)
    
    energies = []
    for _ in range(num_bootstraps):
        noise = np.random.normal(0, sigma)
        e_est = fci_energy + bias + noise
        energies.append(e_est)
        
    energies = np.array(energies)
    mean_energy = np.mean(energies)
    std_dev = np.std(energies)
    
    # 95% Confidence Interval
    ci_lower = mean_energy - 1.96 * sigma # Using theoretical sigma for CI width as per spec
    ci_upper = mean_energy + 1.96 * sigma
    
    return {
        "mean_energy": mean_energy,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "discard_rate": discard_rate,
        "sigma": sigma,
        "bias": bias,
        "fci_energy": fci_energy
    }
