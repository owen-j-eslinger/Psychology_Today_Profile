# Not sure if this is really needed. I pulled down a file from: https://worldpopulationreview.com/zips/virginia

# Stage 2: Read the local CSV and filter to Virginia ZCTAs.
# This runs offline — no API calls. Reuse / re-run as much as you want.

import pandas as pd
from pathlib import Path

def process_va_zctas(
    input_csv="census_data/zcta_dhc_2020.csv",
    output_csv="census_data/va_zcta_dhc_2020.csv"
):
    """
    Loads the local ZCTA CSV, filters to Virginia, and saves the result.
    """
    # Virginia ZCTA prefixes (from USPS allocation)
    va_prefixes = (
        "201", "220", "221", "222", "223", "224", "225", "226", "227",
        "228", "229", "230", "231", "232", "233", "234", "235", "236",
        "237", "238", "239", "240", "241", "242", "243", "244", "245", "246"
    )
    
    # Read CSV — force ZCTA column to string to preserve leading zeros
    df = pd.read_csv(
        input_csv,
        dtype={"zip code tabulation area": str, "H1_001N": "Int64"}
    )
    
    # Rename columns for clarity
    df = df.rename(columns={
        "NAME": "name",
        "H1_001N": "population",
        "zip code tabulation area": "zcta"
    })
    
    print(f"Loaded {len(df):,} total ZCTAs from {input_csv}")
    
    # Filter to Virginia by ZCTA prefix
    va_df = df[df["zcta"].str.startswith(va_prefixes)].copy()
    va_df = va_df.sort_values("zcta").reset_index(drop=True)
    
    print(f"Found {len(va_df):,} Virginia ZCTAs")
    print(f"Total VA population (sum of ZCTAs): {va_df['population'].sum():,}")
    
    # Save filtered result
    va_df.to_csv(output_csv, index=False)
    print(f"Saved: {output_csv}")
    
    # Display top 10
    print("\n--- First 10 Virginia ZCTAs ---")
    print(va_df.head(10).to_string(index=False))
    
    return va_df

if __name__ == "__main__":
    process_va_zctas()