#!/usr/bin/env python3
"""
Scrape ZIP‑code tables (ZIP, City, County, Population) from
worldpopulationreview.com for all 50 U.S. states.

The site's robots.txt (https://worldpopulationreview.com/robots.txt) currently
has no disallow directives, so scraping the /zips/<state> pages is allowed.
We still add a short delay between requests and use a normal browser User‑Agent
to be polite.

"""

import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
BASE_URL = "https://worldpopulationreview.com/zips/{}"

# All states as they appear in the URL (lower‑case, hyphen‑separated).
STATE_SLUGS = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new-hampshire", "new-jersey",
    "new-mexico", "new-york", "north-carolina", "north-dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode-island", "south-carolina",
    "south-dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west-virginia", "wisconsin", "wyoming"
]

# A typical browser header – the site may block obvious "bot" requests.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Pause this many seconds between successive requests.
REQUEST_DELAY_SECONDS = 2

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_page(state_slug: str) -> str:
    """Download the HTML for a given state page."""
    url = BASE_URL.format(state_slug)
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_zips(html: str) -> list[list[str]]:
    """
    Extract ZIP, City, County, and Population from the page HTML.

    Returns a list of rows, each row being [zip, city, county, population].
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try the specific class first; fall back to any <table> if needed.
    table = soup.find("table", {"class": "table"}) or soup.find("table")

    if not table:
        return []

    rows_data = []
    rows = table.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if cells:
            # Extract text from each cell, stripping whitespace
            zip_code = cells[0].get_text(strip=True)
            city = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            county = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            population = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            rows_data.append([zip_code, city, county, population])

    return rows_data


def write_csv(filepath: Path, rows: list[list[str]]) -> None:
    """Write a simple CSV with the given rows."""
    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


# ----------------------------------------------------------------------
# Main scraping logic
# ----------------------------------------------------------------------
def main() -> None:
    # Store results in memory for the combined CSV.
    all_results: dict[str, list[list[str]]] = {}

    for state in STATE_SLUGS:
        print(f"Scraping → {state} …", end=" ", flush=True)
        try:
            html = fetch_page(state)
            rows = parse_zips(html)
            all_results[state] = rows
            print(f"{len(rows)} rows collected")
        except Exception as exc:
            print(f"ERROR – {exc}")
            all_results[state] = []  # still record the state, even if empty

        # Politeness pause.
        time.sleep(REQUEST_DELAY_SECONDS)

    # ------------------------------------------------------------------
    # 1️⃣ Write per‑state CSV files
    # ------------------------------------------------------------------
    for state, rows in all_results.items():
        out_file = Path(f"{state}_zips.csv")
        write_csv(out_file, [["ZIP", "City", "County", "Population"]] + rows)

    # ------------------------------------------------------------------
    # 2️⃣ Write a combined CSV for convenience
    # ------------------------------------------------------------------
    combined_file = Path("all_zips.csv")
    write_csv(
        combined_file,
        [["State", "ZIP", "City", "County", "Population"]]
        + [
            [state] + row
            for state, rows in all_results.items()
            for row in rows
        ]
    )

    print("\n✅ Done! Created:")
    print("   • one CSV per state (e.g., virginia_zips.csv)")
    print("   • all_zips.csv – a single file with every state + ZIP data")


if __name__ == "__main__":
    main()
