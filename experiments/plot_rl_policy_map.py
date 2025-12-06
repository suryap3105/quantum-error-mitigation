"""
RL Policy Map Visualization

Shows which strategy the RL agent chooses for each (bond_length, noise_type, molecule) combination.
This reveals the learned policy and helps interpret adaptive QEM behavior.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import torch
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rl_agent.policy import PolicyNet
from rl_agent.env import QEMEnv
from vqe_qem.strategies import Strategy, NoiseType

# Configuration
MODEL_PATH = "results/rl_policy_improved.pth"
OUTPUT_DIR = "paper_assets/plots"

STRATEGY_NAMES = ["Baseline", "DD", "Sym", "Hybrid"]
STRATEGY_COLORS = {
    "Baseline": "#C0C0C0",
    "DD": "#4C8CFE",
    "Sym": "#F39C12",
    "Hybrid": "#1ABC9C"
}

NOISE_TYPES = [
    ("T1 (Amplitude Damping)", NoiseType.AMPLITUDE_DAMPING),
    ("T2 (Phase Damping)", NoiseType.PHASE_DAMPING),
    ("Depolarizing", NoiseType.DEPOLARIZING),
    ("Composite (Hardware)", NoiseType.COMPOSITE)
]

MOLECULES = ["H2", "LiH", "BeH2"]

def load_policy():
    """Load the trained RL policy"""
    policy = PolicyNet(input_dim=6, output_dim=4)
    
    try:
        policy.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
        policy.eval()
        print(f"✓ Loaded policy from {MODEL_PATH}")
        return policy
    except FileNotFoundError:
        print(f"⚠ Policy file not found: {MODEL_PATH}")
        print("  Using random policy for demonstration")
        return None

def get_policy_action(policy, state):
    """Get policy action for a given state"""
    if policy is None:
        # Random fallback
        return np.random.randint(0, 4)
    
    with torch.no_grad():
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        dist = policy(state_tensor)
        action = dist.sample().item()
    
    return action

def create_policy_map():
    """Create RL policy map visualization"""
    policy = load_policy()
    
    # Create figure with subplots for each noise type
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    gamma = 0.08  # Medium noise level
    depth = 9.0
    
    for idx, (noise_name, noise_type) in enumerate(NOISE_TYPES):
        ax = axes[idx]
        
        # For each molecule, get policy choices across bond lengths
        for mol_idx, molecule in enumerate(MOLECULES):
            env = QEMEnv(molecule_name=molecule)
            bond_lengths = env.bond_lengths
            
            # Get policy choices for each bond length
            choices = []
            for R in bond_lengths:
                # Create state: [gamma, R, noise_idx, last_error, last_discard, depth]
                noise_idx = [nt[1] for nt in NOISE_TYPES].index(noise_type)
                state = np.array([gamma, R, float(noise_idx), 0.0, 0.0, depth], dtype=np.float32)
                
                action = get_policy_action(policy, state)
                choices.append(action)
            
            # Plot as colored bars
            x_positions = np.arange(len(bond_lengths)) + mol_idx * 0.25
            colors = [STRATEGY_COLORS[STRATEGY_NAMES[c]] for c in choices]
            
            bars = ax.bar(x_positions, np.ones(len(bond_lengths)), 
                         width=0.2, color=colors, 
                         label=molecule if idx == 0 else "", alpha=0.8,
                         edgecolor='black', linewidth=0.5)
            
            # Add strategy labels on bars
            for bar, choice in zip(bars, choices):
                height = bar.get_height()
                strategy_short = STRATEGY_NAMES[choice][:3]
                ax.text(bar.get_x() + bar.get_width()/2., height/2,
                       strategy_short, ha='center', va='center',
                       fontsize=7, fontweight='bold', rotation=90)
        
        # Format subplot
        ax.set_title(f"{noise_name}\n(γ = {gamma})", fontsize=12, fontweight='bold')
        ax.set_xlabel("Bond Length (Å)", fontsize=10)
        ax.set_ylabel("RL Strategy Choice", fontsize=10)
        ax.set_ylim(0, 1.2)
        ax.set_yticks([])
        
        # X-axis: use middle molecule's bond lengths
        env = QEMEnv(molecule_name="H2")
        ax.set_xticks(np.arange(len(env.bond_lengths)) + 0.25)
        ax.set_xticklabels([f"{r:.2f}" for r in env.bond_lengths], fontsize=8)
        
        if idx == 0:
            ax.legend(loc='upper left', fontsize=9)
    
    # Add color legend for strategies
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=STRATEGY_COLORS[s], label=s, edgecolor='black') 
                      for s in STRATEGY_NAMES]
    fig.legend(handles=legend_elements, loc='upper center', ncol=4, 
              bbox_to_anchor=(0.5, 0.98), fontsize=11, title="QEM Strategies")
    
    plt.suptitle("RL Policy Map: Learned Strategy Selection\nAcross Noise Types and Molecules",
                fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/rl_policy_map.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved RL Policy Map to {output_path}")
    plt.close()

def create_policy_heatmap():
    """Create heatmap version of policy map for H2 only"""
    policy = load_policy()
    
    molecule = "H2"
    env = QEMEnv(molecule_name=molecule)
    bond_lengths = env.bond_lengths
    gamma_values = [0.025, 0.05, 0.08, 0.11, 0.135]
    
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    
    for idx, (noise_name, noise_type) in enumerate(NOISE_TYPES):
        ax = axes[idx]
        
        # Build policy matrix
        policy_matrix = np.zeros((len(gamma_values), len(bond_lengths)))
        
        for i, gamma in enumerate(gamma_values):
            for j, R in enumerate(bond_lengths):
                noise_idx = [nt[1] for nt in NOISE_TYPES].index(noise_type)
                state = np.array([gamma, R, float(noise_idx), 0.0, 0.0, 9.0], dtype=np.float32)
                action = get_policy_action(policy, state)
                policy_matrix[i, j] = action
        
        # Plot heatmap
        im = ax.imshow(policy_matrix, cmap='tab10', aspect='auto', 
                      vmin=0, vmax=3, interpolation='nearest')
        
        # Add grid
        ax.set_xticks(np.arange(len(bond_lengths)))
        ax.set_yticks(np.arange(len(gamma_values)))
        ax.set_xticklabels([f"{r:.2f}" for r in bond_lengths], fontsize=9)
        ax.set_yticklabels([f"{g:.3f}" for g in gamma_values], fontsize=9)
        
        # Add text annotations
        for i in range(len(gamma_values)):
            for j in range(len(bond_lengths)):
                text = ax.text(j, i, STRATEGY_NAMES[int(policy_matrix[i, j])][:3],
                             ha="center", va="center", color="white", 
                             fontsize=8, fontweight='bold')
        
        ax.set_title(noise_name, fontsize=11, fontweight='bold')
        ax.set_xlabel("Bond Length (Å)", fontsize=10)
        if idx == 0:
            ax.set_ylabel("Noise Level (γ)", fontsize=10)
    
    # Add colorbar legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=plt.cm.tab10(i/3), label=STRATEGY_NAMES[i]) 
                      for i in range(4)]
    fig.legend(handles=legend_elements, loc='upper center', ncol=4,
              bbox_to_anchor=(0.5, 1.05), fontsize=10)
    
    plt.suptitle(f"RL Policy Heatmap for {molecule}\nStrategy Selection vs Noise Type, Level, and Bond Length",
                fontsize=13, fontweight='bold', y=1.08)
    plt.tight_layout()
    
    output_path = f"{OUTPUT_DIR}/rl_policy_heatmap_{molecule}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved RL Policy Heatmap to {output_path}")
    plt.close()

if __name__ == "__main__":
    print("Generating RL Policy Visualizations...")
    create_policy_map()
    create_policy_heatmap()
    print("✓ All RL policy plots generated successfully!")
