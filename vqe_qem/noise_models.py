import numpy as np
from .strategies import Strategy, NoiseType

def compute_bias(strategy: Strategy, gamma: float, noise_type: NoiseType = NoiseType.AMPLITUDE_DAMPING, depth: int = 9) -> float:
    """
    Compute the systematic bias (in Hartree) for a given strategy, noise type, and noise level.
    """
    # Base coefficients for T1 (Amplitude Damping)
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

    # Adjust coefficients based on noise type
    if noise_type == NoiseType.PHASE_DAMPING:
        # T2: Less bias than T1, DD less effective vs Baseline
        a *= 0.6
        b *= 0.6
        if strategy == Strategy.DD: # DD doesn't fight T2 as well as T1
            a *= 1.2 
    elif noise_type == NoiseType.DEPOLARIZING:
        # Depol: High bias, drift to average
        a *= 1.5
        b *= 1.2
        if strategy in [Strategy.SYM, Strategy.HYBRID]: # Sym wrecked by depol
            a *= 2.0 
    elif noise_type == NoiseType.COMPOSITE:
        # Composite: Mix of effects
        a *= 1.1
        b *= 1.1

    raw_bias_mHa = (a + b * depth) * gamma
    return raw_bias_mHa / 1000.0

def compute_discard_rate(strategy: Strategy, gamma: float, noise_type: NoiseType = NoiseType.AMPLITUDE_DAMPING) -> float:
    """
    Compute the discard rate (0.0 to 1.0) for a given strategy and noise level.
    """
    if strategy not in [Strategy.SYM, Strategy.HYBRID]:
        return 0.0

    # Base formula for T1
    # D_sym = 0.30 + 4.5*gamma
    base_slope = 4.5
    base_offset = 0.30
    
    if strategy == Strategy.HYBRID:
        base_slope = 1.5
        base_offset = 0.10

    # Adjust for noise type
    if noise_type == NoiseType.PHASE_DAMPING:
        # T2: Lower discard than T1
        base_slope *= 0.4
        base_offset *= 0.5
    elif noise_type == NoiseType.DEPOLARIZING:
        # Depol: Huge discard
        base_slope *= 1.5
        base_offset *= 1.2
    elif noise_type == NoiseType.COMPOSITE:
        # Composite: Moderate
        base_slope *= 1.1
        base_offset *= 1.1

    val = base_offset + base_slope * gamma
    
    # Clamp based on physics
    max_discard = 0.98 if noise_type == NoiseType.DEPOLARIZING else 0.95
    return float(np.clip(val, 0.0, max_discard))

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
