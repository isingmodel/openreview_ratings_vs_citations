## OpenReview Ratings vs Citations

A simple analysis comparing ICLR OpenReview official ratings and the number of citations of each accepted paper. 

This repository contains:
- OpenReview review lists and citation data of ICLR accepted papers (2017-2020)
- CLI tools for scraping and analysis
- Data analysis codes & results

![citations_vs_ratings_17](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2017.png?raw=true)
![citations_vs_ratings_18](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2018.png?raw=true)
![citations_vs_ratings_19](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2019.png?raw=true)
![citations_vs_ratings_20](https://raw.githubusercontent.com/isingmodel/openreview_ratings_vs_citations/master/figs/Log_Citation_vs_Review_Rating_ICLR_2020.png?raw=true)

## Project Structure

```
project/
├── scripts/
│   ├── scrape_openreview.py    # Fetch data from OpenReview
│   ├── scrape_citations.py     # Fetch Google Scholar citations
│   ├── analyze.py              # Run correlation analysis
│   └── convert_data.py         # Convert legacy .pkl/.hdf5 files
├── data/
│   └── ICLR20**/
│       ├── preprocessed.parquet        # Processed paper data
│       ├── openreview_raw.json         # Raw OpenReview data
│       └── googlescholar_*.json        # Citation data
├── figs/                               # Generated plots
├── utils.py                            # Utility functions
└── analysis_ipynb/                     # Legacy notebooks
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### 1. Scrape OpenReview Data

Fetch paper data for a specific ICLR year:

```bash
python scripts/scrape_openreview.py --year 2024
```

### 2. Fetch Citations

Get Google Scholar citations (requires ScraperAPI key for large batches):

```bash
python scripts/scrape_citations.py --input data/ICLR2024/preprocessed.parquet --apikey YOUR_KEY
```

### 3. Analyze Correlation

Generate correlation plot and statistics:

```bash
python scripts/analyze.py --year 2024
```

Options:
- `--min-rating 6.0` — Exclude papers with ratings below 6 (desk rejects)
- `--output figs/custom/` — Custom output directory

## Troubleshooting

- **OpenReview API changes**: The invitation pattern varies by year. Check `scrape_openreview.py` for supported patterns.
- **Google Scholar blocking**: Use the `--apikey` flag with a [ScraperAPI](https://www.scraperapi.com/) key to avoid IP blocks.
- **Legacy pickle files**: Run `python scripts/convert_data.py` to convert old `.pkl`/`.hdf5` files.

## Ideas for Future Analysis

- Papers with ratings < 6 may be influenced by Program Chair decisions
- The correlation between ratings and citations decreases over time — why?
- What about ICLR rejects that were accepted at ICML?

## References

- [OpenReviewExplorer](https://horace.io/OpenReviewExplorer/)
- [An Open Review of OpenReview](https://openreview.net/forum?id=Cn706AbJaKW)
- [Dynamic Patterns of Open Review Process](https://www.sciencedirect.com/science/article/abs/pii/S0378437121005185)
