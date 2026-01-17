"""Resumable scraper for ICLR 2022-2025 data.

Features:
- Processes one paper at a time
- Saves progress to checkpoint file
- Resumes from last checkpoint if interrupted
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
import time

import pandas as pd
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def get_invitation(year: int) -> str:
    """Get the OpenReview invitation string for a given year."""
    patterns = {
        2022: "ICLR.cc/2022/Conference/-/Blind_Submission",
        2023: "ICLR.cc/2023/Conference/-/Blind_Submission",
        2024: "ICLR.cc/2024/Conference/-/Submission",
        2025: "ICLR.cc/2025/Conference/-/Submission",
    }
    return patterns.get(year, f"ICLR.cc/{year}/Conference/-/Submission")


def load_checkpoint(checkpoint_path: Path) -> dict:
    """Load checkpoint from file."""
    if checkpoint_path.exists():
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_ids": [], "raw_data": [], "records": []}


def save_checkpoint(checkpoint_path: Path, data: dict):
    """Save checkpoint to file."""
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def scrape_year(year: int, output_dir: Path):
    """Scrape ICLR data for a specific year with resume capability."""
    import openreview
    
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.json"
    
    # Load existing checkpoint
    checkpoint = load_checkpoint(checkpoint_path)
    processed_ids = set(checkpoint["processed_ids"])
    raw_data = checkpoint["raw_data"]
    records = checkpoint["records"]
    
    logger.info(f"=== Scraping ICLR {year} ===")
    logger.info(f"Resuming from checkpoint: {len(processed_ids)} already processed")
    
    # Initialize client
    client = openreview.Client(baseurl="https://api.openreview.net")
    invitation = get_invitation(year)
    
    # Get all submissions
    logger.info(f"Fetching submissions with invitation: {invitation}")
    try:
        submissions = list(
            openreview.tools.iterget_notes(client, invitation=invitation, details="original")
        )
    except Exception as e:
        logger.error(f"Failed to fetch submissions: {e}")
        return
    
    logger.info(f"Total submissions: {len(submissions)}")
    
    # Filter out already processed
    to_process = [s for s in submissions if s.id not in processed_ids]
    logger.info(f"Remaining to process: {len(to_process)}")
    
    # Process each submission
    save_interval = 50  # Save checkpoint every N papers
    
    for i, sub in enumerate(tqdm(to_process, desc=f"ICLR {year}")):
        try:
            time.sleep(0.5)
            content = sub.content
            title = content.get("title", "")
            authors = content.get("authors", [])
            
            # Get forum replies for ratings and decision
            forum_notes = client.get_notes(forum=sub.forum)
            
            ratings = []
            decision = None
            
            for note in forum_notes:
                note_content = note.content
                
                # Check for rating (various field names)
                for rating_field in ["rating", "recommendation", "score"]:
                    if rating_field in note_content:
                        rating_str = str(note_content[rating_field])
                        try:
                            ratings.append(int(rating_str.split(":")[0]))
                            break
                        except:
                            pass
                
                if "decision" in note_content:
                    decision = note_content["decision"]
            
            # Save raw data
            raw_data.append({
                "id": sub.id,
                "title": title,
                "authors": authors,
                "ratings": ratings,
                "decision": decision,
            })
            
            # Save to records if accepted
            if decision and "reject" not in decision.lower() and ratings:
                records.append({
                    "title": title,
                    "authors": authors,
                    "rating": ratings,
                    "decision": decision,
                    "mean_rating": sum(ratings) / len(ratings) if ratings else None,
                    "var_rating": pd.Series(ratings).var() if len(ratings) > 1 else 0,
                })
            
            processed_ids.add(sub.id)
            
            # Save checkpoint periodically
            if (i + 1) % save_interval == 0:
                checkpoint = {
                    "processed_ids": list(processed_ids),
                    "raw_data": raw_data,
                    "records": records,
                    "last_save": datetime.now().isoformat(),
                }
                save_checkpoint(checkpoint_path, checkpoint)
                logger.info(f"Checkpoint saved: {len(processed_ids)} processed, {len(records)} accepted")
        
        except Exception as e:
            logger.warning(f"Error processing {sub.id}: {e}")
            continue
    
    # Final save
    checkpoint = {
        "processed_ids": list(processed_ids),
        "raw_data": raw_data,
        "records": records,
        "last_save": datetime.now().isoformat(),
        "completed": True,
    }
    save_checkpoint(checkpoint_path, checkpoint)
    
    # Save final outputs
    raw_path = output_dir / "openreview_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Saved raw data: {raw_path}")
    
    if records:
        df = pd.DataFrame(records)
        df["rating"] = df["rating"].apply(json.dumps)
        df["authors"] = df["authors"].apply(json.dumps)
        
        parquet_path = output_dir / "preprocessed.parquet"
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Saved {len(df)} accepted papers: {parquet_path}")
    else:
        logger.warning("No accepted papers found!")
    
    logger.info(f"=== ICLR {year} Complete ===")
    logger.info(f"Total processed: {len(processed_ids)}")
    logger.info(f"Accepted with ratings: {len(records)}")


def main():
    parser = argparse.ArgumentParser(
        description="Resumable ICLR data scraper for 2022-2025"
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        choices=[2022, 2023, 2024, 2025],
        help="ICLR year to scrape",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: data/ICLR{year}/)",
    )
    args = parser.parse_args()
    
    output_dir = args.output or Path(__file__).parent.parent / "data" / f"ICLR{args.year}"
    
    scrape_year(args.year, output_dir)


if __name__ == "__main__":
    main()
