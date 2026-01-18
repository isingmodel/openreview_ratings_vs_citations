import json
import pandas as pd
from pathlib import Path
import glob

def main():
    data_dir = Path("data/ICLR2019")
    pattern = str(data_dir / "openreview_raw_*_*.json")
    files = glob.glob(pattern)
    
    print(f"Found {len(files)} files to merge.")
    
    full_data = []
    
    for fpath in files:
        print(f"Loading {fpath}...")
        with open(fpath, "r") as f:
            data = json.load(f)
            full_data.extend(data)
            
    # Save merged
    out_path = data_dir / "openreview_raw.json"
    with open(out_path, "w") as f:
        json.dump(full_data, f, indent=2)
    print(f"Saved merged data to {out_path} ({len(full_data)} records)")
    
    # Process valid accepted papers
    records = []
    for sub in full_data:
        decision = sub.get("decision", "")
        venue = sub.get("venue", "") # venue might not be in raw_data, but decision is
        
        # Check acceptance
        is_accepted = False
        if decision:
             is_accepted = "Accept" in decision or "Poster" in decision or "Spotlight" in decision or "Oral" in decision
             if "Reject" in decision:
                 is_accepted = False
        
        ratings = sub.get("ratings", [])
        
        if is_accepted and ratings:
            rating_values = [r["rating"] for r in ratings]
            records.append({
                "title": sub.get("title"),
                "authors": sub.get("authors"),
                "rating": ratings, # List of dicts
                "decision": decision,
                "mean_rating": sum(rating_values) / len(rating_values),
                "var_rating": pd.Series(rating_values).var() if len(rating_values) > 1 else 0,
            })

    print(f"Found {len(records)} accepted papers with ratings.")
    
    if records:
        df = pd.DataFrame(records)
        df["rating"] = df["rating"].apply(json.dumps)
        df["authors"] = df["authors"].apply(json.dumps)
        
        parquet_path = data_dir / "preprocessed.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"Saved preprocessed data to {parquet_path}")

if __name__ == "__main__":
    main()
