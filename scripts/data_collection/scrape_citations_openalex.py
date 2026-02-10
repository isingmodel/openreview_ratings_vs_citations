"""Fetch citation data from OpenAlex API with rate limiting and resumption."""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime
import urllib.parse
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

OPENALEX_API = "https://api.openalex.org/works"


class RateLimiter:
    """Rate limiter to comply with API usage limits."""
    
    def __init__(self, requests_per_second: float = 10.0):
        self.interval = 1.0 / requests_per_second
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


def fetch_paper_data(title: str, session: requests.Session, limiter: RateLimiter, email: str = None) -> dict:
    """Fetch paper data from OpenAlex using title search."""
    params = {
        "filter": f"title.search:{title}",
        "per-page": 1,
    }
    if email:
        params["mailto"] = email

    try:
        limiter.wait()
        
        response = session.get(
            OPENALEX_API, 
            params=params, 
            timeout=10
        )
        
        while response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2))
            logger.warning(f"Rate limit hit. Sleeping for {retry_after}s...")
            time.sleep(retry_after)
            limiter.wait()
            response = session.get(
                OPENALEX_API, 
                params=params, 
                timeout=10
            )

        if response.status_code != 200:
            return {"title": title, "error": f"API Error {response.status_code}"}
            
        data = response.json()
        if not data.get("results"):
            return {"title": title, "error": "not_found"}
            
        result = data["results"][0]
        
        # Verify match
        found_title = result.get("display_name", "") or result.get("title", "")
        sim = similarity(title, found_title)
        
        match_data = {
            "title": title,
            "openalex_id": result.get("id"),
            "num_citations": result.get("cited_by_count"),
            "year": result.get("publication_year"),
            "url": result.get("ids", {}).get("openalex"),
            "similarity": sim
        }

        if sim < 0.8:
            match_data["error"] = "low_confidence_match"
            match_data["found_title"] = found_title
            
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
    parser = argparse.ArgumentParser(description="Fetch OpenAlex citations")
    parser.add_argument("--input", type=Path, required=True, help="Path to preprocessed.parquet")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON file")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of papers")
    parser.add_argument("--email", type=str, default=None, help="Email for 'Polite Pool' (recommended)")
    
    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return

    # OpenAlex is generous, ~10 req/s is usually fine without email, but email is better.
    # We'll stick to a safe default.
    limiter = RateLimiter(requests_per_second=5.0) 
    
    # Load data
    df = pd.read_parquet(args.input)
    if "title" not in df.columns:
        logger.error("Input file must contain a 'title' column")
        return
        
    titles = df["title"].tolist()
    
    if args.limit:
        titles = titles[:args.limit]
        logger.info(f"Limiting to first {args.limit} papers")

    # Output paths
    date_str = datetime.now().strftime("%y%m%d")
    output_filename = f"openalex_citations_{date_str}.json"
    output_path = args.output or args.input.parent / output_filename
    checkpoint_path = output_path.with_suffix(".checkpoint.json")
    
    # Resume
    results = load_checkpoint(checkpoint_path)
    if results:
        logger.info(f"Resuming from checkpoint: {len(results)} papers already processed")
    
    # Filter remaining
    to_process = [t for t in titles if t not in results]
    logger.info(f"Remaining papers to process: {len(to_process)}")

    session = requests.Session()
    save_interval = 50
    
    try:
        for i, title in enumerate(tqdm(to_process, desc="Fetching")):
            result = fetch_paper_data(title, session, limiter, args.email)
            results[title] = result
            
            # Save checkpoint
            if (i + 1) % save_interval == 0:
                save_checkpoint(checkpoint_path, results)
            time.sleep(0.1)
                
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
