"""Scrape paper data from OpenReview for a given ICLR year."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Invitation patterns by year
INVITATION_PATTERNS = {
    2017: "ICLR.cc/2017/conference/-/submission",
    2018: "ICLR.cc/2018/Conference/-/Blind_Submission",
    2019: "ICLR.cc/2019/Conference/-/Blind_Submission",
    2020: "ICLR.cc/2020/Conference/-/Blind_Submission",
    2021: "ICLR.cc/2021/Conference/-/Blind_Submission",
    2022: "ICLR.cc/2022/Conference/-/Blind_Submission",
    2023: "ICLR.cc/2023/Conference/-/Submission",
    2024: "ICLR.cc/2024/Conference/-/Submission",
    2025: "ICLR.cc/2025/Conference/-/Submission",
}


def get_invitation(year: int) -> str:
    """Get the OpenReview invitation string for a given year."""
    if year in INVITATION_PATTERNS:
        return INVITATION_PATTERNS[year]
    # Default pattern for future years
    return f"ICLR.cc/{year}/Conference/-/Submission"


def scrape_openreview(year: int, limit: int | None = None) -> tuple[list, pd.DataFrame]:
    """Scrape OpenReview data for an ICLR year.
    
    Returns:
        Tuple of (raw_data, preprocessed_dataframe)
    """
    import openreview

    invitation = get_invitation(year)
    logger.info(f"Scraping ICLR {year} with invitation: {invitation}")

    client = openreview.api.OpenReviewClient(baseurl="https://api2.openreview.net")

    # Get submissions
    logger.info("Fetching submissions...")
    try:
        submissions = list(client.get_all_notes(invitation=invitation, details="replies"))
    except Exception as e:
        logger.error(f"Failed to fetch with API v2, trying v1: {e}")
        client = openreview.Client(baseurl="https://api.openreview.net")
        submissions = list(
            openreview.tools.iterget_notes(client, invitation=invitation, details="original")
        )

    if limit:
        submissions = submissions[:limit]
        logger.info(f"Limited to {limit} submissions for testing")

    logger.info(f"Found {len(submissions)} submissions")

    # Process each submission
    raw_data = []
    records = []

    for sub in tqdm(submissions, desc="Processing"):
        try:
            content = sub.content

            # Extract title (handle both dict and raw content)
            title = content.get("title", {})
            if isinstance(title, dict):
                title = title.get("value", "")

            # Extract authors
            authors = content.get("authors", {})
            if isinstance(authors, dict):
                authors = authors.get("value", [])

            # Get reviews
            ratings = []
            decision = None

            # Try to get decision from replies
            if hasattr(sub, "details") and sub.details:
                replies = sub.details.get("replies", [])
                for reply in replies:
                    reply_content = reply.get("content", {})

                    # Check for decision
                    if "decision" in reply_content:
                        dec = reply_content["decision"]
                        decision = dec.get("value", dec) if isinstance(dec, dict) else dec

                    # Check for rating
                    if "rating" in reply_content:
                        rating = reply_content["rating"]
                        rating_val = rating.get("value", rating) if isinstance(rating, dict) else rating
                        if isinstance(rating_val, str):
                            try:
                                rating_val = int(rating_val.split(":")[0])
                            except (ValueError, IndexError):
                                continue
                        ratings.append(rating_val)

            raw_data.append({
                "id": sub.id,
                "title": title,
                "authors": authors,
                "ratings": ratings,
                "decision": decision,
            })

            if decision and "reject" not in decision.lower():
                records.append({
                    "title": title,
                    "authors": authors,
                    "rating": ratings,
                    "decision": decision,
                    "mean_rating": sum(ratings) / len(ratings) if ratings else None,
                    "var_rating": pd.Series(ratings).var() if ratings else None,
                })

        except Exception as e:
            logger.warning(f"Error processing submission {sub.id}: {e}")
            continue

    df = pd.DataFrame(records)
    logger.info(f"Processed {len(records)} accepted papers")

    return raw_data, df


def main():
    parser = argparse.ArgumentParser(description="Scrape OpenReview ICLR data")
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="ICLR year to scrape (e.g., 2024)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: data/ICLR{year}/)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of submissions (for testing)",
    )
    args = parser.parse_args()

    output_dir = args.output or Path(__file__).parent.parent / "data" / f"ICLR{args.year}"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_data, df = scrape_openreview(args.year, args.limit)

    # Save raw data as JSON
    raw_path = output_dir / "openreview_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Saved raw data to {raw_path}")

    # Save preprocessed data as Parquet
    if not df.empty:
        # Convert lists to JSON strings for Parquet
        df["rating"] = df["rating"].apply(json.dumps)
        df["authors"] = df["authors"].apply(json.dumps)

        parquet_path = output_dir / "preprocessed.parquet"
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Saved preprocessed data to {parquet_path}")
    else:
        logger.warning("No accepted papers found!")

    print(f"\nDone! Output saved to {output_dir}")


if __name__ == "__main__":
    main()
