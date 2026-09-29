"""Ocean feature extraction shared by dataset building (07), training (09) and maps (10).

Keeping this in one place guarantees the model sees exactly the same features at
prediction time as during training.
"""
import glob
import os
import time
import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import distance_transform_edt
from config import OCEAN_DIR, LAT_MIN, LAT_MAX

MAX_SNAP_KM = 10.0
KM_PER_DEG = 111.2

# Model inputs, in a fixed order
FEATURES = ["sst_c", "sst_front", "chl_log10", "sla_m", "adt_m", "current_ms",
            "depth_m", "dist_coast_km", "day_sin", "day_cos"]

# The six inputs that change day to day (the rest are fixed or come from the date)
OCEAN_FEATURES = ["sst_c", "sst_front", "chl_log10", "sla_m", "adt_m", "current_ms"]
OCEAN_SOURCES = {"sst": ["sst_c", "sst_front"], "ssh": ["sla_m", "adt_m", "current_ms"],
                 "chl": ["chl_log10"]}
CLIM_RES = 0.1       # common grid (degrees) for climatology, forecasts and maps

FEATURE_LABELS = {
    "sst_c": "Sea temperature (°C)", "sst_front": "Temperature front (°C/km)",
    "chl_log10": "Chlorophyll (log10 mg/m³)", "sla_m": "Sea level anomaly (m)",
    "adt_m": "Dynamic topography (m)", "current_ms": "Current speed (m/s)",
    "depth_m": "Depth (m)", "dist_coast_km": "Distance to coast (km)",
    "day_sin": "Season (sin)", "day_cos": "Season (cos)",
}


class Grid:
    """Regular lat/lon grid: maps points to the nearest ocean (non-NaN) cell."""

    def __init__(self, lat, lon, land_mask):
        self.lat0, self.dlat = float(lat[0]), float(lat[1] - lat[0])
        self.lon0, self.dlon = float(lon[0]), float(lon[1] - lon[0])
        self.shape = land_mask.shape
        mean_lat = np.deg2rad((LAT_MIN + LAT_MAX) / 2)
        sampling = (abs(self.dlat) * KM_PER_DEG, abs(self.dlon) * KM_PER_DEG * np.cos(mean_lat))
        dist, (self.near_i, self.near_j) = distance_transform_edt(
            land_mask, sampling=sampling, return_indices=True)
        self.snap_dist = dist

    def index(self, lats, lons, max_snap_km=MAX_SNAP_KM):
        i = np.clip(np.rint((lats - self.lat0) / self.dlat).astype(int), 0, self.shape[0] - 1)
        j = np.clip(np.rint((lons - self.lon0) / self.dlon).astype(int), 0, self.shape[1] - 1)
        ok = self.snap_dist[i, j] <= max_snap_km
        return self.near_i[i, j], self.near_j[i, j], ok


def open_daily(var):
    """Open all yearly files for a variable; reprocessed (my) wins over near-real-time (nrt)."""
    files = sorted(glob.glob(os.path.join(OCEAN_DIR, f"{var}_*_*.nc")),
                   key=lambda f: (os.path.basename(f).split("_")[1], "nrt" in f))
    if not files:
        raise SystemExit(f"No {var}_*.nc files in {OCEAN_DIR}. Run 05_get_ocean_data.py first.")
    day_index = {}
    datasets = []
    for f in files:
        ds = xr.open_dataset(f)
        datasets.append(ds)
        for k, t in enumerate(pd.to_datetime(ds["time"].values).normalize()):
            day_index.setdefault(t, (ds, k))   # first (my) file seen for a day wins
    return datasets, day_index


def available_days(var="sst"):
    datasets, day_index = open_daily(var)
    days = sorted(day_index)
    for ds in datasets:
        ds.close()
    return days


def extract_daily(var, points, fields, verbose=True):
    """For each day, load one 2-D slice per variable and read values at the points.

    fields: function(slice_dict, lat_1d) -> dict of derived 2-D arrays
    """
    datasets, day_index = open_daily(var)
    first = datasets[0]
    lat, lon = first["latitude"].values, first["longitude"].values
    data_vars = list(first.data_vars)
    land = np.isnan(first[data_vars[0]].isel(time=0).values)
    grid = Grid(lat, lon, land)
    ii, jj, ok = grid.index(points["lat"].values, points["lon"].values)
    # Each layer can have its own coastal mask (e.g. adt/currents are blank in some
    # shallow cells where sla has data), so each gets its own nearest-ocean fill.
    fill = {}
    for v in data_vars:
        mask = np.isnan(first[v].isel(time=0).values)
        _, idx = distance_transform_edt(mask, return_indices=True)
        fill[v] = idx

    out = {}
    days = points["date"].dt.normalize()
    unique_days = days.unique()
    t0 = time.time()
    for n, day in enumerate(sorted(unique_days)):
        rows = np.flatnonzero((days == day).values)
        if day not in day_index:
            continue
        ds, k = day_index[day]
        # Fill land with the nearest ocean value so gradients work right up to the coast
        slices = {v: ds[v].isel(time=k).values.astype("float32")[fill[v][0], fill[v][1]]
                  for v in data_vars}
        for name, arr in fields(slices, lat).items():
            col = out.setdefault(name, np.full(len(points), np.nan, dtype="float32"))
            col[rows] = np.where(ok[rows], arr[ii[rows], jj[rows]], np.nan)
        if verbose and (n + 1) % 250 == 0:
            print(f"    {var}: {n + 1}/{len(unique_days)} days ({time.time() - t0:.0f}s)", flush=True)
    for ds in datasets:
        ds.close()
    return pd.DataFrame(out, index=points.index)


