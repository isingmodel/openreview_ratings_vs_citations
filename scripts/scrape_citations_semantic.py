
"""Fetch citation data from Semantic Scholar API with strict rate limiting and resumption."""

from __future__ import annotations

import argparse
import json
import logging
import time
import math
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm
time.sleep(7200)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"


class RateLimiter:
    """Strict rate limiter to comply with API usage limits."""
    
    def __init__(self, requests_per_minute: int = 20):
        # 100 req / 5 min = 20 req / min = 1 req / 3 sec
        # We add a small buffer: 1 req / 3.1 sec
        self.interval = 60.0 / requests_per_minute
        self.last_call = 0.0

    def wait(self):
        """Wait until enough time has passed since the last call."""
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_call = time.time()


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    return "".join(c.lower() for c in title if c.isalnum())


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def fetch_paper_data(title: str, session: requests.Session, limiter: RateLimiter, api_key: str = None) -> dict:
    """Fetch paper data from Semantic Scholar using title search."""
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
        
    try:
        limiter.wait()
        
        params = {
            "query": title,
            "limit": 1,
            "fields": "title,citationCount,year,url,authors"
        }
        response = session.get(
            f"{SEMANTIC_SCHOLAR_API}/paper/search", 
            params=params, 
            headers=headers,
            timeout=10
        )
        
        while response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            logger.warning(f"Rate limit hit. Sleeping for {retry_after}s...")
            time.sleep(retry_after)
            limiter.wait()
            response = session.get(
                f"{SEMANTIC_SCHOLAR_API}/paper/search", 
                params=params, 
                headers=headers,
                timeout=10
            )

        if response.status_code != 200:
            return {"title": title, "error": f"API Error {response.status_code}"}
            
        data = response.json()
        if not data.get("data"):
            return {"title": title, "error": "not_found"}
            
        result = data["data"][0]
        
        # Verify match
        sim = similarity(title, result["title"])
        match_data = {
            "title": title,
            "semantic_id": result.get("paperId"),
            "num_citations": result.get("citationCount"),
            "year": result.get("year"),
            "url": result.get("url"),
            "authors": [a["name"] for a in result.get("authors", [])],
            "similarity": sim
        }

        if sim < 0.8:
            match_data["error"] = "low_confidence_match"
            match_data["found_title"] = result["title"]
            
        return match_data
        
    except Exception as e:
        return {"title": title, "error": str(e)}


def load_checkpoint(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checkpoint(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Fetch Semantic Scholar citations")
    parser.add_argument("--input", type=Path, required=True, help="Path to preprocessed.parquet")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON file")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of papers")
    parser.add_argument("--api-key", type=str, default=None, help="Semantic Scholar API Key")
    parser.add_argument("--requests-per-min", type=int, default=None, help="Override RPS limit")
    
    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return

    # Determine rate limit
    # Free tier: 100 / 5 min = 20 / min
    # Authenticated: Depends on tier, usually higher (e.g. 10/sec = 600/min)
    if args.requests_per_min:
        rpm = args.requests_per_min
    elif args.api_key:
        rpm = 100  # Conservative authenticated default
    else:
        rpm = 19   # Conservative free default (19 < 20)

    limiter = RateLimiter(requests_per_minute=rpm)
    logger.info(f"Rate limit set to {rpm} requests/minute (1 req every {60/rpm:.2f}s)")

    # Load data
    df = pd.read_parquet(args.input)
    titles = df["title"].tolist()
    
    if args.limit:
        titles = titles[:args.limit]
        logger.info(f"Limiting to first {args.limit} papers")

    # Output paths
    output_path = args.output or args.input.parent / "semanticscholar_citations.json"
    checkpoint_path = output_path.with_suffix(".checkpoint.json")
    
    # Resume
    results = load_checkpoint(checkpoint_path)
    if results:
        logger.info(f"Resuming from checkpoint: {len(results)} papers already processed")
    
    # Filter remaining
    to_process = [t for t in titles if t not in results]
    logger.info(f"Remaining papers to process: {len(to_process)}")

    session = requests.Session()
    save_interval = 20
    
    try:
        for i, title in enumerate(tqdm(to_process, desc="Fetching")):
            # Fetch
            time.sleep(5)
            result = fetch_paper_data(title, session, limiter, args.api_key)
            results[title] = result
            
            # Save checkpoint
            if (i + 1) % save_interval == 0:
                save_checkpoint(checkpoint_path, results)
                
    except KeyboardInterrupt:
        logger.warning("\nInterrupted! Saving checkpoint...")
        save_checkpoint(checkpoint_path, results)
        logger.info(f"Checkpoint saved to {checkpoint_path}")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        save_checkpoint(checkpoint_path, results)
        raise

    # Final save
    save_checkpoint(output_path, results)
    logger.info(f"Done! Saved results for {len(results)} papers to {output_path}")
    
    # Clean up checkpoint if complete
    if len(results) == len(titles):
        if checkpoint_path.exists():
            checkpoint_path.unlink()

if __name__ == "__main__":
    main()
