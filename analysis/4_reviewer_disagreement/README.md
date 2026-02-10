# Polarization Analysis

## Hypothesis
**"The Polarization Hypothesis"**: Papers with highly divisive reviews (large variance or range in scores) may be more impactful than papers with consistently moderate scores. High disagreement often signals novel, controversial, or paradigm-shifting ideas.

## Metrics

Instead of simple Variance (which can be unstable with few reviewers), we use **Rating Range**:

$$ \text{Rating Range} = \max(\text{Ratings}) - \min(\text{Ratings}) $$

- **Low Range (0-2)**: Consensus (e.g., 6, 6, 7).
- **High Range (≥4)**: Polarization (e.g., 3, 8, 8).

## Analysis Goals
1.  **Correlation**: Does `Rating Range` correlate with `Log Citations`?
2.  **Group Comparison**: Do "Controversial" papers (Range ≥ 4) have higher average citations than "Consensus" papers, when controlling for the mean rating?
