"""Analyze reviewer confidence impact on prediction."""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from scripts.utils.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def plot_confidence_analysis(df: pd.DataFrame, year: int, output_dir: Path) -> None:
    """Generate plots comparing confidence-weighted metrics."""
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Filter valid data
    df = df.dropna(subset=["citations", "mean_rating"]).copy()
    if df.empty:
        logger.warning(f"No valid data for confidence analysis for year {year}")
        return

    df["log_citations"] = np.log1p(df["citations"])
    
    # 1. Compare Correlations of Different Metrics
    metrics = {
        "Mean Rating": "mean_rating",
        "Weighted Rating": "weighted_rating",
        "High Conf (>4)": "high_conf_rating",
        "Low Conf (<4)": "low_conf_rating"
    }
    
    results = []
    
    for label, col in metrics.items():
        if col not in df.columns:
            continue
            
        sub_df = df.dropna(subset=[col])
        if len(sub_df) < 5:
            continue
        corr, p = stats.pearsonr(sub_df[col], sub_df["log_citations"])
        results.append({
            "Metric": label,
            "Correlation": corr,
            "P-value": p,
            "Count": len(sub_df)
        })
        
    print("\nConfidence Analysis Results:")
    print(pd.DataFrame(results))
    
    # Visualization: Bar chart of Correlations
    if results:
        res_df = pd.DataFrame(results)
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        bars = ax.bar(res_df["Metric"], res_df["Correlation"], color=['#4facfe', '#00f2fe', '#43e97b', '#fa709a'])
        
        ax.set_title(f"ICLR {year}: Predictive Power of Different Rating Aggregations", color='white', fontsize=14)
        ax.set_ylabel("Pearson Correlation with Log(Citations)", color='white')
        ax.tick_params(colors='white')
        
        # Handle negative correlations in y-limits
        min_corr = min(res_df["Correlation"].min(), 0)
        max_corr = max(res_df["Correlation"].max(), 0)
        ax.set_ylim(min_corr * 1.2 if min_corr < 0 else 0, max_corr * 1.2)
        
        # Add labels
        for bar in bars:
            height = bar.get_height()
            label_y = height if height >= 0 else height - 0.05
            val_align = 'bottom' if height >= 0 else 'top'
            
            ax.text(bar.get_x() + bar.get_width()/2., label_y,
                    f'{height:.3f}',
                    ha='center', va=val_align, color='white')
            
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"Confidence_Analysis_ICLR_{year}.png"
        plt.savefig(out_path, dpi=200, bbox_inches="tight", facecolor='#1a1a2e')
        plt.close()
        logger.info(f"Saved confidence analysis plot to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze reviewer confidence")
    parser.add_argument("--year", type=int, required=True, help="ICLR year to analyze")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    data_dir = args.data_dir or repo_root / "data" / f"ICLR{args.year}"
    output_dir = args.output or Path(__file__).parent / "figs"

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    df = load_data(data_dir)
    plot_confidence_analysis(df, args.year, output_dir)


if __name__ == "__main__":
    main()
