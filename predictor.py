"""Sharko predictor: shark presence likelihood for any position and any date.

The 10 model inputs are built differently depending on how far ahead the date is:

  mode       when                           ocean inputs from                 model
  --------   ----------------------------   -------------------------------   --------
  observed   past date, archive on disk     real satellite data of that day   daily
  forecast   within the Copernicus          official ocean forecast           daily
             forecast (~today+9 days)       (bias-corrected, 15_get_forecast)
  outlook    up to 90 days after the last   typical conditions + today's      seasonal
             known day                      unusual part, fading with time
  typical    further ahead (e.g. 2030)      typical conditions for that       seasonal
                                            place and week (2020-2026 mean)

Depth, distance to coast and season are always known exactly.

Known range: a species is only predicted within RANGE_KM of places where it was
actually recorded (2020-2026). Outside that, the likelihood is 0 and the answer says
so. This stops the model from "finding" habitat in regions the species does not use
just because the water there looks similar (e.g. white sharks in the tropical Gulf of
Carpentaria in winter).
In outlook/typical mode a range is also given: the same prediction for a cooler and
a warmer than normal year (sea temperature -/+ its usual year-to-year spread).

Python:
    from predictor import SharkoPredictor
    p = SharkoPredictor()
    p.predict_point(-33.9, 151.3, "2030-01-15")
    p.predict_grid("2030-01-15")            # whole map (0.1 deg) for the website

Command line:
    python predictor.py -33.9 151.3 2030-01-15
    python predictor.py -33.9 151.3 2026-10-04 --species tiger white
"""
import argparse
import glob
import json
import os
import joblib
from scipy.spatial import cKDTree
import numpy as np
import pandas as pd
import xarray as xr
from climatology import Climatology
from config import BASE_DIR, DATA_DIR, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN
from features import (FEATURES, OCEAN_FEATURES, Grid, add_ocean_features, available_days,
                      load_bathymetry, season_features)

DISPLAY = {"tiger": "Tiger Shark", "bull": "Bull Shark", "white": "Great White Shark", "any": "Any shark"}
OUTLOOK_MAX_DAYS = 90
RANGE_KM = 500


