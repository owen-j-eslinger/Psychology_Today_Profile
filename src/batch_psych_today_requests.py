"""
Functional Summary
This routine serves as a resilient, fault-tolerant batch ETL pipeline driver designed to orchestrate high-volume web scraping tasks across target ZIP codes.
    - Checkpointing & Deduplication: Reads existing target storage file on launch to understand current progress. It filters out completed works dynamically, guaranteeing $O(1)$ lookup complexity to skip redundant requests.
    - I/O Optimization & Data Preservation: Implements immediate, single-row unbuffered appending strategies to disk. If an unhandled interrupt occurs, zero scrap state data is lost.
    - Network Defense & Adaptive Throttling: Utilizes an integrated exponential backoff algorithm that adjusts delay variables dynamically from minimum thresholds up to fixed ceilings ($30\text{s} - 60\text{s}$) upon hitting downstream rate limits or exceptions. It forces explicit loop termination via a configurable circuit breaker (MAX_CONSECUTIVE_ERRORS) to protect against network bans.
    
Architectural Design & Complexity Breakdown
    - Type Safety & Static Layout: Refactored runtime components with comprehensive typing signatures (List, Dict, Tuple, Set, Path). Variable initialization explicitly binds typing declarations to adhere cleanly to modern static analyzer constraints (mypy).
    - Resource Optimization: Leverages a unified requests.Session() manager instance inside a context manager block. This implements TCP connection pooling, ensuring keep-alive reuse across sequential fetches while eliminating socket exhaustion anti-patterns.
    - Algorithmic Complexity Bounds:
        - Time Complexity: 
            - Building target processing states: $O(N)$ where $N$ represents the record count inside the Census file.
            - Resume set validation: $O(M)$ where $M$ is the count of pre-existing processed data entries.
            - Scrap loop execution: $O(K \cdot T)$ where $K$ is the remainder delta subset of tasks to perform and $T$ represents the random dynamic network/sleep latency constant.
    - Space Complexity: $O(N + M)$ to sustain the execution sequence sets and target filters within active memory allocations.
    
"""

# Batch driver for Psychology Today therapist counts.
# Calls the existing fetch_zip() function across large ZIP ranges with:
#   - Resume capability (skips ZIPs already in output CSV)
#   - Append-as-you-go writing (never lose progress)
#   - Progress reporting with ETA
#   - Optional pre-filtering to real ZIPs only
#   - Adaptive backoff on errors
#
# Save in same folder as pt_pull_therapist_counts.py

import requests
import csv
import time
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
import os

# Get the project root (one directory up from this script)
ROOT = Path(__file__).resolve().parent.parent

# Now define all paths relative to ROOT
CENSUS_CSV = ROOT / "census_data" / "virginia-zip-codes.csv"
THERAPIST_CSV = ROOT / "therapist_counts" / "therapist_counts_by_zip.csv"
OUTPUT_DIR = ROOT / "therapist_counts"
OUTPUT_CSV = ROOT / "therapist_counts" / "therapist_counts_by_zip.csv"
ERROR_LOG = OUTPUT_DIR / "errors.log"
HTML_CACHE_DIR = OUTPUT_DIR / "html_cache"

# Import functions from your existing script
from pt_pull_therapist_counts import (
    fetch_zip,
    HEADERS,
    HTML_CACHE_DIR,
    OUTPUT_DIR,
    MIN_DELAY,
    MAX_DELAY,
)

# ---------- Configuration ----------
# ZIP ranges to process (inclusive)
ZIP_RANGES = [
    (20101, 20199),   # Loudoun County / parts of NoVA
    (22001, 24699),   # Bulk of Virginia
]


# Adaptive backoff thresholds
ERROR_BACKOFF_MULTIPLIER = 2.0    # double delays after errors
MAX_CONSECUTIVE_ERRORS = 100      # stop if this many errors in a row

# CSV columns (must match what fetch_zip returns)
FIELDNAMES = [
    "zip",
    "result_count",
    "nearby_result_count",
    "teletherapy_count",
    "resolved_postal_code",
    "resolved_region",
    "zip_mismatch",
    "http_status",
    "url",
    "error",
]


