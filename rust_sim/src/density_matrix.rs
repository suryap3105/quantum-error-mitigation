use nalgebra::{DMatrix, ComplexField};
use num_complex::Complex;
use std::f64::consts::PI;

/// Represents a quantum density matrix for an N-qubit system
#[derive(Clone, Debug)]
pub struct DensityMatrix {
    pub matrix: DMatrix<Complex<f64>>,
    pub num_qubits: usize,
}

impl DensityMatrix {
    /// Create a new density matrix in the |0...0⟩ state
    pub fn new(num_qubits: usize) -> Self {
        let dim = 1 << num_qubits; // 2^num_qubits
        let mut matrix = DMatrix::zeros(dim, dim);
        matrix[(0, 0)] = Complex::new(1.0, 0.0); // |0⟩⟨0|
        
        DensityMatrix {
            matrix,
            num_qubits,
        }
    }

    /// Calculate the trace of the density matrix
    pub fn trace(&self) -> Complex<f64> {
        self.matrix.trace()
    }

    /// Calculate the purity Tr(ρ²) - equals 1 for pure states
    pub fn purity(&self) -> f64 {
        let rho_squared = &self.matrix * &self.matrix;
        rho_squared.trace().re
    }

    /// Get the dimension of the Hilbert space
    pub fn dim(&self) -> usize {
        1 << self.num_qubits
    }

    /// Apply a unitary operator to the density matrix: ρ → U ρ U†
    pub fn apply_unitary(&mut self, unitary: &DMatrix<Complex<f64>>) {
        let rho_new = unitary * &self.matrix * unitary.adjoint();
        self.matrix = rho_new;
    }

    /// Apply a Kraus channel: ρ → Σᵢ Kᵢ ρ Kᵢ†
    pub fn apply_kraus(&mut self, kraus_ops: &[DMatrix<Complex<f64>>]) {
        let mut rho_new = DMatrix::zeros(self.dim(), self.dim());
        
        for k in kraus_ops {
            rho_new += k * &self.matrix * k.adjoint();
        }
        
        self.matrix = rho_new;
    }

    /// Get probability distribution from diagonal (computational basis)
    pub fn probabilities(&self) -> Vec<f64> {
        (0..self.dim())
            .map(|i| self.matrix[(i, i)].re.max(0.0))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_initial_state() {
        let rho = DensityMatrix::new(2);
        assert_eq!(rho.dim(), 4);
        assert_relative_eq!(rho.trace().re, 1.0, epsilon = 1e-10);
        assert_relative_eq!(rho.purity(), 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_trace_preservation() {
        let mut rho = DensityMatrix::new(1);
        let hadamard = DMatrix::from_row_slice(2, 2, &[
            Complex::new(1.0/2.0_f64.sqrt(), 0.0), Complex::new(1.0/2.0_f64.sqrt(), 0.0),
            Complex::new(1.0/2.0_f64.sqrt(), 0.0), Complex::new(-1.0/2.0_f64.sqrt(), 0.0),
        ]);
        
        rho.apply_unitary(&hadamard);
        assert_relative_eq!(rho.trace().re, 1.0, epsilon = 1e-10);
    }
}
