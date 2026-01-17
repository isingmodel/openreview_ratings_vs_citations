"""Analyze correlation between review ratings and citations."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_rating(rating_str):
    """Parse rating from various string formats."""
    if isinstance(rating_str, (list, np.ndarray)):
        return list(rating_str)
    if not isinstance(rating_str, str):
        return []
    
    # Try JSON format first: [1, 2, 3]
    try:
        return json.loads(rating_str)
    except json.JSONDecodeError:
        pass
    
    # Try numpy array string format: [1 2 3]
    if rating_str.startswith("[") and rating_str.endswith("]"):
        inner = rating_str[1:-1].strip()
        if inner:
            return [int(x) for x in inner.split()]
    
    return []


def load_data(data_dir: Path) -> pd.DataFrame:
    """Load preprocessed data and merge with citations."""
    # Load preprocessed data
    parquet_path = data_dir / "preprocessed.parquet"
    df = pd.read_parquet(parquet_path)

    # Parse rating from string
    df["rating"] = df["rating"].apply(parse_rating)
    df["mean_rating"] = df["rating"].apply(lambda x: np.mean(x) if x else None)

    # Load citations
    citation_files = list(data_dir.glob("openalex*.json"))
    
    if citation_files:
        # Sort to pick the latest file if multiple exist
        citation_file = sorted(citation_files)[-1]
        with open(citation_file, "r", encoding="utf-8") as f:
            citations = json.load(f)

        # Merge citations
        df["citations"] = df["title"].apply(
            lambda t: citations.get(str(t), {}).get("num_citations")
        )
        logger.info(f"Merged citations from {citation_file.name}")
    else:
        logger.warning(f"No OpenAlex citation file found in {data_dir}!")

    return df


def plot_correlation(
    df: pd.DataFrame, 
    year: int, 
    output_dir: Path,
    min_rating: float | None = None,
) -> Path:
    """Generate scatter plot of ratings vs citations."""
    # Filter data
    plot_df = df.dropna(subset=["mean_rating", "citations"]).copy()
    
    if min_rating:
        plot_df = plot_df[plot_df["mean_rating"] >= min_rating]
    
    if plot_df.empty:
        logger.error("No data available for plotting!")
        return None

    # Log transform citations
    plot_df["log_citations"] = np.log1p(plot_df["citations"])

    # Calculate correlation
    corr, p_value = stats.pearsonr(plot_df["mean_rating"], plot_df["log_citations"])

    # === Premium Plot Styling ===
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 9), facecolor='#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    # Color gradient based on citation count
    colors = plot_df["log_citations"]
    
    scatter = ax.scatter(
        plot_df["mean_rating"],
        plot_df["log_citations"],
        c=colors,
        cmap='plasma',
        alpha=0.35,
        s=50,
        edgecolors='white',
        linewidths=0.3,
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Log(Citations + 1)', fontsize=11, color='white', labelpad=10)
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    # Regression line with confidence interval
    sns.regplot(
        data=plot_df,
        x="mean_rating",
        y="log_citations",
        scatter=False,
        color='#00d4ff',
        line_kws={'linewidth': 2.5, 'linestyle': '--'},
        ax=ax,
    )

    # Styling
    ax.set_xlabel("Mean Review Rating", fontsize=14, color='white', labelpad=10)
    ax.set_ylabel("Log(Citations + 1)", fontsize=14, color='white', labelpad=10)
    ax.tick_params(colors='white', labelsize=11)
    
    # Title
    ax.set_title(
        f"ICLR {year}  •  Review Ratings vs Citations",
        fontsize=18,
        fontweight='bold',
        color='white',
        pad=20,
    )
    
    # Stats annotation box
    stats_text = f"r = {corr:.3f}  |  p = {p_value:.2e}  |  n = {len(plot_df)}"
    ax.text(
        0.5, 0.02, stats_text,
        transform=ax.transAxes,
        fontsize=12,
        color='#cccccc',
        ha='center',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#2d2d44', edgecolor='none', alpha=0.8),
    )
    
    # Grid styling
    ax.grid(True, alpha=0.2, color='white')
    for spine in ax.spines.values():
        spine.set_color('#444466')
        spine.set_linewidth(1.5)

    # Save plot
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Log_Citation_vs_Review_Rating_ICLR_{year}.png"
    plt.savefig(output_path, dpi=200, bbox_inches="tight", facecolor='#1a1a2e', edgecolor='none')
    plt.close()

    logger.info(f"Saved plot to {output_path}")
    return output_path


def print_summary(df: pd.DataFrame, year: int):
    """Print summary statistics."""
    plot_df = df.dropna(subset=["mean_rating", "citations"])

    print(f"\n{'='*50}")
    print(f"ICLR {year} Summary")
    print(f"{'='*50}")
    print(f"Total papers: {len(df)}")
    print(f"Papers with citation data: {len(plot_df)}")
    print(f"\nRating statistics:")
    print(f"  Mean: {plot_df['mean_rating'].mean():.2f}")
    print(f"  Std:  {plot_df['mean_rating'].std():.2f}")
    print(f"  Range: {plot_df['mean_rating'].min():.1f} - {plot_df['mean_rating'].max():.1f}")
    print(f"\nCitation statistics:")
    print(f"  Mean: {plot_df['citations'].mean():.1f}")
    print(f"  Median: {plot_df['citations'].median():.1f}")
    print(f"  Max: {plot_df['citations'].max():.0f}")

    if len(plot_df) > 2:
        corr, p_value = stats.pearsonr(plot_df["mean_rating"], np.log1p(plot_df["citations"]))
        print(f"\nCorrelation (rating vs log citations):")
        print(f"  r = {corr:.3f}")
        print(f"  p = {p_value:.3e}")


def main():
    parser = argparse.ArgumentParser(description="Analyze ratings vs citations")
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="ICLR year to analyze",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Data directory (default: data/ICLR{year}/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for plots (default: figs/)",
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=None,
        help="Minimum rating to include (e.g., 6.0 to exclude desk rejects)",
    )
    args = parser.parse_args()

    data_dir = args.data_dir or Path(__file__).parent.parent / "data" / f"ICLR{args.year}"
    output_dir = args.output or Path(__file__).parent.parent / "figs"

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    df = load_data(data_dir)
    print_summary(df, args.year)
    plot_correlation(df, args.year, output_dir, args.min_rating)


if __name__ == "__main__":
    main()
