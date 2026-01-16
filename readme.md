# OpenReview Ratings vs Citations

> **Do peer review scores predict scientific impact?**  
> An empirical analysis of ICLR papers (2017–2020)

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

📺 **[PyCon Korea 2022 talk (Korean)](https://www.youtube.com/watch?v=MqM2ROgWwhU)**

---

## Key Finding

**The correlation between review ratings and citations has been declining over time:**

| Year | Papers | Pearson (r) | Spearman (ρ) |
|------|--------|-------------|--------------|
| 2017 | 245 | 0.40 | 0.35 |
| 2018 | 425 | 0.37 | 0.36 |
| 2019 | 502 | 0.19 | 0.19 |
| 2020 | 687 | 0.13 | 0.14 |

<table>
  <tr>
    <td><img src="https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2017.png" width="400"/></td>
    <td><img src="https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2018.png" width="400"/></td>
  </tr>
  <tr>
    <td><img src="https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2019.png" width="400"/></td>
    <td><img src="https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2020.png" width="400"/></td>
  </tr>
</table>

### Methodology

We report both **Pearson (r)** and **Spearman (ρ)** correlations:

- **Pearson**: Measures linear relationship between mean rating and log(citations + 1). Assumes roughly normal distributions.
- **Spearman**: Rank-based, non-parametric. More appropriate for ordinal rating data; robust to outliers.

Both methods show consistent results—**the declining trend is robust to the choice of correlation metric**.

**Why log(citations + 1)?**

Citation counts follow a heavy-tailed distribution ([Redner, 1998](https://doi.org/10.1007/s100510050276); [Radicchi et al., 2008](https://doi.org/10.1073/pnas.0806977105)). Log transformation reduces outlier dominance and reflects scale-level differences (10→100 is more meaningful than 10,000→10,090).

---

## Possible Explanations (and Their Limitations)

### Hypothesis 1: Reviewer Quality Degradation
> *As ICLR grew, more reviewers were needed, potentially reducing review quality.*

**Limitation:** This is unfalsifiable—there's no independent measure of "reviewer quality." An alternative explanation is that competition intensified, causing papers near the acceptance threshold to converge in quality, which naturally reduces correlation.

### Hypothesis 2: Citation Lag
> *Recent papers haven't accumulated enough citations yet.*

**Limitation:** In fast-moving ML fields, citation rankings typically stabilize within 1–2 years post-publication. Moreover, if all papers have uniformly low citations, variance decreases and correlation should actually *increase*, not decrease. This hypothesis has a logical flaw.

### Alternative Hypotheses Worth Exploring
- **Field diversification**: As ICLR expanded, subfield-specific papers increased. Reviewers may rate fairly within their expertise, but citation counts are driven by *subfield size* (NLP >> Theory).
- **Matthew Effect**: Famous authors/institutions get cited regardless of ratings. This effect may strengthen as the venue grows.
- **Rating inflation/deflation**: Reviewer scoring norms may shift year-to-year.


---

## Quick Start

```bash
pip install -r requirements.txt
```

### Scrape & Analyze

> **Note:** Fetching citations requires a [ScraperAPI](https://www.scraperapi.com/) key to avoid Google Scholar IP blocks.

```bash
# 1. Fetch OpenReview data
python scripts/scrape_openreview.py --year 2024

# 2. Get Google Scholar citations
python scripts/scrape_citations.py --input data/ICLR2024/preprocessed.parquet --apikey YOUR_KEY

# 3. Generate correlation plot
python scripts/analyze.py --year 2024
```

**Options:**
- `--min-rating 6.0` — Exclude papers below 6 (filter desk rejects influenced by Program Chairs)
- `--output figs/custom/` — Custom output directory

---

## Project Structure

```
├── scripts/
│   ├── scrape_openreview.py    # Fetch data from OpenReview
│   ├── scrape_citations.py     # Fetch Google Scholar citations
│   └── analyze.py              # Run correlation analysis
├── data/ICLR20**/
│   ├── preprocessed.parquet    # Processed paper data
│   └── googlescholar_*.json    # Citation data
└── figs/                       # Generated plots
```

---

## References

- [OpenReview Explorer](https://horace.io/OpenReviewExplorer/) — Interactive visualization
- [An Open Review of OpenReview](https://openreview.net/forum?id=Cn706AbJaKW) — Critical analysis of ML peer review
- [Dynamic Patterns of Open Review Process](https://www.sciencedirect.com/science/article/abs/pii/S0378437121005185) — Dynamics of review systems

---

<p align="center">
  <i>Questions or ideas? Open an issue!</i>
</p>
