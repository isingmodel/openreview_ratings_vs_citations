"""Analyze the Label Effect trends across years (2017-2023)."""

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

def analyze_year(year: int, data_dir: Path):
    """Run regression for a single year and return coefficients."""
    df = load_data(data_dir)
    if df.empty:
        return None

    # Clean and Prepare
    df = df.dropna(subset=['mean_rating', 'citations', 'decision']).copy()
    df['log_citations'] = np.log1p(df['citations'])
    df['decision_tier'] = df['decision'].apply(categorize_decision)
    
    # Filter out 'Other' and 'Unknown'
    df = df[~df['decision_tier'].isin(["Other", "Unknown"])]
    
    # Reorder categories (Base Tier is reference)
    order = ["Base Tier (Poster)", "Middle Tier (Spotlight)", "Top Tier (Oral)"]
    df['decision_tier'] = pd.Categorical(df['decision_tier'], categories=order, ordered=True)
    
    if len(df['decision_tier'].unique()) < 2:
        return None

    try:
        # Formula: log_citations ~ mean_rating + C(decision_tier)
        model = smf.ols("log_citations ~ mean_rating + C(decision_tier)", data=df).fit()
        
        # Extract coefficients and CI
        coefs = {
            "year": year,
            "n_papers": len(df),
            "r_squared": model.rsquared,
            
            # Mean Rating Effect
            "rating_coef": model.params.get("mean_rating", 0),
            "rating_pval": model.pvalues.get("mean_rating", 1),
            "rating_ci_lower": model.conf_int().loc["mean_rating"][0] if "mean_rating" in model.params else 0,
            "rating_ci_upper": model.conf_int().loc["mean_rating"][1] if "mean_rating" in model.params else 0,
            
            # Oral Effect (Top Tier)
            "oral_coef": model.params.get("C(decision_tier)[T.Top Tier (Oral)]", 0),
            "oral_pval": model.pvalues.get("C(decision_tier)[T.Top Tier (Oral)]", 1),
            "oral_ci_lower": model.conf_int().loc["C(decision_tier)[T.Top Tier (Oral)]"][0] if "C(decision_tier)[T.Top Tier (Oral)]" in model.params else 0,
            "oral_ci_upper": model.conf_int().loc["C(decision_tier)[T.Top Tier (Oral)]"][1] if "C(decision_tier)[T.Top Tier (Oral)]" in model.params else 0,

            # Spotlight Effect (Middle Tier)
            "spotlight_coef": model.params.get("C(decision_tier)[T.Middle Tier (Spotlight)]", 0),
            "spotlight_pval": model.pvalues.get("C(decision_tier)[T.Middle Tier (Spotlight)]", 1),
        }
        return coefs
        
    except Exception as e:
        logger.error(f"Error analyzing {year}: {e}")
        return None

def plot_trends(results: list, output_dir: Path):
    """Plot the coefficients over time."""
    df = pd.DataFrame(results)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot Coefficients
    plt.figure(figsize=(12, 8))
    
    # Oral Effect
    plt.errorbar(
        df['year'], df['oral_coef'], 
        yerr=[df['oral_coef'] - df['oral_ci_lower'], df['oral_ci_upper'] - df['oral_coef']],
        label="Oral Label Effect", marker='o', capsize=5, linewidth=2, color='#e74c3c'
    )
    
    # Rating Effect
    plt.errorbar(
        df['year'], df['rating_coef'], 
        yerr=[df['rating_coef'] - df['rating_ci_lower'], df['rating_ci_upper'] - df['rating_coef']],
        label="Review Rating Effect", marker='s', capsize=5, linewidth=2, color='#3498db'
    )
    
    plt.title("The 'Label Effect' vs 'Review Rating' (2017-2023)", fontsize=16)
    plt.ylabel("Regression Coefficient (Effect on Log Citations)", fontsize=12)
    plt.xlabel("Year", fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add annotations for p-values > 0.05
    for _, row in df.iterrows():
        if row['rating_pval'] > 0.05:
            plt.annotate('ns', (row['year'], row['rating_coef']), textcoords="offset points", xytext=(0,10), ha='center', color='blue')
        if row['oral_pval'] > 0.05:
            plt.annotate('ns', (row['year'], row['oral_coef']), textcoords="offset points", xytext=(0,10), ha='center', color='red')

    output_path = output_dir / "Label_Effect_Trends_2017_2023.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved trend plot to {output_path}")

def main():
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "analysis" / "label_effect" / "figs"
    
    years = range(2017, 2024)
    results = []
    
    for year in years:
        data_dir = repo_root / "data" / f"ICLR{year}"
        if not data_dir.exists():
            continue
            
        res = analyze_year(year, data_dir)
        if res:
            results.append(res)
            print(f"ICLR {year}: Oral Coef={res['oral_coef']:.3f}, Rating Coef={res['rating_coef']:.3f}")
    
    if results:
        plot_trends(results, output_dir)
        
        # Save CSV
        pd.DataFrame(results).to_csv(output_dir / "label_effect_coeffs.csv", index=False)
    else:
        logger.warning("No results generated.")

if __name__ == "__main__":
    main()
