# Virginia ZIP Code Population Lookup

This file explains how to search Virginia ZIP code population counts using Census ZIP Code Tabulation Areas (ZCTAs).

## Why use ZCTAs
The U.S. Census Bureau publishes population data by ZIP Code Tabulation Area (ZCTA), not USPS ZIP codes. For population counts, use ZCTAs and map them to Virginia using the state FIPS code `51`.

## Census API example
Use this request to get Virginia ZCTA population data from the 2020 Census PL dataset:

```bash
curl "https://api.census.gov/data/2020/dec/pl?get=NAME,P1_001N&for=zip%20code%20tabulation%20area:*&in=state:51"
```

- `NAME` = ZCTA name
- `P1_001N` = total population

## Python script example
```python
import requests

url = "https://api.census.gov/data/2020/dec/pl"
params = {
    "get": "NAME,P1_001N",
    "for": "zip code tabulation area:*",
    "in": "state:51"
}

resp = requests.get(url, params=params)
resp.raise_for_status()

data = resp.json()
headers = data[0]
rows = data[1:]

for row in rows:
    name, population, zcta = row
    print(f"{zcta}: {name} => {population}")
```

## Notes
- Virginia state FIPS code is `51`.
- Census ZCTA data is the standard source for ZIP code area population counts.
- If you need USPS ZIP codes, you'll need a USPS ZIP code directory and a separate mapping to ZCTAs.
