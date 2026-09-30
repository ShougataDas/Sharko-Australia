"""Step 8: check every dataset in the pipeline and print a stats report.

Checks
  1. Raw shark downloads (OBIS, GBIF, QLD)       rows, date range, top species
  2. Merged shark table                          per year / source / species, duplicates
  3. Ocean data files (SST, SSH, CHL)            day coverage, missing days, value ranges
  4. Bathymetry                                  depth / distance-to-coast ranges
  5. Model dataset                               balance, missing values, duplicates,
                                                 feature ranges, sharks vs background,
                                                 per-species / per-year counts, warnings

Usage:
    python 08_check_dataset.py            # print report
The same report is saved to data/dataset_report.txt
"""
import glob
import io
import os
import sys
from contextlib import redirect_stdout
import numpy as np
import pandas as pd
import xarray as xr
from config import DATA_DIR, RAW_DIR, OCEAN_DIR, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)

FEATURES = ["sst_c", "sst_front", "chl_log10", "sla_m", "adt_m", "current_ms",
            "depth_m", "dist_coast_km", "day_sin", "day_cos"]
# Physically sensible ranges for Australian waters; values outside are flagged
EXPECTED = {
    "sst_c": (5, 35), "sst_front": (0, 1), "chl_log10": (-3, 2.5), "sla_m": (-1.5, 1.5),
    "adt_m": (-1, 2.5), "current_ms": (0, 3), "depth_m": (-1, 8000),
    "dist_coast_km": (0, 1500), "day_sin": (-1, 1), "day_cos": (-1, 1),
}
MIN_PRESENCES_FOR_MODEL = 300

warnings = []


