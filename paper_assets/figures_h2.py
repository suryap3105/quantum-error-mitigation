import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
RESULTS_FILE = "results/h2_vqe_experiments.csv"
PLOTS_DIR = "paper_assets/plots"

# Styling
COLORS = {
    "baseline": "#C0C0C0", # Grey
    "dd": "#4C8CFE",       # Blue
    "sym": "#F39C12",      # Orange
    "hybrid": "#1ABC9C",   # Green
    "rl": "#9B59B6",       # Purple
    "fci": "#FF6B6B"       # Red
}

LABELS = {
    "baseline": "Baseline",
    "dd": "DD (Active)",
    "sym": "Sym (Passive)",
    "hybrid": "Hybrid (DD + Sym)",
    "rl": "RL Agent",
    "fci": "FCI (Exact)"
}

def generate_figures():
    Path(PLOTS_DIR).mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = pd.read_csv(RESULTS_FILE)
    
    # Get unique gammas
    gammas = df["gamma"].unique()
    
    for gamma in gammas:
        plot_dissociation_curve(df, gamma)
        
    print(f"Figures generated in {PLOTS_DIR}")

def plot_dissociation_curve(df, gamma):
    plt.figure(figsize=(10, 6))
    
    # Filter by gamma
    df_g = df[df["gamma"] == gamma]
    
    # Plot FCI (Red Dashed) - take from any strategy (e.g., baseline)
    df_fci = df_g[df_g["strategy"] == "baseline"].sort_values("R")
    plt.plot(df_fci["R"], df_fci["fci_energy"], 
             color=COLORS["fci"], linestyle="--", label=LABELS["fci"], linewidth=2)
    
    # Plot Strategies
    strategies = ["baseline", "dd", "sym", "hybrid", "rl"]
    
    for strat in strategies:
        data = df_g[df_g["strategy"] == strat].sort_values("R")
        
        if data.empty:
            continue
            
        color = COLORS.get(strat, "black")
        label = LABELS.get(strat, strat)
        
        # Mean line
        plt.plot(data["R"], data["mean_energy"], 
                 color=color, label=label, marker="o", markersize=4)
        
        # Confidence Interval (Shaded)
        plt.fill_between(data["R"], data["ci_lower"], data["ci_upper"],
                         color=color, alpha=0.3)
                         
    # Styling
    plt.title(f"H2 Dissociation Curve (Noise $\gamma={gamma}$)\nFixed Shot Budget (N=10,000) | Shaded Areas = 95% Confidence Interval")
    plt.xlabel("Bond Length R (Å)")
    plt.ylabel("Energy (Hartree)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save
    filename = f"{PLOTS_DIR}/dissociation_gamma_{gamma}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"Saved {filename}")

if __name__ == "__main__":
    generate_figures()
