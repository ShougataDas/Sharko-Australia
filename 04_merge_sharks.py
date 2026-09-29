"""Step 4: merge OBIS + GBIF + QLD Shark Control into one clean shark table.

Cleaning:
  - keep records identified to species, with a valid day-level date
  - drop records whose location is uncertain by more than 10 km
  - remove duplicates: same species, same day, same ~1 km spot
    (OBIS and GBIF share many datasets, and an acoustic receiver logs the
    same shark hundreds of times a day)
Output: data/sharks_australia.csv
"""
import os
import pandas as pd
from config import RAW_DIR, DATA_DIR, START_DATE, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX

COLS = ["source", "species", "date", "lat", "lon", "dataset", "basis", "uncertainty_m"]

obis = pd.read_csv(os.path.join(RAW_DIR, "obis_sharks.csv"), low_memory=False)
obis = pd.DataFrame({
    "source": "OBIS",
    "species": obis["species"],
    "date": pd.to_datetime(obis["eventDate"].astype(str).str[:10], errors="coerce"),
    "lat": obis["decimalLatitude"], "lon": obis["decimalLongitude"],
    "dataset": obis["datasetName"], "basis": obis["basisOfRecord"],
    "uncertainty_m": obis.get("coordinateUncertaintyInMeters"),
})

gbif = pd.read_csv(os.path.join(RAW_DIR, "gbif_sharks.csv"), low_memory=False)
gbif = gbif.dropna(subset=["year", "month", "day"])
gbif = pd.DataFrame({
    "source": "GBIF",
    "species": gbif["species"],
    "date": pd.to_datetime(dict(year=gbif["year"], month=gbif["month"], day=gbif["day"]), errors="coerce"),
    "lat": gbif["decimalLatitude"], "lon": gbif["decimalLongitude"],
    "dataset": gbif["datasetName"].fillna(gbif["institutionCode"]), "basis": gbif["basisOfRecord"],
    "uncertainty_m": gbif["coordinateUncertaintyInMeters"],
})

qld = pd.read_csv(os.path.join(RAW_DIR, "qld_scp_catches.csv"))
qld = pd.DataFrame({
    "source": "QLD_SCP",
    "species": qld["Scientific Name"].str.strip(),
    "date": pd.to_datetime(qld["date"], errors="coerce"),
    "lat": qld["lat"], "lon": qld["lon"],
    "dataset": "Queensland Shark Control Program", "basis": "Catch",
    "uncertainty_m": 1000,
})

df = pd.concat([obis[COLS], gbif[COLS], qld[COLS]], ignore_index=True)
print("Raw records by source:\n" + df["source"].value_counts().to_string())

df = df.dropna(subset=["species", "date", "lat", "lon"])
df = df[df["date"] >= START_DATE]
df = df[df["lat"].between(LAT_MIN, LAT_MAX) & df["lon"].between(LON_MIN, LON_MAX)]
df = df[~(pd.to_numeric(df["uncertainty_m"], errors="coerce") > 10000)]

# Duplicate key: species + day + ~1 km cell. QLD first so its catch records win ties.
df["source"] = pd.Categorical(df["source"], ["QLD_SCP", "OBIS", "GBIF"], ordered=True)
df = df.sort_values("source")
df["_k"] = (df["species"].str.lower() + "|" + df["date"].dt.strftime("%Y-%m-%d") + "|"
            + df["lat"].round(2).astype(str) + "|" + df["lon"].round(2).astype(str))
before = len(df)
df = df.drop_duplicates("_k").drop(columns="_k").sort_values("date")
print(f"\nRemoved {before - len(df):,} duplicates; {len(df):,} unique records remain.")

out = os.path.join(DATA_DIR, "sharks_australia.csv")
df.to_csv(out, index=False)
print(f"Saved -> {out}\n")
print("Records per year:\n" + df["date"].dt.year.value_counts().sort_index().to_string())
print("\nTop species:\n" + df["species"].value_counts().head(20).to_string())
