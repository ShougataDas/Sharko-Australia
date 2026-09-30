"""Step 3: download Queensland Shark Control Program catches (Great Barrier Reef beaches).

Catch files list the beach name but no coordinates, so they are joined to the
official gear (drumline/net) locations file. Every beach with gear is also saved
separately: it was fished all year, so it is useful as known sampling effort.
Outputs: data/raw/qld_scp_catches.csv, data/raw/qld_scp_gear_locations.csv
"""
import io
import os
import re
import requests
import pandas as pd
from config import RAW_DIR, SHARK_ORDERS, START_DATE

GEAR_URL = ("https://www.publications.qld.gov.au/dataset/e20e6bcd-c076-42a2-9e17-7d549b02254e/"
            "resource/d3b7093a-1781-4d1e-ae9c-5c538be8d1ab/download/shark-gear-locations.xlsx")
PACKAGE = ("https://www.data.qld.gov.au/api/3/action/package_show"
           "?id=qld-shark-control-program-catch-statistics-great-barrier-reef-marine-park")


def to_float(x):
    return float(re.sub(r"[^0-9.]", "", str(x)))


# --- Gear locations: one sheet per area, degrees + decimal minutes ---
sheets = pd.read_excel(io.BytesIO(requests.get(GEAR_URL, timeout=120).content),
                       sheet_name=None, header=None)
gear = []
for area, sh in sheets.items():
    if area == "Summary":
        continue
    header = sh.index[sh[0].astype(str).str.strip() == "Location"]
    if len(header) == 0:
        continue
    body = sh.loc[header[0] + 1:, :6].copy()
    body[0] = body[0].ffill()
    for _, r in body.iterrows():
        try:
            lat = -(to_float(r[3]) + to_float(r[4]) / 60)
            lon = to_float(r[5]) + to_float(r[6]) / 60
        except ValueError:
            continue
        gear.append({"area": area, "location": str(r[0]).strip(), "gear_type": r[1],
                     "lat": lat, "lon": lon})
gear = pd.DataFrame(gear)
gear.to_csv(os.path.join(RAW_DIR, "qld_scp_gear_locations.csv"), index=False)
beaches = gear.groupby("location", as_index=False)[["lat", "lon"]].mean()
beaches["key"] = beaches["location"].str.lower().str.replace(r"[^a-z]", "", regex=True)
print(f"Gear: {len(gear)} drumlines/nets at {len(beaches)} beaches")

# --- Catch CSVs (financial years, 2020-21 onwards are CSV) ---
resources = requests.get(PACKAGE, timeout=120).json()["result"]["resources"]
catches = []
for res in resources:
    if not res["url"].lower().endswith(".csv"):
        continue
    raw = requests.get(res["url"], timeout=120).content.decode("utf-8-sig", errors="replace")
    df = pd.read_csv(io.StringIO(raw))
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"ScientificName": "Scientific Name", "Species Name": "Scientific Name"})
    if "Date" not in df.columns or "Scientific Name" not in df.columns:
        print(f"  skipped (different layout): {res['name'][:70]}")
        continue
    # Files mix day/month order (e.g. 2020-21 uses 7/13/2020): pick whichever parses cleanly
    dmy = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    mdy = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    df["date"] = dmy if dmy.isna().sum() <= mdy.isna().sum() else mdy
    df = df[df["date"] >= START_DATE]
    if df.empty:
        continue
    catches.append(df[["date", "Area", "Location", "Common Name", "Scientific Name", "Fate"]])
    print(f"  {len(df):>5} rows  {res['name'][:70]}")
catches = pd.concat(catches, ignore_index=True)
# Drop gear codes such as "SMART 605 Emu Park" or "CAD 6- Palm Cove"
catches["Location"] = (catches["Location"].astype(str).str.strip()
                       .str.replace(r"^(SMART|CAD)\s*\d+\s*-?\s*", "", regex=True))

# Keep sharks only: look up each scientific name's order in GBIF
orders = {}
for name in catches["Scientific Name"].dropna().unique():
    m = requests.get("https://api.gbif.org/v1/species/match",
                     params={"name": name}, timeout=60).json()
    orders[name] = m.get("order")
catches["order"] = catches["Scientific Name"].map(orders)
sharks = catches[catches["order"].isin(SHARK_ORDERS)].copy()

sharks["key"] = sharks["Location"].str.lower().str.replace(r"[^a-z]", "", regex=True)
sharks = sharks.merge(beaches[["key", "lat", "lon"]], on="key", how="left")
missing = sharks[sharks["lat"].isna()]["Location"].unique()
if len(missing):
    print(f"  No coordinates for {len(missing)} beach names: {', '.join(missing[:15])}")

out = os.path.join(RAW_DIR, "qld_scp_catches.csv")
sharks.to_csv(out, index=False)
print(f"Saved {len(sharks):,} shark catches ({sharks['lat'].notna().sum():,} with coordinates) -> {out}")
print(sharks["Scientific Name"].value_counts().head(10).to_string())
