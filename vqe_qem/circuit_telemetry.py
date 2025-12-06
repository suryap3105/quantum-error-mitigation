"""
Circuit telemetry utilities for analyzing quantum circuits.
Provides metrics like gate count, depth, and CNOT count.
"""

def get_circuit_telemetry(molecule, ansatz_layers=2):
    """
    Calculate circuit telemetry for a given molecular system.
    
    Args:
        molecule: str - Molecule name ("H2", "LiH", "BeH2")
        ansatz_layers: int - Number of ansatz layers
        
    Returns:
        dict with keys: num_qubits, circuit_depth, gate_count, cnot_count
    """
    # Molecular active space configurations
    qubit_config = {
        "H2": 4,
        "LiH": 4,
        "BeH2": 6,
        "H4": 8  # If you add this molecule later
    }
    
    num_qubits = qubit_config.get(molecule, 4)
    
    # VQE ansatz structure: Each layer has:
    # - Single qubit rotations (RY) on each qubit: num_qubits gates
    # - Entangling CNOT ladder: num_qubits - 1 CNOTs
    # - Another set of rotations: num_qubits gates
    
    gates_per_layer = 2 * num_qubits + (num_qubits - 1)
    cnots_per_layer = num_qubits - 1
    
    total_gates = ansatz_layers * gates_per_layer
    total_cnots = ansatz_layers * cnots_per_layer
    
    # Circuit depth (assuming sequential execution):
    # Each layer: num_qubits rotations + (num_qubits-1) CNOTs + num_qubits rotations
    # Depth per layer ≈ 2 (rotations can be parallel) + (num_qubits-1) (CNOTs sequential)
    depth_per_layer = 2 + (num_qubits - 1)
    circuit_depth = ansatz_layers * depth_per_layer
    
    return {
        "molecule": molecule,
        "num_qubits": num_qubits,
        "circuit_depth": circuit_depth,
        "gate_count": total_gates,
        "cnot_count": total_cnots,
        "ansatz_layers": ansatz_layers
    }


def print_circuit_telemetry(molecule, ansatz_layers=2):
    """Print formatted circuit telemetry"""
    telemetry = get_circuit_telemetry(molecule, ansatz_layers)
    
    print(f"\n{'='*50}")
    print(f"Circuit Telemetry: {telemetry['molecule']}")
    print(f"{'='*50}")
    print(f"Qubits:        {telemetry['num_qubits']}")
    print(f"Circuit Depth: {telemetry['circuit_depth']}")
    print(f"Total Gates:   {telemetry['gate_count']}")
    print(f"CNOT Count:    {telemetry['cnot_count']}")
    print(f"Ansatz Layers: {telemetry['ansatz_layers']}")
    print(f"{'='*50}\n")
    
    return telemetry


# Chemical accuracy threshold (in Hartree)
CHEMICAL_ACCURACY = 0.0016  # 1.6 mHa = 1 kcal/mol


def is_within_chemical_accuracy(error):
    """Check if error is within chemical accuracy threshold"""
    return abs(error) <= CHEMICAL_ACCURACY


if __name__ == "__main__":
    # Example usage
    for molecule in ["H2", "LiH", "BeH2"]:
        print_circuit_telemetry(molecule, ansatz_layers=2)
