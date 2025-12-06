import csv
import numpy as np
from pathlib import Path
from vqe_qem.strategies import Strategy, NoiseType
from vqe_qem.h2_system import build_h2_hamiltonian
from vqe_qem.sampling_eval import evaluate_point
import torch
from rl_agent.policy import PolicyNet

# Experiment Configuration
BOND_LENGTHS = [0.5, 0.74, 1.0, 1.5, 2.0, 2.5]
GAMMAS = [0.025, 0.08, 0.135]
STRATEGIES = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
RESULTS_FILE = "results/h2_vqe_experiments.csv"

def run_experiments():
    Path("results").mkdir(exist_ok=True)
    
    # Load RL Policy
    policy = PolicyNet(input_dim=3, output_dim=4) # Updated input dim
    try:
        policy.load_state_dict(torch.load("results/rl_policy.pth"))
        policy.eval()
        print("Loaded RL policy.")
    except FileNotFoundError:
        print("Warning: RL policy not found. RL strategy will use random actions.")

    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "R", "gamma", "strategy", "mean_energy", "ci_lower", "ci_upper",
            "fci_energy", "mean_abs_error_mHa", "discard_rate", "sigma", "noise_type"
        ])
        writer.writeheader()
        
        # Add RL to strategies
        strategies_to_run = STRATEGIES + [Strategy.RL]
        
        # Use Composite Noise for main results as requested ("hardware presets")
        # We could loop over all types, but let's stick to the most realistic one for the main plot first.
        noise_type = NoiseType.COMPOSITE
        noise_idx = 3 # Index for Composite in env
        
        total = len(BOND_LENGTHS) * len(GAMMAS) * len(strategies_to_run)
        count = 0
        
        print(f"Starting H2 Grid Search ({total} points) with {noise_type.value} noise...")
        
        for R in BOND_LENGTHS:
            # Get FCI energy for this bond length
            _, _, fci_energy = build_h2_hamiltonian(R)
            
            for gamma in GAMMAS:
                for strategy in strategies_to_run:
                    count += 1
                    print(f"[{count}/{total}] R={R}, gamma={gamma}, strategy={strategy.value}...", end="", flush=True)
                    
                    if strategy == Strategy.RL:
                        # RL Agent Decision
                        # State: [gamma, R, noise_idx]
                        state = torch.FloatTensor([gamma, R, noise_idx])
                        with torch.no_grad():
                            dist = policy(state)
                            action_idx = dist.sample().item() # Stochastic sampling
                        
                        # Map action to strategy
                        # 0: Baseline, 1: DD, 2: Sym, 3: Hybrid
                        rl_strategies = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
                        chosen_strategy = rl_strategies[action_idx]
                        
                        # Evaluate using chosen strategy
                        stats = evaluate_point(R, gamma, chosen_strategy, fci_energy, noise_type)
                        
                        # Note: We record it as "rl" strategy in CSV, but stats come from the chosen one.
                    else:
                        # Evaluate using Phenomenological Model
                        stats = evaluate_point(R, gamma, strategy, fci_energy, noise_type)
                    
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
                        "sigma": stats["sigma"],
                        "noise_type": noise_type.value
                    })
                    
                    print(f" Error={error_mHa:.1f} mHa, Discard={stats['discard_rate']:.1%}")

    print(f"Experiments complete. Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_experiments()
