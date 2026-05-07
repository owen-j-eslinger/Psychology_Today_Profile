import requests
import sys

# To suppress SSL warnings if verify=False is used
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_va_zcta_population():
    """
    Fetches 2020 Census population for Virginia ZCTAs.
    Uses 'zip code tabulation area (or part)' to force state-level filtering.
    """
    # The 2020 Redistricting Data Endpoint
    url = "https://api.census.gov/data/2020/dec/pl"
    
    # Hierarchy trick: Using 'part' allows the 'in=state:51' filter to work
    params = {
        "get": "NAME,P1_001N",
        "for": "zip code tabulation area (or part):*",
        "in": "state:51"
    }

    try:
        print("Initiating secure request to Census API (VA State Filter)...")
        
        # NOTE: If your environment has a strict proxy, you may need:
        # verify=False (to bypass SSL issues) or a timeout to prevent hanging.
        response = requests.get(url, params=params, timeout=15, verify=True)
        
        if response.status_code != 200:
            print(f"API Error {response.status_code}: {response.text}")
            return

        data = response.json()
        headers = data[0]
        rows = data[1:]

        # Map columns
        pop_idx = headers.index("P1_001N")
        zcta_idx = headers.index("zip code tabulation area (or part)")
        
        # Sort by ZCTA
        rows.sort(key=lambda x: x[zcta_idx])

        print(f"\n{'ZCTA':<10} | {'Population':<12} | {'Census Name'}")
        print("-" * 65)
        
        for row in rows:
            print(f"{row[zcta_idx]:<10} | {row[pop_idx]:<12} | {row[0]}")
            
        print("-" * 65)
        print(f"Total Virginia ZCTAs: {len(rows)}")

    except requests.exceptions.ConnectTimeout:
        print("Error: The connection timed out. Your firewall may be blocking the request.")
    except requests.exceptions.ConnectionError as e:
        print(f"Network Error: Could not reach Census API. Details: {e}")
    except Exception as e:
        print(f"Processing Error: {e}")

if __name__ == "__main__":
    get_va_zcta_population()
