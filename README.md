# Psychology_Today_Profile
Search Psychology Today profiles by zip code.

I pulled population data from: https://worldpopulationreview.com/zips/virginia

Run $ROOT/src/batch_psych_today_requests.py
Uses $ROOT/src/pt_pull_therapist_counts.py
This routine will look into the already run set of therapists and skip those. Any remaining will be sent to Psychology Today.

