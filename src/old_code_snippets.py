# Psychology Today therapist count lookup by ZIP code.
# Extracts 'results_total' directly from the embedded JSON in the page.
# This is far more reliable than parsing rendered HTML.
# Compatible with Python 3.7+

import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import random
import sys
import json
from pathlib import Path
from urllib.parse import urlencode


# ---------- Configuration ----------
BASE_URL = "https://www.psychologytoday.com/us/therapists"
OUTPUT_DIR = Path("therapist_counts")
OUTPUT_CSV = OUTPUT_DIR / "therapist_counts_by_zip.csv"
HTML_CACHE_DIR = OUTPUT_DIR / "html_cache"

MIN_DELAY = 4.0
MAX_DELAY = 8.0
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Regex to find 'results_total': 963  (or "results_total":963 etc.)
# Tolerates whitespace and either single/double quotes around the key.
RESULTS_TOTAL_PATTERN = re.compile(
    r'["\']?results_total["\']?\s*:\s*(\d+)'
)


# ---------- Core extraction ----------
def extract_results_total(html_text):
    """
    Extract the 'results_total' integer from the page HTML.
    Returns int or None.
    
    Strategy: Find ALL matches of the pattern. If they all agree, return that
    value. If they disagree, return the largest (heuristic: the page-level
    total is usually the biggest number among any nested counts).
    """
    matches = RESULTS_TOTAL_PATTERN.findall(html_text)
    if not matches:
        return None
    
    # Convert all matches to integers
    values = [int(v) for v in matches]
    
    # If all agree, use that value
    if len(set(values)) == 1:
        return values[0]
    
    # Otherwise return the maximum (typically the directory-wide total)
    return max(values)


# ---------- Fetch one ZIP ----------
def fetch_zip(zip_code, session, save_html=True):
    """
    Fetches Psychology Today search page for one ZIP and extracts results_total.
    """
    url = "{}?{}".format(BASE_URL, urlencode({"search": zip_code}))
    
    result = {
        "zip": zip_code,
        "url": url,
        "http_status": None,
        "results_total": None,
        "all_matches": None,    # for debugging — every value found
        "error": None,
    }
    
    try:
        resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        result["http_status"] = resp.status_code
        
        if resp.status_code in (403, 429, 503):
            result["error"] = "Likely blocked or rate-limited (HTTP {})".format(
                resp.status_code
            )
            return result
        
        resp.raise_for_status()
        
        # Save raw HTML for offline re-parsing / audit
        if save_html:
            HTML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            (HTML_CACHE_DIR / "{}.html".format(zip_code)).write_text(
                resp.text, encoding="utf-8"
            )
        
        # Find ALL results_total values for transparency
        all_values = [int(v) for v in RESULTS_TOTAL_PATTERN.findall(resp.text)]
        result["all_matches"] = ",".join(str(v) for v in all_values) if all_values else None
        
        # Pick the canonical value
        result["results_total"] = extract_results_total(resp.text)
        
        if result["results_total"] is None:
            result["error"] = "results_total not found in page HTML"
        
    except requests.exceptions.RequestException as e:
        result["error"] = "Request error: {}".format(e)
    except Exception as e:
        result["error"] = "Parse error: {}".format(e)
    
    return result


# ---------- Re-parse from cached HTML (no network needed) ----------
def reparse_cached(zip_code):
    """
    Re-extract results_total from a previously cached HTML file.
    Useful for re-running analysis without hitting the site again.
    """
    html_file = HTML_CACHE_DIR / "{}.html".format(zip_code)
    if not html_file.exists():
        return None
    html = html_file.read_text(encoding="utf-8")
    return extract_results_total(html)


