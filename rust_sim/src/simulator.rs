use nalgebra::DMatrix;
use num_complex::Complex;
use crate::density_matrix::DensityMatrix;
use crate::gates::*;
use crate::noise_model::*;
use rand::Rng;
use rand::distributions::WeightedIndex;
use rand::prelude::*;

/// Main quantum simulator using density matrix formalism
pub struct QuantumSimulator {
    state: DensityMatrix,
    num_qubits: usize,
}

impl QuantumSimulator {
    /// Create a new simulator with N qubits in |0...0⟩ state
    pub fn new(num_qubits: usize) -> Self {
        QuantumSimulator {
            state: DensityMatrix::new(num_qubits),
            num_qubits,
        }
    }

    /// Reset to |0...0⟩ state
    pub fn reset(&mut self) {
        self.state = DensityMatrix::new(self.num_qubits);
    }

    /// Get current density matrix
    pub fn get_state(&self) -> &DensityMatrix {
        &self.state
    }

    /// Apply a quantum gate
    pub fn apply_gate(
        &mut self,
        gate_name: &str,
        wires: &[usize],
        params: &[f64],
    ) -> Result<(), String> {
        let unitary = match gate_name {
            "PauliX" | "X" => {
                if wires.len() != 1 {
                    return Err("PauliX requires exactly 1 wire".to_string());
                }
                build_single_qubit_unitary(&pauli_x(), wires[0], self.num_qubits)
            },
            "PauliY" | "Y" => {
                if wires.len() != 1 {
                    return Err("PauliY requires exactly 1 wire".to_string());
                }
                build_single_qubit_unitary(&pauli_y(), wires[0], self.num_qubits)
            },
            "PauliZ" | "Z" => {
                if wires.len() != 1 {
                    return Err("PauliZ requires exactly 1 wire".to_string());
                }
                build_single_qubit_unitary(&pauli_z(), wires[0], self.num_qubits)
            },
            "Hadamard" | "H" => {
                if wires.len() != 1 {
                    return Err("Hadamard requires exactly 1 wire".to_string());
                }
                build_single_qubit_unitary(&hadamard(), wires[0], self.num_qubits)
            },
            "RX" => {
                if wires.len() != 1 || params.is_empty() {
                    return Err("RX requires 1 wire and 1 parameter".to_string());
                }
                build_single_qubit_unitary(&rx(params[0]), wires[0], self.num_qubits)
            },
            "RY" => {
                if wires.len() != 1 || params.is_empty() {
                    return Err("RY requires 1 wire and 1 parameter".to_string());
                }
                build_single_qubit_unitary(&ry(params[0]), wires[0], self.num_qubits)
            },
            "RZ" => {
                if wires.len() != 1 || params.is_empty() {
                    return Err("RZ requires 1 wire and 1 parameter".to_string());
                }
                build_single_qubit_unitary(&rz(params[0]), wires[0], self.num_qubits)
            },
            "CNOT" | "CX" => {
                if wires.len() != 2 {
                    return Err("CNOT requires exactly 2 wires".to_string());
                }
                build_cnot_unitary(wires[0], wires[1], self.num_qubits)
            },
            _ => return Err(format!("Unknown gate: {}", gate_name)),
        };

        self.state.apply_unitary(&unitary);
        Ok(())
    }

    /// Apply idle noise to a specific qubit
    pub fn apply_noise(&mut self, wire: usize, protected: bool) {
        if wire >= self.num_qubits {
            return;
        }
        apply_idle_noise(&mut self.state, wire, protected);
    }

    /// Apply phase damping (T2) noise
    pub fn apply_phase_damping(&mut self, wire: usize, lambda: f64) {
        if wire >= self.num_qubits {
            return;
        }
        apply_dephasing(&mut self.state, wire, lambda);
    }

    /// Apply depolarizing noise
    pub fn apply_depolarizing(&mut self, wire: usize, p: f64) {
        if wire >= self.num_qubits {
            return;
        }
        apply_depolarizing(&mut self.state, wire, p);
    }

    /// Measure all qubits and return single bitstring
    pub fn measure(&self) -> Vec<usize> {
        let probs = self.state.probabilities();
        let mut rng = thread_rng();
        
        // Sample from probability distribution
        let dist = WeightedIndex::new(&probs).unwrap();
        let outcome = dist.sample(&mut rng);
        
        // Convert integer to bitstring
        (0..self.num_qubits)
            .map(|i| (outcome >> (self.num_qubits - 1 - i)) & 1)
            .collect()
    }

    /// Measure N shots and return all bitstrings
    pub fn measure_shots(&self, n_shots: usize) -> Vec<Vec<usize>> {
        (0..n_shots).map(|_| self.measure()).collect()
    }

    /// Calculate expectation value of an observable (Pauli string)
    pub fn expectation_value(&self, observable: &DMatrix<Complex<f64>>) -> f64 {
        let result = observable * &self.state.matrix;
        result.trace().re
    }

    /// Get trace and purity metrics
    pub fn get_metrics(&self) -> (f64, f64) {
        (self.state.trace().re, self.state.purity())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_simulator_creation() {
        let sim = QuantumSimulator::new(2);
        let (trace, purity) = sim.get_metrics();
        assert_relative_eq!(trace, 1.0, epsilon = 1e-10);
        assert_relative_eq!(purity, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_gate_application() {
        let mut sim = QuantumSimulator::new(1);
        sim.apply_gate("PauliX", &[0], &[]).unwrap();
        
        // After X gate on |0⟩, should be in |1⟩
        let probs = sim.get_state().probabilities();
        assert_relative_eq!(probs[0], 0.0, epsilon = 1e-10);
        assert_relative_eq!(probs[1], 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_hadamard_superposition() {
        let mut sim = QuantumSimulator::new(1);
        sim.apply_gate("Hadamard", &[0], &[]).unwrap();
        
        let probs = sim.get_state().probabilities();
        assert_relative_eq!(probs[0], 0.5, epsilon = 1e-10);
        assert_relative_eq!(probs[1], 0.5, epsilon = 1e-10);
    }
}
