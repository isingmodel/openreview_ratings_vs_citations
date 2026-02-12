"""Validate: Is it appropriate to classify 'Invite to Workshop Track' as Poster?

Compares Workshop-invited papers vs Poster papers in 2017-2018 on:
1. Rating distributions (mean, std, KS test)
2. Citation distributions (mean, median, KS test)
3. Rating–citation correlation within each group
4. Regression coefficients with workshop as a separate dummy
"""

import logging
import sys
from pathlib import Path

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


def get_label(decision: str) -> str:
    """Classify decision into Oral / Poster / Workshop / Other."""
    if not isinstance(decision, str):
        return "Unknown"
    d = decision.lower()
    if "oral" in d or "talk" in d or "top-5%" in d:
        return "Oral"
    if "spotlight" in d or "top-25%" in d:
        return "Spotlight"
    if "invite" in d or "workshop" in d:
        return "Workshop"
    if "poster" in d:
        return "Poster"
    return "Other"


def load_year(year: int, data_root: Path) -> pd.DataFrame:
    year_dir = data_root / f"ICLR{year}"
    if not year_dir.exists():
        return pd.DataFrame()
    df = load_data(year_dir)
    if df.empty:
        return df
    df = df.dropna(subset=["mean_rating", "citations", "decision"]).copy()
    df["log_citations"] = np.log1p(df["citations"])
    df["label"] = df["decision"].apply(get_label)
    df["year"] = year
    return df


def compare_distributions(df_poster: pd.DataFrame, df_workshop: pd.DataFrame, year: int):
    """Compare rating and citation distributions between Poster and Workshop."""
    print(f"\n{'='*70}")
    print(f"  ICLR {year}: Poster vs Workshop Track Comparison")
    print(f"{'='*70}")

    print(f"\n  Sample sizes: Poster = {len(df_poster)}, Workshop = {len(df_workshop)}")

    # --- Rating comparison ---
    print(f"\n  --- Rating Distribution ---")
    print(f"  {'':>20}  {'Poster':>10}  {'Workshop':>10}")
    print(f"  {'Mean':>20}  {df_poster['mean_rating'].mean():>10.2f}  {df_workshop['mean_rating'].mean():>10.2f}")
    print(f"  {'Median':>20}  {df_poster['mean_rating'].median():>10.2f}  {df_workshop['mean_rating'].median():>10.2f}")
    print(f"  {'Std':>20}  {df_poster['mean_rating'].std():>10.2f}  {df_workshop['mean_rating'].std():>10.2f}")
    print(f"  {'Min':>20}  {df_poster['mean_rating'].min():>10.2f}  {df_workshop['mean_rating'].min():>10.2f}")
    print(f"  {'Max':>20}  {df_poster['mean_rating'].max():>10.2f}  {df_workshop['mean_rating'].max():>10.2f}")

    ks_stat, ks_p = stats.ks_2samp(df_poster["mean_rating"], df_workshop["mean_rating"])
    t_stat, t_p = stats.ttest_ind(df_poster["mean_rating"], df_workshop["mean_rating"])
    print(f"\n  KS test (ratings): D = {ks_stat:.3f}, p = {ks_p:.4f}")
    print(f"  t-test (ratings):  t = {t_stat:.3f}, p = {t_p:.4f}")

    # --- Citation comparison ---
    print(f"\n  --- Citation Distribution ---")
    print(f"  {'':>20}  {'Poster':>10}  {'Workshop':>10}")
    print(f"  {'Mean citations':>20}  {df_poster['citations'].mean():>10.1f}  {df_workshop['citations'].mean():>10.1f}")
    print(f"  {'Median citations':>20}  {df_poster['citations'].median():>10.1f}  {df_workshop['citations'].median():>10.1f}")
    print(f"  {'Mean log(cit+1)':>20}  {df_poster['log_citations'].mean():>10.2f}  {df_workshop['log_citations'].mean():>10.2f}")

    ks_stat_c, ks_p_c = stats.ks_2samp(df_poster["log_citations"], df_workshop["log_citations"])
    t_stat_c, t_p_c = stats.ttest_ind(df_poster["log_citations"], df_workshop["log_citations"])
    mwu_stat, mwu_p = stats.mannwhitneyu(df_poster["citations"], df_workshop["citations"], alternative="two-sided")
    print(f"\n  KS test (log-cit): D = {ks_stat_c:.3f}, p = {ks_p_c:.4f}")
    print(f"  t-test (log-cit):  t = {t_stat_c:.3f}, p = {t_p_c:.4f}")
    print(f"  Mann-Whitney U:    U = {mwu_stat:.0f}, p = {mwu_p:.4f}")

    # --- Within-group correlations ---
    print(f"\n  --- Rating-Citation Correlation ---")
    for name, sub in [("Poster", df_poster), ("Workshop", df_workshop)]:
        if len(sub) >= 10:
            r, p = stats.pearsonr(sub["mean_rating"], sub["log_citations"])
            print(f"  {name:>10}: r = {r:.3f}, p = {p:.4f}, n = {len(sub)}")
        else:
            print(f"  {name:>10}: too few samples (n={len(sub)})")

    return {
        "year": year,
        "n_poster": len(df_poster),
        "n_workshop": len(df_workshop),
        "mean_rating_poster": df_poster["mean_rating"].mean(),
        "mean_rating_workshop": df_workshop["mean_rating"].mean(),
        "rating_t_p": t_p,
        "mean_logcit_poster": df_poster["log_citations"].mean(),
        "mean_logcit_workshop": df_workshop["log_citations"].mean(),
        "citation_mwu_p": mwu_p,
    }


