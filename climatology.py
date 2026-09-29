"""Typical ocean conditions ("climatology") for any place and day of the year.

Built by 12_build_climatology.py. For each 0.1-degree ocean cell and each week of
the year it stores:
  <feature>_mean   the average over all years (e.g. typical mid-January sea temperature)
  <feature>_std    how much that week varies from year to year (used for ranges)
and, per feature, how long an unusual condition tends to last (persistence r(lag)),
which lets a warm/cold spell seen today fade gradually into the typical value.
"""
import json
import numpy as np
import pandas as pd
import xarray as xr
from features import OCEAN_FEATURES, Grid

N_WEEKS = 52


def week_position(dates):
    """Fractional week of the year -> (week0, week1, weight of week1). Weeks wrap around."""
    doy = pd.DatetimeIndex(dates).dayofyear.values
    pos = (doy - 4) / 7.0                       # week w is centred on day 7w + 4
    w0 = np.floor(pos).astype(int)
    f = pos - w0
    return w0 % N_WEEKS, (w0 + 1) % N_WEEKS, f


class Climatology:
    def __init__(self, path):
        with xr.open_dataset(path) as ds:
            ds = ds.load()
        self.path = path
        self.lats, self.lons = ds["lat"].values, ds["lon"].values
        self.mean = {f: ds[f"{f}_mean"].values.astype("float32") for f in OCEAN_FEATURES}
        self.std = {f: ds[f"{f}_std"].values.astype("float32") for f in OCEAN_FEATURES}
        self.depth, self.dist = ds["depth_m"].values, ds["dist_coast_km"].values
        self.ocean = np.isfinite(self.mean["sst_c"][0])
        self.years = ds.attrs.get("years", "")
        self.persistence = json.loads(ds.attrs["persistence"])   # {feature: [r(1 week), r(2 weeks), ...]}
        self.grid = Grid(self.lats, self.lons, ~self.ocean)

    def cells(self, lats, lons, max_snap_km=25.0):
        """Nearest ocean cell of the climatology grid for each point."""
        return self.grid.index(np.asarray(lats, float), np.asarray(lons, float), max_snap_km)

    def sample(self, lats, lons, dates, stat="mean"):
        """Typical conditions at points on dates, interpolated between weeks."""
        i, j, ok = self.cells(lats, lons)
        w0, w1, f = week_position(dates)
        src = self.mean if stat == "mean" else self.std
        out = {}
        for feat in OCEAN_FEATURES:
            a = src[feat]
            v = (1 - f) * a[w0, i, j] + f * a[w1, i, j]
            out[feat] = np.where(ok, v, np.nan)
        return pd.DataFrame(out)

    def field(self, date, stat="mean"):
        """Whole-grid typical conditions for one date: {feature: 2-D array}."""
        w0, w1, f = week_position([date])
        src = self.mean if stat == "mean" else self.std
        return {feat: (1 - f[0]) * src[feat][w0[0]] + f[0] * src[feat][w1[0]] for feat in OCEAN_FEATURES}

    def persistence_factor(self, feature, lead_days):
        """How much of today's anomaly is expected to remain after `lead_days` (0..1)."""
        r = np.concatenate([[1.0], np.asarray(self.persistence[feature], float)])
        weeks = np.clip(np.asarray(lead_days, float) / 7.0, 0, len(r) - 1)
        return np.clip(np.interp(weeks, np.arange(len(r)), r), 0, 1)
