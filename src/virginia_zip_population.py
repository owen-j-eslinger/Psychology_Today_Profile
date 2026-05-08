# Not sure if this is really needed. I pulled down a file from: https://worldpopulationreview.com/zips/virginia

# Stage 1: Download the entire 2020 DHC ZCTA dataset from the Census API
# and save it locally as both raw JSON and a clean CSV for later processing.

import requests
import json
import csv
import sys
from pathlib import Path

def download_zcta_dhc(output_dir="census_data"):
    """
    Downloads 2020 Census DHC population data for ALL ZCTAs nationwide
    and saves to disk as JSON (raw) and CSV (cleaned).
    """
    url = "https://api.census.gov/data/2020/dec/dhc"
    params = {
        "get": "NAME,H1_001N",
        "for": "zip code tabulation area:*"
    }
    
    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    json_file = out_path / "zcta_dhc_2020_raw.json"
    csv_file  = out_path / "zcta_dhc_2020.csv"
    
    try:
        print(f"Connecting to Census API...")
        print(f"URL: {url}")
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        
        print(f"HTTP {response.status_code} — {len(response.content):,} bytes received")
        
        data = response.json()
        
        # 1. Save raw JSON exactly as received
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved raw JSON: {json_file}")
        
        # 2. Save as CSV with proper headers
        headers = data[0]
        rows = data[1:]
        
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)  # column names from API
            writer.writerows(rows)
        print(f"Saved CSV:      {csv_file}  ({len(rows):,} ZCTAs)")
        
        print("\nDownload complete.")
        return str(csv_file)
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
    return None

if __name__ == "__main__":
    download_zcta_dhc()