def regression_with_workshop_dummy(df: pd.DataFrame, year: int):
    """Run regression with Workshop as a separate category (not merged with Poster)."""
    sub = df[df["label"].isin(["Poster", "Workshop", "Oral"])].copy()
    sub["label"] = pd.Categorical(sub["label"], categories=["Poster", "Workshop", "Oral"], ordered=True)

    print(f"\n  --- Regression with Workshop as Separate Dummy (ICLR {year}) ---")
    model = smf.ols("log_citations ~ mean_rating + C(label)", data=sub).fit()

    print(f"\n  {'Variable':>25}  {'Coef':>8}  {'Std Err':>8}  {'t':>7}  {'P>|t|':>8}")
    print(f"  {'-'*60}")
    for var in model.params.index:
        coef = model.params[var]
        se = model.bse[var]
        t = model.tvalues[var]
        p = model.pvalues[var]
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
        short = var.replace("C(label)[T.", "").replace("]", "")
        print(f"  {short:>25}  {coef:>8.3f}  {se:>8.3f}  {t:>7.2f}  {p:>7.4f} {sig}")

    return model


def plot_comparison(df: pd.DataFrame, year: int, output_dir: Path):
    """Side-by-side violin plots for Poster vs Workshop."""
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    sub = df[df["label"].isin(["Poster", "Workshop"])].copy()
    palette = {"Poster": "#3498db", "Workshop": "#e67e22"}

    # Rating distribution
    import seaborn as sns
    sns.violinplot(data=sub, x="label", y="mean_rating", palette=palette,
                   inner="quartile", ax=axes[0])
    axes[0].set_title(f"ICLR {year}: Rating Distribution", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Mean Review Rating", fontsize=11)

    # Citation distribution
    sns.violinplot(data=sub, x="label", y="log_citations", palette=palette,
                   inner="quartile", ax=axes[1])
    axes[1].set_title(f"ICLR {year}: Citation Distribution", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Log(Citations + 1)", fontsize=11)

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"Poster_vs_Workshop_{year}.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved {path}")


def main():
    repo_root = Path(__file__).resolve().parents[2]
    data_root = repo_root / "data"
    output_dir = Path(__file__).resolve().parent / "figs"

    print("\n" + "=" * 70)
    print("  ANALYSIS: Should 'Invite to Workshop Track' be classified as Poster?")
    print("=" * 70)

    all_results = []

    for year in [2017, 2018]:
        df = load_year(year, data_root)
        if df.empty:
            continue

        df_poster = df[df["label"] == "Poster"]
        df_workshop = df[df["label"] == "Workshop"]

        if df_workshop.empty:
            logger.warning(f"No Workshop papers found for {year}")
            continue

        result = compare_distributions(df_poster, df_workshop, year)
        all_results.append(result)
        regression_with_workshop_dummy(df, year)
        plot_comparison(df, year, output_dir)

    # --- Summary verdict ---
    print(f"\n\n{'='*70}")
    print("  SUMMARY VERDICT")
    print(f"{'='*70}\n")

    for r in all_results:
        yr = r["year"]
        rating_sig = "YES (different)" if r["rating_t_p"] < 0.05 else "NO (similar)"
        cit_sig = "YES (different)" if r["citation_mwu_p"] < 0.05 else "NO (similar)"
        print(f"  ICLR {yr}:")
        print(f"    Rating distributions significantly different? {rating_sig} (p={r['rating_t_p']:.4f})")
        print(f"    Citation distributions significantly different? {cit_sig} (p={r['citation_mwu_p']:.4f})")
        print(f"    Mean rating: Poster={r['mean_rating_poster']:.2f}, Workshop={r['mean_rating_workshop']:.2f}")
        print(f"    Mean log-cit: Poster={r['mean_logcit_poster']:.2f}, Workshop={r['mean_logcit_workshop']:.2f}")
        print()


if __name__ == "__main__":
    main()
