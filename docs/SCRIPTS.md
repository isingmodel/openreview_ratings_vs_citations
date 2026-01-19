# Scripts Documentation

Detailed documentation for scraping and analysis scripts.

---

## 1. scrape_openreview.py

Collects ICLR paper data from OpenReview.

### API Versioning

| Year | API Version | Endpoint |
|------|-------------|----------|
| 2017-2020 | v1 (legacy) | `api.openreview.net` |
| 2021-2025 | v2 | `api2.openreview.net` |

```python
# Automatic version selection
scrape_openreview(year)  # Tries v1 → falls back to v2 (2021+)
```

### Usage

```bash
# Basic usage
python scripts/scrape_openreview.py --year 2024

# Testing (limited)
python scripts/scrape_openreview.py --year 2024 --limit 100

# Resume from offset
python scripts/scrape_openreview.py --year 2019 --offset 500
```

### Output

```
data/ICLR{year}/
├── openreview_raw.json      # All submission data
└── preprocessed.parquet     # Accepted papers + computed metrics
```

---

## 2. scrape_citations_openalex.py

Fetches paper citation counts using the OpenAlex API.

### Usage

```bash
python scripts/scrape_citations_openalex.py \
    --input data/ICLR2024/preprocessed.parquet \
    --email your_email@example.com
```

> **Note**: OpenAlex recommends providing an email for polite pool access.

### Output

```
data/ICLR{year}/openalex_citations_{YYMMDD}.json
```

---

## 3. analyze.py

Analyzes the correlation between review scores and citation counts.

### Key Functions

| Function | Description |
|----------|-------------|
| `load_data()` | Loads parquet + OpenAlex data with **case-insensitive** title matching |
| `parse_rating_data()` | Parses ratings from JSON/list formats |
| `calculate_weighted_rating()` | Computes confidence-weighted average |

### Confidence Metrics

```python
# Computed metrics
mean_rating        # Simple average
weighted_rating    # Σ(rating × confidence) / Σ(confidence)
high_conf_rating   # Mean of reviews with Confidence ≥ 4
low_conf_rating    # Mean of reviews with Confidence < 4
```

### Usage

```bash
# Basic analysis
python scripts/analyze.py --year 2024

# Filter by minimum rating
python scripts/analyze.py --year 2019 --min-rating 6.0

# Custom output directory
python scripts/analyze.py --year 2024 --output figs/custom/
```

---

## 4. analyze_multi_year.py

Analyzes trends across multiple years.

### Usage

```bash
python scripts/analyze_multi_year.py --years 2017 2018 2019 2020 2021 2022 2023
```

### Output

- `figs/analysis/Correlation_Trends_2017_2023.png`
- `analysis/result.md`

---

## Testing

### Setup

```bash
pip install pytest
```

### Run Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific tests
python -m pytest tests/test_scrape_openreview.py -v
python -m pytest tests/test_scrape_openalex.py -v
```

### Test Coverage

| File | Tests |
|------|-------|
| `test_scrape_openreview.py` | Invitation patterns, API version selection, rating parsing |
| `test_scrape_openalex.py` | Title normalization, response parsing |

### Example Test Output

```
tests/test_scrape_openreview.py::TestGetInvitation::test_known_year_2019 PASSED
tests/test_scrape_openreview.py::TestAPIVersionSelection::test_v1_years PASSED
tests/test_scrape_openalex.py::TestTitleNormalization::test_case_insensitive PASSED
```
