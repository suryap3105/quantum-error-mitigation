import pennylane as qml
from pennylane import qchem
from pennylane import numpy as np

# Cache for Hamiltonians and FCI energies
_CACHE = {}

def build_h2_hamiltonian(bond_length: float):
    """
    Build the H2 Hamiltonian for a given bond length.
    Returns (H, num_qubits, fci_energy).
    """
    if bond_length in _CACHE:
        return _CACHE[bond_length]

    symbols = ["H", "H"]
    coordinates = np.array([0.0, 0.0, -bond_length/2, 0.0, 0.0, bond_length/2])

    # Build molecular Hamiltonian
    H, qubits = qchem.molecular_hamiltonian(
        symbols,
        coordinates,
        charge=0,
        mult=1,
        basis="sto-3g",
        mapping="jordan_wigner"
    )

    # Compute FCI energy (exact diagonalization)
    # For 4 qubits, we can use qml.matrix
    mat = qml.matrix(H)
    # qml.matrix returns a dense matrix by default in recent versions, or we can ensure it
    eigvals = np.linalg.eigvalsh(mat)
    fci_energy = eigvals[0]

    _CACHE[bond_length] = (H, qubits, fci_energy)
    return H, qubits, fci_energy
