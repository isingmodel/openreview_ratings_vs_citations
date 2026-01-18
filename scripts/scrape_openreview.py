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
    2023: "ICLR.cc/2023/Conference/-/Blind_Submission",
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

    logger.info(f"Scraping ICLR {year}...")

    # Use API v1 for all years first (more reliable)
    result = scrape_openreview_v1(year, limit)
    
    # If v1 returns no data for recent years, try v2
    if len(result[1]) == 0 and year >= 2021:
        logger.info("No data from v1, trying v2 API...")
        result = scrape_openreview_v2(year, limit)
    
    return result


def scrape_openreview_v2(year: int, limit: int | None = None) -> tuple[list, pd.DataFrame]:
    """Scrape using OpenReview API v2 (for 2021+)."""
    import openreview

    client = openreview.api.OpenReviewClient(baseurl="https://api2.openreview.net")
    
    venue_id = f"ICLR.cc/{year}/Conference"
    
    # Get accepted papers using venue query
    logger.info(f"Fetching accepted papers from {venue_id}...")
    
    try:
        # Try to get submissions with accepted venue
        submissions = list(client.get_all_notes(
            content={"venueid": venue_id},
            details="replies"
        ))
        logger.info(f"Found {len(submissions)} total notes")
        
        # Filter for actual submissions
        submissions = [s for s in submissions if hasattr(s, 'content') and 'title' in s.content]
        
        if not submissions:
            raise ValueError("No submissions found using venue_id query")
            
    except Exception as e:
        logger.warning(f"Venue query failed/empty: {e}, trying invitation-based query...")
        invitation = get_invitation(year) # Now returns Blind_Submission for 2023
        submissions = list(client.get_all_notes(invitation=invitation, details="replies"))

    if limit:
        submissions = submissions[:limit]
        logger.info(f"Limited to {limit} submissions for testing")

    logger.info(f"Processing {len(submissions)} submissions...")

    raw_data = []
    records = []

    for sub in tqdm(submissions, desc="Processing"):
        try:
            content = sub.content

            # Extract title
            title = content.get("title", {})
            if isinstance(title, dict):
                title = title.get("value", "")

            # Extract authors
            authors = content.get("authors", {})
            if isinstance(authors, dict):
                authors = authors.get("value", [])

            # Get venue (to check if accepted)
            venue = content.get("venue", {})
            if isinstance(venue, dict):
                venue = venue.get("value", "")
            
            # Get decision
            decision = content.get("decision", {})
            if isinstance(decision, dict):
                decision = decision.get("value", "")
            
            # Determine if accepted
            is_accepted = False
            if decision:
                is_accepted = "accept" in decision.lower()
            elif venue:
                is_accepted = "reject" not in venue.lower() and venue != ""

            # Get ratings from replies
            ratings = []
            if hasattr(sub, "details") and sub.details:
                replies = sub.details.get("replies", [])
                for reply in replies:
                    reply_content = reply.get("content", {})
                    
                    # Check for rating and confidence
                    rating_val = None
                    confidence_val = None

                    # Extract Rating
                    for field in ["rating", "recommendation", "score"]:
                        if field in reply_content:
                            val = reply_content[field]
                            val = val.get("value", val) if isinstance(val, dict) else val
                            if isinstance(val, str):
                                try:
                                    rating_val = int(val.split(":")[0])
                                except (ValueError, IndexError):
                                    continue
                            elif isinstance(val, (int, float)):
                                rating_val = int(val)
                            break
                    
                    # Extract Confidence
                    for field in ["confidence"]:
                        if field in reply_content:
                            val = reply_content[field]
                            val = val.get("value", val) if isinstance(val, dict) else val
                            if isinstance(val, str):
                                try:
                                    confidence_val = int(val.split(":")[0])
                                except (ValueError, IndexError):
                                    continue
                            elif isinstance(val, (int, float)):
                                confidence_val = int(val)
                            break

                    if rating_val is not None:
                        ratings.append({
                            "rating": rating_val,
                            "confidence": confidence_val
                        })

            raw_data.append({
                "id": sub.id,
                "title": title,
                "authors": authors,
                "ratings": ratings,
                "decision": decision or venue,
            })

            # Calculate stats for V2
            if is_accepted and ratings:
                rating_values = [r["rating"] for r in ratings]
                records.append({
                    "title": title,
                    "authors": authors,
                    "rating": ratings,  # List of dicts
                    "decision": decision or venue,
                    "mean_rating": sum(rating_values) / len(rating_values) if rating_values else None,
                    "var_rating": pd.Series(rating_values).var() if len(rating_values) > 1 else 0,
                })

        except Exception as e:
            logger.warning(f"Error processing submission {sub.id}: {e}")
            continue

    df = pd.DataFrame(records)
    logger.info(f"Processed {len(records)} accepted papers with ratings")

    return raw_data, df


