import csv
import numpy as np
from pathlib import Path
from vqe_qem.strategies import Strategy
from vqe_qem.h2_system import build_h2_hamiltonian
from vqe_qem.sampling_eval import evaluate_point

# Experiment Configuration
BOND_LENGTHS = [0.5, 0.74, 1.0, 1.5, 2.0, 2.5]
GAMMAS = [0.025, 0.08, 0.135]
STRATEGIES = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
RESULTS_FILE = "results/h2_vqe_experiments.csv"

def run_experiments():
    Path("results").mkdir(exist_ok=True)
    
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "R", "gamma", "strategy", "mean_energy", "ci_lower", "ci_upper",
            "fci_energy", "mean_abs_error_mHa", "discard_rate", "sigma"
        ])
        writer.writeheader()
        
        total = len(BOND_LENGTHS) * len(GAMMAS) * len(STRATEGIES)
        count = 0
        
        print(f"Starting H2 Grid Search ({total} points)...")
        
        for R in BOND_LENGTHS:
            # Get FCI energy for this bond length
            _, _, fci_energy = build_h2_hamiltonian(R)
            
            for gamma in GAMMAS:
                for strategy in STRATEGIES:
                    count += 1
                    print(f"[{count}/{total}] R={R}, gamma={gamma}, strategy={strategy.value}...", end="", flush=True)
                    
                    # Evaluate using Phenomenological Model
                    stats = evaluate_point(R, gamma, strategy, fci_energy)
                    
                    # Compute error
                    error_mHa = abs(stats["mean_energy"] - fci_energy) * 1000.0
                    
                    writer.writerow({
                        "R": R,
                        "gamma": gamma,
                        "strategy": strategy.value,
                        "mean_energy": stats["mean_energy"],
                        "ci_lower": stats["ci_lower"],
                        "ci_upper": stats["ci_upper"],
                        "fci_energy": fci_energy,
                        "mean_abs_error_mHa": error_mHa,
                        "discard_rate": stats["discard_rate"],
                        "sigma": stats["sigma"]
                    })
                    
                    print(f" Error={error_mHa:.1f} mHa, Discard={stats['discard_rate']:.1%}")

    print(f"Experiments complete. Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_experiments()
