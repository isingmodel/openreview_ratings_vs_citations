# 📊 OpenReview Ratings vs Citations

> **Do peer review scores predict scientific impact?**  
> An empirical analysis of ICLR papers (2017–2020)

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

📺 **[PyCon Korea 2022 talk (Korean)](https://www.youtube.com/watch?v=MqM2ROgWwhU)**

---

## Key Finding

**The correlation between review ratings and citations has been declining over time:**

| Year | Papers | Correlation (r) | p-value |
|------|--------|-----------------|---------|
| 2017 | 245 | 0.40 | 6.9e-11 |
| 2018 | 425 | 0.37 | 1.6e-15 |
| 2019 | 502 | 0.19 | 1.2e-05 |
| 2020 | 687 | 0.13 | 8.9e-04 |

![2017](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2017.png?raw=true)
![2018](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2018.png?raw=true)
![2019](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2019.png?raw=true)
![2020](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2020.png?raw=true)

---

## Possible Explanations (and Their Limitations)

### ❓ Hypothesis 1–2: Reviewer Quality Degradation
> *As ICLR grew, more reviewers were needed, potentially reducing review quality.*

**Limitation:** This is unfalsifiable—there's no independent measure of "reviewer quality." An alternative explanation is that competition intensified, causing papers near the acceptance threshold to converge in quality, which naturally reduces correlation.

### ❓ Hypothesis 3: Citation Lag
> *Recent papers haven't accumulated enough citations yet.*

**Limitation:** In fast-moving ML fields, citation rankings typically stabilize within 1–2 years post-publication. Moreover, if all papers have uniformly low citations, variance decreases and correlation should actually *increase*, not decrease. This hypothesis has a logical flaw.

### 🔍 Alternative Hypotheses Worth Exploring
- **Field diversification**: As ICLR expanded, subfield-specific papers increased. Reviewers may rate fairly within their expertise, but citation counts are driven by *subfield size* (NLP >> Theory).
- **Matthew Effect**: Famous authors/institutions get cited regardless of ratings. This effect may strengthen as the venue grows.
- **Rating inflation/deflation**: Reviewer scoring norms may shift year-to-year.

---

## For Rigorous Science-of-Science Analysis

To make this publishable, consider:
1. **Apples-to-apples comparison** — Use citations at a fixed time window (e.g., 3 years post-publication) for all years
2. **Control for confounders** — Include author h-index, institution prestige, topic/subfield
3. **Statistical rigor** — Bootstrap confidence intervals to test if year-over-year differences are significant

---

## Quick Start

```bash
pip install -r requirements.txt
```

### Scrape & Analyze

> ⚠️ **Note:** Fetching citations requires a [ScraperAPI](https://www.scraperapi.com/) key to avoid Google Scholar IP blocks.

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
