import csv
from pathlib import Path

# Input and output file paths
INPUT_CSV = Path("../therapist_counts/therapist_counts_by_zip_old.csv")
OUTPUT_CSV = Path("../therapist_counts/therapist_counts_by_zip.csv")

# Read and filter rows
with open(INPUT_CSV, "r", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)
    rows = [row for row in reader if not (row.get("error") or "").strip()]

# Sort by zip code (as integer)
rows_sorted = sorted(rows, key=lambda r: int(r["zip"]))

# Write to output file
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows_sorted)

print(f"Wrote {len(rows_sorted)} rows to {OUTPUT_CSV}")