import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

def plot_paper_results():
    df = pd.read_csv('results/paper_results.csv')
    
    # Colors as specified
    colors = {
        "baseline": "#C0C0C0", # Grey
        "dd":       "#4C8CFE", # Blue
        "sym":      "#F39C12", # Orange
        "hybrid":   "#1ABC9C", # Green
        "fci":      "#FF6B6B"  # Red
    }
    
    labels = {
        "baseline": "Baseline",
        "dd":       "Active (DD)",
        "sym":      "Passive (Sym)",
        "hybrid":   "Active + Passive (Hybrid)"
    }
    
    # Plot for each Gamma
    gammas = sorted(df['gamma'].unique())
    
    for gamma in gammas:
        plt.figure(figsize=(10, 6))
        
        # Plot FCI first (dashed red)
        fci_data = df[df['strategy'] == 'baseline'] # FCI is same for all, just pick one subset
        plt.plot(fci_data['R'], fci_data['E_fci'], 
                 color=colors['fci'], linestyle='--', linewidth=2, label='FCI (Exact)')
        
        # Plot strategies
        for strategy in ["baseline", "dd", "sym", "hybrid"]:
            subset = df[(df['gamma'] == gamma) & (df['strategy'] == strategy)]
            
            # Main curve
            plt.plot(subset['R'], subset['E_mean'], 
                     color=colors[strategy], linewidth=2.5, marker='o', markersize=6,
                     label=labels[strategy])
            
            # Shaded CI
            plt.fill_between(subset['R'], subset['ci_lower'], subset['ci_upper'],
                             color=colors[strategy], alpha=0.2)
        
        plt.title(f'H₂ Energy Estimation (Noise $\gamma={gamma}$)\nFixed Shot Budget (N=10,000) | Shaded Areas = 95% Confidence Interval', 
                  fontsize=12, pad=15)
        plt.xlabel('Bond Length R (Å)', fontsize=12)
        plt.ylabel('Energy (Hartree)', fontsize=12)
        plt.legend(loc='upper right', frameon=True, framealpha=0.9)
        
        # Save
        filename = f'plots/paper_results_gamma_{gamma}.png'
        plt.tight_layout()
        plt.savefig(filename, bbox_inches='tight')
        print(f"Saved {filename}")
        plt.close()

if __name__ == "__main__":
    plot_paper_results()