def scrape_openreview_v1(year: int, limit: int | None = None) -> tuple[list, pd.DataFrame]:
    """Scrape using OpenReview API v1 (for pre-2021)."""
    import openreview

    invitation = get_invitation(year)
    logger.info(f"Using invitation: {invitation}")

    client = openreview.Client(baseurl="https://api.openreview.net")
    
    submissions = list(
        openreview.tools.iterget_notes(client, invitation=invitation, details="original")
    )

    if limit:
        submissions = submissions[:limit]
        logger.info(f"Limited to {limit} submissions for testing")

    logger.info(f"Found {len(submissions)} submissions")

    raw_data = []
    records = []

    for sub in tqdm(submissions, desc="Processing"):
        try:
            content = sub.content
            title = content.get("title", "")
            authors = content.get("authors", [])
            
            venue = content.get("venue", "")
            venue_id = content.get("venueid", "")
            
            # Get forum replies for ratings and decision
            forum_notes = client.get_notes(forum=sub.forum)
            
            ratings = []
            decision = None
            
            for i, note in enumerate(forum_notes):
                note_content = note.content
                
                # Check for rating
                rating_val = None
                confidence_val = None

                # Extract Rating (check multiple fields)
                for field in ["rating", "recommendation", "score"]:
                    if field in note_content:
                        val = note_content[field]
                        try:
                            # Parse "8: ..." or just 8
                            if isinstance(val, str):
                                rating_val = int(val.split(":")[0])
                            elif isinstance(val, (int, float)):
                                rating_val = int(val)
                            
                            # Break if found valid rating
                            if rating_val is not None:
                                break
                        except:
                            continue
                
                if "confidence" in note_content:
                    conf_str = note_content["confidence"]
                    try:
                        confidence_val = int(conf_str.split(":")[0])
                    except:
                        pass
                
                if rating_val is not None:
                    ratings.append({
                        "rating": rating_val,
                        "confidence": confidence_val
                    })

                if "decision" in note_content:
                    decision = note_content["decision"]

            # Fallback to venue for decision
            final_decision = decision
            if not final_decision:
                if "Accept" in venue or "Poster" in venue or "Spotlight" in venue or "Oral" in venue:
                    final_decision = venue
                elif "Reject" in venue:
                    final_decision = "Reject"
                elif venue:
                     final_decision = venue

            if len(raw_data) < 5:
                print(f"DEBUG: ID={sub.id} Venue='{venue}' Decision='{decision}' Final='{final_decision}'")

            raw_data.append({
                "id": sub.id,
                "title": title,
                "authors": authors,
                "ratings": ratings,
                "decision": final_decision,
            })

            # Check acceptance using final_decision
            is_accepted = False
            if final_decision:
                is_accepted = "Accept" in final_decision or "Poster" in final_decision or "Spotlight" in final_decision or "Oral" in final_decision or "notable" in final_decision.lower()
                if "Reject" in final_decision:
                    is_accepted = False

            if is_accepted and ratings:
                rating_values = [r["rating"] for r in ratings]
                records.append({
                    "title": title,
                    "authors": authors,
                    "rating": ratings, # List of dicts
                    "decision": final_decision,
                    "mean_rating": sum(rating_values) / len(rating_values),
                    "var_rating": pd.Series(rating_values).var() if len(rating_values) > 1 else 0,
                })

        except Exception as e:
            logger.warning(f"Error processing {sub.id}: {e}")
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