def gradient_per_km(arr, lat, dlat_deg, dlon_deg):
    gy, gx = np.gradient(arr)
    dy = dlat_deg * KM_PER_DEG
    dx = dlon_deg * KM_PER_DEG * np.cos(np.deg2rad(lat))[:, None]
    return np.hypot(gy / dy, gx / dx)


def sst_fields(s, lat):
    sst = s["analysed_sst"] - 273.15
    return {"sst_c": sst, "sst_front": gradient_per_km(sst, lat, 0.05, 0.05)}


def chl_fields(s, lat):
    with np.errstate(divide="ignore", invalid="ignore"):
        return {"chl_log10": np.log10(s["CHL"])}


def ssh_fields(s, lat):
    return {"sla_m": s["sla"], "adt_m": s["adt"], "current_ms": np.hypot(s["ugos"], s["vgos"])}


def load_bathymetry():
    with xr.open_dataset(os.path.join(OCEAN_DIR, "bathymetry.nc")) as b:
        return b.load()


def add_ocean_features(points, bathy=None, verbose=True):
    """Add all FEATURES columns to a DataFrame with `date`, `lat`, `lon` columns."""
    points = points.copy()
    points["date"] = pd.to_datetime(points["date"])
    for var, fn in (("sst", sst_fields), ("ssh", ssh_fields), ("chl", chl_fields)):
        t = time.time()
        points = points.join(extract_daily(var, points, fn, verbose=verbose))
        if verbose:
            print(f"  {var} done in {time.time() - t:.0f}s")

    bathy = load_bathymetry() if bathy is None else bathy
    blat, blon = bathy["lat"].values, bathy["lon"].values
    bgrid = Grid(blat, blon, np.isnan(bathy["depth_m"].values))
    bi, bj, bok = bgrid.index(points["lat"].values, points["lon"].values)
    points["depth_m"] = np.where(bok, bathy["depth_m"].values[bi, bj], np.nan)
    points["dist_coast_km"] = np.where(bok, bathy["dist_coast_km"].values[bi, bj], np.nan)

    doy = points["date"].dt.dayofyear
    points["day_sin"] = np.sin(2 * np.pi * doy / 365.25)
    points["day_cos"] = np.cos(2 * np.pi * doy / 365.25)
    points["month"] = points["date"].dt.month
    points["year"] = points["date"].dt.year
    return points


FIELD_FUNCS = {"sst": sst_fields, "ssh": ssh_fields, "chl": chl_fields}


def season_features(dates):
    doy = pd.DatetimeIndex(dates).dayofyear
    return np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)


def common_grid(res=CLIM_RES, bathy=None):
    """0.1-degree grid over the study area.

    Returns lats (ny), lons (nx), ocean mask (ny, nx) and, for ocean cells,
    depth and distance to coast taken from the high-resolution bathymetry.
    """
    from config import LON_MIN, LON_MAX
    lats = np.round(np.arange(LAT_MIN + res / 2, LAT_MAX, res), 4)
    lons = np.round(np.arange(LON_MIN + res / 2, LON_MAX, res), 4)
    bathy = load_bathymetry() if bathy is None else bathy
    glon, glat = np.meshgrid(lons, lats)
    sel = dict(lat=xr.DataArray(glat.ravel()), lon=xr.DataArray(glon.ravel()), method="nearest")
    depth = bathy["depth_m"].sel(**sel).values.reshape(glat.shape)
    dist = bathy["dist_coast_km"].sel(**sel).values.reshape(glat.shape)
    ocean = np.isfinite(depth)
    return lats, lons, ocean, depth, dist


def iter_daily_on_cells(var, cell_lats, cell_lons, days=None, max_snap_km=20.0):
    """Yield (day, {feature: values at the cells}) for every day of a satellite variable.

    Uses exactly the same field calculations and nearest-ocean snapping as training.
    """
    datasets, day_index = open_daily(var)
    first = datasets[0]
    lat, lon = first["latitude"].values, first["longitude"].values
    data_vars = list(first.data_vars)
    grid = Grid(lat, lon, np.isnan(first[data_vars[0]].isel(time=0).values))
    ii, jj, ok = grid.index(np.asarray(cell_lats), np.asarray(cell_lons), max_snap_km)
    fill = {v: distance_transform_edt(np.isnan(first[v].isel(time=0).values), return_indices=True)[1]
            for v in data_vars}
    wanted = sorted(day_index) if days is None else [d for d in days if d in day_index]
    try:
        for day in wanted:
            ds, k = day_index[day]
            slices = {v: ds[v].isel(time=k).values.astype("float32")[fill[v][0], fill[v][1]]
                      for v in data_vars}
            yield day, {name: np.where(ok, arr[ii, jj], np.nan).astype("float32")
                        for name, arr in FIELD_FUNCS[var](slices, lat).items()}
    finally:
        for ds in datasets:
            ds.close()
