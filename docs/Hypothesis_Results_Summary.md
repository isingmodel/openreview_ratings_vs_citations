# Analysis Results: Polarization & Label Effect (2017-2023)

## 1. Label Effect Trends (2017-2023)
**Key Finding**: The "Label" (Oral/Spotlight) has consistently outweighed the raw review score, and the gap is widening.

### Regression Coefficients Over Time
We compared the effect size (coefficient) of having an "Oral" label vs. a 1-point increase in Review Rating.

| Year | Oral Label Coef | Rating Coef | Ratio (Label/Rating) |
|------|-----------------|-------------|----------------------|
| 2017 | 1.040           | 0.342       | 3.0x                 |
| 2018 | 0.680           | 0.297       | 2.3x                 |
| 2019 | 0.922           | 0.246       | 3.7x                 |
| 2020 | 0.410           | 0.099 (ns)  | 4.1x                 |
| 2021 | 0.703           | 0.225       | 3.1x                 |
| 2022 | 0.586           | 0.241       | 2.4x                 |
| **2023** | **1.090**   | **0.090 (ns)** | **12.1x**            |

> *(ns) = Not Statistically Significant (p > 0.05)*

### Interpretation
- **Dominance of Labels**: In every single year, the "Oral" label was a stronger predictor of citations than the review score itself.
- **The 2023 Shift**: In 2023, the effect of Review Rating correctly collapsed (Coef 0.09, p>0.05), while the Oral Label effect soared (Coef 1.09). This suggests that for the most recent ICLR, **the review score essentially became irrelevant** for predicting impact once the decision label was known.
- **"The Matthew Effect"**: The rich get richer. The "Oral" badge acts as a powerful signal that drives citations, potentially overshadowing the actual quality signal contained in the fine-grained review scores.

![Trend Plot](analysis/label_effect/figs/Label_Effect_Trends_2017_2023.png)

## 2. Polarization Hypothesis (Summary)
**Status**: Inconclusive / Weak Signal.
While "Controversial" papers exist (~13%), they do not consistently outperform "Consensus" papers when controlling for other factors. The "Label Effect" is the far stronger driver of citation differences.
