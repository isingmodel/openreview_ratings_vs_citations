# Polarization Analysis (Reviewer Disagreement)

**Last Updated:** Feb 11, 2026
**Status:** COMPLETE (Workshop Papers Excluded)

## Hypothesis
**"The Polarization Hypothesis"**: Papers with highly divisive reviews (large variance or range in scores) may be more impactful than papers with consistently moderate scores. High disagreement often signals novel, controversial, or paradigm-shifting ideas.

## Methodology

### Changes (Feb 2026)
- **Data Filtering:** "Invite to Workshop Track" papers (2017-2018) have been **excluded** to align with other analyses. These papers introduce noise as they are statistically distinct from standard acceptances.
- **Metric:** We consistently use **Rating Range** ($\max - \min$) as the measure of disagreement.
  - **Consensus**: Range < 4
  - **Controversial**: Range ≥ 4 (e.g., ratings of 3, 8, 8)

## Results (2017-2023)

The analysis compares the mean Log(Citations + 1) of "Controversial" vs "Consensus" papers.

| Year | Total Papers | % Controversial | Mean Citations (Controversial) | Mean Citations (Consensus) | P-Value (T-Test) | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2017** | 198 | 5.1% | 793.2 | **1232.0** | 0.73 | No Effect (Lower) |
| **2018** | 337 | 11.6% | **861.3** | 739.9 | 0.45 | No Effect (Higher) |
| **2019** | 502 | 7.6% | 487.6 | 460.6 | 0.78 | No Effect |
| **2020** | 687 | 20.5% | 277.8 | 301.8 | 0.09 | No Effect (Lower) |
| **2021** | 859 | 12.0% | 218.3 | **328.7** | 0.38 | No Effect (Lower) |
| **2022** | 1094 | 11.6% | 95.6 | **157.2** | 0.36 | No Effect (Lower) |
| **2023** | 1573 | 12.9% | **130.4** | 101.8 | 0.09 | No Effect (Higher) |

*> Note: P-values > 0.05 indicate no statistically significant difference between the groups.*

## Conclusion

**The Polarization Hypothesis is NOT supported by the data.**

1.  **No Consistent Advantage:** In 5 out of 7 years (2017, 2019, 2020, 2021, 2022), "Controversial" papers had *lower* or effectively equal average citations compared to "Consensus" papers.
2.  **Occasional Signals are Weak:** While 2018 and 2023 showed higher averages for controversial papers, the differences were not statistically significant (p = 0.45 and p = 0.09 respectively).
3.  **Reviewer Disagreement is not a Signal of Quality:** High variance in ratings does not consistently predict future impact. It is more likely a sign of genuine flaws or mixed quality rather than "misunderstood genius."

## Figures

The generated figures in `figs/` visualize these distributions:
- **Boxplots**: Show the citation distribution for each Rating Range bucket.
- **Scatterplots**: Highlight controversial papers in Red against the mean rating trend.
