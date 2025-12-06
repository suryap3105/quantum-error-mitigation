import pennylane as qml

def h2_ansatz(params, wires):
    """
    Hardware-efficient ansatz for H2 (4 qubits).
    Structure:
    - Initial RY, RZ rotations
    - Entangling CNOT ladder
    - Repeated layers
    """
    num_qubits = len(wires)
    num_layers = params.shape[0]
    
    for l in range(num_layers):
        # Rotation layer
        for i in range(num_qubits):
            qml.RY(params[l, i, 0], wires=wires[i])
            qml.RZ(params[l, i, 1], wires=wires[i])
            
        # Entangling layer (CNOT ladder)
        # 0->1, 1->2, 2->3, 3->0
        for i in range(num_qubits):
            qml.CNOT(wires=[wires[i], wires[(i+1)%num_qubits]])

def init_params(num_qubits, num_layers, seed=None):
    """Initialize random parameters."""
    if seed is not None:
        qml.numpy.random.seed(seed)
    # Shape: (layers, qubits, 2 params per qubit)
    return qml.numpy.random.random((num_layers, num_qubits, 2)) * 2 * qml.numpy.pi
