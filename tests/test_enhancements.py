"""
Test multi-qubit expectation value calculation.
Verifies that marginal density matrix computation is correct.
"""

import numpy as np
import pennylane as qml
from pl_rust_device import RustDensityMatrixDevice

def test_multi_qubit_pauli_x():
    """Test <X> measurement on multi-qubit system"""
    print("\n[Test 1] Multi-qubit Pauli-X expectation")
    
    # 2-qubit system: prepare |+0> state
    dev = RustDensityMatrixDevice(wires=2, shots=None, noise_type="amplitude_damping", noise_gamma=0.0)
    
    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(wires=0)  # qubit 0 in |+>, qubit 1 in |0>
        return qml.expval(qml.PauliX(wires=0))
    
    result = circuit()
    print(f"<X> on wire 0 (|+0> state): {result:.6f} (expected: 1.0)")
    
    assert abs(result - 1.0) < 1e-5,  f"Expected 1.0, got {result}"
    print("✅ PASS")


def test_multi_qubit_with_noise():
    """Test multi-qubit expectation with noise"""
    print("\n[Test 2] Multi-qubit with phase damping")
    
    dev = RustDensityMatrixDevice(wires=2, shots=None, noise_type="phase_damping", noise_gamma=0.2)
    
    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(wires=0)
        qml.Hadamard(wires=1)
        return [qml.expval(qml.PauliX(wires=0)), qml.expval(qml.PauliX(wires=1))]
    
    results = circuit()
    
    # Both should give 1 - 2*lambda = 1 - 2*0.2 = 0.6
    print(f"<X> on wire 0: {results[0]:.6f} (expected: 0.6)")
    print(f"<X> on wire 1: {results[1]:.6f} (expected: 0.6)")
    
    assert abs(results[0] - 0.6) < 1e-5
    assert abs(results[1] - 0.6) < 1e-5
    print("✅ PASS")


def test_parameter_validation():
    """Test that parameter validation works"""
    print("\n[Test 3] Parameter validation")
    
    # Test invalid noise_type
    try:
        dev = RustDensityMatrixDevice(wires=1, noise_type="invalid_noise")
        print("❌ FAIL: Should have raised ValueError for invalid noise_type")
    except ValueError as e:
        print(f"✅ PASS: Caught invalid noise_type - {e}")
    
    # Test invalid gamma (out of range)
    try:
        dev = RustDensityMatrixDevice(wires=1, noise_gamma=1.5)
        print("❌ FAIL: Should have raised ValueError for gamma > 1")
    except ValueError as e:
        print(f"✅ PASS: Caught invalid gamma - {e}")


def main():
    print("="*60)
    print("Testing Production Enhancements")
    print("="*60)
    
    test_multi_qubit_pauli_x()
    test_multi_qubit_with_noise()
    test_parameter_validation()
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)


if __name__ == "__main__":
    main()
