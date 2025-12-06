use nalgebra::DMatrix;
use num_complex::Complex;
use std::f64::consts::PI;

/// Pauli X gate matrix
pub fn pauli_x() -> DMatrix<Complex<f64>> {
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(0.0, 0.0), Complex::new(1.0, 0.0),
        Complex::new(1.0, 0.0), Complex::new(0.0, 0.0),
    ])
}

/// Pauli Y gate matrix
pub fn pauli_y() -> DMatrix<Complex<f64>> {
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(0.0, 0.0), Complex::new(0.0, -1.0),
        Complex::new(0.0, 1.0), Complex::new(0.0, 0.0),
    ])
}

/// Pauli Z gate matrix
pub fn pauli_z() -> DMatrix<Complex<f64>> {
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(1.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(-1.0, 0.0),
    ])
}

/// Hadamard gate matrix
pub fn hadamard() -> DMatrix<Complex<f64>> {
    let factor = 1.0 / 2.0_f64.sqrt();
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(factor, 0.0), Complex::new(factor, 0.0),
        Complex::new(factor, 0.0), Complex::new(-factor, 0.0),
    ])
}

/// Identity gate matrix
pub fn identity() -> DMatrix<Complex<f64>> {
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(1.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(1.0, 0.0),
    ])
}

/// RX rotation gate (rotation around X axis)
pub fn rx(theta: f64) -> DMatrix<Complex<f64>> {
    let c = (theta / 2.0).cos();
    let s = (theta / 2.0).sin();
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(c, 0.0), Complex::new(0.0, -s),
        Complex::new(0.0, -s), Complex::new(c, 0.0),
    ])
}

/// RY rotation gate (rotation around Y axis)
pub fn ry(theta: f64) -> DMatrix<Complex<f64>> {
    let c = (theta / 2.0).cos();
    let s = (theta / 2.0).sin();
    DMatrix::from_row_slice(2, 2, &[
        Complex::new(c, 0.0), Complex::new(-s, 0.0),
        Complex::new(s, 0.0), Complex::new(c, 0.0),
    ])
}

/// RZ rotation gate (rotation around Z axis)
pub fn rz(theta: f64) -> DMatrix<Complex<f64>> {
    let exp_neg = Complex::new(0.0, -theta / 2.0).exp();
    let exp_pos = Complex::new(0.0, theta / 2.0).exp();
    DMatrix::from_row_slice(2, 2, &[
        exp_neg, Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), exp_pos,
    ])
}

/// CNOT gate for 2-qubit system (control=0, target=1)
/// Basis ordering: |00⟩, |01⟩, |10⟩, |11⟩
pub fn cnot() -> DMatrix<Complex<f64>> {
    DMatrix::from_row_slice(4, 4, &[
        Complex::new(1.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(1.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(1.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(1.0, 0.0), Complex::new(0.0, 0.0),
    ])
}

/// CZ gate for 2-qubit system
pub fn cz() -> DMatrix<Complex<f64>> {
    DMatrix::from_row_slice(4, 4, &[
        Complex::new(1.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(1.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(1.0, 0.0), Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(0.0, 0.0), Complex::new(-1.0, 0.0),
    ])
}

/// Kronecker product of two matrices
pub fn kron(a: &DMatrix<Complex<f64>>, b: &DMatrix<Complex<f64>>) -> DMatrix<Complex<f64>> {
    let (m, n) = (a.nrows(), a.ncols());
    let (p, q) = (b.nrows(), b.ncols());
    
    let mut result = DMatrix::zeros(m * p, n * q);
    
    for i in 0..m {
        for j in 0..n {
            for k in 0..p {
                for l in 0..q {
                    result[(i * p + k, j * q + l)] = a[(i, j)] * b[(k, l)];
                }
            }
        }
    }
    
    result
}

/// Build a multi-qubit unitary by applying single-qubit gate on specified wire
pub fn build_single_qubit_unitary(
    gate: &DMatrix<Complex<f64>>,
    wire: usize,
    num_qubits: usize,
) -> DMatrix<Complex<f64>> {
    let mut result = if wire == 0 {
        gate.clone()
    } else {
        identity()
    };
    
    for i in 1..num_qubits {
        let next = if i == wire {
            gate
        } else {
            &identity()
        };
        result = kron(&result, next);
    }
    
    result
}

/// Build CNOT gate for multi-qubit system
pub fn build_cnot_unitary(
    control: usize,
    target: usize,
    num_qubits: usize,
) -> DMatrix<Complex<f64>> {
    let dim = 1 << num_qubits;
    let mut result = DMatrix::zeros(dim, dim);
    
    for i in 0..dim {
        let control_bit = (i >> (num_qubits - 1 - control)) & 1;
        let target_bit = (i >> (num_qubits - 1 - target)) & 1;
        
        let j = if control_bit == 1 {
            i ^ (1 << (num_qubits - 1 - target))
        } else {
            i
        };
        
        result[(j, i)] = Complex::new(1.0, 0.0);
    }
    
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_pauli_x_squared() {
        let x = pauli_x();
        let x2 = &x * &x;
        let id = identity();
        
        for i in 0..2 {
            for j in 0..2 {
                assert_relative_eq!(x2[(i, j)].re, id[(i, j)].re, epsilon = 1e-10);
                assert_relative_eq!(x2[(i, j)].im, id[(i, j)].im, epsilon = 1e-10);
            }
        }
    }

    #[test]
    fn test_hadamard_creates_superposition() {
        let h = hadamard();
        assert_relative_eq!(h[(0, 0)].re, 1.0 / 2.0_f64.sqrt(), epsilon = 1e-10);
    }
}
