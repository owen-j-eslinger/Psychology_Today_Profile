# Psychology Today ZIP Code Therapist Count Lookup

This file explains how to search Psychology Today therapist profiles by ZIP code and estimate the number of therapists listed.

## Manual search steps

1. Go to `https://www.psychologytoday.com/us/therapists`
2. Enter the target ZIP code in the location field.
3. Review the search results page for the total number of therapists listed or the number of profile entries shown.

## Notes on page structure

- Psychology Today does not provide a public API for therapist directory counts.
- The site may show a total count near the top of the results or use pagination indicators.
- HTML selectors and page structure change frequently.

## Python scraping example

This is a basic scraping approach. It may need adjustment depending on the page layout and should be used with care.

```python
import requests
from bs4 import BeautifulSoup

zip_code = "22102"
url = "https://www.psychologytoday.com/us/therapists"

params = {
    "q": zip_code
}

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; Python script)"
}

resp = requests.get(url, params=params, headers=headers)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# Example selectors: these may need to be updated if the site changes.
count_element = soup.select_one(".search-results-count, .results-count, h1")

if count_element:
    print("Count text:", count_element.get_text(strip=True))
else:
    profiles = soup.select(".result-row, .provider-result")
    print("Profiles found:", len(profiles))
```

## Important considerations

- Automated scraping may violate Psychology Today's terms of service.
- The site may block or throttle scripted requests.
- Prefer manual lookup or obtain permission before automating.
- This file is intended as a starting reference, not a guaranteed production scraper.
