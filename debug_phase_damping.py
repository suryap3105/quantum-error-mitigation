import numpy as np
import pennylane as qml
from pl_rust_device import RustDensityMatrixDevice

print("Debugging Phase Damping Issue...")

# Test 1: No noise, should get <X> = 1.0
print("\n[Test 1] Lambda = 0.0 (no noise)")
dev = RustDensityMatrixDevice(wires=1, shots=None, noise_type="phase_damping", noise_gamma=0.0)

@qml.qnode(dev)
def circuit_no_noise():
    qml.Hadamard(wires=0)
    return qml.expval(qml.PauliX(wires=0))

result = circuit_no_noise()
print(f"<X> with no noise: {result} (expected: 1.0)")

# Test 2: Check probabilities instead
@qml.qnode(dev)
def circuit_probs():
    qml.Hadamard(wires=0)
    return qml.probs(wires=0)

probs = circuit_probs()
print(f"Probabilities: {probs} (expected: [0.5, 0.5])")

# Test 3: Try without any custom noise type (using amplitude damping as baseline)
print("\n[Test 2] Using amplitude_damping with gamma=0")
dev2 = RustDensityMatrixDevice(wires=1, shots=None, noise_type="amplitude_damping", noise_gamma=0.0)

@qml.qnode(dev2)
def circuit_baseline():
    qml.Hadamard(wires=0)
    return qml.expval(qml.PauliX(wires=0))

result2 = circuit_baseline()
print(f"<X> with amplitude_damping(0): {result2} (expected: 1.0)")

# Test 4: Check what happens with just state preparation, no noise
print("\n[Test 3] State |+> without measurement")
dev3 = RustDensityMatrixDevice(wires=1, shots=None, noise_type="amplitude_damping", noise_gamma=0.0)

@qml.qnode(dev3)
def just_hadamard():
    qml.Hadamard(wires=0)
    return qml.state()

try:
    state = just_hadamard()
    print(f"State vector: {state}")
except Exception as e:
    print(f"Can't get state: {e}")
