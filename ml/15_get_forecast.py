"""Step 15: download the official Copernicus ocean forecast (next ~9 days) for Australia.

Copernicus runs a physics + biology model of the global ocean every day, like a
weather forecast for the sea. We take the last 45 days (the model's best estimate
of the recent past) and the forecast days ahead, and turn them into the same six
changing inputs the shark models use, on the common 0.1-degree grid:

  sea temperature, temperature front   <- thetao (surface water temperature)
  sea level anomaly, sea height         <- zos (sea surface height)
  current speed                         <- uo, vo (surface currents)
  chlorophyll                           <- chl (plankton model, 0.25 deg)

Bias correction: a forecast model is not identical to satellite measurements (for
example it may run slightly warm in some places, and its sea height has a different
reference level). Where the satellite archive is available, the average difference
"satellite - model" over the recent days both cover is computed for every cell and
added to the forecast. The correction is saved (data/forecast/bias.nc) so a server
without the 20 GB archive can reuse it.

Output: data/forecast/forecast.nc  (days x 0.1-degree grid, 6 corrected inputs)
Usage:  python 15_get_forecast.py            (needs: copernicusmarine login)
Run daily (e.g. with Windows Task Scheduler / cron) to keep the forecast fresh.
"""
import os
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import copernicusmarine as cm
from scipy.ndimage import distance_transform_edt
from config import DATA_DIR, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
from features import (OCEAN_FEATURES, OCEAN_SOURCES, Grid, available_days, common_grid,
                      gradient_per_km, iter_daily_on_cells)

FC_DIR = os.path.join(DATA_DIR, "forecast")
RAW_DIR = os.path.join(FC_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)
PAST_DAYS = 45
AHEAD_DAYS = 14
BIAS_DAYS = 30
KEEP_PAST_DAYS = 7        # recent days kept in forecast.nc (older days are only used for bias)

SOURCES = {
    "thetao": ("cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m", ["thetao"], True),
    "zos": ("cmems_mod_glo_phy_anfc_0.083deg_P1D-m", ["zos"], False),
    "cur": ("cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m", ["uo", "vo"], True),
    "chl": ("cmems_mod_glo_bgc-pft_anfc_0.25deg_P1D-m", ["chl"], True),
}

if not cm.login(check_credentials_valid=True):
    raise SystemExit("Not logged in. Run:  copernicusmarine login")

today = pd.Timestamp.today().normalize()
start, end = today - pd.Timedelta(days=PAST_DAYS), today + pd.Timedelta(days=AHEAD_DAYS)
raw = {}
for key, (dataset_id, variables, has_depth) in SOURCES.items():
    fname = f"{key}.nc"
    kw = dict(dataset_id=dataset_id, variables=variables,
              minimum_longitude=LON_MIN, maximum_longitude=LON_MAX,
              minimum_latitude=LAT_MIN, maximum_latitude=LAT_MAX,
              start_datetime=f"{start:%Y-%m-%d}T00:00:00", end_datetime=f"{end:%Y-%m-%d}T00:00:00",
              coordinates_selection_method="inside", output_directory=RAW_DIR,
              output_filename=fname, overwrite=True, disable_progress_bar=True)
    if has_depth:
        kw.update(minimum_depth=0, maximum_depth=1)
    cm.subset(**kw)
    with xr.open_dataset(os.path.join(RAW_DIR, fname)) as ds:
        ds = ds.load()
    if "depth" in ds.dims:
        ds = ds.isel(depth=0)
    raw[key] = ds
    t = pd.to_datetime(ds["time"].values)
    print(f"{key:<7} {dataset_id}: {t.min():%Y-%m-%d} -> {t.max():%Y-%m-%d} ({len(t)} days)")

days = pd.DatetimeIndex(sorted(set.intersection(*[set(pd.to_datetime(d["time"].values).normalize())
                                                   for d in raw.values()])))
print(f"Days available in all four: {days.min():%Y-%m-%d} -> {days.max():%Y-%m-%d}")

# ---------------------------------------------------------------------------
# Model fields -> the six inputs on the 0.1-degree cells
# ---------------------------------------------------------------------------
lats, lons, ocean, _, _ = common_grid()
glon, glat = np.meshgrid(lons, lats)
cell_lat, cell_lon = glat[ocean], glon[ocean]


class Sampler:
    """Fill land with nearest ocean value, then read at the 0.1-degree cells."""

    def __init__(self, ds, var):
        self.lat, self.lon = ds["latitude"].values, ds["longitude"].values
        mask = ~np.isfinite(ds[var].isel(time=0).values)
        self.fill = distance_transform_edt(mask, return_indices=True)[1]
        g = Grid(self.lat, self.lon, mask)
        self.i, self.j, self.ok = g.index(cell_lat, cell_lon, 25.0)

    def filled(self, arr):
        return arr[self.fill[0], self.fill[1]]

    def cells(self, arr):
        return np.where(self.ok, arr[self.i, self.j], np.nan).astype("float32")


