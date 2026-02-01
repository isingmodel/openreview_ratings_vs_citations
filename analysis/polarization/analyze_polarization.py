"""Analyze the Polarization Hypothesis using Rating Range."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scripts.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate rating range and controversy flags."""
    # Ensure ratings are list of dicts or list of values
    # The preprocessed.parquet usually stores ratings as a JSON string or list of dicts.
    # load_data from src.py handles some of this, but let's be safe.
    
    def get_range(rating_col):
        # rating_col is a list of dicts like [{'rating': 8, ...}, ...]
        if not rating_col or not isinstance(rating_col, list):
            return 0
        try:
            values = [r['rating'] for r in rating_col if isinstance(r, dict) and 'rating' in r]
            if not values:
                return 0
            return max(values) - min(values)
        except Exception:
            return 0

    df = df.copy()
    if 'rating' in df.columns:
        df['rating_range'] = df['rating'].apply(get_range)
    
    # Define "Controversial" as Range >= 4
    df['is_controversial'] = df['rating_range'] >= 4
    df['log_citations'] = np.log1p(df['citations'])
    
    return df

def plot_polarization(df: pd.DataFrame, year: int, output_dir: Path):
    """Generate plots for polarization analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Scatter Plot: Rating Range vs Log Citations
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='rating_range', y='log_citations', palette='viridis')
    plt.title(f"ICLR {year}: Citation Distribution by Rating Range")
    plt.xlabel("Rating Range (Max - Min)")
    plt.ylabel("Log(Citations + 1)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / f"Boxplot_Range_vs_Citations_{year}.png", dpi=150)
    plt.close()
    
    # 2. Regression with Hue
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='mean_rating', y='log_citations', hue='is_controversial', alpha=0.6, palette={True: 'red', False: 'blue'})
    plt.title(f"ICLR {year}: Citations vs Mean Rating (Red=Controversial)")
    plt.xlabel("Mean Rating")
    plt.ylabel("Log(Citations + 1)")
    plt.legend(title="Range >= 4")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / f"Scatter_Controversy_Highlight_{year}.png", dpi=150)
    plt.close()

def analyze_year(year: int, data_dir: Path, output_dir: Path):
    logger.info(f"Analyzing polarization for ICLR {year}...")
    
    df = load_data(data_dir)
    if df.empty:
        logger.warning(f"No data for {year}")
        return

    df = calculate_metrics(df)
    
    # Filter for valid data
    df = df.dropna(subset=['mean_rating', 'citations'])
    
    # Stats
    high_pol = df[df['is_controversial']]
    low_pol = df[~df['is_controversial']]
    
    print(f"\n--- ICLR {year} Results ---")
    print(f"Total Papers: {len(df)}")
    print(f"Controversial (Range>=4): {len(high_pol)} ({len(high_pol)/len(df)*100:.1f}%)")
    print(f"Consensus (Range<4): {len(low_pol)}")
    
    print(f"Mean Citations (Controversial): {high_pol['citations'].mean():.1f}")
    print(f"Mean Citations (Consensus):     {low_pol['citations'].mean():.1f}")
    
    # T-test
    t_stat, p_val = stats.ttest_ind(high_pol['log_citations'], low_pol['log_citations'], equal_var=False)
    print(f"T-test (Log Citations): t={t_stat:.3f}, p={p_val:.4f}")
    
    plot_polarization(df, year, output_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--years", nargs="+", type=int, help="Analyze multiple years")
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[2]
    
    years = args.years if args.years else [args.year]
    
    for year in years:
        data_dir = repo_root / "data" / f"ICLR{year}"
        output_dir = repo_root / "analysis" / "polarization" / "figs"
        analyze_year(year, data_dir, output_dir)

if __name__ == "__main__":
    main()
