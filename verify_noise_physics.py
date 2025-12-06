
import numpy as np
import pennylane as qml
from pl_rust_device import RustDensityMatrixDevice
import matplotlib.pyplot as plt

def verify_physics():
    print("Verifying QEM Physics Implementation...")
    
    # 1. Amplitude Damping (T1) verification
    print("\n[1] Check Amplitude Damping (T1)...")
    gammas = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    p1_values = []
    
    for g in gammas:
        dev = RustDensityMatrixDevice(wires=1, shots=None, noise_type="amplitude_damping", noise_gamma=g)
        @qml.qnode(dev)
        def circuit_t1():
            qml.PauliX(wires=0) # Prepare |1>
            return qml.probs(wires=0)
        p1_values.append(circuit_t1()[1])
        
    print(f"Gammas: {gammas}")
    print(f"P(|1>): {p1_values}")
    
    # Check theoretical match: P(1) = 1 - gamma
    errors_t1 = [abs(p - (1.0 - g)) for p, g in zip(p1_values, gammas)]
    max_err_t1 = max(errors_t1)
    if max_err_t1 < 1e-5:
        print("SUCCESS: Amplitude Damping perfectly matches theory (P(|1>) = 1 - gamma)")
    else:
        print(f"FAILURE: Amplitude Damping mismatch! Max error: {max_err_t1}")

    # 2. Phase Damping (T2) verification
    print("\n[2] Check Phase Damping (T2)...")
    lambdas = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    coherences = []
    
    for l in lambdas:
        dev = RustDensityMatrixDevice(wires=1, shots=None, noise_type="phase_damping", noise_gamma=l)
        @qml.qnode(dev)
        def circuit_t2():
            qml.Hadamard(wires=0) # Prepare |+>
            return qml.expval(qml.PauliX(wires=0))
            
        coherences.append(circuit_t2())
        
    print(f"Lambdas: {lambdas}")
    print(f"<X>: {coherences}")
    
    # Check theoretical match for Phase Flip: <X> = 1 - 2*lambda
    errors_t2 = [abs(c - (1.0 - 2.0*l)) for c, l in zip(coherences, lambdas)]
    max_err_t2 = max(errors_t2)
    
    if max_err_t2 < 1e-5:
         print("SUCCESS: Phase Damping matches theory (Phase Flip model: <X> = 1 - 2lambda)")
    else:
         print(f"FAILURE: Phase Damping mismatch! Max error: {max_err_t2}")

    # 3. Depolarizing verification
    print("\n[3] Check Depolarizing...")
    probs_depol = []
    ps = [0.0, 0.5, 1.0] 
    
    for p in ps:
        dev = RustDensityMatrixDevice(wires=1, shots=None, noise_type="depolarizing", noise_gamma=p)
        @qml.qnode(dev)
        def circuit_depol():
            qml.PauliX(wires=0) # Prepare |1>
            return qml.probs(wires=0)
        probs_depol.append(circuit_depol()[1])
        
    print(f"Probs: {ps}")
    print(f"P(|1>): {probs_depol}")
    
    errors_depol = [abs(val - (1.0 - p/2.0)) for val, p in zip(probs_depol, ps)]
    if max(errors_depol) < 1e-5:
        print("SUCCESS: Depolarizing matches theory (P(|1>) = 1 - p/2)")
    else:
        print(f"FAILURE: Depolarizing mismatch! {errors_depol}")

    # 4. Composite verification
    print("\n[4] Check Composite Noise...")
    g_small = 0.1
    dev_small = RustDensityMatrixDevice(wires=1, shots=None, noise_type="composite", noise_gamma=g_small)
    @qml.qnode(dev_small)
    def circuit_comp_small():
        qml.PauliX(wires=0) # |1>
        return qml.probs(wires=0)
    
    p1_small = circuit_comp_small()[1]
    
    # Theory recap:
    # 1. T1(0.1): P(1) = 0.9. rho=[[0.1,0],[0,0.9]]
    # 2. T2(0.05): Diagonals don't change.
    # 3. Depol(0.01): rho -> 0.99*rho + 0.01*I/2. P(1) -> 0.99*0.9 + 0.005 = 0.891 + 0.005 = 0.896
    
    print(f"Composite (g={g_small}): P(|1>) = {p1_small:.4f} (Expected ~0.896)")
    # Allow small margin
    if abs(p1_small - 0.896) < 0.005:
        print("SUCCESS: Composite noise behaves as expected")
    else:
        print(f"FAILURE: Composite noise unexpected result: {p1_small:.4f}")

    print("\nPHYSICS VERIFICATION COMPLETE")

if __name__ == "__main__":
    verify_physics()