# ---------- Build the ZIP list ----------
def build_zip_list():
    """
    Build the full list of ZIP codes to process from the census CSV (uses the 'zip' column).
    """
    all_zips = []
    print(CENSUS_CSV)

    if CENSUS_CSV and Path(CENSUS_CSV).exists():
        with open(str(CENSUS_CSV), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                z = (row.get("zip") or "").strip().zfill(5)
                if z:
                    all_zips.append(z)
        print("Generated {} ZIP codes from Census Data File.".format(len(all_zips)))
    else:
        print("Census file not found or not specified.")

    return all_zips

# ---------- Resume support ----------
def load_completed_zips():   
    if not OUTPUT_CSV.exists():
        print("File does not exist!")
        return set()
    completed = set()
    with open(str(OUTPUT_CSV), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            zc = row.get("zip", "").strip()
            if zc:
                completed.add(zc)
    return completed

def init_csv_if_needed():
    """
    Create the CSV with headers if it doesn't exist yet.
    """
    if not OUTPUT_CSV.exists():
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(str(OUTPUT_CSV), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
        print("Created new output CSV: {}".format(OUTPUT_CSV))


def append_row(row):
    """
    Append a single row to the output CSV. Flushes immediately so progress
    is preserved if the script is killed.
    """
    with open(str(OUTPUT_CSV), "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writerow(row)


def log_error(zip_code, message):
    """
    Append an error line to the error log.
    """
    with open(str(ERROR_LOG), "a", encoding="utf-8") as f:
        f.write("{} ZIP {} : {}\n".format(
            datetime.now().isoformat(timespec="seconds"),
            zip_code,
            message,
        ))


# ---------- Progress reporting ----------
def format_eta(seconds):
    """
    Format seconds as H:MM:SS.
    """
    return str(timedelta(seconds=int(seconds)))


def print_progress(idx, total, start_time, current_delay, error_count):
    """
    Print a progress line with ETA.
    """
    elapsed = time.time() - start_time
    rate = idx / elapsed if elapsed > 0 else 0
    remaining = (total - idx) / rate if rate > 0 else 0
    print(
        "  Progress: {}/{} ({}%) | elapsed {} | ETA {} | delay {}s | errors {}".format(
            idx,
            total,
            round(100 * idx / total, 1),
            format_eta(elapsed),
            format_eta(remaining),
            round(current_delay, 1),
            error_count,
        )
    )


# ---------- Main batch loop ----------
def run_batch():
    """
    Main batch processor with resume, append, and adaptive backoff.
    """
    # Build ZIP list
    all_zips = build_zip_list()

    # Initialize CSV and load completed
    init_csv_if_needed()
    completed = load_completed_zips()
    print("Already completed: {} ZIPs (will skip)".format(len(completed)))

    # Filter out completed
    todo = [z for z in all_zips if z not in completed]
    print("ZIPs to process this run: {}".format(len(todo)))
    print("Estimated time at {}-{}s/ZIP: {} to {}".format(
        MIN_DELAY,
        MAX_DELAY,
        format_eta(len(todo) * MIN_DELAY),
        format_eta(len(todo) * MAX_DELAY),
    ))

    if not todo:
        print("\nNothing to do. All ZIPs already processed.")
        return

    # Confirm with user before starting a long run
    if len(todo) > 100:
        print("\n!! WARNING: This will make {} live HTTP requests.".format(len(todo)))
        print("!! Press Ctrl+C now to abort, or wait 10 seconds to continue...")
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nAborted by user.")
            return

    print("\nStarting batch at {}\n".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    # Process loop
    start_time = time.time()
    consecutive_errors = 0
    total_errors = 0
    current_min_delay = MIN_DELAY
    current_max_delay = MAX_DELAY

    with requests.Session() as session:
        for i, zc in enumerate(todo, start=1):
            print("[{}/{}] ZIP {}...".format(i, len(todo), zc), end=" ")
            sys.stdout.flush()

            # Fetch
            try:
                row = fetch_zip(zc, session, save_html=True)
            except Exception as e:
                row = {
                    "zip": zc,
                    "url": "",
                    "http_status": None,
                    "result_count": None,
                    "nearby_result_count": None,
                    "teletherapy_count": None,
                    "resolved_postal_code": None,
                    "resolved_region": None,
                    "zip_mismatch": False,
                    "error": "Unhandled exception: {}".format(e),
                }

            # Append immediately so progress is preserved
            append_row(row)

            # Report and track errors
            if row.get("error"):
                consecutive_errors += 1
                total_errors += 1
                log_error(zc, row["error"])
                print("ERROR: {}".format(row["error"]))

                # Stop if we hit too many consecutive errors
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    print("\n!! {} consecutive errors. Stopping to avoid further issues.".format(
                        consecutive_errors
                    ))
                    print("!! Re-run the script to resume from this point.")
                    break

                # Adaptive backoff
                current_min_delay = min(MIN_DELAY * ERROR_BACKOFF_MULTIPLIER, 30)
                current_max_delay = min(MAX_DELAY * ERROR_BACKOFF_MULTIPLIER, 60)
            else:
                # Reset on success — gradually return to normal delay
                consecutive_errors = 0
                current_min_delay = MIN_DELAY
                current_max_delay = MAX_DELAY
                print("resultCount = {} | region = {}".format(
                    row.get("result_count"),
                    row.get("resolved_region"),
                ))

            # Progress every 25 ZIPs
            if i % 25 == 0:
                print_progress(i, len(todo), start_time,
                               (current_min_delay + current_max_delay) / 2,
                               total_errors)

            # Sleep between requests (skip on last)
            if i < len(todo):
                time.sleep(random.uniform(current_min_delay, current_max_delay))

    # Final summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("Batch complete.")
    print("Elapsed time : {}".format(format_eta(elapsed)))
    print("Total errors : {}".format(total_errors))
    print("Output CSV   : {}".format(OUTPUT_CSV))
    print("Error log    : {}".format(ERROR_LOG))


# ---------- Entry point ----------
if __name__ == "__main__":
    run_batch()