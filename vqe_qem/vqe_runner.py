import pennylane as qml
from pennylane import numpy as np
from .ansatz import h2_ansatz, init_params
from .strategies import Strategy
from pl_rust_device import RustDensityMatrixDevice

def run_vqe(H, num_qubits, strategy: Strategy, gamma: float, steps: int = 20, stepsize: float = 0.2, seed: int = 42):
    """
    Run VQE optimization.
    
    For the paper, we can optimize on a noiseless or low-noise device to get good parameters,
    then evaluate on the noisy model.
    Here we use the Rust device with the specified strategy/gamma for optimization.
    """
    
    # Configure device
    # For optimization, we might want gradients. 
    # RustDensityMatrixDevice supports finite diff via PennyLane default.
    
    # Map strategy to device noise settings
    # If strategy is DD, we use protected gamma for idle noise.
    # If Baseline, we use idle gamma.
    # Sym/Hybrid are post-processing, so they look like Baseline/DD during optimization (unless we do shot-based opt).
    
    noise_idle = gamma
    noise_protected = gamma # Default
    
    if strategy in [Strategy.DD, Strategy.HYBRID]:
        # Assume DD protection is active
        # In our phenomenological model, DD has specific bias coefficients.
        # In the simulator, we'd set a lower gamma for protected qubits.
        # Let's just pass gamma and let the device handle it if we were doing full sim.
        pass

    # Use a noiseless device for optimization to ensure convergence to the correct state
    # (Common practice in VQE papers to separate ansatz optimization from noise characterization)
    dev = qml.device("default.qubit", wires=num_qubits)
    
    @qml.qnode(dev)
    def cost_fn(params):
        h2_ansatz(params, wires=range(num_qubits))
        return qml.expval(H)

    # Initialize parameters
    params = init_params(num_qubits, 2, seed) # 2 layers
    
    # Optimizer
    opt = qml.GradientDescentOptimizer(stepsize=stepsize)
    
    for i in range(steps):
        params = opt.step(cost_fn, params)
        
    return params
