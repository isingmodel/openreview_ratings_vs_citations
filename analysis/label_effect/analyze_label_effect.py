"""Analyze the Label Effect Hypothesis."""

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
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scripts.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def categorize_decision(decision: str) -> str:
    """Map decision strings to standardized tiers."""
    if not isinstance(decision, str):
        return "Unknown"
    
    d = decision.lower()
    
    # Oral / Top Tier
    if "oral" in d or "talk" in d or "top-5%" in d:
        return "Top Tier (Oral)"
    
    # Spotlight / Middle Tier
    if "spotlight" in d or "top-25%" in d:
        return "Middle Tier (Spotlight)"
    
    # Poster / Base Tier
    if "poster" in d:
        return "Base Tier (Poster)"
        
    return "Other"

def analyze_label_effect(year: int, data_dir: Path, output_dir: Path):
    logger.info(f"Analyzing Label Effect for ICLR {year}...")
    
    df = load_data(data_dir)
    if df.empty:
        logger.warning(f"No data for {year}")
        return

    # Clean and Prepare
    df = df.dropna(subset=['mean_rating', 'citations', 'decision']).copy()
    df['log_citations'] = np.log1p(df['citations'])
    df['decision_tier'] = df['decision'].apply(categorize_decision)
    
    # Filter out 'Other' (Workshops, etc.) and 'Unknown'
    df = df[~df['decision_tier'].isin(["Other", "Unknown"])]
    
    # Reorder categories
    order = ["Base Tier (Poster)", "Middle Tier (Spotlight)", "Top Tier (Oral)"]
    df['decision_tier'] = pd.Categorical(df['decision_tier'], categories=order, ordered=True)
    
    print(f"\n--- ICLR {year} Data Structure ---")
    print(df['decision_tier'].value_counts())
    
    if len(df['decision_tier'].unique()) < 2:
        logger.warning("Not enough variance in decision tiers for analysis.")
        return

    # 1. Regression Analysis
    # Formula: log_citations ~ mean_rating + C(decision_tier)
    # We want to see if decision_tier adds value beyond mean_rating
    
    try:
        model = smf.ols("log_citations ~ mean_rating + C(decision_tier)", data=df).fit()
        print(f"\n--- OLS Regression Results ({year}) ---")
        print(model.summary())
        
        # Save summary
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / f"Regression_Summary_{year}.txt", "w") as f:
            f.write(model.summary().as_text())
            
    except Exception as e:
        logger.error(f"Regression failed: {e}")

    # 2. Visualization
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='decision_tier', y='log_citations', palette="Set2")
    plt.title(f"ICLR {year}: Citations by Decision Tier")
    plt.xlabel("Decision Tier")
    plt.ylabel("Log(Citations + 1)")
    plt.grid(True, alpha=0.3)
    plt.savefig(output_dir / f"Boxplot_Decision_Tier_{year}.png", dpi=150)
    plt.close()
    
    # Scatter with colored tiers
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='mean_rating', y='log_citations', hue='decision_tier', style='decision_tier', alpha=0.7)
    plt.title(f"ICLR {year}: Rating vs Citations (Labeled by Decision)")
    plt.xlabel("Mean Rating")
    plt.ylabel("Log(Citations + 1)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.tight_layout()
    plt.savefig(output_dir / f"Scatter_Decision_Tier_{year}.png", dpi=150)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--years", nargs="+", type=int, help="Analyze multiple years")
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[2]
    
    years = args.years if args.years else [args.year]
    
    for year in years:
        data_dir = repo_root / "data" / f"ICLR{year}"
        output_dir = repo_root / "analysis" / "label_effect" / "figs"
        analyze_label_effect(year, data_dir, output_dir)

if __name__ == "__main__":
    main()
