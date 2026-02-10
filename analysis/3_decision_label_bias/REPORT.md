# The "Label Effect": How Conference Distinctions Overshadow Peer Review Scores
**An Empirical Analysis of ICLR (2017–2023)**

## Abstract
This study investigates the relationship between peer review ratings, conference decision labels (e.g., Oral, Spotlight, Poster), and future scientific impact (measured by citations). Analyzing data from ICLR 2017 to 2023, we test the **"Label Effect Hypothesis"**: that the visible distinction assigned by the conference affects citation counts more significantly than the underlying review scores. Our results confirm a strong and increasing "Matthew Effect," where the "Oral" label significantly boosts citations regardless of the review rating. Most notably, in 2023, the predictive power of review ratings collapsed to statistical insignificance, while the "Oral" label remained the dominant predictor of impact (`Coef=1.09`, `p<0.001`).

---

## 1. Introduction & Hypothesis

### 1.1 The Problem
Peer review scores are intended to be a proxy for paper quality. Ideally, a paper with a score of 8.0 should be more impactful than a paper with a score of 6.0, regardless of whether it was assigned an "Oral" or "Poster" presentation. However, conferences enforce discrete categorizations—winning papers (Orals) vs. accepted papers (Posters)—which may create artificial gaps in visibility and prestige.

### 1.2 The Hypothesis
**The Label Effect Hypothesis**: The distinction assigned to a paper (specifically the "Oral" label) serves as a primary signal for the community, driving citations independently of the paper's actual review quality.
- **Null Hypothesis ($H_0$)**: Citation counts are primarily driven by paper quality (proxied by Review Rating). The Decision Label adds marginal or no predictive power once Rating is controlled for.
- **Alternative Hypothesis ($H_1$)**: The Decision Label is a significant predictor of citations even when controlling for Review Rating. Furthermore, this effect may be growing over time as the field becomes saturated and relies more on heuristic signals.

---

## 2. Methodology

### 2.1 Data Collection
- **Source**: OpenReview (via `openreview-py` API).
- **Scope**: All accepted papers at ICLR from 2017 to 2023.
- **Metrics**:
    - **Review Rating**: The average score given by reviewers (1-10 scale).
    - **Citations**: Collected from Google Scholar (via Zyte) and OpenAlex. We use `log(citations + 1)` to handle the heavy-tailed distribution.
    - **Decision Tier**: Categorized based on the final decision field:
        - **Top Tier**: Oral, Talk, Notable-Top-5%
        - **Middle Tier**: Spotlight, Notable-Top-25%
        - **Base Tier**: Poster

### 2.2 Statistical Model
We employ an Ordinary Least Squares (OLS) regression model to isolate the effect of the Label from the Rating:

$$ \log(\text{Citations} + 1) = \beta_0 + \beta_1 \cdot \text{MeanRating} + \beta_2 \cdot I(\text{Spotlight}) + \beta_3 \cdot I(\text{Oral}) + \epsilon $$

- $\beta_1$ represents the effect of a 1-point increase in review score.
- $\beta_3$ represents the "boost" in citations provided by the Oral label, holding the review score constant.

---

## 3. Results

### 3.1 Single Year Deep Dive (ICLR 2023)
For the most recent conference year (2023), the regression results are striking:

| Variable | Coefficient | Std. Error | t-statistic | P-value |
|----------|-------------|------------|-------------|---------|
| **Intercept** | 2.808 | 0.344 | 8.16 | < 0.001 |
| **Oral Label** | **1.090** | 0.156 | **6.99** | **< 0.001** |
| **Spotlight Label** | 0.451 | 0.095 | 4.75 | < 0.001 |
| **Mean Rating** | 0.090 | 0.053 | 1.68 | **0.092 (ns)** |

**Key Finding**: In 2023, the **Review Rating became statistically insignificant** ($p=0.092$). The "Oral" label, however, was highly significant, adding approximately `exp(1.09) ≈ 2.97x` more citations compared to a Poster baseline, regardless of the score.

### 3.2 Longitudinal Trend (2017–2023)
We tracked the regression coefficients ($\beta_1$ vs $\beta_3$) over 7 years to observe the evolution of these signals.

![Label Effect Trends](figs/Label_Effect_Trends_2017_2023.png)

| Year | Oral Label Effect ($\beta_3$) | Rating Effect ($\beta_1$) | Ratio (Label / Rating) |
|------|-------------------------------|---------------------------|------------------------|
| 2017 | 1.040 | 0.342 | 3.0x |
| 2018 | 0.680 | 0.297 | 2.3x |
| 2019 | 0.922 | 0.246 | 3.7x |
| 2020 | 0.410 | 0.099 (ns) | 4.1x |
| 2021 | 0.703 | 0.225 | 3.1x |
| 2022 | 0.586 | 0.241 | 2.4x |
| **2023** | **1.090** | **0.090 (ns)** | **12.1x** |

**Trend Analysis**:
1.  **Persistent Gap**: The Oral label has consistently been a stronger predictor than the rating score (ranging from 2.3x to 12.1x stronger).
2.  **The 2023 Divergence**: While the Label Effect has fluctuated, the Rating Effect collapsed in 2023. This suggests a transition where the community may be relying almost exclusively on the "badge" of the decision rather than the granular quality signal of the reviews.

---

## 4. Discussion & Conclusion

### 4.1 The "Matthew Effect" in Science
Our findings strongly support the existence of a **Label Effect** (or Matthew Effect), where "the rich get richer." Once a paper is designated as an "Oral," it gains visibility that drives citations, overshadowing its intrinsic review score. A paper with a 6.0 score and an Oral label will likely receive far more citations than a paper with an 8.0 score and a Poster label.

### 4.2 Implications for Peer Review
The collapse of the rating's predictive power in 2023 is concerning. It implies that:
1.  **Signal Dilution**: As the venue grows, fine-grained scores (6 vs 8) lose their meaning to the wider community.
2.  **Heuristic Reliance**: Researchers, overwhelmed by volume, may use "Oral" status as a primary filter for what to read and cite.
3.  **Arbitrary Impact**: Since the decision boundary between Oral and Poster can be subjective (and distinct from raw scores), the future impact of a paper may hinge on a binary decision made by Program Chairs, rather than the collective assessment of reviewers.

### 4.3 Future Work
Further text analysis (e.g., matching review content to decision outcomes) is needed to understand *why* certain papers with lower scores get Oral labels and whether those decisions were justified ex-post by their high impact.
