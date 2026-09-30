"""Step 2: download shark records around Australia from GBIF (no account needed).

GBIF includes the Atlas of Living Australia, museums, state fisheries, citizen science.
The search API can page through at most 100,000 records per query, so records are
fetched one year at a time. Output: data/raw/gbif_sharks.csv
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd
from config import BBOX_WKT, START_DATE, END_DATE, RAW_DIR, SHARK_ORDERS

API = "https://api.gbif.org/v1"
LIMIT = 300
KEEP = ["key", "scientificName", "species", "genus", "family", "order", "eventDate",
        "year", "month", "day", "decimalLatitude", "decimalLongitude",
        "coordinateUncertaintyInMeters", "datasetName", "datasetKey", "basisOfRecord",
        "individualCount", "country", "institutionCode"]


def get(url, params):
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(5 * (attempt + 1))
    raise SystemExit("GBIF keeps failing, try again later.")


order_keys = []
for name in SHARK_ORDERS:
    m = get(f"{API}/species/match", {"name": name, "rank": "ORDER", "strict": "true"})
    if "usageKey" in m:
        order_keys.append(m["usageKey"])
print("Shark order keys:", order_keys)

base = {
    "geometry": BBOX_WKT,
    "hasCoordinate": "true",
    "hasGeospatialIssue": "false",
    "occurrenceStatus": "PRESENT",
    "orderKey": order_keys,
    "limit": LIMIT,
}

def fetch_year(year):
    out, offset = [], 0
    while True:
        page = get(f"{API}/occurrence/search", {**base, "year": year, "offset": offset})
        out.extend({k: rec.get(k) for k in KEEP} for rec in page["results"])
        offset += LIMIT
        print(f"  {year}: {len(out):,} / {page['count']:,}", flush=True)
        if page["endOfRecords"] or offset >= 100000:
            return out


# Each GBIF page takes a few seconds, so download the years in parallel
years = range(int(START_DATE[:4]), int(END_DATE[:4]) + 1)
with ThreadPoolExecutor(max_workers=4) as pool:
    rows = [r for year_rows in pool.map(fetch_year, years) for r in year_rows]

df = pd.DataFrame(rows)
out = os.path.join(RAW_DIR, "gbif_sharks.csv")
df.to_csv(out, index=False)
print(f"Saved {len(df):,} records -> {out}")
print(df["species"].value_counts().head(15).to_string())
