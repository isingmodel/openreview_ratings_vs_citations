# Label Effect Analysis

## Hypothesis
**"The Label Effect Hypothesis"**: The visible label of a paper (Oral, Spotlight, Poster) impacts its citation count significantly, potentially more than the review score itself. This is a form of "Matthew Effect" where the rich get richer because they were labeled as "rich".

## Metrics

We categorize papers based on their final decision:

- **Top Tier**: Oral / Talk / Notable-Top-5%
- **Middle Tier**: Spotlight / Notable-Top-25%
- **Base Tier**: Poster

## Analysis Goals
1.  **Regression Analysis**: `Log Citations ~ Mean Rating + C(Decision_Tier)`
    - Check if `Decision_Tier` is statistically significant when controlling for `Mean Rating`.
2.  **Visualization**: Box plots of citations by tier.
