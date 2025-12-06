use pyo3::prelude::*;
use rust_sim::QuantumSimulator as RustSimulator;

/// Python-exposed quantum simulator class
#[pyclass(name = "QuantumSimulator")]
pub struct PyQuantumSimulator {
    inner: RustSimulator,
}

#[pymethods]
impl PyQuantumSimulator {
    #[new]
    fn new(num_qubits: usize) -> Self {
        PyQuantumSimulator {
            inner: RustSimulator::new(num_qubits),
        }
    }

    /// Reset to |0...0⟩ state
    fn reset(&mut self) {
        self.inner.reset();
    }

    /// Apply a quantum gate
    fn apply_gate(
        &mut self,
        gate_name: &str,
        wires: Vec<usize>,
        params: Vec<f64>,
    ) -> PyResult<()> {
        self.inner
            .apply_gate(gate_name, &wires, &params)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }

    /// Apply idle noise to a qubit
    fn apply_idle_noise(&mut self, wire: usize, protected: bool) {
        self.inner.apply_noise(wire, protected);
    }

    /// Apply amplitude damping (T1) noise
    fn apply_amplitude_damping(&mut self, wire: usize, gamma: f64) {
        self.inner.apply_amplitude_damping(wire, gamma);
    }

    /// Apply phase damping (T2) noise
    fn apply_phase_damping(&mut self, wire: usize, lambda: f64) {
        self.inner.apply_phase_damping(wire, lambda);
    }

    /// Apply depolarizing noise
    fn apply_depolarizing(&mut self, wire: usize, p: f64) {
        self.inner.apply_depolarizing(wire, p);
    }

    /// Measure all qubits once and return bitstring
    fn measure(&self) -> PyResult<Vec<usize>> {
        Ok(self.inner.measure())
    }

    /// Measure multiple shots
    fn measure_shots(&self, n_shots: usize) -> PyResult<Vec<Vec<usize>>> {
        Ok(self.inner.measure_shots(n_shots))
    }

    /// Get probability distribution from density matrix diagonal
    fn probabilities(&self) -> PyResult<Vec<f64>> {
        Ok(self.inner.get_state().probabilities())
    }

    /// Get trace and purity
    fn get_metrics(&self) -> PyResult<(f64, f64)> {
        Ok(self.inner.get_metrics())
    }

    /// Get density matrix as (real_parts, imag_parts)
    fn get_density_matrix(&self) -> PyResult<(Vec<f64>, Vec<f64>)> {
        Ok(self.inner.get_density_matrix())
    }

    /// Get number of qubits
    #[getter]
    fn num_qubits(&self) -> usize {
        self.inner.get_state().num_qubits
    }
}

/// Python module definition
#[pymodule]
fn quantum_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyQuantumSimulator>()?;
    Ok(())
}
