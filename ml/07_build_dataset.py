"""Step 7: build the model-ready dataset (shark records + ocean conditions on the day).

Presences (presence = 1)
  Shark records from data/sharks_australia.csv, thinned to one record per
  species per ~5 km cell per week, so a single acoustic receiver or a popular
  dive site does not dominate.

Background points (presence = 0)
  Sharks are only recorded where people look (dive sites, receivers, beaches).
  To stop the model learning "where people are" instead of "where sharks are":
    - 75% "target-group" background: placed in proportion to where ANY shark
      was recorded, on the same dates as real records (same observer bias)
    - 25% uniform background anywhere in the ocean, so maps can cover offshore
  Background points are shared by all species; filter presences by `species`
  when training a model for one species.

Ocean conditions, matched on the exact day of each point
  sst_c           sea surface temperature (deg C)                      OSTIA 0.05 deg
  sst_front       SST gradient (deg C per km) = strength of thermal fronts
  chl_log10       log10 chlorophyll-a (mg/m3) = productivity / food     GlobColour 4 km
  sla_m, adt_m    sea level anomaly / absolute dynamic topography = eddies
  current_ms      surface geostrophic current speed (m/s)             DUACS 0.125 deg
  depth_m, dist_coast_km                                              ETOPO 1 arc-min
Points on land/rivers are moved to the nearest ocean cell if it is within 10 km.

Output: data/model_dataset.csv.gz
"""
import os
import numpy as np
import pandas as pd
from config import DATA_DIR, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
from features import FEATURES, add_ocean_features, load_bathymetry

RNG = np.random.default_rng(42)
THIN_CELL_DEG = 0.05          # thinning grid (~5 km)
BIAS_CELL_DEG = 0.25          # grid used to measure where people record sharks
BACKGROUND_PER_PRESENCE = 1.0
TARGET_GROUP_SHARE = 0.75


# ---------------------------------------------------------------------------
# 1. Presences
# ---------------------------------------------------------------------------
print("STEP 1: shark presences")
sharks = pd.read_csv(os.path.join(DATA_DIR, "sharks_australia.csv"), parse_dates=["date"])
iso = sharks["date"].dt.isocalendar()
sharks["_cell"] = (np.floor(sharks["lat"] / THIN_CELL_DEG).astype(int).astype(str) + "_"
                   + np.floor(sharks["lon"] / THIN_CELL_DEG).astype(int).astype(str))
sharks["_week"] = iso["year"].astype(str) + "-" + iso["week"].astype(str)
before = len(sharks)
pres = sharks.drop_duplicates(["species", "_cell", "_week"]).drop(columns=["_cell", "_week"])
pres = pres[["species", "source", "dataset", "date", "lat", "lon"]].assign(presence=1)
print(f"  {before:,} records -> {len(pres):,} after thinning (1 per species / 5 km / week)")

# ---------------------------------------------------------------------------
# 2. Background points
# ---------------------------------------------------------------------------
print("STEP 2: background points")
bathy = load_bathymetry()
ocean = ~np.isnan(bathy["depth_m"].values)
blat, blon = bathy["lat"].values, bathy["lon"].values


def is_ocean(lats, lons):
    i = np.clip(np.rint((lats - blat[0]) / (blat[1] - blat[0])).astype(int), 0, len(blat) - 1)
    j = np.clip(np.rint((lons - blon[0]) / (blon[1] - blon[0])).astype(int), 0, len(blon) - 1)
    return ocean[i, j]


def sample_points(n, cell_weights=None):
    """Random ocean points; if cell_weights given, choose 0.25-deg cells by weight."""
    lats, lons = [], []
    while sum(map(len, lats)) < n:
        m = 2 * n
        if cell_weights is None:
            la = RNG.uniform(LAT_MIN, LAT_MAX, m)
            lo = RNG.uniform(LON_MIN, LON_MAX, m)
        else:
            cells = RNG.choice(len(cell_weights), m, p=cell_weights.values)
            ci = np.array([c[0] for c in cell_weights.index])[cells]
            cj = np.array([c[1] for c in cell_weights.index])[cells]
            la = (ci + RNG.random(m)) * BIAS_CELL_DEG
            lo = (cj + RNG.random(m)) * BIAS_CELL_DEG
        keep = is_ocean(la, lo)
        lats.append(la[keep])
        lons.append(lo[keep])
    return np.concatenate(lats)[:n], np.concatenate(lons)[:n]


n_bg = int(len(pres) * BACKGROUND_PER_PRESENCE)
n_tg = int(n_bg * TARGET_GROUP_SHARE)
counts = pres.groupby([np.floor(pres["lat"] / BIAS_CELL_DEG).astype(int),
                       np.floor(pres["lon"] / BIAS_CELL_DEG).astype(int)]).size()
tg_lat, tg_lon = sample_points(n_tg, counts / counts.sum())
un_lat, un_lon = sample_points(n_bg - n_tg)
bg = pd.DataFrame({
    "species": np.nan, "source": ["background_target_group"] * n_tg + ["background_uniform"] * (n_bg - n_tg),
    "dataset": np.nan,
    "date": RNG.choice(pres["date"].values, n_bg),          # same dates as real records
    "lat": np.concatenate([tg_lat, un_lat]), "lon": np.concatenate([tg_lon, un_lon]),
    "presence": 0,
})
print(f"  {n_tg:,} target-group + {n_bg - n_tg:,} uniform = {n_bg:,} background points")

points = pd.concat([pres, bg], ignore_index=True)
points["date"] = pd.to_datetime(points["date"])

# ---------------------------------------------------------------------------
# 3. Ocean conditions on the day
# ---------------------------------------------------------------------------
print("STEP 3: extracting ocean conditions (one daily map at a time)")
points = add_ocean_features(points, bathy)

# ---------------------------------------------------------------------------
# 4. Season features, clean up, save
# ---------------------------------------------------------------------------
missing = points[FEATURES].isna().any(axis=1)
print(f"\nSTEP 4: dropping {missing.sum():,} points without complete ocean data "
      f"(inland/river records, or dates not yet covered)")
print(points.loc[missing].groupby("source").size().to_string())
print("  missing values per feature: "
      + ", ".join(f"{c}={n}" for c, n in points[FEATURES].isna().sum().items() if n))
final = points[~missing].reset_index(drop=True)
for c in FEATURES[:-2]:
    final[c] = final[c].astype("float32").round(5)

out = os.path.join(DATA_DIR, "model_dataset.csv.gz")
final.to_csv(out, index=False, compression="gzip")
print(f"\nSaved {len(final):,} rows -> {out}")
print(f"  presences: {int(final['presence'].sum()):,}   background: {int((final['presence'] == 0).sum()):,}")
print("\nPresences per species (top 15):")
print(final[final["presence"] == 1]["species"].value_counts().head(15).to_string())
print("\nFeature summary (presence vs background means):")
print(final.groupby("presence")[FEATURES[:-2]].mean().T.round(3).to_string())
