# Psychology_Today_Profile

Search Psychology Today profiles by zip code.

Main Routine - Running.ipynb
- 

Actual Population by Zip Code
- I pulled population data from (https://worldpopulationreview.com/zips/virginia). I did the same thing for the rest of the states.
- I had tried to write some python to go retreive this information in various ways. Nothing was returning satisfactory results. Instead I just downloaded the accepted data. 

This routine serves as a resilient, fault-tolerant batch ETL pipeline driver designed to orchestrate high-volume web scraping tasks across target (ZIP codes).
- Run $ROOT/src/batch_psych_today_requests.py

Webscraper used by batch_psych_today_requests.py to parse the html code that was returned.
- Uses $ROOT/src/pt_pull_therapist_counts.py


