import pennylane as qml
try:
    from pennylane import QubitDevice
except ImportError:
    from pennylane.devices import QubitDevice
from pennylane import DeviceError
import numpy as np
import quantum_core  # This is our Rust binding

class RustDensityMatrixDevice(QubitDevice):
    """
    PennyLane device backed by the Rust QuantumSimulator.
    Supports density matrix evolution with accurate noise modeling.
    """
    name = "Rust Density Matrix Device"
    short_name = "rust.density_matrix"
    pennylane_requires = ">=0.30.0"
    version = "0.1.0"
    author = "Surya"

    operations = {
        "PauliX", "PauliY", "PauliZ", "Hadamard", "CNOT", "RX", "RY", "RZ",
        "DDSequence" # Custom operation for DD
    }
    observables = {"PauliX", "PauliY", "PauliZ", "Hadamard", "Identity", "Hermitian"}

    def __init__(self, wires, shots=None, noise_type="amplitude_damping", noise_gamma=0.0):
        # Validate noise parameters
        valid_noise_types = ["amplitude_damping", "phase_damping", "depolarizing", "composite"]
        if noise_type not in valid_noise_types:
            raise ValueError(f"Invalid noise_type '{noise_type}'. Must be one of {valid_noise_types}")
        
        if not 0 <= noise_gamma <= 1:
            raise ValueError(f"noise_gamma must be in [0, 1], got {noise_gamma}")
        
        super().__init__(wires=wires, shots=shots)
        self.num_qubits = len(self.wires)
        self.noise_type = noise_type
        self.noise_gamma = noise_gamma
        
        # Initialize Rust simulator
        self._sim = quantum_core.QuantumSimulator(self.num_qubits)

    def apply(self, operations, **kwargs):
        self._sim.reset()
        
        # Process operations
        for op in operations:
            wires = op.wires.tolist()
            params = op.parameters
            
            if op.name == "DDSequence":
                # Apply DD protection (low noise)
                # For DD, we want to apply REDUCED noise of the selected type
                # Standard DD efficiency is ~80% reduction (factor 0.2)
                protected_gamma = self.noise_gamma * 0.2
                
                for w in wires:
                    self._apply_noise_to_wire(w, protected_gamma)
            else:
                # Apply gate
                self._sim.apply_gate(op.name, wires, params)
                
                # Apply idle noise (high noise) to active wires
                for w in wires:
                    self._apply_noise_to_wire(w, self.noise_gamma)

    def _apply_noise_to_wire(self, wire, gamma):
        """Apply the configured noise type to a specific wire with strength gamma"""
        if gamma <= 0.0:
            return

        if self.noise_type == "amplitude_damping":
            self._sim.apply_amplitude_damping(wire, gamma)
        elif self.noise_type == "phase_damping":
            self._sim.apply_phase_damping(wire, gamma)
        elif self.noise_type == "depolarizing":
            self._sim.apply_depolarizing(wire, gamma)
        elif self.noise_type == "composite":
            # Composite: Apply T1 then T2 then Depolarizing
            # We split the total gamma among them or apply consistent physical model?
            # Standard model: T1 and T2 happen simultaneously.
            # Here we apply them sequentially as an approximation.
            # Using same gamma for all implies severe noise.
            # Usually T2 <= 2*T1.  Let's assume gamma governs T1, and T2/Depol scale with it.
            
            # 1. Amplitude Damping (T1)
            self._sim.apply_amplitude_damping(wire, gamma)
            
            # 2. Phase Damping (T2) - typically smaller or equal
            self._sim.apply_phase_damping(wire, gamma * 0.5)
            
            # 3. Depolarizing - typically smaller
            self._sim.apply_depolarizing(wire, gamma * 0.1)
        else:
            # Default to Amplitude Damping if unknown
            self._sim.apply_amplitude_damping(wire, gamma)
    def expval(self, observable, shot_range=None, bin_size=None):
        """
        Compute expectation value <ψ|O|ψ> for observable O.
        For density matrix: <O> = Tr(ρ O)
        """
        # For single-qubit Pauli observables, compute directly from density matrix
        if hasattr(observable, 'name'):
            obs_name = observable.name
            obs_wires = observable.wires.tolist() if hasattr(observable.wires, 'tolist') else list(observable.wires)
            
            # For single-qubit Pauli observables
            if len(obs_wires) == 1 and obs_name in ['PauliX', 'PauliY', 'PauliZ']:
                wire = obs_wires[0]
                
                # Get full density matrix
                real_parts, imag_parts = self._sim.get_density_matrix()
                dim = 2 ** self.num_qubits
                rho = np.array(real_parts).reshape(dim, dim) + 1j * np.array(imag_parts).reshape(dim, dim)
                
                # For single qubit system, compute directly
                if self.num_qubits == 1:
                    if obs_name == 'PauliZ':
                        return np.real(rho[0, 0] - rho[1, 1])
                    elif obs_name == 'PauliX':
                        return 2 * np.real(rho[0, 1])
                    elif obs_name == 'PauliY':
                        return 2 * np.imag(rho[0, 1])
                else:
                    # Multi-qubit system: compute marginal density matrix for target wire
                    rho_marginal = self._marginal_density_matrix(rho, wire)
                    
                    if obs_name == 'PauliZ':
                        return np.real(rho_marginal[0, 0] - rho_marginal[1, 1])
                    elif obs_name == 'PauliX':
                        return 2 * np.real(rho_marginal[0, 1])
                    elif obs_name == 'PauliY':
                        return 2 * np.imag(rho_marginal[0, 1])
        # Fallback to parent class implementation for complex observables        
        return super().expval(observable, shot_range, bin_size)

    def _marginal_density_matrix(self, rho, target_wire):
        """
        Compute marginal density matrix for a single wire by tracing out all others.
        
        Args:
            rho: Full density matrix (2^N × 2^N)
            target_wire: Wire to keep (0-indexed)
            
        Returns:
            2×2 marginal density matrix for target wire
        """
        n = self.num_qubits
        dim = 2 ** n
        rho_marginal = np.zeros((2, 2), dtype=complex)
        
        # Trace out all qubits except target_wire
        # For each basis state |i⟩ of target wire (|0⟩ or |1⟩)
        # and |j⟩ of target wire
        for i in range(2):
            for j in range(2):
                # Sum over all basis states of other qubits
                for k in range(2 ** (n - 1)):
                    # Construct full basis state indices
                    # Insert bit i at position target_wire
                    idx_i = self._insert_bit_at_position(k, i, target_wire, n)
                    idx_j = self._insert_bit_at_position(k, j, target_wire, n)
                    rho_marginal[i, j] += rho[idx_i, idx_j]
        
        return rho_marginal
    
    def _insert_bit_at_position(self, base_num, bit, position, total_bits):
        """
        Insert a bit at a specific position in a number's binary representation.
        
        Example: base_num=5 (101), bit=1, position=1, total_bits=4
        Result: 1011 (11 in decimal)
        """
        # Split base_num into high and low parts around insertion point
        low_bits = base_num & ((1 << (total_bits - position - 1)) - 1)
        high_bits = base_num >> (total_bits - position - 1)
        
        # Construct result: high_bits | bit | low_bits
        result = (high_bits << (total_bits - position)) | (bit << (total_bits - position - 1)) | low_bits
        return result

    def probability(self, wires=None, shot_range=None, bin_size=None):
        probs = self._sim.probabilities()
        return self.marginal_prob(np.array(probs), wires)

    def generate_samples(self):
        if self.shots is None:
            raise DeviceError("Shots must be specified for sampling")
            
        # Get samples from Rust
        # Rust returns Vec<Vec<usize>> (list of bitstrings)
        samples = self._sim.measure_shots(self.shots)
        return np.array(samples)
