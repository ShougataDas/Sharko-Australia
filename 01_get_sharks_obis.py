"""Step 1: download shark records around Australia from OBIS (no account needed).

Includes IMOS acoustic tracking, iNaturalist, BRUVS surveys, CSIRO surveys, etc.
Output: data/raw/obis_sharks.csv
"""
import os
import time
import requests
import pandas as pd
from config import BBOX_WKT, START_DATE, END_DATE, RAW_DIR, OBIS_SHARK_TAXON_ID

API = "https://api.obis.org/v3/occurrence"
FIELDS = ("id,scientificName,species,genus,family,order,eventDate,date_year,"
          "decimalLatitude,decimalLongitude,coordinateUncertaintyInMeters,"
          "datasetName,dataset_id,basisOfRecord,individualCount")
PAGE_SIZE = 10000

params = {
    "taxonid": OBIS_SHARK_TAXON_ID,
    "geometry": BBOX_WKT,
    "startdate": START_DATE,
    "enddate": END_DATE,
    "size": PAGE_SIZE,
    "fields": FIELDS,
}

total = requests.get(API, params={**params, "size": 1}, timeout=120).json()["total"]
print(f"OBIS reports {total:,} shark records ({START_DATE} to {END_DATE}). Downloading...")

rows, after = [], None
while True:
    p = dict(params)
    if after:
        p["after"] = after
    for attempt in range(5):
        try:
            r = requests.get(API, params=p, timeout=300)
            r.raise_for_status()
            break
        except requests.RequestException as e:
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit("OBIS keeps failing, try again later (the script can simply be re-run).")

    batch = r.json()["results"]
    if not batch:
        break
    rows.extend(batch)
    after = batch[-1]["id"]
    print(f"  {len(rows):,} / {total:,}")
    if len(batch) < PAGE_SIZE:
        break

df = pd.DataFrame(rows)
out = os.path.join(RAW_DIR, "obis_sharks.csv")
df.to_csv(out, index=False)
print(f"Saved {len(df):,} records -> {out}")
print(df["species"].value_counts().head(15).to_string())
