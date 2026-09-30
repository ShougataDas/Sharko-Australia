"""Step 12: build "typical ocean conditions" (climatology) for future-date predictions.

For every 0.1-degree ocean cell and every week of the year, averages the real daily
satellite data over all years, e.g. the typical sea temperature off Sydney in the
3rd week of January = the mean of ~7 Januaries (2020-2026).

For each of the 6 changing inputs (sea temperature, front, chlorophyll, sea level
anomaly, sea height, current speed) it saves:
  mean  typical value for that place and week (smoothed over +-2 weeks)
  std   year-to-year spread (how different a warm or cool year can be)
  persistence  how long an unusual condition lasts: correlation between this week's
               anomaly and the anomaly 1, 2, ... 26 weeks later

Two files are written:
  data/climatology/clim_all.nc         all years  -> used for real predictions
  data/climatology/clim_backtest.nc    years <= 2024 only -> used by the honest
                                       future test (14_backtest_future.py)
Needs the daily ocean files from 05_get_ocean_data.py. Takes ~10 minutes.
"""
import json
import os
import time
import warnings
import numpy as np
import pandas as pd
import xarray as xr
from config import DATA_DIR
from features import OCEAN_SOURCES, common_grid, iter_daily_on_cells, load_bathymetry

OUT_DIR = os.path.join(DATA_DIR, "climatology")
os.makedirs(OUT_DIR, exist_ok=True)
N_WEEKS = 52
SMOOTH_WEEKS = 5                 # +-2 weeks, i.e. roughly +-15 days
MAX_LAG_WEEKS = 26
BACKTEST_LAST_YEAR = 2024
PACKING = {                      # int16 storage: (scale, offset) keeps files small
    "sst_c": (0.001, 20), "sst_front": (0.00002, 0.6), "chl_log10": (0.0002, 0),
    "sla_m": (0.0001, 0), "adt_m": (0.0001, 1), "current_ms": (0.0001, 1.5),
}


def circular_smooth(a, width):
    """Running nan-mean over the week axis (axis=1), wrapping December -> January."""
    half = width // 2
    total = np.zeros_like(a)
    n = np.zeros(a.shape, "float32")
    for s in range(-half, half + 1):
        r = np.roll(a, s, axis=1)
        good = np.isfinite(r)
        total[good] += r[good]
        n += good
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, total / n, np.nan).astype("float32")


def persistence(weekly, clim_mean):
    """Pooled lag correlation of weekly anomalies, lags 1..MAX_LAG_WEEKS weeks."""
    anom = (weekly - clim_mean[None]).reshape(-1, weekly.shape[-1])   # continuous weekly series
    r = []
    for k in range(1, MAX_LAG_WEEKS + 1):
        a, b = anom[:-k], anom[k:]
        ok = np.isfinite(a) & np.isfinite(b)
        a, b = np.where(ok, a, 0), np.where(ok, b, 0)
        r.append(float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())))
    return r


def summarise(weekly, year_mask):
    """weekly: (years, 52, cells) block means -> mean, std, persistence for chosen years."""
    w = weekly[year_mask]
    smooth = circular_smooth(w, SMOOTH_WEEKS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean = np.nanmean(smooth, axis=0)
        std = np.nanstd(smooth, axis=0, ddof=1)
    return mean.astype("float32"), std.astype("float32"), persistence(w, mean)


# ---------------------------------------------------------------------------
bathy = load_bathymetry()
lats, lons, ocean, depth, dist = common_grid(bathy=bathy)
glon, glat = np.meshgrid(lons, lats)
cell_lat, cell_lon = glat[ocean], glon[ocean]
n_cells = int(ocean.sum())
print(f"Grid: {len(lats)} x {len(lons)} at 0.1 deg, {n_cells:,} ocean cells")

results = {}          # feature -> {"all": (mean, std, r), "backtest": (...)}
years_all = None
for var, feats in OCEAN_SOURCES.items():
    t0 = time.time()
    sums, counts, years = {}, {}, []
    n_days = 0
    for day, values in iter_daily_on_cells(var, cell_lat, cell_lon):
        if day.year not in years:
            years.append(day.year)
            for f in feats:
                sums.setdefault(f, []).append(np.zeros((N_WEEKS, n_cells), "float32"))
                counts.setdefault(f, []).append(np.zeros((N_WEEKS, n_cells), "float32"))
        y = years.index(day.year)
        w = min((day.dayofyear - 1) // 7, N_WEEKS - 1)
        for f in feats:
            v = values[f]
            good = np.isfinite(v)
            sums[f][y][w][good] += v[good]
            counts[f][y][w][good] += 1
        n_days += 1
        if n_days % 500 == 0:
            print(f"  {var}: {n_days} days ({time.time() - t0:.0f}s)", flush=True)
    years_all = years
    year_arr = np.array(years)
    for f in feats:
        with np.errstate(invalid="ignore", divide="ignore"):
            weekly = np.stack(sums[f]) / np.stack(counts[f])       # (years, 52, cells)
        results[f] = {"all": summarise(weekly, np.ones(len(years), bool)),
                      "backtest": summarise(weekly, year_arr <= BACKTEST_LAST_YEAR)}
        del weekly
    del sums, counts
    print(f"  {var}: {n_days} days, years {years[0]}-{years[-1]} done in {time.time() - t0:.0f}s")


def to_grid(vec):
    g = np.full(ocean.shape, np.nan, "float32")
    g[ocean] = vec
    return g


for version, year_label in (("all", f"{years_all[0]}-{years_all[-1]}"),
                            ("backtest", f"{years_all[0]}-{BACKTEST_LAST_YEAR}")):
    data_vars, encoding, pers = {}, {}, {}
    for f, res in results.items():
        mean, std, r = res[version]
        data_vars[f"{f}_mean"] = (("week", "lat", "lon"), np.stack([to_grid(m) for m in mean]))
        data_vars[f"{f}_std"] = (("week", "lat", "lon"), np.stack([to_grid(s) for s in std]))
        scale, offset = PACKING[f]
        for k in (f"{f}_mean", f"{f}_std"):
            encoding[k] = {"dtype": "int16", "scale_factor": scale, "add_offset": offset,
                           "_FillValue": -32768, "zlib": True, "complevel": 4}
        pers[f] = [round(x, 4) for x in r]
    data_vars["depth_m"] = (("lat", "lon"), np.where(ocean, depth, np.nan).astype("float32"))
    data_vars["dist_coast_km"] = (("lat", "lon"), np.where(ocean, dist, np.nan).astype("float32"))
    ds = xr.Dataset(data_vars, coords={"week": np.arange(N_WEEKS), "lat": lats, "lon": lons},
                    attrs={"years": year_label, "persistence": json.dumps(pers),
                           "description": "Weekly ocean climatology (mean, year-to-year std) on 0.1 deg"})
    path = os.path.join(OUT_DIR, f"clim_{version}.nc")
    ds.to_netcdf(path, encoding=encoding)
    print(f"\nSaved {path} ({os.path.getsize(path) / 1e6:.0f} MB, years {year_label})")
    print("  how long unusual conditions last (correlation after 1 / 4 / 8 / 13 weeks):")
    for f, r in pers.items():
        print(f"    {f:<11} {r[0]:.2f} / {r[3]:.2f} / {r[7]:.2f} / {r[12]:.2f}")
