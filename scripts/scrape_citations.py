"""Fetch citation data from Google Scholar for papers in a preprocessed dataset."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def scrape_citations(titles: list[str], apikey: str | None = None) -> dict:
    """Fetch citation counts from Google Scholar.
    
    Args:
        titles: List of paper titles to search
        apikey: Optional ScraperAPI key for proxy
        
    Returns:
        Dict mapping title -> citation info
    """
    from scholarly import scholarly, ProxyGenerator

    if apikey:
        pg = ProxyGenerator()
        pg.ScraperAPI(apikey)
        scholarly.use_proxy(pg)
        logger.info("Using ScraperAPI proxy")

    results = {}
    
    for title in tqdm(titles, desc="Fetching citations"):
        try:
            search = scholarly.search_pubs(title)
            pub = next(search)
            results[title] = {
                "num_citations": pub.get("num_citations", 0),
                "pub_url": pub.get("pub_url", ""),
                "year": pub.get("bib", {}).get("pub_year", ""),
            }
        except StopIteration:
            logger.warning(f"No results for: {title[:50]}...")
            results[title] = {"num_citations": None, "error": "not_found"}
        except Exception as e:
            logger.warning(f"Error for {title[:50]}...: {e}")
            results[title] = {"num_citations": None, "error": str(e)}

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch Google Scholar citations")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to preprocessed.parquet file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file (default: same directory as input)",
    )
    parser.add_argument(
        "--apikey",
        type=str,
        default=None,
        help="ScraperAPI key for proxy (recommended to avoid IP blocks)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of papers (for testing)",
    )
    args = parser.parse_args()

    # Load preprocessed data
    df = pd.read_parquet(args.input)
    logger.info(f"Loaded {len(df)} papers from {args.input}")

    titles = df["title"].tolist()
    if args.limit:
        titles = titles[:args.limit]
        logger.info(f"Limited to {args.limit} papers for testing")

    # Scrape citations
    citations = scrape_citations(titles, args.apikey)

    # Save results
    output_path = args.output or args.input.parent / "googlescholar_citations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(citations, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved citations to {output_path}")

    # Print summary
    found = sum(1 for v in citations.values() if v.get("num_citations") is not None)
    print(f"\nDone! Found citations for {found}/{len(titles)} papers")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
