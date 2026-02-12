"""Generate a 2x3 grid of correlation plots for ICLR 2017-2022."""

import logging
import sys
from pathlib import Path

# Add project root to path to allow importing scripts
sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scripts.utils.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def setup_academic_style():
    """Set up matplotlib style for academic publication."""
    # Use seaborn-v0_8-paper or similar base, but override with specific needs
    plt.style.use('seaborn-v0_8-whitegrid')
    
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'axes.edgecolor': 'black',
        'axes.linewidth': 1.0,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
    })

def plot_single_panel(ax, df: pd.DataFrame, year: int):
    """Plot a single correlation panel on the provided axes."""
    # Filter data
    plot_df = df.dropna(subset=["mean_rating", "citations"]).copy()
    if plot_df.empty:
        ax.text(0.5, 0.5, "No Data", ha='center', va='center')
        return

    # Log transform citations
    plot_df["log_citations"] = np.log1p(plot_df["citations"])

    # Calculate correlation
    corr, p_value = stats.pearsonr(plot_df["mean_rating"], plot_df["log_citations"])
    n_samples = len(plot_df)

    # Scatter plot
    # Using a solid color or mapped color. 
    # Let's map color to citations but use a perceptually uniform colormap compatible with white paper.
    scatter = ax.scatter(
        plot_df["mean_rating"],
        plot_df["log_citations"],
        c=plot_df["log_citations"],
        cmap='viridis',
        alpha=0.6,
        s=30,
        edgecolors='white',
        linewidths=0.5
    )

    # Regression line
    sns.regplot(
        data=plot_df,
        x="mean_rating",
        y="log_citations",
        scatter=False,
        color='black',
        line_kws={'linewidth': 2, 'linestyle': '--'},
        ax=ax
    )

    # Annotations
    stats_text = f"$r = {corr:.2f}$\n$p < 0.001$" if p_value < 0.001 else f"$r = {corr:.2f}$\n$p = {p_value:.3f}$"
    stats_text += f"\n$n = {n_samples}$"
    
    # Place text in bottom right or top left depending on data distribution? 
    # Bottom right is usually safe for this positive correlation.
    ax.text(
        0.95, 0.05, stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='bottom',
        horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray')
    )

    # Title
    ax.set_title(f"ICLR {year}", fontsize=14, fontweight='bold', pad=10)
    
    # Labels (only set them, but we might hide them in the grid loop for inner plots)
    ax.set_xlabel("Mean Review Rating")
    ax.set_ylabel("Log(Citations + 1)")
    
    return scatter

def main():
    repo_root = Path(__file__).resolve().parents[2]
    setup_academic_style()

    # Create figure 2x3
    fig, axes = plt.subplots(2, 3, figsize=(15, 10), sharex=True, sharey=True)
    axes = axes.flatten()
    
    years = [2017, 2018, 2019, 2020, 2021, 2022]
    
    global_scatter = None

    for i, year in enumerate(years):
        data_dir = repo_root / "data" / f"ICLR{year}"
        logger.info(f"Processing ICLR {year}...")
        
        if not data_dir.exists():
            logger.warning(f"Data directory not found for {year}")
            axes[i].text(0.5, 0.5, f"Data Not Found\n{year}", ha='center', va='center')
            continue

        df = load_data(data_dir)
        # Exclude "Invite to Workshop Track" papers (2017-2018 only)
        df = df[~df['decision'].str.contains('Workshop', case=False, na=False)]
        scatter = plot_single_panel(axes[i], df, year)
        if scatter:
            global_scatter = scatter

    # Adjust layout
    plt.tight_layout()
    
    # Add a global colorbar? 
    # Since each plot uses the same log scale (roughly), a common colorbar might be nice, 
    # but the range might differ per year. 
    # For simplicity and to match the "correlation" focus, we might skip the colorbar or add one on the side.
    # Let's add one common colorbar on the right.
    if global_scatter:
        fig.subplots_adjust(right=0.92)
        cbar_ax = fig.add_axes([0.94, 0.15, 0.015, 0.7])
        cbar = fig.colorbar(global_scatter, cax=cbar_ax)
        cbar.set_label('Log(Citations + 1)', fontsize=12)

    output_dir = Path(__file__).parent / "figs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "combined_correlation_grid.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"Saved combined plot to {output_path}")

if __name__ == "__main__":
    main()
