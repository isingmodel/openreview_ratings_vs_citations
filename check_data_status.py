import json
import glob
from pathlib import Path
import os

def check_file(year):
    files = glob.glob(f"data/ICLR{year}/googlescholar_iclr{year}_*.json")
    if not files:
        print(f"ICLR{year}: No file found.")
        return
    
    # Get latest file
    latest_file = max(files, key=os.path.getctime)
    print(f"ICLR{year}: Checking {latest_file}...")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        total = len(data)
        errors_403 = 0
        other_errors = 0
        valid = 0
        
        for k, v in data.items():
            if v.get('error'):
                if '403' in str(v.get('error')):
                    errors_403 += 1
                else:
                    other_errors += 1
            else:
                valid += 1
                
        print(f"  Total: {total}")
        print(f"  Valid: {valid} ({valid/total*100:.1f}%)")
        print(f"  403 Errors: {errors_403}")
        print(f"  Other Errors: {other_errors}")
        
    except Exception as e:
        print(f"  Error reading file: {e}")

print("="*40)
print("DATA INTEGRITY CHECK")
print("="*40)

years = [2017, 2018, 2019, 2020, 2021]
for year in years:
    check_file(year)
    print("-" * 20)

# Cleanup debug script
if os.path.exists("temp_debug_keys.py"):
    os.remove("temp_debug_keys.py")
    print("Deleted temp_debug_keys.py")
