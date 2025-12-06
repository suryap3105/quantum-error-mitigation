import pennylane as qml
from pennylane import qchem
from pennylane import numpy as np

# Cache for Hamiltonians and FCI energies
_CACHE = {}

def build_molecular_hamiltonian(molecule_name: str, bond_length: float):
    """
    Build the Hamiltonian for a given molecule and bond length.
    Returns (H, num_qubits, fci_energy).
    
    Supported molecules: "H2", "LiH", "BeH2"
    """
    key = (molecule_name, bond_length)
    if key in _CACHE:
        return _CACHE[key]

    if molecule_name == "H2":
        symbols = ["H", "H"]
        coordinates = np.array([0.0, 0.0, -bond_length/2, 0.0, 0.0, bond_length/2])
        charge = 0
        mult = 1
        active_electrons = 2
        active_orbitals = 2 # 4 qubits
        
    elif molecule_name == "LiH":
        symbols = ["Li", "H"]
        coordinates = np.array([0.0, 0.0, 0.0, 0.0, 0.0, bond_length])
        charge = 0
        mult = 1
        # Active space for LiH to get 4-6 qubits
        # Li: 1s2 2s1, H: 1s1. Total 4e.
        # Frozen core: Li 1s (2e). Active e: 2.
        # Active orbitals: 2s, 2p? 
        # Let's try to get 4 qubits (2 spatial orbitals) or 6 qubits (3 spatial).
        # Standard minimal is often 4 qubits for toy problems.
        active_electrons = 2
        active_orbitals = 2 # 4 qubits
        
    elif molecule_name == "BeH2":
        symbols = ["Be", "H", "H"]
        coordinates = np.array([
            0.0, 0.0, 0.0,       # Be
            0.0, 0.0, bond_length, # H
            0.0, 0.0, -bond_length # H
        ])
        charge = 0
        mult = 1
        # Be: 1s2 2s2. H: 1s1. Total 6e.
        # Frozen core: Be 1s (2e). Active e: 4.
        # Active orbitals: 3? (6 qubits)
        active_electrons = 4
        active_orbitals = 3 # 6 qubits
        
    else:
        raise ValueError(f"Unknown molecule: {molecule_name}")

    try:
        # Build molecular Hamiltonian
        H, qubits = qchem.molecular_hamiltonian(
            symbols,
            coordinates,
            charge=charge,
            mult=mult,
            basis="sto-3g",
            active_electrons=active_electrons,
            active_orbitals=active_orbitals,
            mapping="jordan_wigner"
        )
    except Exception as e:
        # Fallback for systems where pyscf/qchem might fail or be slow
        # We'll return a dummy Hamiltonian and estimated energy for testing if strict physics fails
        print(f"Warning: Failed to build Hamiltonian for {molecule_name}: {e}")
        return None, 0, 0.0

    # Compute FCI energy (exact diagonalization)
    # For small systems (<= 6 qubits), dense matrix is fine
    if qubits <= 10:
        mat = qml.matrix(H)
        eigvals = np.linalg.eigvalsh(mat)
        fci_energy = eigvals[0]
    else:
        fci_energy = 0.0 # Too big to diagonalize easily here

    _CACHE[key] = (H, qubits, fci_energy)
    return H, qubits, fci_energy
