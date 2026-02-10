import pandas as pd
import json
import glob
import os
from pathlib import Path

def verify_year(year):
    print(f"\n{'='*40}")
    print(f"Verifying ICLR{year}")
    print(f"{'='*40}")
    
    # Load original list
    parquet_path = Path("data") / f"ICLR{year}" / "preprocessed.parquet"
    if not parquet_path.exists():
        print(f"[X] Original data not found: {parquet_path}")
        return

    df = pd.read_parquet(parquet_path)
    original_titles = set(df["title"].tolist())
    print(f"  Target Papers: {len(original_titles)}")
    
    # Load scraped data
    json_files = glob.glob(f"data/ICLR{year}/googlescholar_iclr{year}_*.json")
    if not json_files:
        print(f"[X] No scraped JSON file found for ICLR{year}")
        return
        
    # Get latest file
    latest_file = max(json_files, key=os.path.getctime)
    print(f"  Checking File: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[X] Error reading JSON: {e}")
        return

    scraped_titles = set(data.keys())
    
    # Completeness Check
    missing = original_titles - scraped_titles
    print(f"  Scraped Count: {len(scraped_titles)}")
    
    if missing:
        print(f"[X] Missing Papers: {len(missing)}")
        for i, t in enumerate(list(missing)[:3]):
            print(f"    - {t}")
        if len(missing) > 3:
            print(f"    ... and {len(missing)-3} more")
    else:
        print("[OK] Completenss: All papers found in JSON keys.")
        
    # Quality Check
    errors = 0
    empty_citations = 0
    valid_citations = 0
    max_citations = 0
    
    error_types = {}
    
    for title, info in data.items():
        if info.get("error"):
            errors += 1
            etype = info.get("error")
            error_types[etype] = error_types.get(etype, 0) + 1
        else:
            cites = info.get("num_citations", 0)
            if cites == 0:
                empty_citations += 1
            else:
                valid_citations += 1
                max_citations = max(max_citations, cites)
                
    print(f"  Errors: {errors} (Original API errors)")
    if errors > 0:
        print(f"    Types: {error_types}")
        
    print(f"  Valid Entries: {len(data) - errors}")
    print(f"    - With Citations: {valid_citations}")
    print(f"    - Zero Citations: {empty_citations}")
    print(f"    - Max Citations: {max_citations}")
    
    if errors == 0 and len(missing) == 0:
        print("[PERFECT]")
    elif len(missing) == 0 and errors < len(original_titles) * 0.05:
         print("[WARNING] Good (Some errors)")
    else:
         print("[NEEDS ATTENTION]")

def main():
    years = range(2017, 2024)
    for year in years:
        verify_year(year)

if __name__ == "__main__":
    main()
