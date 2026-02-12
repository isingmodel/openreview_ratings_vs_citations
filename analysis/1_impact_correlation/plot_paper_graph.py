"""Generate publication-quality correlation trend graph."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from scripts.utils.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def compute_metrics_for_year(year: int, data_dir: Path) -> dict:
    """Compute correlation metrics for a single year."""
    year_dir = data_dir / f"ICLR{year}"
    if not year_dir.exists():
        logger.warning(f"Data directory for {year} not found.")
        return None

    df = load_data(year_dir)
    if df.empty or "citations" not in df.columns:
        logger.warning(f"No valid data for {year}.")
        return None

    # Filter invalid data
    df = df.dropna(subset=["citations", "mean_rating"]).copy()
    if len(df) < 10:
        logger.warning(f"Not enough data for {year} (n={len(df)}).")
        return None

    # Log transform citations
    df["log_citations"] = pd.Series(df["citations"]).apply(lambda x: 0 if x < 0 else x).add(1).apply(lambda x: np.log(x))

    metrics = {}
    
    # 1. Standard Metrics
    metric_cols = {
        "Mean Rating": "mean_rating",
    }
    
    for label, col in metric_cols.items():
        if col in df.columns:
            sub = df.dropna(subset=[col, "log_citations"])
            if len(sub) > 10:
                r, p = stats.pearsonr(sub[col], sub["log_citations"])
                metrics[label] = r
            else:
                metrics[label] = None

    return metrics


def plot_paper_trends(results: list, output_dir: Path):
    """Plot correlation trends with publication-quality styling."""
    df = pd.DataFrame(results)
    if df.empty:
        return

    df = df.set_index("Year")
    
    # Paper-quality style
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot line
    ax.plot(
        df.index, 
        df["Mean Rating"], 
        marker='o', 
        linewidth=2.5, 
        color='#333333',
        label="Correlation (Review Rating vs Log Citations)",
        markersize=8
    )

    # Styling
    min_year = df.index.min()
    max_year = df.index.max()
    
    ax.set_title("Correlation between Review Ratings and Impact (Citations) over Time", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Pearson Correlation (r)", fontsize=12)
    ax.tick_params(labelsize=11)
    
    # Set y-axis limits to verify if it makes sense (usually 0.2-0.5)
    # ax.set_ylim(0, 0.6) 

    # Grid
    ax.grid(True, linestyle='--', alpha=0.7)

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "paper_correlation_trends.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    logger.info(f"Saved paper trend plot to {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2017, 2018, 2019, 2020, 2021, 2022, 2023]) 
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = args.data_dir or repo_root / "data"
    output_dir = args.output_dir or Path(__file__).parent / "figs"
    
    results = []
    
    print(f"{'Year':<6} | {'Mean Correlation':<16}")
    print("-" * 25)

    for year in args.years:
        metrics = compute_metrics_for_year(year, data_dir)
        if metrics:
            metrics["Year"] = year
            results.append(metrics)
            
            val = metrics.get('Mean Rating')
            fmt_val = f"{val:.3f}" if val is not None else "N/A"
            print(f"{year:<6} | {fmt_val:<16}")
    
    if results:
        # Save plots
        plot_paper_trends(results, output_dir)

if __name__ == "__main__":
    main()
