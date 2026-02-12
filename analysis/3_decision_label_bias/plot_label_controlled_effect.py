"""Analyze and visualize the Label Effect controlled by Review Rating."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from scripts.utils.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Minimum sample size per (rating_bin, label) group to include in the plot
MIN_N = 5


def categorize_decision(decision: str) -> str:
    """Map decision strings to standardized tiers."""
    if not isinstance(decision, str):
        return "Unknown"
    
    d = decision.lower()
    
    if "oral" in d or "talk" in d or "top-5%" in d:
        return "Oral"
    if "spotlight" in d or "top-25%" in d:
        return "Spotlight"
    if "poster" in d:
        return "Poster"
        
    return "Other"


def load_all_years(years: list, data_root: Path) -> pd.DataFrame:
    """Load and aggregate data from multiple years."""
    all_dfs = []
    
    for year in years:
        year_dir = data_root / f"ICLR{year}"
        if not year_dir.exists():
            continue
            
        df = load_data(year_dir)
        if not df.empty:
            df['year'] = year
            all_dfs.append(df)
            
    if not all_dfs:
        return pd.DataFrame()
        
    return pd.concat(all_dfs, ignore_index=True)


def prepare_data(df: pd.DataFrame, rating_min: float = 5.0, rating_max: float = 9.0, bin_width: float = 1.0) -> pd.DataFrame:
    """Clean, filter, and bin the data."""
    df = df.dropna(subset=['mean_rating', 'citations', 'decision']).copy()
    df['log_citations'] = np.log1p(df['citations'])
    df['label'] = df['decision'].apply(categorize_decision)
    
    # Filter for main categories and rating range
    valid_labels = ["Oral", "Spotlight", "Poster"]
    df = df[df['label'].isin(valid_labels)]
    df = df[(df['mean_rating'] >= rating_min) & (df['mean_rating'] <= rating_max)]
    
    df['label'] = pd.Categorical(df['label'], categories=valid_labels, ordered=True)
    
    # Bin ratings
    df['rating_bin'] = (df['mean_rating'] / bin_width).round() * bin_width
    
    return df


def _plot_panel(ax, df: pd.DataFrame, title: str, palette: dict, show_ylabel: bool = True, show_n: bool = True):
    """Plot a single panel of the label effect chart."""
    
    # Aggregate for sample size annotations
    agg = df.groupby(['rating_bin', 'label'], observed=True).agg(
        mean_log_cit=('log_citations', 'mean'),
        n=('log_citations', 'count')
    ).reset_index()
    
    # Filter out groups with too few samples
    valid_groups = agg[agg['n'] >= MIN_N][['rating_bin', 'label']]
    df_filtered = df.merge(valid_groups, on=['rating_bin', 'label'], how='inner')
    
    # Plot with seaborn lineplot (auto CI)
    sns.lineplot(
        data=df_filtered,
        x="rating_bin", 
        y="log_citations", 
        hue="label",
        style="label",
        palette=palette,
        markers=True,
        dashes=False,
        linewidth=2.5,
        err_style="band",
        errorbar=('ci', 95),
        ax=ax
    )
    
    # Add sample size annotations for Oral (smallest group)
    if show_n:
        oral_agg = agg[(agg['label'] == 'Oral') & (agg['n'] >= MIN_N)]
        for _, row in oral_agg.iterrows():
            ax.annotate(
                f"n={int(row['n'])}",
                (row['rating_bin'], row['mean_log_cit']),
                textcoords="offset points", xytext=(0, 12),
                ha='center', fontsize=7, color='#c0392b', alpha=0.8
            )
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel("Mean Review Rating", fontsize=12)
    if show_ylabel:
        ax.set_ylabel("Log(Citations + 1)", fontsize=12)
    else:
        ax.set_ylabel("")
    ax.tick_params(labelsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1.0))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))


def plot_label_effect_controlled(df: pd.DataFrame, output_dir: Path):
    """Generate publication-quality single-panel figure for all years."""
    
    palette = {"Oral": "#e74c3c", "Spotlight": "#f39c12", "Poster": "#3498db"}
    df_all = prepare_data(df)
    
    # --- Figure ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 6))
    
    _plot_panel(ax, df_all, "", palette, show_ylabel=True)
    
    # Style legend
    ax.legend(title="Decision Label", title_fontsize=12, fontsize=11, loc='upper left')
    
    ax.set_title(
        "Impact of Decision Label on Citations\nControlled for Review Rating",
        fontsize=15, fontweight='bold', pad=16
    )
    
    plt.tight_layout()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "Label_Effect_Controlled_by_Rating.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved plot to {output_path}")
    
    # --- Gap Statistics ---
    print("\n--- Label Gap Analysis (at same rating) ---")
    df_all['rating_int'] = df_all['mean_rating'].round().astype(int)
    pivot = df_all.groupby(['rating_int', 'label'], observed=True)['log_citations'].mean().unstack()
    
    if 'Oral' in pivot.columns and 'Poster' in pivot.columns:
        pivot['Oral_vs_Poster'] = pivot['Oral'] - pivot['Poster']
    if 'Spotlight' in pivot.columns and 'Poster' in pivot.columns:
        pivot['Spotlight_vs_Poster'] = pivot['Spotlight'] - pivot['Poster']
    
    cols = [c for c in ['Oral_vs_Poster', 'Spotlight_vs_Poster'] if c in pivot.columns]
    if cols:
        print("\nAverage Log Citation Gap by Rating:")
        print(pivot[cols].dropna().round(3))
        print("\n(Gap of 0.69 ≈ 2x citations, Gap of 1.1 ≈ 3x citations)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2017, 2024)))
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[2]
    data_root = repo_root / "data"
    output_dir = repo_root / "analysis" / "3_decision_label_bias" / "figs"
    
    df = load_all_years(args.years, data_root)
    if df.empty:
        logger.error("No data found.")
        return
        
    plot_label_effect_controlled(df, output_dir)


if __name__ == "__main__":
    main()