# ---------- Batch driver ----------
def lookup_zips(zip_codes):
    """
    Iterates over ZIP codes with polite delays.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    
    with requests.Session() as session:
        for i, zc in enumerate(zip_codes, start=1):
            print("[{}/{}] ZIP {}...".format(i, len(zip_codes), zc), end=" ")
            sys.stdout.flush()
            
            res = fetch_zip(zc, session)
            results.append(res)
            
            if res["error"]:
                print("ERROR: {}".format(res["error"]))
            else:
                print("results_total = {} (all matches: {})".format(
                    res["results_total"], res["all_matches"]
                ))
            
            if i < len(zip_codes):
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    return results


def save_results(results, path=OUTPUT_CSV):
    """
    Saves results to CSV.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "zip", "results_total", "all_matches",
        "http_status", "url", "error"
    ]
    with open(str(path), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print("\nSaved {} rows to {}".format(len(results), path))


# ---------- Entry point ----------
if __name__ == "__main__":
    test_zips = [
        "22102",  # McLean
        "22030",  # Fairfax
        "22201",  # Arlington
        "20120",  # Centreville
        "22310",  # Alexandria
    ]
    
    print("Looking up {} ZIP codes\n".format(len(test_zips)))
    results = lookup_zips(test_zips)
    save_results(results)
    
    # Summary
    successful = [r for r in results if r["results_total"] is not None]
    failed = [r for r in results if r["results_total"] is None]
    
    print("\n--- Summary ---")
    print("Successful: {}/{}".format(len(successful), len(results)))
    print("Failed:     {}/{}".format(len(failed), len(results)))
    if successful:
        total = sum(r["results_total"] for r in successful)
        avg = total / len(successful)
        print("Total therapists across all ZIPs: {:,}".format(total))
        print("Average per ZIP: {:.1f}".format(avg))
        
        
# Psychology Today therapist count lookup by ZIP code.
# Extracts 'resultCount' from the embedded dataLayer JSON in the page HTML.
# FIXED: Removed all &lt; and &gt; format specifiers — uses .ljust()/.rjust() instead.
# Compatible with Python 3.7+

import requests
import csv
import re
import time
import random
import sys
from pathlib import Path
from urllib.parse import urlencode


# ---------- Configuration ----------
BASE_URL = "https://www.psychologytoday.com/us/therapists"
OUTPUT_DIR = Path("therapist_counts")
OUTPUT_CSV = OUTPUT_DIR / "therapist_counts_by_zip.csv"
HTML_CACHE_DIR = OUTPUT_DIR / "html_cache"

MIN_DELAY = 4.0
MAX_DELAY = 8.0
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Precise regex patterns targeting the dataLayer push block
RESULT_COUNT_PATTERN   = re.compile(r'"resultCount"\s*:\s*(\d+)')
NEARBY_COUNT_PATTERN   = re.compile(r'"nearbyResultCount"\s*:\s*(\d+)')
TELE_COUNT_PATTERN     = re.compile(r'"teletherapyExpandedCount"\s*:\s*(\d+)')
POSTAL_CODE_PATTERN    = re.compile(r'"postalCode"\s*:\s*"(\d+)"')
REGION_PATTERN         = re.compile(r'"regionName"\s*:\s*"([^"]+)"')


# ---------- Helpers ----------
def safe_str(val, width=0, align="left"):
    """
    Safely convert val to string. Optionally pad to width.
    align: 'left' uses ljust, 'right' uses rjust.
    Avoids all &lt; and &gt; inside format strings.
    """
    s = str(val) if val is not None else "N/A"
    if width > 0:
        if align == "right":
            return s.rjust(width)
        return s.ljust(width)
    return s


def safe_int(match_obj):
    """
    Return int from a regex match group(1), or None if no match.
    """
    if match_obj:
        try:
            return int(match_obj.group(1))
        except ValueError:
            return None
    return None


# ---------- Core extraction ----------
def extract_data_from_html(html_text, zip_code):
    """
    Extracts resultCount and supporting metadata from the embedded
    dataLayer JSON block in the Psychology Today page HTML.
    Returns a dict with all extracted fields.
    """
    result = {
        "result_count":         safe_int(RESULT_COUNT_PATTERN.search(html_text)),
        "nearby_result_count":  safe_int(NEARBY_COUNT_PATTERN.search(html_text)),
        "teletherapy_count":    safe_int(TELE_COUNT_PATTERN.search(html_text)),
        "resolved_postal_code": None,
        "resolved_region":      None,
        "zip_mismatch":         False,
        "extraction_ok":        False,
    }

    # Mark extraction as successful only if we got the primary count
    if result["result_count"] is not None:
        result["extraction_ok"] = True

    # Resolved postal code
    m = POSTAL_CODE_PATTERN.search(html_text)
    if m:
        result["resolved_postal_code"] = m.group(1)
        result["zip_mismatch"] = (result["resolved_postal_code"] != zip_code)

    # Resolved region name
    m = REGION_PATTERN.search(html_text)
    if m:
        result["resolved_region"] = m.group(1)

    return result


# ---------- Fetch one ZIP ----------
def fetch_zip(zip_code, session, save_html=True):
    """
    Fetches the Psychology Today search page for one ZIP code,
    saves the HTML, and extracts resultCount from the dataLayer block.
    """
    url = "{}?{}".format(BASE_URL, urlencode({"search": zip_code}))

    result = {
        "zip":                  zip_code,
        "url":                  url,
        "http_status":          None,
        "result_count":         None,
        "nearby_result_count":  None,
        "teletherapy_count":    None,
        "resolved_postal_code": None,
        "resolved_region":      None,
        "zip_mismatch":         False,
        "error":                None,
    }

    try:
        resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        result["http_status"] = resp.status_code

        # Detect bot blocking
        if resp.status_code in (403, 429, 503):
            result["error"] = "Likely blocked or rate-limited (HTTP {})".format(
                resp.status_code
            )
            return result

        resp.raise_for_status()

        # Save raw HTML to cache
        if save_html:
            HTML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path = HTML_CACHE_DIR / "{}.html".format(zip_code)
            cache_path.write_text(resp.text, encoding="utf-8")

        # Extract all fields from HTML
        extracted = extract_data_from_html(resp.text, zip_code)
        result.update(extracted)

        if not extracted["extraction_ok"]:
            result["error"] = (
                "resultCount not found. "
                "Site may have changed or returned a bot-challenge page."
            )

    except requests.exceptions.RequestException as e:
        result["error"] = "Request error: {}".format(e)
    except Exception as e:
        result["error"] = "Parse error: {}".format(e)

    return result


# ---------- Re-parse all cached HTML offline ----------
def reparse_all_cached():
    """
    Re-extracts counts from all cached HTML files with no network calls.
    Useful when extraction logic changes without needing to re-fetch.
    """
    results = []
    html_files = sorted(HTML_CACHE_DIR.glob("*.html"))

    if not html_files:
        print("No cached HTML files found in {}".format(HTML_CACHE_DIR))
        return results

    print("Re-parsing {} cached HTML files...".format(len(html_files)))

    for html_file in html_files:
        zip_code = html_file.stem
        html = html_file.read_text(encoding="utf-8")
        extracted = extract_data_from_html(html, zip_code)

        row = {"zip": zip_code}
        row.update(extracted)
        results.append(row)

        status = "OK  " if extracted["extraction_ok"] else "MISS"
        print("  {} {}  resultCount = {}  region = {}".format(
            status,
            safe_str(zip_code, width=6),
            safe_str(extracted["result_count"], width=6, align="right"),
            safe_str(extracted["resolved_region"]),
        ))

    return results


# ---------- Batch driver ----------
def lookup_zips(zip_codes, use_cache_if_available=True):
    """
    Iterates over ZIP codes with polite delays.
    Uses cached HTML if available to avoid re-hitting the site.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    with requests.Session() as session:
        for i, zc in enumerate(zip_codes, start=1):

            cache_file = HTML_CACHE_DIR / "{}.html".format(zc)

            # Use cache if available and requested
            if use_cache_if_available and cache_file.exists():
                print("[{}/{}] ZIP {} (from cache)...".format(
                    i, len(zip_codes), zc
                ), end=" ")
                html = cache_file.read_text(encoding="utf-8")
                extracted = extract_data_from_html(html, zc)
                res = {"zip": zc, "url": "(cached)", "http_status": "(cached)"}
                res.update(extracted)
                res["error"] = (
                    None if extracted["extraction_ok"] else "resultCount not found"
                )
            else:
                print("[{}/{}] ZIP {} (live fetch)...".format(
                    i, len(zip_codes), zc
                ), end=" ")
                res = fetch_zip(zc, session)

            results.append(res)
            sys.stdout.flush()

            # Print result row — no &lt; or &gt; used anywhere
            if res.get("error"):
                print("ERROR: {}".format(res["error"]))
            else:
                mismatch_flag = ""
                if res.get("zip_mismatch"):
                    mismatch_flag = " [MISMATCH to {}]".format(
                        res.get("resolved_postal_code")
                    )
                print(
                    "resultCount = {}  nearby = {}  tele = {}  region = {}{}".format(
                        safe_str(res.get("result_count"),        width=6, align="right"),
                        safe_str(res.get("nearby_result_count"), width=5, align="right"),
                        safe_str(res.get("teletherapy_count"),   width=5, align="right"),
                        safe_str(res.get("resolved_region")),
                        mismatch_flag,
                    )
                )

            # Polite delay between live fetches
            if i < len(zip_codes) and not (use_cache_if_available and cache_file.exists()):
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    return results


# ---------- Save to CSV ----------
def save_results(results, path=OUTPUT_CSV):
    """
    Saves results list to CSV. Uses extrasaction='ignore' to handle
    any extra keys gracefully.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    with open(str(path), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    print("\nSaved {} rows to {}".format(len(results), path))


# ---------- Entry point ----------
if __name__ == "__main__":
    test_zips = [
        "22102",  # McLean
        "22030",  # Fairfax
        "22201",  # Arlington
        "20120",  # Centreville
        "22310",  # Alexandria
    ]

    print("Looking up {} ZIP codes\n".format(len(test_zips)))

    results = lookup_zips(test_zips, use_cache_if_available=True)
    save_results(results)

    # Summary stats — no &lt; or &gt; used
    good       = [r for r in results if r.get("result_count") is not None]
    mismatches = [r for r in results if r.get("zip_mismatch")]
    failed     = [r for r in results if r.get("result_count") is None]

    print("\n--- Summary ---")
    print("ZIPs with count  : {}/{}".format(len(good), len(results)))
    print("ZIP mismatches   : {}".format(len(mismatches)))
    print("Failed / no data : {}".format(len(failed)))
    if good:
        counts = [r["result_count"] for r in good]
        print("Total therapists : {}".format(sum(counts)))
        print("Average per ZIP  : {}".format(round(sum(counts) / len(counts), 1)))
        print("Min count        : {}".format(min(counts)))
        print("Max count        : {}".format(max(counts)))