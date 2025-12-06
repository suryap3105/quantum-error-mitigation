import numpy as np
from .strategies import Strategy

def compute_bias(strategy: Strategy, gamma: float, depth: int = 9) -> float:
    """
    Compute the systematic bias (in Hartree) for a given strategy and noise level.
    Formula: bias = (a + b * depth) * gamma
    """
    if strategy == Strategy.BASELINE:
        a, b = 110.0, 10.0
    elif strategy == Strategy.DD:
        a, b = 80.0, 15.0
    elif strategy == Strategy.SYM:
        a, b = 22.0, 5.0
    elif strategy == Strategy.HYBRID:
        a, b = 20.0, 3.0
    else:
        return 0.0
        
    raw_bias_mHa = (a + b * depth) * gamma
    return raw_bias_mHa / 1000.0  # Convert mHa to Ha

def compute_discard_rate(strategy: Strategy, gamma: float) -> float:
    """
    Compute the discard rate (0.0 to 1.0) for a given strategy and noise level.
    """
    if strategy == Strategy.SYM:
        # D_sym = clamp(0.30 + 4.5*gamma, 0.4, 0.95)
        val = 0.30 + 4.5 * gamma
        return float(np.clip(val, 0.4, 0.95))
        
    elif strategy == Strategy.HYBRID:
        # D_hyb = clamp(0.10 + 1.5*gamma, 0.1, 0.35)
        val = 0.10 + 1.5 * gamma
        return float(np.clip(val, 0.1, 0.35))
        
    return 0.0

def compute_sampling_sigma(discard_rate: float, N_physical: int = 10000) -> float:
    """
    Compute the standard error of the mean for energy estimation.
    sigma = H_scale / sqrt(N_valid)
    """
    N_valid = N_physical * (1.0 - discard_rate)
    if N_valid < 1.0:
        N_valid = 1.0
        
    H_scale = 1.0 # Hartree
    sigma = H_scale / np.sqrt(N_valid)
    
    # Clamp to avoid zero variance
    return max(sigma, 1e-6)