def header(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def warn(msg):
    warnings.append(msg)
    print(f"  !! {msg}")


def read_csv(path, **kw):
    if not os.path.exists(path):
        warn(f"missing file: {os.path.relpath(path, DATA_DIR)}")
        return None
    return pd.read_csv(path, low_memory=False, **kw)


# ---------------------------------------------------------------------------
def check_raw():
    header("1. RAW SHARK DOWNLOADS")
    specs = {
        "obis_sharks.csv": ("eventDate", "species"),
        "gbif_sharks.csv": ("eventDate", "species"),
        "qld_scp_catches.csv": ("date", "Scientific Name"),
    }
    for fname, (date_col, sp_col) in specs.items():
        df = read_csv(os.path.join(RAW_DIR, fname))
        if df is None:
            continue
        dates = pd.to_datetime(df[date_col].astype(str).str[:10], errors="coerce")
        print(f"\n{fname}: {len(df):,} rows | {df[sp_col].nunique()} species | "
              f"{dates.min():%Y-%m-%d} -> {dates.max():%Y-%m-%d} | "
              f"{dates.isna().mean():.1%} bad dates | {df[sp_col].isna().mean():.1%} no species")
        print("  top species: " + ", ".join(f"{s} ({n})" for s, n in df[sp_col].value_counts().head(5).items()))
    gear = read_csv(os.path.join(RAW_DIR, "qld_scp_gear_locations.csv"))
    if gear is not None:
        print(f"\nqld_scp_gear_locations.csv: {len(gear)} gear units at {gear['location'].nunique()} beaches")


# ---------------------------------------------------------------------------
def check_merged():
    header("2. MERGED SHARK TABLE (data/sharks_australia.csv)")
    df = read_csv(os.path.join(DATA_DIR, "sharks_australia.csv"), parse_dates=["date"])
    if df is None:
        return
    print(f"{len(df):,} records | {df['species'].nunique()} species | "
          f"{df['date'].min():%Y-%m-%d} -> {df['date'].max():%Y-%m-%d}")
    outside = ~(df["lat"].between(LAT_MIN, LAT_MAX) & df["lon"].between(LON_MIN, LON_MAX))
    if outside.any():
        warn(f"{outside.sum()} records outside the study box")
    dups = df.duplicated(["species", "date", "lat", "lon"]).sum()
    print(f"exact duplicates: {dups}")
    print("\nrecords per year x source:")
    print(pd.crosstab(df["date"].dt.year, df["source"], margins=True, margins_name="total").to_string())
    print("\ntop 10 datasets:")
    print(df["dataset"].fillna("(unknown)").value_counts().head(10).to_string())


# ---------------------------------------------------------------------------
def check_ocean():
    header("3. OCEAN DATA FILES (data/ocean)")
    for var in ("sst", "ssh", "chl"):
        files = sorted(glob.glob(os.path.join(OCEAN_DIR, f"{var}_*_*.nc")))
        if not files:
            warn(f"no {var} files - run 05_get_ocean_data.py")
            continue
        print(f"\n{var.upper()}: {len(files)} files, "
              f"{sum(os.path.getsize(f) for f in files) / 1024**3:.1f} GB")
        all_days = set()
        rows = []
        for f in files:
            with xr.open_dataset(f) as ds:
                t = pd.to_datetime(ds["time"].values).normalize()
                all_days.update(t)
                v = list(ds.data_vars)[0]
                mid = ds[v].isel(time=len(t) // 2).values
                rows.append({
                    "file": os.path.basename(f), "days": len(t),
                    "first": f"{t.min():%Y-%m-%d}", "last": f"{t.max():%Y-%m-%d}",
                    "grid": f"{ds.sizes['latitude']}x{ds.sizes['longitude']}",
                    f"{v} min": np.nanmin(mid), f"{v} max": np.nanmax(mid),
                    "land/NaN %": round(100 * np.isnan(mid).mean(), 1),
                })
        print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        days = pd.DatetimeIndex(sorted(all_days))
        full = pd.date_range(days.min(), days.max(), freq="D")
        gaps = full.difference(days)
        print(f"  coverage: {days.min():%Y-%m-%d} -> {days.max():%Y-%m-%d}, "
              f"{len(days):,} days, {len(gaps)} missing days")
        if len(gaps):
            warn(f"{var}: {len(gaps)} missing days, e.g. {', '.join(str(g.date()) for g in gaps[:5])}")
        if var == "sst":
            lo, hi = rows[0]["analysed_sst min"] - 273.15, rows[0]["analysed_sst max"] - 273.15
            print(f"  (SST in Kelvin; {rows[0]['file']} mid-year = {lo:.1f} to {hi:.1f} deg C)")


# ---------------------------------------------------------------------------
def check_bathymetry():
    header("4. BATHYMETRY (data/ocean/bathymetry.nc)")
    path = os.path.join(OCEAN_DIR, "bathymetry.nc")
    if not os.path.exists(path):
        warn("missing bathymetry.nc - run 06_get_bathymetry.py")
        return
    with xr.open_dataset(path) as b:
        d, dc = b["depth_m"].values, b["dist_coast_km"].values
        print(f"grid {b.sizes['lat']}x{b.sizes['lon']} | ocean cells {np.isfinite(d).mean():.1%}")
        print(f"depth: {np.nanmin(d):.0f} to {np.nanmax(d):.0f} m (median {np.nanmedian(d):.0f})")
        print(f"distance to coast: 0 to {np.nanmax(dc):.0f} km (median {np.nanmedian(dc):.0f})")


# ---------------------------------------------------------------------------
def check_model_dataset():
    header("5. MODEL DATASET (data/model_dataset.csv.gz)")
    df = read_csv(os.path.join(DATA_DIR, "model_dataset.csv.gz"), parse_dates=["date"])
    if df is None:
        warn("run 07_build_dataset.py first")
        return
    pres, bg = df[df["presence"] == 1], df[df["presence"] == 0]
    print(f"{len(df):,} rows x {df.shape[1]} columns | "
          f"{df['date'].min():%Y-%m-%d} -> {df['date'].max():%Y-%m-%d}")
    print(f"presences {len(pres):,} ({len(pres) / len(df):.1%}) | background {len(bg):,} "
          f"({len(bg) / len(df):.1%}) | species {pres['species'].nunique()}")

    missing_cols = [c for c in FEATURES if c not in df.columns]
    if missing_cols:
        warn(f"missing feature columns: {missing_cols}")
    feats = [c for c in FEATURES if c in df.columns]

    # Missing / duplicates
    na = df[feats].isna().sum()
    print(f"\nmissing values: {'none' if na.sum() == 0 else na[na > 0].to_dict()}")
    if na.sum():
        warn("dataset has missing feature values")
    dups = df.duplicated(["presence", "species", "date", "lat", "lon"]).sum()
    print(f"duplicate rows: {dups}")
    if dups:
        warn(f"{dups} duplicate rows")
    if pres["species"].isna().any():
        warn(f"{pres['species'].isna().sum()} presences without species")

    # Feature ranges
    print("\nfeature ranges (all rows):")
    desc = df[feats].describe(percentiles=[0.01, 0.5, 0.99]).T
    desc["out_of_range"] = [int((~df[c].between(*EXPECTED[c])).sum()) for c in feats]
    print(desc[["min", "1%", "50%", "99%", "max", "out_of_range"]].round(3).to_string())
    for c in feats:
        if desc.loc[c, "out_of_range"]:
            warn(f"{c}: {desc.loc[c, 'out_of_range']} values outside {EXPECTED[c]}")
        if df[c].nunique() <= 1:
            warn(f"{c} is constant - useless as a feature")

    # Sharks vs background: standardised difference shows which features separate them
    print("\nsharks vs background (median, and effect size = mean diff / pooled std):")
    rows = []
    for c in feats:
        pooled = np.sqrt((pres[c].var() + bg[c].var()) / 2)
        rows.append({"feature": c, "shark median": pres[c].median(), "background median": bg[c].median(),
                     "effect size": (pres[c].mean() - bg[c].mean()) / pooled if pooled else 0})
    eff = pd.DataFrame(rows).set_index("feature")
    eff["strength"] = pd.cut(eff["effect size"].abs(), [-1, 0.2, 0.5, 0.8, 99],
                             labels=["tiny", "small", "medium", "large"])
    print(eff.round(3).to_string())

    # Correlations between features (very high = redundant)
    corr = df[feats].corr().abs()
    pairs = [(a, b, corr.loc[a, b]) for i, a in enumerate(feats) for b in feats[i + 1:]
             if corr.loc[a, b] > 0.8]
    print("\nhighly correlated feature pairs (|r| > 0.8): "
          + (", ".join(f"{a}~{b} ({r:.2f})" for a, b, r in pairs) or "none"))

    # Composition
    print("\nrows per source:")
    print(df["source"].value_counts().to_string())
    print("\nrows per year (presence vs background):")
    print(pd.crosstab(df["date"].dt.year, df["presence"]).rename(columns={0: "background", 1: "sharks"}).to_string())
    print("\nsharks per month (seasonality of records):")
    print(pres["date"].dt.month.value_counts().sort_index().to_frame("sharks").T.to_string())

    # Species
    counts = pres["species"].value_counts()
    enough = counts[counts >= MIN_PRESENCES_FOR_MODEL]
    print(f"\nspecies with >= {MIN_PRESENCES_FOR_MODEL} presences (enough for their own model): {len(enough)}")
    summary = pres.groupby("species").agg(
        records=("species", "size"), years=("year", "nunique"),
        lat_min=("lat", "min"), lat_max=("lat", "max"),
        sst_median=("sst_c", "median"), depth_median=("depth_m", "median"),
        coast_km_median=("dist_coast_km", "median"),
    ).loc[enough.index]
    print(summary.round(1).to_string())

    # Spatial spread: records per rough region
    region = pd.cut(pres["lon"], [110, 129, 141, 160], labels=["West", "Central/North", "East"])
    print("\nsharks per region (by longitude):")
    print(region.value_counts().to_string())


# ---------------------------------------------------------------------------
buf = io.StringIO()


class Tee(io.TextIOBase):
    def write(self, s):
        sys.__stdout__.write(s)
        buf.write(s)
        return len(s)


with redirect_stdout(Tee()):
    check_raw()
    check_merged()
    check_ocean()
    check_bathymetry()
    check_model_dataset()
    header("SUMMARY")
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("All checks passed - no warnings.")

report = os.path.join(DATA_DIR, "dataset_report.txt")
with open(report, "w", encoding="utf-8") as f:
    f.write(buf.getvalue())
print(f"\nReport saved -> {report}")