class SharkoPredictor:
    def __init__(self, base_dir=BASE_DIR, use_archive=True):
        models_dir = os.path.join(base_dir, "models")
        self.daily = self._load_models(models_dir)
        self.seasonal = self._load_models(os.path.join(models_dir, "seasonal"))
        if not self.daily:
            raise FileNotFoundError("No models in models/. Run 09_train_models.py")
        self.clim = Climatology(os.path.join(DATA_DIR, "climatology", "clim_all.nc"))

        fc_path = os.path.join(DATA_DIR, "forecast", "forecast.nc")
        self.forecast, self.fc_days, self.fc_issued = None, pd.DatetimeIndex([]), None
        if os.path.exists(fc_path):
            with xr.open_dataset(fc_path) as ds:
                self.forecast = ds.load()
            self.fc_days = pd.DatetimeIndex(self.forecast["time"].values).normalize()
            self.fc_issued = pd.Timestamp(self.forecast.attrs.get("issued"))
            self.fc_grid = Grid(self.forecast["lat"].values, self.forecast["lon"].values,
                                ~np.isfinite(self.forecast["sst_c"].isel(time=0).values))

        self.archive_days = set()
        if use_archive:
            try:
                self.archive_days = (set(available_days("sst")) & set(available_days("ssh"))
                                     & set(available_days("chl")))
            except SystemExit:
                pass

        self.bathy = load_bathymetry()
        self.bathy_grid = Grid(self.bathy["lat"].values, self.bathy["lon"].values,
                               np.isnan(self.bathy["depth_m"].values))
        self._build_ranges()

    @staticmethod
    def _xy_km(lats, lons):
        lats, lons = np.asarray(lats, float), np.asarray(lons, float)
        return np.c_[lats * 111.2, lons * 111.2 * np.cos(np.deg2rad(lats))]

    def _build_ranges(self):
        """KD-tree of recorded sightings per species, for the known-range check."""
        sightings = pd.read_csv(os.path.join(DATA_DIR, "sharks_australia.csv"))
        self.range_trees = {}
        for name, b in self.daily.items():
            rec = sightings if b["species"] == "ANY" else sightings[sightings["species"] == b["species"]]
            self.range_trees[name] = cKDTree(self._xy_km(rec["lat"], rec["lon"]))

    def in_range(self, name, lats, lons):
        dist, _ = self.range_trees[name].query(self._xy_km(lats, lons), k=1)
        return dist <= RANGE_KM

    @staticmethod
    def _load_models(folder):
        out = {}
        for path in sorted(glob.glob(os.path.join(folder, "*_model.joblib"))):
            name = os.path.basename(path).replace("_model.joblib", "")
            out[name] = joblib.load(path)
        return out

    # ------------------------------------------------------------------
    def last_known_day(self):
        days = list(self.fc_days) + sorted(self.archive_days)
        return max(days) if days else None

    def choose_mode(self, date):
        date = pd.Timestamp(date).normalize()
        if date in self.archive_days:
            return "observed"
        if date in set(self.fc_days):
            return "forecast"
        last = self.last_known_day()
        if last is not None and last < date <= last + pd.Timedelta(days=OUTLOOK_MAX_DAYS):
            return "outlook"
        return "typical"

    def _static(self, lats, lons, date):
        i, j, ok = self.bathy_grid.index(np.asarray(lats, float), np.asarray(lons, float))
        depth = np.where(ok, self.bathy["depth_m"].values[i, j], np.nan)
        dist = np.where(ok, self.bathy["dist_coast_km"].values[i, j], np.nan)
        s, c = season_features([date] * len(depth))
        return pd.DataFrame({"depth_m": depth, "dist_coast_km": dist, "day_sin": s, "day_cos": c})

    def _forecast_values(self, lats, lons, day):
        i, j, ok = self.fc_grid.index(np.asarray(lats, float), np.asarray(lons, float), 25.0)
        k = int(np.flatnonzero(self.fc_days == day)[0])
        return pd.DataFrame({f: np.where(ok, self.forecast[f].values[k][i, j], np.nan)
                             for f in OCEAN_FEATURES})

    def _known_anomaly(self, lats, lons):
        """Unusual part (value - typical) of the conditions on the last known day."""
        last = self.last_known_day()
        if last in set(self.fc_days):
            known = self._forecast_values(lats, lons, last)
        else:
            pts = pd.DataFrame({"date": last, "lat": lats, "lon": lons})
            known = add_ocean_features(pts, verbose=False)[OCEAN_FEATURES]
        typical = self.clim.sample(lats, lons, [last] * len(known))
        return last, (known.reset_index(drop=True) - typical).fillna(0.0)

    def inputs(self, lats, lons, date):
        """Build the 10 model inputs for points on one date. Returns (features, mode, info)."""
        date = pd.Timestamp(date).normalize()
        lats, lons = np.atleast_1d(np.asarray(lats, float)), np.atleast_1d(np.asarray(lons, float))
        mode = self.choose_mode(date)
        static = self._static(lats, lons, date)
        info = {}
        if mode == "observed":
            pts = pd.DataFrame({"date": date, "lat": lats, "lon": lons})
            ocean = add_ocean_features(pts, verbose=False)[OCEAN_FEATURES].reset_index(drop=True)
            info["source"] = "satellite measurements of this day"
        elif mode == "forecast":
            ocean = self._forecast_values(lats, lons, date)
            kind = "forecast" if date > self.fc_issued else "analysis"
            info["source"] = (f"Copernicus ocean {kind} issued {self.fc_issued:%Y-%m-%d}, "
                              "bias-corrected to satellite")
        else:
            ocean = self.clim.sample(lats, lons, [date] * len(lats))
            info["source"] = f"typical conditions for this place and week ({self.clim.years})"
            if mode == "outlook":
                last, anomaly = self._known_anomaly(lats, lons)
                lead = (date - last).days
                for f in OCEAN_FEATURES:
                    ocean[f] = ocean[f] + self.clim.persistence_factor(f, lead) * anomaly[f]
                info["source"] += (f" + {self.clim.persistence_factor('sst_c', lead):.0%} of the unusual "
                                   f"temperature seen on {last:%Y-%m-%d} ({lead} days earlier)")
        X = pd.concat([ocean.reset_index(drop=True), static], axis=1)[FEATURES]
        outside = ~((lats >= LAT_MIN) & (lats <= LAT_MAX) & (lons >= LON_MIN) & (lons <= LON_MAX))
        X.loc[outside, :] = np.nan                   # no data outside the study area
        return X, mode, info

    def _models_for(self, mode):
        if mode in ("observed", "forecast") or not self.seasonal:
            return self.daily, "daily"
        return self.seasonal, "seasonal"

    def _scores(self, X, models, species, known_range):
        valid = X.notna().all(axis=1).values
        out = {}
        for name in species:
            b = models[name]
            p = np.full(len(X), np.nan)
            if valid.any():
                p[valid] = b["model"].predict_proba(X.loc[valid, b["features"]])[:, 1]
            out[name] = np.where(known_range[name] | ~valid, p, 0.0)
        return out

    # ------------------------------------------------------------------
    def predict_points(self, lats, lons, date, species=None):
        """Scores for many points on one date. Returns DataFrame + mode + info."""
        X, mode, info = self.inputs(lats, lons, date)
        models, kind = self._models_for(mode)
        species = [s for s in (species or models) if s in models]
        lats, lons = np.atleast_1d(lats), np.atleast_1d(lons)
        known = {s: self.in_range(s, lats, lons) for s in species}
        scores = self._scores(X, models, species, known)
        df = pd.DataFrame({"lat": lats, "lon": lons})
        for s in species:
            df[s] = scores[s]
            df[f"{s}_in_range"] = known[s]
        if kind == "seasonal":                       # cooler / warmer year scenarios
            std = self.clim.sample(df["lat"], df["lon"], [pd.Timestamp(date)] * len(df), stat="std")
            for label, sign in (("cool", -1), ("warm", 1)):
                Xs = X.copy()
                Xs["sst_c"] = X["sst_c"] + sign * std["sst_c"].fillna(0).values
                sc = self._scores(Xs, models, species, known)
                for s in species:
                    df[f"{s}_{label}"] = sc[s]
        return df, X, mode, kind, info

    def predict_point(self, lat, lon, date, species=None):
        date = pd.Timestamp(date).normalize()
        df, X, mode, kind, info = self.predict_points([lat], [lon], date, species)
        row, x = df.iloc[0], X.iloc[0]
        models, _ = self._models_for(mode)
        if x.isna().any():
            return {"position": {"lat": lat, "lon": lon}, "date": f"{date:%Y-%m-%d}", "mode": mode,
                    "error": "No ocean data here (on land, far inland, or outside 110-160E / 9-46S)"}
        confidence = {
            "observed": "high - real satellite conditions of this day",
            "forecast": "high - official ocean forecast for this day",
            "outlook": "medium - typical conditions, adjusted by today's unusual conditions",
            "typical": "medium - typical conditions for this time of year; "
                       "cannot know if that year will be unusually warm or cool",
        }[mode]
        sharks = {}
        for name in [c for c in df.columns if c in models]:
            b = models[name]
            entry = {"species": b["species"] if b["species"] != "ANY" else "all shark species",
                     "presence_likelihood": round(float(row[name]), 3),
                     "likely_habitat": bool(row[name] >= b["threshold"]),
                     "threshold": round(float(b["threshold"]), 3),
                     "model": f"{b['model_name']} ({kind})",
                     "in_known_range": bool(row[f"{name}_in_range"])}
            if not entry["in_known_range"]:
                entry["note"] = f"not recorded within {RANGE_KM} km of here (2020-2026)"
            if f"{name}_cool" in row:
                lo, hi = sorted([row[f"{name}_cool"], row[f"{name}_warm"], row[name]])[::2]
                entry["range"] = [round(float(lo), 3), round(float(hi), 3)]
            sharks[DISPLAY.get(name, name)] = entry
        return {
            "position": {"lat": lat, "lon": lon},
            "date": f"{date:%Y-%m-%d}",
            "mode": mode,
            "confidence": confidence,
            "conditions_source": info["source"],
            "ocean_conditions": {
                "sea_temperature_c": round(float(x["sst_c"]), 2),
                "temperature_front_c_per_km": round(float(x["sst_front"]), 4),
                "chlorophyll_mg_m3": round(float(10 ** x["chl_log10"]), 3),
                "sea_level_anomaly_m": round(float(x["sla_m"]), 3),
                "current_speed_m_s": round(float(x["current_ms"]), 3),
                "depth_m": round(float(x["depth_m"]), 1),
                "distance_to_coast_km": round(float(x["dist_coast_km"]), 1),
            },
            "sharks": sharks,
        }

    def predict_grid(self, date, species=None):
        """Whole-Australia map on the 0.1-degree grid (ocean cells only)."""
        glon, glat = np.meshgrid(self.clim.lons, self.clim.lats)
        lats, lons = glat[self.clim.ocean], glon[self.clim.ocean]
        df, X, mode, kind, info = self.predict_points(lats, lons, date, species)
        df.attrs.update({"mode": mode, "model_kind": kind, "source": info["source"]})
        return df

    def status(self):
        return {
            "daily_models": sorted(self.daily), "seasonal_models": sorted(self.seasonal),
            "climatology_years": self.clim.years,
            "archive_days": (f"{min(self.archive_days):%Y-%m-%d} -> {max(self.archive_days):%Y-%m-%d}"
                             if self.archive_days else "none"),
            "forecast_days": (f"{self.fc_days.min():%Y-%m-%d} -> {self.fc_days.max():%Y-%m-%d} "
                              f"(issued {self.fc_issued:%Y-%m-%d})" if len(self.fc_days) else "none"),
        }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Shark presence likelihood for a position and date")
    ap.add_argument("lat", type=float)
    ap.add_argument("lon", type=float)
    ap.add_argument("date", help="YYYY-MM-DD, past or future")
    ap.add_argument("--species", nargs="+", help="tiger bull white any (default: all)")
    args = ap.parse_args()
    p = SharkoPredictor()
    print(json.dumps(p.predict_point(args.lat, args.lon, args.date, args.species), indent=2, ensure_ascii=False))
