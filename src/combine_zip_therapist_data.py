import csv
from pathlib import Path

# ---------- Configuration ----------
ROOT = Path(__file__).resolve().parent.parent
CENSUS_CSV     = ROOT / "census_data" / "virginia-zip-codes.csv"
THERAPIST_CSV  = ROOT / "therapist_counts" / "therapist_counts_by_zip.csv"
OUTPUT_CSV     = ROOT / "combined_zip_population_therapists.csv"

# ---------- Region label rubric ----------
REGION_RULES = [
    (201, 201, "Northern VA - North/West"),
    (220, 220, "Northern VA - Central NoVA"),
    (221, 221, "Northern VA - East/Central"),
    (222, 222, "Northern VA - Arlington"),
    (223, 223, "Northern VA - Alexandria"),
    (230, 232, "Central/East VA - Richmond Area"),
    (233, 235, "Central/East VA - Hampton Roads/Tidewater"),
    (236, 237, "Central/East VA - Peninsula/Hampton Roads"),
    (238, 239, "Central/East VA - Southside/Central"),
    (240, 241, "Western/SW VA - Roanoke Area"),
    (242, 242, "Western/SW VA - Far Southwest"),
    (243, 244, "Western/SW VA - Mountain Region"),
    (245, 245, "Western/SW VA - Southern/Piedmont"),
]

def label_zip(zip_code):
    try:
        prefix = int(zip_code[:3])
    except (ValueError, TypeError):
        return "Other"
    for low, high, label in REGION_RULES:
        if low <= prefix <= high:
            return label
    return "Other"

# ---------- Load Census population data ----------
def load_population():
    """
    Reads census_data/virginia-zip-codes.csv and returns a dict:
        { zip_string : population_int }
    The header is:
        "zip","city","county","population"
    """
    pop = {}
    with open(str(CENSUS_CSV), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        skipped_blank = 0
        for row in reader:
            zip_raw = (row.get("zip") or "").strip()
            if not zip_raw:
                skipped_blank += 1
                continue
            zip_code = zip_raw.zfill(5)
            try:
                population = int(row.get("population", "0").strip())
            except ValueError:
                population = 0
            pop[zip_code] = population
    print("Loaded population data for {} ZIPs ({} blank rows skipped)".format(
        len(pop), skipped_blank
    ))
    return pop

# ---------- Load therapist counts ----------
def load_therapist_counts():
    counts = {}
    skipped_error = 0
    skipped_blank = 0
    with open(str(THERAPIST_CSV), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            zip_raw = (row.get("zip") or "").strip()
            if not zip_raw:
                skipped_blank += 1
                continue
            zip_code = zip_raw.zfill(5)
            error = (row.get("error") or "").strip()
            if error:
                skipped_error += 1
                continue
            count_raw = (row.get("result_count") or "").strip()
            if not count_raw:
                skipped_blank += 1
                continue
            try:
                count = int(count_raw)
            except ValueError:
                skipped_blank += 1
                continue
            counts[zip_code] = count
    print("Loaded therapist counts for {} ZIPs".format(len(counts)))
    print("  Skipped due to error  : {}".format(skipped_error))
    print("  Skipped blank/invalid : {}".format(skipped_blank))
    return counts

# ---------- Combine and write output ----------
def combine_and_write(population, counts):
    rows_out = []
    matched = 0
    skipped_no_pop_match = 0
    skipped_no_count_match = 0
    skipped_zero_pop = 0
    all_zips = set(counts.keys()) | set(population.keys())
    for zip_code in sorted(all_zips):
        count = counts.get(zip_code)
        pop = population.get(zip_code)
        if count is None:
            skipped_no_count_match += 1
            continue
        if pop is None:
            skipped_no_pop_match += 1
            continue
        if pop == 0:
            skipped_zero_pop += 1
            continue
        density = (count / pop) * 10000.0
        region = label_zip(zip_code)
        rows_out.append({
            "Zip":        zip_code,
            "Population": pop,
            "Count":      count,
            "Density":    round(density, 4),
            "Region":     region,
        })
        matched += 1
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["Zip", "Population", "Count", "Density", "Region"]
    with open(str(OUTPUT_CSV), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)
    print("\n--- Join Summary ---")
    print("Matched (in output)         : {}".format(matched))
    print("Therapist ZIPs not in Census: {}".format(skipped_no_pop_match))
    print("Census ZIPs not in counts   : {}".format(skipped_no_count_match))
    print("Dropped zero-population     : {}".format(skipped_zero_pop))
    print("\nWrote {} rows to {}".format(matched, OUTPUT_CSV))
    total_population = sum(row["Population"] for row in rows_out)
    print("\n\nTotal population of all ZIP codes in output: {:,}".format(total_population))
    return total_population

def print_region_summary():
    if not OUTPUT_CSV.exists():
        return
    by_region = {}
    with open(str(OUTPUT_CSV), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = row["Region"]
            by_region.setdefault(r, {"zips": 0, "pop": 0, "count": 0})
            by_region[r]["zips"]  += 1
            by_region[r]["pop"]   += int(row["Population"])
            by_region[r]["count"] += int(row["Count"])
    print("\n--- Summary by Region ---")
    print("{:50s} {:>6s} {:>12s} {:>10s} {:>10s}".format(
        "Region", "ZIPs", "Population", "Therapists", "Density"
    ))
    print("-" * 92)
    for region in sorted(by_region.keys()):
        d = by_region[region]
        density = (d["count"] / d["pop"] * 10000.0) if d["pop"] else 0
        print("{:50s} {:>6d} {:>12,d} {:>10,d} {:>10.2f}".format(
            region, d["zips"], d["pop"], d["count"], density
        ))

if __name__ == "__main__":
    print("Loading Census population data...")
    population = load_population()
    print("\nLoading therapist counts...")
    counts = load_therapist_counts()
    print("\nJoining datasets...")
    combine_and_write(population, counts)
    print_region_summary()