"""Test: Is the rating–citation correlation entirely mediated by the decision label?

Hypothesis: correlation(rating, citations) > 0 only because
   higher rating → higher-prestige label (Oral/Spotlight) → more citations.
If true, after controlling for label, the partial correlation should ≈ 0.

Tests:
1. Within-label partial correlations (Poster-only, Spotlight-only, Oral-only)
2. Hierarchical regression: total effect vs direct effect (attenuation %)
3. Year-wise panel of all the above
"""

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
from scipy import stats
import statsmodels.formula.api as smf
from scripts.utils.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

YEARS = list(range(2017, 2024))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def load_year(year: int, data_root: Path) -> pd.DataFrame:
    """Load a single year, add derived columns."""
    year_dir = data_root / f"ICLR{year}"
    if not year_dir.exists():
        return pd.DataFrame()
    df = load_data(year_dir)
    if df.empty:
        return df
    df = df.dropna(subset=["mean_rating", "citations", "decision"]).copy()
    df["log_citations"] = np.log1p(df["citations"])
    df["label"] = df["decision"].apply(categorize_decision)
    df = df[df["label"].isin(["Oral", "Spotlight", "Poster"])]
    df["year"] = year
    return df


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def within_label_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson r(mean_rating, log_citations) within each decision label."""
    rows = []
    for label in ["Poster", "Spotlight", "Oral"]:
        subset = df[df["label"] == label]
        n = len(subset)
        if n < 10:
            rows.append({"label": label, "n": n, "r": np.nan, "p": np.nan})
            continue
        r, p = stats.pearsonr(subset["mean_rating"], subset["log_citations"])
        rows.append({"label": label, "n": n, "r": r, "p": p})
    return pd.DataFrame(rows)


def hierarchical_regression(df: pd.DataFrame) -> dict:
    """Compare total vs direct effect of mean_rating on log_citations.

    Model A (total):  log_citations ~ mean_rating
    Model B (direct): log_citations ~ mean_rating + C(label)

    Returns dict with beta_total, beta_direct, attenuation_pct, etc.
    """
    df = df.copy()
    df["label"] = pd.Categorical(df["label"],
                                  categories=["Poster", "Spotlight", "Oral"],
                                  ordered=True)
    # Model A – total effect
    model_a = smf.ols("log_citations ~ mean_rating", data=df).fit()
    beta_total = model_a.params["mean_rating"]
    p_total = model_a.pvalues["mean_rating"]

    # Model B – direct effect (controlling for label)
    model_b = smf.ols("log_citations ~ mean_rating + C(label)", data=df).fit()
    beta_direct = model_b.params["mean_rating"]
    p_direct = model_b.pvalues["mean_rating"]

    attenuation = (1 - beta_direct / beta_total) * 100 if beta_total != 0 else np.nan

    return {
        "beta_total": beta_total,
        "p_total": p_total,
        "r2_total": model_a.rsquared,
        "beta_direct": beta_direct,
        "p_direct": p_direct,
        "r2_with_label": model_b.rsquared,
        "attenuation_pct": attenuation,
    }


def overall_correlation(df: pd.DataFrame) -> dict:
    """Overall Pearson r(mean_rating, log_citations)."""
    r, p = stats.pearsonr(df["mean_rating"], df["log_citations"])
    return {"r_overall": r, "p_overall": p, "n": len(df)}


# ---------------------------------------------------------------------------
# Year-wise runner
# ---------------------------------------------------------------------------

def run_all_years(data_root: Path, years: list = None):
    """Run analysis for every year, collect results."""
    if years is None:
        years = YEARS
    reg_rows = []
    corr_rows = []

    for year in years:
        df = load_year(year, data_root)
        if df.empty or len(df) < 30:
            logger.warning(f"Skipping {year}: too few records ({len(df)})")
            continue

        # Overall correlation for this year
        ov = overall_correlation(df)

        # Hierarchical regression
        hr = hierarchical_regression(df)
        hr["year"] = year
        hr["r_overall"] = ov["r_overall"]
        hr["p_overall"] = ov["p_overall"]
        hr["n"] = ov["n"]
        reg_rows.append(hr)

        # Within-label correlations
        wl = within_label_correlations(df)
        wl["year"] = year
        corr_rows.append(wl)

    reg_df = pd.DataFrame(reg_rows)
    corr_df = pd.concat(corr_rows, ignore_index=True)
    return reg_df, corr_df


# ---------------------------------------------------------------------------
# Pretty-print
# ---------------------------------------------------------------------------

def print_results(reg_df: pd.DataFrame, corr_df: pd.DataFrame):
    print("\n" + "=" * 80)
    print("  TEST: Is rating–citation correlation entirely mediated by decision label?")
    print("=" * 80)

    # --- Hierarchical regression summary ---
    print("\n--- Hierarchical Regression (Rating effect: Total vs Direct) ---\n")
    header = f"{'Year':>6}  {'N':>5}  {'r(overall)':>11}  {'β_total':>9}  {'p_total':>9}  {'β_direct':>9}  {'p_direct':>9}  {'Attenuation':>11}"
    print(header)
    print("-" * len(header))
    for _, row in reg_df.iterrows():
        sig_total = "***" if row["p_total"] < 0.001 else ("**" if row["p_total"] < 0.01 else ("*" if row["p_total"] < 0.05 else "ns"))
        sig_direct = "***" if row["p_direct"] < 0.001 else ("**" if row["p_direct"] < 0.01 else ("*" if row["p_direct"] < 0.05 else "ns"))
        print(
            f"{int(row['year']):>6}  {int(row['n']):>5}  "
            f"{row['r_overall']:>8.3f}     "
            f"{row['beta_total']:>8.4f} {sig_total:<3}  "
            f"{row['beta_direct']:>8.4f} {sig_direct:<3}  "
            f"{row['attenuation_pct']:>8.1f}%"
        )

    # --- Within-label correlations ---
    print("\n\n--- Within-Label Correlations: r(rating, log_citations) ---\n")
    pivot = corr_df.pivot(index="year", columns="label", values="r")
    pivot_p = corr_df.pivot(index="year", columns="label", values="p")
    pivot_n = corr_df.pivot(index="year", columns="label", values="n")

    for label in ["Poster", "Spotlight", "Oral"]:
        if label not in pivot.columns:
            continue
    
    header2 = f"{'Year':>6}  {'Poster r':>10}  {'p':>7}  {'n':>5}  {'Spotlight r':>12}  {'p':>7}  {'n':>5}  {'Oral r':>8}  {'p':>7}  {'n':>5}"
    print(header2)
    print("-" * len(header2))

    for year in sorted(corr_df["year"].unique()):
        parts = [f"{year:>6}"]
        for label in ["Poster", "Spotlight", "Oral"]:
            try:
                r_val = pivot.loc[year, label]
                p_val = pivot_p.loc[year, label]
                n_val = int(pivot_n.loc[year, label])
                if np.isnan(r_val):
                    parts.append(f"{'N/A':>10}  {'N/A':>7}  {n_val:>5}")
                else:
                    sig = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else "ns"))
                    parts.append(f"{r_val:>10.3f}  {sig:>7}  {n_val:>5}")
            except (KeyError, ValueError):
                parts.append(f"{'N/A':>10}  {'N/A':>7}  {'N/A':>5}")
        print("  ".join(parts))

    # --- Interpretation ---
    print("\n\n--- Interpretation ---")
    mean_attenuation = reg_df["attenuation_pct"].mean()
    n_direct_sig = (reg_df["p_direct"] < 0.05).sum()
    n_years = len(reg_df)
    poster_corrs = corr_df[corr_df["label"] == "Poster"]["r"].dropna()
    mean_poster_r = poster_corrs.mean() if len(poster_corrs) > 0 else np.nan

    print(f"\n  Mean attenuation of rating effect after controlling for label: {mean_attenuation:.1f}%")
    print(f"  Rating remains significant (p<0.05) in {n_direct_sig}/{n_years} years after label control")
    print(f"  Mean within-Poster correlation: r = {mean_poster_r:.3f}")

    if mean_attenuation > 80 and n_direct_sig <= 1:
        print("\n  ★ CONCLUSION: Strong evidence for COMPLETE mediation.")
        print("    The rating–citation correlation is almost entirely explained by the decision label.")
    elif mean_attenuation > 50:
        print("\n  ★ CONCLUSION: Evidence for PARTIAL mediation.")
        print("    The decision label accounts for a substantial share, but rating retains some direct effect.")
    else:
        print("\n  ★ CONCLUSION: Weak mediation.")
        print("    Rating has a substantial direct effect on citations beyond the label.")


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_mediation_decomposition(reg_df: pd.DataFrame, output_dir: Path):
    """Bar chart: β_total vs β_direct per year, showing attenuation."""
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5.5))

    x = np.arange(len(reg_df))
    width = 0.35

    bars_total = ax.bar(x - width / 2, reg_df["beta_total"], width,
                        label="Total effect (Rating only)", color="#3498db", alpha=0.85)
    bars_direct = ax.bar(x + width / 2, reg_df["beta_direct"], width,
                         label="Direct effect (Rating | Label)", color="#e74c3c", alpha=0.85)

    # Annotate attenuation %
    for i, (_, row) in enumerate(reg_df.iterrows()):
        att = row["attenuation_pct"]
        sig_d = "ns" if row["p_direct"] >= 0.05 else "*"
        ax.annotate(
            f"−{att:.0f}%",
            (x[i], max(row["beta_total"], row["beta_direct"]) + 0.01),
            ha="center", fontsize=9, fontweight="bold", color="#2c3e50"
        )

    ax.set_xticks(x)
    ax.set_xticklabels([str(int(y)) for y in reg_df["year"]], fontsize=11)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("β (Rating coefficient)", fontsize=12)
    ax.set_title("Rating Effect on Citations: Total vs After Controlling for Label",
                 fontsize=14, fontweight="bold", pad=14)
    ax.legend(fontsize=11)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.tick_params(labelsize=11)

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "Mediation_Decomposition.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved {path}")


def plot_within_label_correlations(corr_df: pd.DataFrame, output_dir: Path):
    """Line chart: within-label r(rating, citations) per year."""
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5.5))

    palette = {"Poster": "#3498db", "Spotlight": "#f39c12", "Oral": "#e74c3c"}

    for label in ["Poster", "Spotlight", "Oral"]:
        sub = corr_df[corr_df["label"] == label].copy()
        sub = sub.dropna(subset=["r"])
        if sub.empty:
            continue
        ax.plot(sub["year"], sub["r"], marker="o", linewidth=2.2, label=label,
                color=palette[label], markersize=7)

        # Mark significance
        for _, row in sub.iterrows():
            if row["p"] >= 0.05:
                ax.annotate("ns", (row["year"], row["r"]),
                            textcoords="offset points", xytext=(0, 10),
                            fontsize=8, ha="center", color="grey")

    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Pearson r (rating vs log-citations)", fontsize=12)
    ax.set_title("Within-Label Correlation: Rating vs Citations\n(controlling for decision label)",
                 fontsize=14, fontweight="bold", pad=14)
    ax.legend(title="Label", fontsize=11, title_fontsize=12)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.tick_params(labelsize=11)

    plt.tight_layout()
    path = output_dir / "Within_Label_Correlations.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, default=YEARS)
    args = parser.parse_args()

    years_to_run = args.years

    repo_root = Path(__file__).resolve().parents[2]
    data_root = repo_root / "data"
    output_dir = Path(__file__).resolve().parent / "figs"

    reg_df, corr_df = run_all_years(data_root, years_to_run)

    if reg_df.empty:
        logger.error("No results – check data.")
        return

    print_results(reg_df, corr_df)
    plot_mediation_decomposition(reg_df, output_dir)
    plot_within_label_correlations(corr_df, output_dir)


if __name__ == "__main__":
    main()
