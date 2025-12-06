import csv
import numpy as np
from pathlib import Path
from vqe_qem.strategies import Strategy, NoiseType
from vqe_qem.system_factory import build_molecular_hamiltonian
from vqe_qem.sampling_eval import evaluate_point
import torch
from rl_agent.policy import PolicyNet

# Experiment Configuration
MOLECULES = ["H2", "LiH", "BeH2"]
GAMMAS = [0.025, 0.08, 0.135]
STRATEGIES = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
RESULTS_FILE = "results/paper_results.csv"

def run_experiments():
    Path("results").mkdir(exist_ok=True)
    
    # Load RL Policy
    policy = PolicyNet(input_dim=6, output_dim=4)
    try:
        policy.load_state_dict(torch.load("results/rl_policy.pth"))
        policy.eval()
        print("Loaded RL policy.")
    except FileNotFoundError:
        print("Warning: RL policy not found. RL strategy will use random actions.")

    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "molecule", "R", "gamma", "strategy", "mean_energy", "ci_lower", "ci_upper",
            "fci_energy", "mean_abs_error_mHa", "discard_rate", "sigma", "noise_type", "depth"
        ])
        writer.writeheader()
        
        strategies_to_run = STRATEGIES + [Strategy.RL]
        
        # Use Composite Noise for main results
        noise_type = NoiseType.COMPOSITE
        noise_idx = 3 
        
        print(f"Starting Multi-Molecule Grid Search with {noise_type.value} noise...")
        
        for mol in MOLECULES:
            if mol == "H2":
                bond_lengths = [0.5, 0.74, 1.0, 1.5, 2.0, 2.5]
                depth = 9
            elif mol == "LiH":
                bond_lengths = [1.0, 1.2, 1.4, 1.6, 2.0, 2.5]
                depth = 20
            elif mol == "BeH2":
                bond_lengths = [1.0, 1.3, 1.6, 2.0, 2.5, 3.0]
                depth = 30
            else:
                bond_lengths = [1.0]
                depth = 10

            for R in bond_lengths:
                # Get FCI energy
                _, _, fci_energy = build_molecular_hamiltonian(mol, R)
                
                # Initialize history for RL
                last_error = 0.0
                last_discard = 0.0
                
                for gamma in GAMMAS:
                    for strategy in strategies_to_run:
                        
                        if strategy == Strategy.RL:
                            # RL Agent Decision
                            # State: [gamma, R, noise_idx, last_error, last_discard, depth]
                            state = torch.FloatTensor([gamma, R, float(noise_idx), last_error, last_discard, float(depth)])
                            with torch.no_grad():
                                dist = policy(state)
                                action_idx = dist.sample().item()
                            
                            rl_strategies = [Strategy.BASELINE, Strategy.DD, Strategy.SYM, Strategy.HYBRID]
                            chosen_strategy = rl_strategies[action_idx]
                            
                            # Evaluate
                            stats = evaluate_point(R, gamma, chosen_strategy, fci_energy, noise_type)
                        else:
                            stats = evaluate_point(R, gamma, strategy, fci_energy, noise_type)
                        
                        error_mHa = abs(stats["mean_energy"] - fci_energy) * 1000.0
                        
                        # Update history for next step (approximate, since we loop strategies)
                        # Ideally RL runs in sequence. Here we just use current result as "last" for next gamma?
                        # Or just keep it 0 for independent points.
                        # The user said "Last measured error" is in observation.
                        # For grid search, we can't easily maintain history unless we run episodes.
                        # We'll use 0.0 or the current error as a proxy for "steady state".
                        last_error = error_mHa
                        last_discard = stats["discard_rate"]
                        
                        writer.writerow({
                            "molecule": mol,
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
                            "noise_type": noise_type.value,
                            "depth": depth
                        })
                        
            print(f"Finished {mol}.")

if __name__ == "__main__":
    run_experiments()
