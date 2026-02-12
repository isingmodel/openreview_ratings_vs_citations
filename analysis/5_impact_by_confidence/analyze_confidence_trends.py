"""Analyze confidence-weighted correlation trends across multiple ICLR years."""

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
    """Compute confidence-weighted correlation metrics for a single year."""
    year_dir = data_dir / f"ICLR{year}"
    if not year_dir.exists():
        logger.warning(f"Data directory for {year} not found.")
        return None

    df = load_data(year_dir)
    # Exclude "Invite to Workshop Track" papers (2017-2018 only)
    df = df[~df['decision'].str.contains('Workshop', case=False, na=False)]
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
    
    # Metrics to analyze
    metric_cols = {
        "Mean Rating": "mean_rating",
        "Weighted Rating": "weighted_rating",
        "High Conf (>=4)": "high_conf_rating",
        "Low Conf (<4)": "low_conf_rating",
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


def plot_trends(results: list, output_dir: Path):
    """Plot confidence correlation trends over years."""
    df = pd.DataFrame(results)
    if df.empty:
        return

    df = df.set_index("Year")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 8), facecolor='#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    # Plot lines for each metric
    markers = ['o', 's', '^', 'v', 'D']
    colors = ['#4facfe', '#00f2fe', '#43e97b', '#fa709a', '#fecfef']
    
    for i, col in enumerate(df.columns):
        if df[col].isna().all():
            continue
            
        ax.plot(
            df.index, 
            df[col], 
            marker=markers[i % len(markers)], 
            linewidth=2.5, 
            label=col,
            color=colors[i % len(colors)]
        )

    min_year = df.index.min()
    max_year = df.index.max()
    ax.set_title(f"Confidence Analysis Trends ({min_year}-{max_year})", fontsize=16, color='white', pad=20)
    ax.set_xlabel("Year", fontsize=12, color='white')
    ax.set_ylabel("Pearson Correlation with Log(Citations)", fontsize=12, color='white')
    ax.tick_params(colors='white')
    
    # Legend
    legend = ax.legend(frameon=True, facecolor='#2d2d44', edgecolor='none', labelcolor='white')
    
    # Ref line at 0
    ax.axhline(0, color='#666666', linestyle='--', alpha=0.5)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "confidence_trends.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor='#1a1a2e')
    plt.close()
    
    logger.info(f"Saved trend plot to {out_path}")


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
    
    print(f"{'Year':<6} | {'Mean':<8} | {'Weighted':<8} | {'HighConf':<8} | {'LowConf':<8}")
    print("-" * 55)

    for year in args.years:
        metrics = compute_metrics_for_year(year, data_dir)
        if metrics:
            metrics["Year"] = year
            results.append(metrics)
            
            def fmt(val):
                return f"{val:.3f}" if val is not None else "N/A   "
            
            print(f"{year:<6} | {fmt(metrics.get('Mean Rating'))}    | {fmt(metrics.get('Weighted Rating'))}    | {fmt(metrics.get('High Conf (>=4)'))}    | {fmt(metrics.get('Low Conf (<4)'))}")
    
    if results:
        # Save plots
        plot_trends(results, output_dir)
        
        # Save markdown summary
        md_dir = output_dir.parent
        md_dir.mkdir(parents=True, exist_ok=True)
        res_df = pd.DataFrame(results).set_index("Year")
        md_path = md_dir / "confidence_trends.md"
        with open(md_path, "w") as f:
            f.write("# Confidence Analysis Trends\n\n")
            f.write(res_df.to_markdown())
        logger.info(f"Saved summary table to {md_path}")

if __name__ == "__main__":
    main()
