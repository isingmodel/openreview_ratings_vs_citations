"""Shared logic for OpenReview analysis."""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_rating_data(rating_data):
    """Parse rating data from various formats into a standardized list of dicts.
    
    Rating data in the preprocessed parquet may be stored as:
    - JSON string: '[{"rating": 6, "confidence": 4}, ...]'
    - List of ints (legacy): [6, 7, 8]
    - List of dicts: [{'rating': 6, 'confidence': 4}, ...]
    
    Args:
        rating_data: Raw rating data in any of the above formats.
    
    Returns:
        list: Standardized list of dicts with 'rating' and 'confidence' keys.
              Empty list if parsing fails.
    """
    if isinstance(rating_data, str):
        try:
            rating_data = json.loads(rating_data)
        except:
            return []
            
    if not isinstance(rating_data, list):
        return []

    # Check if it's list of ints or dicts
    if not rating_data:
        return []
        
    if isinstance(rating_data[0], int):
        # Legacy format: [6, 6, 8] -> treat as confidence 4 (average)
        return [{"rating": r, "confidence": 4} for r in rating_data]
        
    if isinstance(rating_data[0], dict):
        return rating_data
        
    return []


def calculate_weighted_rating(ratings):
    """Calculate confidence-weighted average rating.
    
    Computes: sum(rating_i * confidence_i) / sum(confidence_i)
    
    This weights each reviewer's rating by their stated confidence,
    giving more influence to reviewers who are more certain.
    
    Args:
        ratings: List of dicts with 'rating' and 'confidence' keys.
    
    Returns:
        float: Weighted average rating, or None if no valid ratings.
    """
    if not ratings:
        return None
    
    total_score = 0
    total_conf = 0
    
    for r in ratings:
        val = r.get("rating")
        conf = r.get("confidence")
        
        if val is None:
            continue
            
        # Default confidence to 1 if missing (or maybe 3? using 1 for safe low weight)
        weight = conf if conf is not None else 1
        
        total_score += val * weight
        total_conf += weight
        
    if total_conf == 0:
        return None
        
    return total_score / total_conf



def normalize_title(title: str) -> str:
    """Normalize title for matching.
    
    Logic:
    - Lowercase conversion
    - Whitespace normalization (multiple spaces -> single space)
    - Stripping leading/trailing whitespace
    """
    return " ".join(str(title).lower().split())


def load_data(data_dir: Path) -> pd.DataFrame:
    """Load preprocessed paper data and merge with citation data.
    
    Loads the preprocessed.parquet file and matches papers with OpenAlex
    citation counts using case-insensitive, whitespace-normalized title matching.
    
    Args:
        data_dir: Path to the ICLR year directory (e.g., data/ICLR2019/).
    
    Returns:
        pd.DataFrame with columns:
            - title, authors, rating, decision (from parquet)
            - rating_data: Parsed list of rating dicts
            - mean_rating: Simple average of ratings
            - weighted_rating: Confidence-weighted average
            - high_conf_rating: Mean of ratings with confidence >= 4
            - low_conf_rating: Mean of ratings with confidence < 4
            - citations: Citation count from OpenAlex (or None if not matched)
    """
    # Load preprocessed data
    parquet_path = data_dir / "preprocessed.parquet"
    if not parquet_path.exists():
        return pd.DataFrame()
        
    df = pd.read_parquet(parquet_path)

    # Parse rating data
    df["rating_data"] = df["rating"].apply(parse_rating_data)
    
    # Calculate simple mean rating
    df["mean_rating"] = df["rating_data"].apply(
        lambda x: np.mean([r["rating"] for r in x]) if x else None
    )
    
    # Calculate weighted mean rating
    df["weighted_rating"] = df["rating_data"].apply(calculate_weighted_rating)
    
    # Calculate high confidence mean rating (Confidence >= 4)
    def mean_high_conf(ratings):
        vals = [r["rating"] for r in ratings if (r.get("confidence") or 0) >= 4]
        return np.mean(vals) if vals else None
    df["high_conf_rating"] = df["rating_data"].apply(mean_high_conf)
    
    # Calculate low confidence mean rating (Confidence < 4)
    def mean_low_conf(ratings):
        vals = [r["rating"] for r in ratings if (r.get("confidence") or 0) < 4 and r.get("confidence") is not None]
        return np.mean(vals) if vals else None
    df["low_conf_rating"] = df["rating_data"].apply(mean_low_conf)

    # Load citations
    citation_files = list(data_dir.glob("openalex*.json"))
    
    if citation_files:
        # Sort to pick the latest file if multiple exist
        citation_file = sorted(citation_files)[-1]
        with open(citation_file, "r", encoding="utf-8") as f:
            citations = json.load(f)

        # Build case-insensitive lookup (normalize: lowercase + strip whitespace)
        citation_lookup = {
            normalize_title(t): v 
            for t, v in citations.items()
        }
        
        # Merge citations with case-insensitive matching
        df["citations"] = df["title"].apply(
            lambda t: citation_lookup.get(
                normalize_title(t), {}
            ).get("num_citations")
        )
        logger.info(f"Merged citations from {citation_file.name}")
    else:
        logger.warning(f"No OpenAlex citation file found in {data_dir}!")

    return df
