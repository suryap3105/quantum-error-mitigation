
import numpy as np
import quantum_core
from pl_rust_device import RustDensityMatrixDevice
import pennylane as qml

def verify_noise_control():
    print("Verifying if noise strength is controllable...")
    
    # 1. Initialize device with specific gamma
    # Now using new API: noise_type and noise_gamma
    dev = RustDensityMatrixDevice(wires=1, shots=None, noise_type="amplitude_damping", noise_gamma=0.5) 
    # If working correctly, gamma=0.5 should cause huge noise.
    # If using hardcoded 0.05, it will be small noise.
    
    @qml.qnode(dev)
    def circuit():
        qml.PauliX(wires=0) # Prepare |1>
        return qml.probs(wires=0)
        
    probs = circuit()
    print(f"Gamma=0.5, P(|1>) = {probs[1]:.4f}")
    
    # Check if P(|1>) reflects gamma=0.5
    # T1 decay from |1>: P(1) = 1 - gamma (roughly for short time) or exp(-t/T1)
    # The rust implementation amplitude_damping_kraus(gamma):
    # K0 = diag(1, sqrt(1-gamma)), K1 = [[0, sqrt(gamma)], [0, 0]]
    # rho = |1><1| = [[0,0],[0,1]]
    # K0 rho K0d = [[0,0], [0, 1-gamma]]
    # K1 rho K1d = [[gamma, 0], [0,0]]
    # rho' = [[gamma, 0], [0, 1-gamma]]
    # So P(1) should be 1 - gamma.
    
    expected_p1 = 1.0 - 0.5
    if abs(probs[1] - expected_p1) < 0.05:
        print("✅ Noise control WORKS (matched 0.5)")
    elif abs(probs[1] - (1.0 - 0.05)) < 0.05:
        print("❌ Noise control BROKEN (matched hardcoded 0.05)")
    else:
        print(f"❓ Noise control unknown behavior: {probs[1]}")

def main():
    verify_noise_control()

if __name__ == "__main__":
    main()
