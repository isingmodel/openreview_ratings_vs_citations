"""Correlation analysis restricted to Poster-only papers.

Rationale: The full-sample correlation between review ratings and citations
may be inflated by the "Matthew Effect" — Oral/Spotlight papers get a
visibility boost that drives extra citations.  By restricting to Poster
papers only, we remove this confound and measure the *direct* association
between review quality signal and subsequent impact.

This mirrors analysis/1_impact_correlation but filters to Poster papers.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scripts.utils.src import load_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

YEARS = list(range(2017, 2024))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def categorize_decision(decision: str) -> str:
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


def load_poster_only(year: int, data_root: Path) -> pd.DataFrame:
    """Load data for a single year, filter to Poster papers only."""
    year_dir = data_root / f"ICLR{year}"
    if not year_dir.exists():
        return pd.DataFrame()
    df = load_data(year_dir)
    if df.empty:
        return df
    df = df.dropna(subset=["mean_rating", "citations", "decision"]).copy()
    df["label"] = df["decision"].apply(categorize_decision)
    df = df[df["label"] == "Poster"]
    df["log_citations"] = np.log1p(df["citations"])
    df["year"] = year
    return df


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def compute_correlations(data_root: Path, years: list) -> pd.DataFrame:
    """Compute year-by-year correlations for poster-only vs all-papers."""
    rows = []
    for year in years:
        # --- Poster only ---
        df_poster = load_poster_only(year, data_root)
        n_poster = len(df_poster)

        # --- All papers (for comparison) ---
        year_dir = data_root / f"ICLR{year}"
        df_all = load_data(year_dir) if year_dir.exists() else pd.DataFrame()
        if not df_all.empty:
            # Exclude Workshop papers from "All" group too, for consistent baseline
            df_all = df_all[~df_all['decision'].str.contains('Workshop', case=False, na=False)]
            df_all = df_all.dropna(subset=["mean_rating", "citations"]).copy()
            df_all["log_citations"] = np.log1p(df_all["citations"])
        n_all = len(df_all)

        row = {"year": year, "n_all": n_all, "n_poster": n_poster}

        # All papers correlation
        if n_all >= 10:
            r_all, p_all = stats.pearsonr(df_all["mean_rating"], df_all["log_citations"])
            row["r_all"] = r_all
            row["p_all"] = p_all
        else:
            row["r_all"] = np.nan
            row["p_all"] = np.nan

        # Poster-only correlation
        if n_poster >= 10:
            r_poster, p_poster = stats.pearsonr(df_poster["mean_rating"], df_poster["log_citations"])
            row["r_poster"] = r_poster
            row["p_poster"] = p_poster
        else:
            row["r_poster"] = np.nan
            row["p_poster"] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def print_results(corr_df: pd.DataFrame):
    print("\n" + "=" * 80)
    print("  Poster-Only Correlation: Controlling for the Matthew Effect")
    print("=" * 80)
    print()

    header = f"{'Year':>6}  {'n(all)':>7}  {'r(all)':>7}  {'sig':>4}  {'n(poster)':>10}  {'r(poster)':>10}  {'sig':>4}  {'Δr':>7}"
    print(header)
    print("-" * len(header))

    for _, row in corr_df.iterrows():
        sig_all = _sig(row.get("p_all", np.nan))
        sig_poster = _sig(row.get("p_poster", np.nan))
        delta = row["r_all"] - row["r_poster"] if not np.isnan(row["r_all"]) and not np.isnan(row["r_poster"]) else np.nan
        delta_str = f"{delta:>+7.3f}" if not np.isnan(delta) else f"{'N/A':>7}"
        print(
            f"{int(row['year']):>6}  "
            f"{int(row['n_all']):>7}  "
            f"{row['r_all']:>7.3f}  {sig_all:>4}  "
            f"{int(row['n_poster']):>10}  "
            f"{row['r_poster']:>10.3f}  {sig_poster:>4}  "
            f"{delta_str}"
        )

    # Summary
    valid = corr_df.dropna(subset=["r_all", "r_poster"])
    if not valid.empty:
        mean_r_all = valid["r_all"].mean()
        mean_r_poster = valid["r_poster"].mean()
        mean_delta = mean_r_all - mean_r_poster
        pct_drop = (mean_delta / mean_r_all) * 100 if mean_r_all != 0 else np.nan

        print(f"\n  Mean r(all papers): {mean_r_all:.3f}")
        print(f"  Mean r(poster only): {mean_r_poster:.3f}")
        print(f"  Mean Δr: {mean_delta:+.3f} ({pct_drop:.0f}% reduction)")

        n_sig = (valid["p_poster"] < 0.05).sum()
        print(f"  Poster-only correlation significant in {n_sig}/{len(valid)} years")


def _sig(p):
    if np.isnan(p):
        return "N/A"
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def setup_academic_style():
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "axes.labelsize": 12,
        "axes.titlesize": 14,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.edgecolor": "black",
        "axes.linewidth": 1.0,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def plot_correlation_trend(corr_df: pd.DataFrame, output_dir: Path):
    """Line chart comparing all-papers vs poster-only correlations over time."""
    setup_academic_style()
    fig, ax = plt.subplots(figsize=(10, 5.5))

    valid = corr_df.dropna(subset=["r_all", "r_poster"])

    ax.plot(valid["year"], valid["r_all"], marker="s", linewidth=2.5,
            label="All accepted papers", color="#3498db", markersize=8)
    ax.plot(valid["year"], valid["r_poster"], marker="o", linewidth=2.5,
            label="Poster papers only", color="#e74c3c", markersize=8)

    # Shade the gap
    ax.fill_between(valid["year"], valid["r_all"], valid["r_poster"],
                     alpha=0.12, color="#9b59b6")

    # Annotate gap
    for _, row in valid.iterrows():
        delta = row["r_all"] - row["r_poster"]
        mid_y = (row["r_all"] + row["r_poster"]) / 2
        if abs(delta) > 0.02:
            ax.annotate(
                f"Δ={delta:+.2f}",
                (row["year"], mid_y),
                textcoords="offset points", xytext=(12, 0),
                fontsize=8, color="#7f8c8d", ha="left"
            )

    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Pearson r (rating vs log-citations)", fontsize=12)
    ax.set_title("Rating–Citation Correlation:\nAll Papers vs Poster-Only (Matthew Effect Controlled)",
                 fontsize=14, fontweight="bold", pad=14)
    ax.legend(fontsize=11, loc="upper right")
    ax.tick_params(labelsize=11)

    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.tight_layout()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "Poster_Only_Correlation_Trend.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved {path}")


def plot_poster_scatter_grid(data_root: Path, years: list, output_dir: Path):
    """2x4 grid of scatter plots (poster-only) for each year."""
    setup_academic_style()

    n_years = len(years)
    ncols = min(4, n_years)
    nrows = (n_years + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows),
                              sharex=True, sharey=True)
    if nrows == 1 and ncols == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    global_scatter = None
    for i, year in enumerate(years):
        ax = axes[i]
        df = load_poster_only(year, data_root)

        if df.empty or len(df) < 10:
            ax.text(0.5, 0.5, f"No Data\n{year}", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(f"ICLR {year}", fontsize=13, fontweight="bold")
            continue

        r, p = stats.pearsonr(df["mean_rating"], df["log_citations"])
        n = len(df)

        scatter = ax.scatter(
            df["mean_rating"], df["log_citations"],
            c=df["log_citations"], cmap="viridis",
            alpha=0.6, s=25, edgecolors="white", linewidths=0.4,
        )
        global_scatter = scatter

        sns.regplot(data=df, x="mean_rating", y="log_citations",
                    scatter=False, color="black",
                    line_kws={"linewidth": 2, "linestyle": "--"}, ax=ax)

        sig_str = f"p < 0.001" if p < 0.001 else f"p = {p:.3f}"
        stats_text = f"$r = {r:.2f}$\n${sig_str}$\n$n = {n}$"
        ax.text(0.95, 0.05, stats_text, transform=ax.transAxes, fontsize=9,
                va="bottom", ha="right",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85, edgecolor="gray"))

        ax.set_title(f"ICLR {year} (Poster Only)", fontsize=13, fontweight="bold", pad=8)
        ax.set_xlabel("Mean Review Rating")
        ax.set_ylabel("Log(Citations + 1)")

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.tight_layout()

    if global_scatter:
        fig.subplots_adjust(right=0.92)
        cbar_ax = fig.add_axes([0.94, 0.15, 0.012, 0.7])
        cbar = fig.colorbar(global_scatter, cax=cbar_ax)
        cbar.set_label("Log(Citations + 1)", fontsize=11)

    path = output_dir / "Poster_Only_Scatter_Grid.png"
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

    repo_root = Path(__file__).resolve().parents[2]
    data_root = repo_root / "data"
    output_dir = Path(__file__).resolve().parent / "figs"

    corr_df = compute_correlations(data_root, args.years)

    if corr_df.empty:
        logger.error("No data found.")
        return

    print_results(corr_df)
    plot_correlation_trend(corr_df, output_dir)
    plot_poster_scatter_grid(data_root, args.years, output_dir)


if __name__ == "__main__":
    main()
