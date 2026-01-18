"""Analyze correlation trends across multiple ICLR years."""

import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from analyze import load_data
from scipy import stats

import numpy as np

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
    df["log_citations"] = pd.Series(df["citations"]).apply(lambda x: 0 if x < 0 else x).add(1).apply(lambda x: np.log(x)) # Handle potential negative or zero

    metrics = {}
    
    # 1. Standard Metrics
    metric_cols = {
        "Mean Rating": "mean_rating",
        "Weighted Rating": "weighted_rating",
        "High Conf (>4)": "high_conf_rating",
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

    # 2. Variance Metric
    # Hypothesis: Higher variance (controversial) -> Higher impact?
    if "var_rating" in df.columns:
        sub = df.dropna(subset=["var_rating", "log_citations"])
        if len(sub) > 10:
            r, p = stats.pearsonr(sub["var_rating"], sub["log_citations"])
            metrics["Rating Variance"] = r

    # 3. Decision Type (Oral vs Poster)
    # This requires 'decision' column parsing which might vary by year.
    # Simple check: Does Oral predict better? (Point-biserial correlation)
    # Mapping various accept types to Oral=1, Others=0 is complex across years.
    # We will skip this specific correlation for now to avoid noise.

    return metrics


def plot_trends(results: list, output_dir: Path):
    """Plot correlation trends over years."""
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

    ax.set_title("Evolution of Reviewer Predictive Power (2017-2023)", fontsize=16, color='white', pad=20)
    ax.set_xlabel("Year", fontsize=12, color='white')
    ax.set_ylabel("Pearson Correlation with Log(Citations)", fontsize=12, color='white')
    ax.tick_params(colors='white')
    
    # Legend
    legend = ax.legend(frameon=True, facecolor='#2d2d44', edgecolor='none', labelcolor='white')
    
    # Ref line at 0
    ax.axhline(0, color='#666666', linestyle='--', alpha=0.5)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "Correlation_Trends_2017_2023.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor='#1a1a2e')
    plt.close()
    
    logger.info(f"Saved trend plot to {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=[2017, 2018, 2019, 2020, 2021, 2022, 2023]) 
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    
    results = []
    
    print(f"{'Year':<6} | {'Mean':<8} | {'Weighted':<8} | {'HighConf':<8} | {'LowConf':<8} | {'Var':<8}")
    print("-" * 65)

    for year in args.years:
        metrics = compute_metrics_for_year(year, args.data_dir)
        if metrics:
            metrics["Year"] = year
            results.append(metrics)
            
            def fmt(val):
                return f"{val:.3f}" if val is not None else "N/A   "
            
            print(f"{year:<6} | {fmt(metrics.get('Mean Rating'))}    | {fmt(metrics.get('Weighted Rating'))}    | {fmt(metrics.get('High Conf (>4)'))}    | {fmt(metrics.get('Low Conf (<4)'))}    | {fmt(metrics.get('Rating Variance'))}")
    
    if results:
        # Save plots to figs/analysis/ still, but markdown to analysis/
        plot_dir = Path("figs/analysis")
        plot_trends(results, plot_dir)
        
        args.output_dir.mkdir(parents=True, exist_ok=True)
        res_df = pd.DataFrame(results).set_index("Year")
        md_path = args.output_dir / "result.md"
        with open(md_path, "w") as f:
            f.write("# Correlation Trends Analysis\n\n")
            f.write(res_df.to_markdown())
        logger.info(f"Saved summary table to {md_path}")

if __name__ == "__main__":
    main()
