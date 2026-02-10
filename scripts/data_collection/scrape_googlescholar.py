"""Scrape Google Scholar citations using Zyte Smart Proxy Manager.

Usage:
    python scripts/scrape_googlescholar.py --test
    python scripts/scrape_googlescholar.py --year 2017 --reset
    python scripts/scrape_googlescholar.py --years 2017-2023 --reset
"""

import argparse
import json
import time
import sys
import random
import re
import requests
import urllib.parse
from datetime import datetime
from pathlib import Path
import os

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configuration
API_KEY_FILE = Path(__file__).parent.parent / "api_key.txt"
ZYTE_PROXY_HOST = "proxy.zyte.com:8011"
SCRAPE_DELAY = 0.1
TIMEOUT = 60

def load_zyte_key() -> str:
    """Load Zyte API key."""
    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"API key file not found: {API_KEY_FILE}")
    with open(API_KEY_FILE, "r") as f:
        return f.read().strip()

def scrape_single_paper(title: str, api_key: str) -> dict:
    """Fetch citation data using Zyte proxy with detailed error reporting."""
    
    encoded_title = urllib.parse.quote(title)
    url = f"https://scholar.google.com/scholar?q={encoded_title}&hl=en"
    proxy_url = f"http://{api_key}:@proxy.zyte.com:8011"
    
    proxies = {"http": proxy_url, "https": proxy_url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        # verify=False for Zyte
        response = requests.get(
            url, 
            headers=headers, 
            proxies=proxies, 
            timeout=TIMEOUT,
            verify=False 
        )
        
        # Immediate error check for status codes
        if response.status_code != 200:
            return {"error": f"http_error_{response.status_code}", "details": response.text[:200]}
        
        # Soft block checks
        if "recaptcha" in response.text.lower() or "unusual traffic" in response.text.lower():
            return {"error": "blocked_captcha", "details": "Recaptcha detected"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = soup.find('div', class_='gs_ri')
        if not result:
            if "did not match any articles" in response.text:
                 return {"error": "not_found"}
            if "sorry" in response.url or "sorry" in response.text.lower():
                return {"error": "blocked_sorry", "details": "Google Sorry page"}
            return {"error": "no_results_structure", "details": "No gs_ri class found but not 404"}
        
        # Parsing (Assumed robust)
        title_elem = result.find('h3', class_='gs_rt')
        found_title = ""
        pub_url = ""
        if title_elem:
            found_title = title_elem.get_text()
            found_title = re.sub(r'^\[.*?\]\s*', '', found_title)
            link = title_elem.find('a')
            if link and link.get('href'):
                pub_url = link.get('href')
        
        num_citations = 0
        citedby_url = ""
        links = result.find_all('a')
        for link in links:
            text = link.get_text()
            if 'Cited by' in text:
                try:
                    num_citations = int(text.replace('Cited by ', ''))
                    citedby_url = "https://scholar.google.com" + link.get('href', '')
                except ValueError:
                    pass
                break
        
        info_elem = result.find('div', class_='gs_a')
        authors = []
        pub_year = ""
        venue = ""
        if info_elem:
            info_text = info_elem.get_text()
            parts = info_text.split(' - ')
            if parts:
                author_part = parts[0].strip()
                author_part = author_part.replace('…', '').strip()
                authors = [a.strip() for a in author_part.split(',') if a.strip()]
            if len(parts) > 1:
                venue_part = parts[1]
                year_match = re.search(r'\b(19|20)\d{2}\b', info_text)
                if year_match:
                    pub_year = year_match.group()
                venue = re.sub(r',?\s*(19|20)\d{2}\s*$', '', venue_part).strip()

        abstract_elem = result.find('div', class_='gs_rs')
        abstract = abstract_elem.get_text() if abstract_elem else ""

        return {
            "container_type": "Publication",
            "bib": {
                "title": found_title,
                "author": authors,
                "pub_year": pub_year,
                "venue": venue,
                "abstract": abstract,
            },
            "filled": False,
            "gsrank": 1,
            "pub_url": pub_url,
            "num_citations": num_citations,
            "citedby_url": citedby_url,
            "scraped_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {"error": f"exception_{type(e).__name__}", "details": str(e)}

def load_checkpoint(year: int) -> dict:
    checkpoint_path = Path(__file__).parent.parent / "data" / f"ICLR{year}" / "googlescholar.checkpoint.json"
    if checkpoint_path.exists():
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_checkpoint(year: int, data: dict):
    checkpoint_path = Path(__file__).parent.parent / "data" / f"ICLR{year}" / "googlescholar.checkpoint.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_final_results(year: int, data: dict):
    date_str = datetime.now().strftime("%y%m%d")
    output_path = Path(__file__).parent.parent / "data" / f"ICLR{year}" / f"googlescholar_iclr{year}_{date_str}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path

def scrape_year(year: int, api_key: str, reset: bool = False):
    print(f"\n{'='*60}")
    print(f"Scraping ICLR{year} (Strict Error Mode)")
    print(f"{'='*60}")
    
    checkpoint_path = Path(__file__).parent.parent / "data" / f"ICLR{year}" / "googlescholar.checkpoint.json"
    if reset and checkpoint_path.exists():
        print(f"[RESET] Deleting existing checkpoint: {checkpoint_path}")
        os.remove(checkpoint_path)

    parquet_path = Path(__file__).parent.parent / "data" / f"ICLR{year}" / "preprocessed.parquet"
    if not parquet_path.exists():
        print(f"Parquet file not found: {parquet_path}. Skipping.")
        return
        
    df = pd.read_parquet(parquet_path)
    titles = df["title"].tolist()
    
    results = load_checkpoint(year)
    if results:
        print(f"Resuming with {len(results)} records")

    to_scrape = [t for t in titles if t not in results]
    print(f"Papers to scrape: {len(to_scrape)}")
    if not to_scrape:
        save_final_results(year, results)
        return

    pbar = tqdm(total=len(to_scrape), desc=f"ICLR{year}")
    
    idx = 0
    MAX_RETRIES = 2
    retry_count = 0
    
    while idx < len(to_scrape):
        title = to_scrape[idx]
        result = scrape_single_paper(title, api_key)
        
        error = result.get("error")
        if error:
            # Check if it's a "not found" (which is valid empty result)
            if error == "not_found":
                results[title] = result # Store as is
                idx += 1
                pbar.update(1)
                retry_count = 0
                time.sleep(SCRAPE_DELAY)
                continue
            
            # For network/transient errors, retry a few times
            if retry_count < MAX_RETRIES:
                retry_count += 1
                tqdm.write(f"\n[WARNING] {error} on '{title}'. Retrying ({retry_count}/{MAX_RETRIES})...")
                time.sleep(3)
                continue
            else:
                # Critical Stop
                tqdm.write(f"\n[CRITICAL ERROR] Failed specific paper after retries or hit strict block.")
                tqdm.write(f"Paper: {title}")
                tqdm.write(f"Error: {error}")
                tqdm.write(f"Details: {result.get('details', '')}")
                tqdm.write("Stopping collection to prevent further issues and allow debugging.")
                
                # Save what we have
                save_checkpoint(year, results)
                sys.exit(1) # Exit script with error code
        
        # Success
        results[title] = result
        idx += 1
        pbar.update(1)
        retry_count = 0
        
        if idx % 20 == 0:
            save_checkpoint(year, results)
        
        time.sleep(SCRAPE_DELAY)

    pbar.close()
    save_checkpoint(year, results)
    save_final_results(year, results)
    print(f"Completed ICLR{year}")

def test_scraping():
    import urllib3
    urllib3.disable_warnings()
    try:
        key = load_zyte_key()
    except:
        print("No API Key")
        return
    print("Testing 'Attention Is All You Need'...")
    res = scrape_single_paper("Attention Is All You Need", key)
    print(res)

def main():
    import urllib3
    urllib3.disable_warnings()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--year", type=int)
    parser.add_argument("--years", type=str)
    parser.add_argument("--reset", action="store_true", help="Delete existing checkpoint and start fresh")
    args = parser.parse_args()

    try:
        api_key = load_zyte_key()
    except Exception as e:
        print(e)
        return

    if args.test:
        test_scraping()
        return

    if args.year:
        scrape_year(args.year, api_key, args.reset)
    elif args.years:
        start, end = map(int, args.years.split("-"))
        for year in range(start, end + 1):
            scrape_year(year, api_key, args.reset)

if __name__ == "__main__":
    main()