samp = {"thetao": Sampler(raw["thetao"], "thetao"), "zos": Sampler(raw["zos"], "zos"),
        "cur": Sampler(raw["cur"], "uo"), "chl": Sampler(raw["chl"], "chl")}
dlat = float(np.diff(raw["thetao"]["latitude"].values).mean())
dlon = float(np.diff(raw["thetao"]["longitude"].values).mean())


def model_inputs(day):
    sel = lambda key, v: samp[key].filled(raw[key][v].sel(time=day, method="nearest").values.astype("float32"))
    sst = sel("thetao", "thetao")
    zos = sel("zos", "zos")
    speed = np.hypot(sel("cur", "uo"), sel("cur", "vo"))
    with np.errstate(divide="ignore", invalid="ignore"):
        chl = np.log10(np.clip(sel("chl", "chl"), 1e-3, None))
    return {
        "sst_c": samp["thetao"].cells(sst),
        "sst_front": samp["thetao"].cells(gradient_per_km(sst, samp["thetao"].lat, dlat, dlon)),
        "sla_m": samp["zos"].cells(zos),        # offsets fixed by bias correction below
        "adt_m": samp["zos"].cells(zos),
        "current_ms": samp["cur"].cells(speed),
        "chl_log10": samp["chl"].cells(chl),
    }


model = {d: model_inputs(d) for d in days}

# ---------------------------------------------------------------------------
# Bias correction against the satellite archive (if present)
# ---------------------------------------------------------------------------
bias_path = os.path.join(FC_DIR, "bias.nc")
try:
    sat_days = set(available_days("sst")) & set(available_days("ssh")) & set(available_days("chl"))
except SystemExit:
    sat_days = set()
overlap = sorted(set(days) & sat_days)[-BIAS_DAYS:]
if overlap:
    print(f"Bias correction from {len(overlap)} overlapping days "
          f"({overlap[0]:%Y-%m-%d} -> {overlap[-1]:%Y-%m-%d})")
    diffs = {f: [] for f in OCEAN_FEATURES}
    for var, feats in OCEAN_SOURCES.items():
        for day, sat in iter_daily_on_cells(var, cell_lat, cell_lon, days=overlap):
            for f in feats:
                diffs[f].append(sat[f] - model[day][f])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        bias = {f: np.nanmean(np.stack(v), axis=0).astype("float32") for f, v in diffs.items()}
    for f in OCEAN_FEATURES:        # cells with no overlap: use the domain median
        bias[f] = np.where(np.isfinite(bias[f]), bias[f], np.nanmedian(bias[f]))
    bias_ds = xr.Dataset({f: (("cell",), bias[f]) for f in OCEAN_FEATURES},
                         attrs={"from": f"{overlap[0]:%Y-%m-%d}", "to": f"{overlap[-1]:%Y-%m-%d}"})
    bias_ds.to_netcdf(bias_path)
elif os.path.exists(bias_path):
    with xr.open_dataset(bias_path) as b:
        bias = {f: b[f].values for f in OCEAN_FEATURES}
    print(f"No satellite archive here - reusing saved bias correction ({bias_path})")
else:
    bias = {f: np.zeros(len(cell_lat), "float32") for f in OCEAN_FEATURES}
    print("WARNING: no satellite archive and no saved bias - forecast used without correction")

print("Average correction (satellite - model): " +
      ", ".join(f"{f} {np.nanmean(bias[f]):+.3f}" for f in OCEAN_FEATURES))

# ---------------------------------------------------------------------------
# Save corrected inputs on the grid
# ---------------------------------------------------------------------------
days = days[days >= today - pd.Timedelta(days=KEEP_PAST_DAYS)]
out = {}
for f in OCEAN_FEATURES:
    arr = np.full((len(days),) + ocean.shape, np.nan, "float32")
    for k, d in enumerate(days):
        arr[k][ocean] = model[d][f] + bias[f]
    out[f] = (("time", "lat", "lon"), arr)
ds = xr.Dataset(out, coords={"time": days, "lat": lats, "lon": lons},
                attrs={"issued": f"{today:%Y-%m-%d}",
                       "note": "days <= issued are the model's analysis of the recent past; later days are forecast",
                       "bias_corrected": "yes" if overlap or os.path.exists(bias_path) else "no"})
path = os.path.join(FC_DIR, "forecast.nc")
ds.to_netcdf(path, encoding={f: {"zlib": True, "complevel": 4} for f in OCEAN_FEATURES})
print(f"Saved {path}: {days.min():%Y-%m-%d} -> {days.max():%Y-%m-%d} "
      f"(forecast beyond {today:%Y-%m-%d}), {os.path.getsize(path) / 1e6:.0f} MB")
