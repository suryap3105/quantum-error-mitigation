import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

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
        plot_dissociation_curve_with_discard(df, gamma)
        
    print(f"Figures generated in {PLOTS_DIR}")

def plot_dissociation_curve_with_discard(df, gamma):
    """Create enhanced dissociation curve with discard rate bars"""
    
    # Create figure with 2 subplots vertically (main curve + discard bars)
    fig = plt.figure(figsize=(12, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.15)
    ax_main = fig.add_subplot(gs[0])
    ax_discard = fig.add_subplot(gs[1], sharex=ax_main)
    
    # Filter by gamma
    df_g = df[df["gamma"] == gamma]
    
    # Plot FCI (Red Dashed) - take from any strategy (e.g., baseline)
    df_fci = df_g[df_g["strategy"] == "baseline"].sort_values("R")
    ax_main.plot(df_fci["R"], df_fci["fci_energy"], 
             color=COLORS["fci"], linestyle="--", label=LABELS["fci"], linewidth=2.5)
    
    # Plot Strategies on main plot
    strategies = ["baseline", "dd", "sym", "hybrid", "rl"]
    
    discard_data = {}  # Store discard rates for bar plot
    
    for strat in strategies:
        data = df_g[df_g["strategy"] == strat].sort_values("R")
        
        if data.empty:
            continue
            
        color = COLORS.get(strat, "black")
        label = LABELS.get(strat, strat)
        
        # Mean line
        ax_main.plot(data["R"], data["mean_energy"], 
                 color=color, label=label, marker="o", markersize=6, linewidth=2.5)
        
        # Confidence Interval (Shaded)
        ax_main.fill_between(data["R"], data["ci_lower"], data["ci_upper"],
                         color=color, alpha=0.25)
        
        # Collect discard rates if available
        if strat in ["sym", "hybrid"] and "discard_rate" in data.columns:
            discard_data[strat] = (data["R"].values, data["discard_rate"].values * 100)
                         
    # Styling main plot
    ax_main.set_title(f"H₂ Dissociation Curve (Noise γ={gamma})\\nFixed Shot Budget (N=10,000) | Shaded Areas = 95% Confidence Interval",
                     fontsize=13, fontweight='bold')
    ax_main.set_ylabel("Energy (Hartree)", fontsize=12, fontweight='bold')
    ax_main.legend(loc='best', fontsize=10, framealpha=0.9)
    ax_main.grid(True, alpha=0.3)
    ax_main.tick_params(axis='x', labelbottom=False)  # Hide x labels on top plot
    
    # Plot discard rates as grouped bars
    if discard_data:
        R_values = df_fci["R"].values
        x_pos = np.arange(len(R_values))
        width = 0.35
        
        for i, (strat, (R_vals, discard_vals)) in enumerate(discard_data.items()):
            offset = (i - 0.5) * width
            ax_discard.bar(x_pos + offset, discard_vals, width,
                          label=LABELS[strat], color=COLORS[strat],
                          alpha=0.75, edgecolor='black', linewidth=1.2)
        
        ax_discard.set_ylabel("Discard Rate (%)", fontsize=11, fontweight='bold')
        ax_discard.set_xlabel("Bond Length R (Å)", fontsize=12, fontweight='bold')
        ax_discard.set_xticks(x_pos)
        ax_discard.set_xticklabels([f"{r:.2f}" for r in R_values], fontsize=10)
        ax_discard.set_ylim(0, 100)
        ax_discard.axhline(y=50, color='red', linestyle=':', alpha=0.6, linewidth=2)
        ax_discard.legend(fontsize=9, loc='upper right', framealpha=0.9)
        ax_discard.grid(True, alpha=0.3, axis='y')
    else:
        ax_discard.text(0.5, 0.5, "No discard data available", 
                       ha='center', va='center', transform=ax_discard.transAxes,
                       fontsize=11, style='italic', color='gray')
        ax_discard.set_ylabel("Discard Rate (%)", fontsize=11, fontweight='bold')
        ax_discard.set_xlabel("Bond Length R (Å)", fontsize=12, fontweight='bold')
        ax_discard.set_ylim(0, 100)
        ax_discard.grid(True, alpha=0.3)
    
    # Save
    filename = f"{PLOTS_DIR}/dissociation_gamma_{gamma}_with_discard.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"Saved {filename}")
    plt.close()

if __name__ == "__main__":
    generate_figures()
