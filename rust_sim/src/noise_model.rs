use nalgebra::DMatrix;
use num_complex::Complex;
use crate::density_matrix::DensityMatrix;

/// Amplitude damping channel - models energy relaxation (T1 decay)
/// Describes decay from |1⟩ to |0⟩ with probability gamma
pub fn amplitude_damping_kraus(gamma: f64) -> Vec<DMatrix<Complex<f64>>> {
    let k0 = DMatrix::from_row_slice(2, 2, &[
        Complex::new(1.0, 0.0), 
        Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), 
        Complex::new((1.0 - gamma).sqrt(), 0.0),
    ]);
    
    let k1 = DMatrix::from_row_slice(2, 2, &[
        Complex::new(0.0, 0.0), 
        Complex::new(gamma.sqrt(), 0.0),
        Complex::new(0.0, 0.0), 
        Complex::new(0.0, 0.0),
    ]);
    
    vec![k0, k1]
}

/// Dephasing channel - models loss of quantum coherence without energy loss (T2 decay)
pub fn dephasing_kraus(lambda: f64) -> Vec<DMatrix<Complex<f64>>> {
    let k0 = DMatrix::from_row_slice(2, 2, &[
        Complex::new((1.0 - lambda).sqrt(), 0.0), 
        Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), 
        Complex::new((1.0 - lambda).sqrt(), 0.0),
    ]);
    
    let k1 = DMatrix::from_row_slice(2, 2, &[
        Complex::new(lambda.sqrt(), 0.0), 
        Complex::new(0.0, 0.0),
        Complex::new(0.0, 0.0), 
        Complex::new(-lambda.sqrt(), 0.0),
    ]);
    
    vec![k0, k1]
}

/// Depolarizing channel - models symmetric contraction of the Bloch sphere
/// rho -> (1-p)rho + p I/2
pub fn depolarizing_kraus(p: f64) -> Vec<DMatrix<Complex<f64>>> {
    let i = Complex::new(0.0, 1.0);
    let one = Complex::new(1.0, 0.0);
    let zero = Complex::new(0.0, 0.0);
    
    let sqrt_1_3p_4 = (1.0 - 3.0 * p / 4.0).sqrt();
    let sqrt_p_4 = (p / 4.0).sqrt();
    
    // K0 = sqrt(1-3p/4) * I
    let k0 = DMatrix::from_row_slice(2, 2, &[
        one * sqrt_1_3p_4, zero,
        zero, one * sqrt_1_3p_4
    ]);
    
    // K1 = sqrt(p/4) * X
    let k1 = DMatrix::from_row_slice(2, 2, &[
        zero, one * sqrt_p_4,
        one * sqrt_p_4, zero
    ]);
    
    // K2 = sqrt(p/4) * Y
    let k2 = DMatrix::from_row_slice(2, 2, &[
        zero, -i * sqrt_p_4,
        i * sqrt_p_4, zero
    ]);
    
    // K3 = sqrt(p/4) * Z
    let k3 = DMatrix::from_row_slice(2, 2, &[
        one * sqrt_p_4, zero,
        zero, -one * sqrt_p_4
    ]);
    
    vec![k0, k1, k2, k3]
}

/// Apply depolarizing noise to a specific qubit wire
pub fn apply_depolarizing(
    rho: &mut DensityMatrix,
    wire: usize,
    p: f64,
) {
    if p <= 0.0 {
        return; // No noise
    }
    
    let single_qubit_kraus = depolarizing_kraus(p);
    let full_kraus = expand_kraus_to_full_system(&single_qubit_kraus, wire, rho.num_qubits);
    rho.apply_kraus(&full_kraus);
}

/// Apply amplitude damping noise to a specific qubit wire
pub fn apply_amplitude_damping(
    rho: &mut DensityMatrix,
    wire: usize,
    gamma: f64,
) {
    if gamma <= 0.0 {
        return; // No noise
    }
    
    let single_qubit_kraus = amplitude_damping_kraus(gamma);
    let full_kraus = expand_kraus_to_full_system(&single_qubit_kraus, wire, rho.num_qubits);
    rho.apply_kraus(&full_kraus);
}

/// Apply dephasing noise to a specific qubit wire
pub fn apply_dephasing(
    rho: &mut DensityMatrix,
    wire: usize,
    lambda: f64,
) {
    if lambda <= 0.0 {
        return; // No noise
    }
    
    let single_qubit_kraus = dephasing_kraus(lambda);
    let full_kraus = expand_kraus_to_full_system(&single_qubit_kraus, wire, rho.num_qubits);
    rho.apply_kraus(&full_kraus);
}

/// Apply idle noise to a qubit - combines amplitude damping and dephasing
/// Protected flag determines noise strength:
/// - protected = true: gamma = 0.001 (DD-protected, 100x reduction)
/// - protected = false: gamma = 0.05 (unprotected idle)
pub fn apply_idle_noise(
    rho: &mut DensityMatrix,
    wire: usize,
    protected: bool,
) {
    // Realistic DD Efficiency: 80% noise suppression (Factor of 5)
    // This models imperfect pulses and finite correlation times.
    // Ideally, T2_eff = T2 * 5.
    let suppression_factor = if protected { 0.2 } else { 1.0 };
    
    let (gamma, lambda) = (
        0.05 * suppression_factor,  // T1 noise
        0.02 * suppression_factor   // T2 noise
    );
    
    apply_amplitude_damping(rho, wire, gamma);
    apply_dephasing(rho, wire, lambda);
}

/// Expand single-qubit Kraus operators to full multi-qubit system
fn expand_kraus_to_full_system(
    single_qubit_kraus: &[DMatrix<Complex<f64>>],
    target_wire: usize,
    num_qubits: usize,
) -> Vec<DMatrix<Complex<f64>>> {
    use crate::gates::{kron, identity};
    
    single_qubit_kraus.iter().map(|k| {
        let mut result = if target_wire == 0 {
            k.clone()
        } else {
            identity()
        };
        
        for i in 1..num_qubits {
            let next = if i == target_wire {
                k
            } else {
                &identity()
            };
            result = kron(&result, next);
        }
        
        result
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_kraus_completeness() {
        let kraus = amplitude_damping_kraus(0.3);
        let mut sum = DMatrix::zeros(2, 2);
        
        for k in &kraus {
            sum += k.adjoint() * k;
        }
        
        // Should equal identity
        assert_relative_eq!(sum[(0, 0)].re, 1.0, epsilon = 1e-10);
        assert_relative_eq!(sum[(1, 1)].re, 1.0, epsilon = 1e-10);
        assert_relative_eq!(sum[(0, 1)].norm(), 0.0, epsilon = 1e-10);
    }

    #[test]
    fn test_amplitude_damping_preserves_trace() {
        let mut rho = DensityMatrix::new(1);
        let trace_before = rho.trace().re;
        
        apply_amplitude_damping(&mut rho, 0, 0.3);
        let trace_after = rho.trace().re;
        
        assert_relative_eq!(trace_before, trace_after, epsilon = 1e-10);
    }
}
