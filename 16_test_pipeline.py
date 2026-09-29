"""Step 16: end-to-end test of the whole Sharko pipeline.

Checks every stage, from downloaded data to the final predict(lat, lon, date):

  1. environment     required packages import
  2. data            raw downloads, merged sharks, model datasets (daily + seasonal)
  3. features        re-computing inputs from the satellite archive gives exactly the
                     training values (train / predict consistency)
  4. climatology     physical ranges, seasons, no 2025-26 information in the backtest file
  5. forecast        covers the coming days, realistic values, agrees with satellite
  6. models          daily + seasonal models load and output valid probabilities
  7. predictor       picks the right mode for past / forecast / outlook / far-future
                     dates, gives the same answer as the models on training rows,
                     handles land and out-of-area positions, outlook fades smoothly
                     from forecast to typical, biology makes sense for future dates,
                     whole-Australia map works, speed
  8. backtest        honest future accuracy (if 14_backtest_future.py has been run)

Result per check: PASS, FAIL (broken - must fix), WARN (works but questionable),
SKIP (input not available, e.g. no 20 GB archive on a server).
Exit code 1 if anything FAILs.  Report: models/pipeline_test_report.md

Usage:
  python 16_test_pipeline.py          # everything (~2-3 min)
  python 16_test_pipeline.py --quick  # skip the slow checks (~30 s)
"""
import argparse
import functools
import glob
import importlib
import os
import sys
import time
import traceback
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
from config import BASE_DIR, DATA_DIR, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, OCEAN_DIR, RAW_DIR

RESULTS = []
CHECKS = []


class Skip(Exception):
    pass


class Warn(Exception):
    pass


def check(group, slow=False):
    def deco(fn):
        CHECKS.append((group, fn, slow))
        return fn
    return deco


def run(quick):
    for group, fn, slow in CHECKS:
        name = fn.__doc__.strip().splitlines()[0] if fn.__doc__ else fn.__name__
        if slow and quick:
            status, detail = "SKIP", "slow check (run without --quick)"
        else:
            t = time.time()
            try:
                detail = fn() or ""
                status = "PASS"
            except Skip as e:
                status, detail = "SKIP", str(e)
            except Warn as e:
                status, detail = "WARN", str(e)
            except AssertionError as e:
                status, detail = "FAIL", str(e) or "assertion failed"
            except Exception as e:
                status, detail = "FAIL", f"{type(e).__name__}: {e}"
                traceback.print_exc()
            detail = f"{detail} ({time.time() - t:.1f}s)" if status in ("PASS", "WARN") else detail
        RESULTS.append((group, name, status, detail))
        icon = {"PASS": "ok  ", "FAIL": "FAIL", "WARN": "warn", "SKIP": "skip"}[status]
        print(f"[{icon}] {group:<11} {name} - {detail}", flush=True)


# ---------------------------------------------------------------------------
# Shared, loaded once
# ---------------------------------------------------------------------------
@functools.cache
def daily_data():
    return pd.read_csv(os.path.join(DATA_DIR, "model_dataset.csv.gz"), parse_dates=["date"], low_memory=False)


@functools.cache
def seasonal_data():
    path = os.path.join(DATA_DIR, "model_dataset_seasonal.csv.gz")
    if not os.path.exists(path):
        raise Skip("run 13_build_seasonal_dataset.py")
    return pd.read_csv(path, parse_dates=["date"], low_memory=False)


@functools.cache
def archive_available():
    return len(glob.glob(os.path.join(OCEAN_DIR, "sst_*_*.nc"))) > 0


@functools.cache
def clim(version="all"):
    from climatology import Climatology
    path = os.path.join(DATA_DIR, "climatology", f"clim_{version}.nc")
    if not os.path.exists(path):
        raise Skip("run 12_build_climatology.py")
    return Climatology(path)


@functools.cache
def predictor():
    from predictor import SharkoPredictor
    return SharkoPredictor()


def feats():
    from features import FEATURES
    return FEATURES


# ---------------------------------------------------------------------------
# 1. Environment
# ---------------------------------------------------------------------------
@check("environment")
def t_imports():
    """required packages import"""
    missing = []
    for m in ["numpy", "pandas", "xarray", "scipy", "sklearn", "lightgbm", "joblib", "netCDF4"]:
        try:
            importlib.import_module(m)
        except ImportError:
            missing.append(m)
    assert not missing, f"missing: {missing} (pip install -r requirements.txt)"
    return "all present"


# ---------------------------------------------------------------------------
# 2. Data
# ---------------------------------------------------------------------------
@check("data")
def t_raw():
    """raw shark downloads present"""
    files = ["obis_sharks.csv", "gbif_sharks.csv", "qld_scp_catches.csv"]
    sizes = {f: len(pd.read_csv(os.path.join(RAW_DIR, f), low_memory=False)) for f in files}
    assert all(n > 100 for n in sizes.values()), f"too few rows: {sizes}"
    return ", ".join(f"{f.split('_')[0]} {n:,}" for f, n in sizes.items())


@check("data")
def t_sharks():
    """merged shark records are clean"""
    s = pd.read_csv(os.path.join(DATA_DIR, "sharks_australia.csv"), parse_dates=["date"])
    assert s["lat"].between(LAT_MIN, LAT_MAX).all() and s["lon"].between(LON_MIN, LON_MAX).all(), "records outside area"
    assert s["date"].min() >= pd.Timestamp("2020-01-01"), "records before 2020"
    assert s[["species", "date", "lat", "lon"]].notna().all().all(), "missing values"
    key = s.assign(lat2=s["lat"].round(2), lon2=s["lon"].round(2))
    dups = key.duplicated(["species", "date", "lat2", "lon2"]).sum()
    assert dups == 0, f"{dups} duplicates"
    return f"{len(s):,} records, {s['species'].nunique()} species"


@check("data")
def t_daily_dataset():
    """daily model dataset is complete and balanced"""
    d = daily_data()
    missing = [f for f in feats() if f not in d.columns]
    assert not missing, f"missing columns {missing}"
    assert d[feats()].notna().all().all(), "NaN in features"
    assert set(d["presence"].unique()) == {0, 1}, "presence not 0/1"
    share = d["presence"].mean()
    assert 0.3 < share < 0.7, f"unbalanced: {share:.0%} presences"
    return f"{len(d):,} rows, {share:.0%} sightings"


@check("data")
def t_seasonal_dataset():
    """seasonal dataset matches the daily one row for row"""
    d, s = daily_data(), seasonal_data()
    assert len(d) == len(s), f"{len(d)} vs {len(s)} rows"
    for c in ["presence", "lat", "lon", "depth_m", "dist_coast_km", "day_sin"]:
        assert np.allclose(d[c], s[c], equal_nan=True), f"column {c} differs"
    assert (d["date"] == s["date"]).all(), "dates differ"
    assert s[feats()].notna().all().all(), "NaN in features"
    assert s["sst_c"].std() < d["sst_c"].std() + 0.1, "typical conditions should be smoother than daily"
    return "same points, typical ocean inputs"


@check("data")
def t_bathymetry():
    """bathymetry depth / distance ranges"""
    import xarray as xr
    with xr.open_dataset(os.path.join(OCEAN_DIR, "bathymetry.nc")) as b:
        d, c = b["depth_m"].values, b["dist_coast_km"].values
    assert 0 < np.nanmin(d) and np.nanmax(d) < 11000, "depth out of range"
    assert 0 < np.nanmin(c) and np.nanmax(c) < 2000, "distance out of range"
    return f"depth to {np.nanmax(d):.0f} m, ocean {np.isfinite(d).mean():.0%}"


# ---------------------------------------------------------------------------
# 3. Features: archive -> same values as training
# ---------------------------------------------------------------------------
@check("features")
def t_archive_days():
    """satellite archive has no missing days"""
    if not archive_available():
        raise Skip("no daily ocean archive on this machine")
    from features import available_days
    out = []
    for var in ("sst", "ssh", "chl"):
        days = pd.DatetimeIndex(available_days(var))
        gaps = pd.date_range(days.min(), days.max()).difference(days)
        assert len(gaps) == 0, f"{var}: {len(gaps)} missing days"
        out.append(f"{var} to {days.max():%Y-%m-%d}")
    return ", ".join(out)


@check("features", slow=True)
def t_feature_reproduction():
    """re-computed inputs equal the training values"""
    if not archive_available():
        raise Skip("no daily ocean archive on this machine")
    from features import add_ocean_features
    d = daily_data().sample(200, random_state=7)
    r = add_ocean_features(d[["date", "lat", "lon"]], verbose=False)
    diff = (r[feats()].values - d[feats()].values)
    worst = pd.Series(np.nanmax(np.abs(diff), axis=0), index=feats())
    tol = pd.Series(1e-3, index=feats()); tol["depth_m"] = 1.0
    bad = worst[worst > tol]
    assert bad.empty, f"differences: {bad.round(4).to_dict()}"
    return f"200 random rows identical (max diff {worst.drop('depth_m').max():.1e})"


# ---------------------------------------------------------------------------
# 4. Climatology
# ---------------------------------------------------------------------------
@check("climatology")
def t_clim_ranges():
    """typical conditions are physically realistic"""
    c = clim("all")
    ranges = {"sst_c": (0, 35), "chl_log10": (-3, 2.5), "sla_m": (-1, 1), "adt_m": (-1, 3), "current_ms": (0, 3)}
    for f, (lo, hi) in ranges.items():
        v = c.mean[f][:, c.ocean]
        assert np.nanmin(v) >= lo and np.nanmax(v) <= hi, f"{f} {np.nanmin(v):.2f}..{np.nanmax(v):.2f}"
        assert np.nanmin(c.std[f][:, c.ocean]) >= 0, f"{f} negative spread"
    assert np.isfinite(c.mean["sst_c"][:, c.ocean]).mean() > 0.99, "gaps in climatology"
    return f"years {c.years}, {c.ocean.sum():,} ocean cells x 52 weeks"


@check("climatology")
def t_clim_seasons():
    """seasons and latitudes make sense"""
    c = clim("all")
    sst = lambda lat, lon, d: float(c.sample([lat], [lon], [d])["sst_c"][0])
    hob_j, hob_jul = sst(-43.2, 147.8, "2030-01-15"), sst(-43.2, 147.8, "2030-07-15")
    cairns_j = sst(-16.7, 146.0, "2030-01-15")
    syd = sst(-33.9, 151.3, "2030-01-15")
    assert hob_j > hob_jul + 2, f"Hobart summer {hob_j:.1f} not warmer than winter {hob_jul:.1f}"
    assert cairns_j > hob_j + 5, "tropics not warmer than Tasmania"
    assert 20 < syd < 26, f"Sydney January {syd:.1f} C unrealistic"
    return f"Sydney Jan {syd:.1f} C, Hobart Jan/Jul {hob_j:.1f}/{hob_jul:.1f} C, Cairns Jan {cairns_j:.1f} C"


@check("climatology")
def t_clim_persistence():
    """unusual conditions fade over time"""
    c = clim("all")
    for f in ("sst_c", "chl_log10", "sla_m"):
        r = [c.persistence_factor(f, d) for d in (0, 7, 30, 90, 180)]
        assert all(0 <= x <= 1 for x in r), f"{f} factor outside 0..1"
        assert r[0] == 1 and r[1] > r[3] > r[4] - 0.05, f"{f} does not fade: {np.round(r, 2)}"
    s = [round(float(c.persistence_factor("sst_c", d)), 2) for d in (7, 30, 90)]
    return f"sst anomaly kept after 1 wk / 1 mo / 3 mo: {s}"


@check("climatology")
def t_clim_no_leak():
    """backtest climatology contains no 2025-26 data"""
    c = clim("backtest")
    assert c.years.endswith("2024"), f"backtest climatology covers {c.years}"
    return c.years


@check("climatology")
def t_seasonal_matches_clim():
    """seasonal dataset = climatology at each point"""
    s = seasonal_data().sample(500, random_state=3)
    from features import OCEAN_FEATURES
    v = clim("all").sample(s["lat"], s["lon"], s["date"])
    worst = np.nanmax(np.abs(v[OCEAN_FEATURES].values - s[OCEAN_FEATURES].values))
    assert worst < 1e-3, f"max difference {worst}"
    return f"500 rows match (max diff {worst:.1e})"


# ---------------------------------------------------------------------------
# 5. Forecast
# ---------------------------------------------------------------------------
@check("forecast")
def t_forecast_file():
    """forecast covers the coming days"""
    p = predictor()
    if not len(p.fc_days):
        raise Skip("no data/forecast/forecast.nc - run 15_get_forecast.py")
    ahead = (p.fc_days.max() - pd.Timestamp.today().normalize()).days
    age = (pd.Timestamp.today().normalize() - p.fc_issued).days
    if age > 3:
        raise Warn(f"forecast issued {age} days ago - re-run 15_get_forecast.py")
    assert ahead >= 3, f"forecast only reaches {ahead} days ahead"
    sst = p.forecast["sst_c"].values
    assert 0 < np.nanmin(sst) and np.nanmax(sst) < 35, "unrealistic forecast SST"
    return f"{p.fc_days.min():%Y-%m-%d} -> {p.fc_days.max():%Y-%m-%d}, {ahead} days ahead"


@check("forecast", slow=True)
def t_forecast_vs_satellite():
    """bias-corrected forecast agrees with satellite"""
    p = predictor()
    if not len(p.fc_days) or not archive_available():
        raise Skip("needs forecast file and satellite archive")
    common = sorted(set(p.fc_days) & p.archive_days)
    if not common:
        raise Skip("no day in both forecast and archive")
    day = common[-1]
    rng = np.random.default_rng(0)
    idx = rng.choice(np.flatnonzero(p.clim.ocean.ravel()), 300, replace=False)
    glon, glat = np.meshgrid(p.clim.lons, p.clim.lats)
    lats, lons = glat.ravel()[idx], glon.ravel()[idx]
    from features import add_ocean_features
    sat = add_ocean_features(pd.DataFrame({"date": day, "lat": lats, "lon": lons}), verbose=False)
    fc = p._forecast_values(lats, lons, day)
    err = np.nanmean(np.abs(fc["sst_c"].values - sat["sst_c"].values))
    typ = p.clim.sample(lats, lons, [day] * len(lats))
    err_typ = np.nanmean(np.abs(typ["sst_c"].values - sat["sst_c"].values))
    assert err < 1.0, f"forecast SST off by {err:.2f} C on average"
    if err > err_typ:
        raise Warn(f"forecast ({err:.2f} C) no better than typical conditions ({err_typ:.2f} C)")
    return f"{day:%Y-%m-%d}: SST error {err:.2f} C (typical-conditions guess: {err_typ:.2f} C)"


# ---------------------------------------------------------------------------
# 6. Models
# ---------------------------------------------------------------------------
@check("models")
def t_models():
    """daily and seasonal models load and output probabilities"""
    p = predictor()
    X = daily_data()[feats()].sample(500, random_state=1)
    out = []
    for kind, models in (("daily", p.daily), ("seasonal", p.seasonal)):
        for name, b in models.items():
            assert b["features"] == feats(), f"{kind}/{name}: feature list differs"
            pr = b["model"].predict_proba(X)[:, 1]
            assert np.isfinite(pr).all() and pr.min() >= 0 and pr.max() <= 1, f"{kind}/{name}: bad output"
            assert 0 < b["threshold"] < 1, f"{kind}/{name}: bad threshold"
        out.append(f"{kind}: {', '.join(sorted(models)) or 'none'}")
    if not p.seasonal:
        raise Warn("no seasonal models - long-range dates fall back to daily models "
                   "(run 09_train_models.py --mode seasonal)")
    missing = set(p.daily) - set(p.seasonal)
    if missing:
        raise Warn(f"no seasonal model for {sorted(missing)}; " + "; ".join(out))
    return "; ".join(out)


@check("models")
def t_model_quality():
    """models beat 0.7 AUC on unseen regions"""
    p = predictor()
    rows = [(f"{k}/{n}", b["metrics"]["spatial_auc"]) for k, m in (("daily", p.daily), ("seasonal", p.seasonal))
            for n, b in m.items()]
    weak = [f"{n} {a:.2f}" for n, a in rows if a < 0.7]
    if weak:
        raise Warn(f"weak: {weak}")
    return ", ".join(f"{n} {a:.2f}" for n, a in rows)


# ---------------------------------------------------------------------------
# 7. Predictor (the function the website will call)
# ---------------------------------------------------------------------------
@check("predictor")
def t_modes():
    """right mode for each kind of date"""
    p = predictor()
    cases = {"2030-06-01": "typical"}
    if p.archive_days:
        cases["2025-01-15"] = "observed"
    if len(p.fc_days):
        future_fc = [d for d in p.fc_days if d not in p.archive_days]
        if future_fc:
            cases[f"{future_fc[-1]:%Y-%m-%d}"] = "forecast"
    last = p.last_known_day()
    if last is not None:
        cases[f"{last + pd.Timedelta(days=30):%Y-%m-%d}"] = "outlook"
        cases[f"{last + pd.Timedelta(days=200):%Y-%m-%d}"] = "typical"
    wrong = {d: (p.choose_mode(d), m) for d, m in cases.items() if p.choose_mode(d) != m}
    assert not wrong, f"got/expected: {wrong}"
    return ", ".join(f"{d}->{m}" for d, m in cases.items())


@check("predictor")
def t_output_schema():
    """point prediction has all fields and valid numbers"""
    p = predictor()
    r = p.predict_point(-33.9, 151.3, "2030-01-15")
    for k in ("position", "date", "mode", "confidence", "conditions_source", "ocean_conditions", "sharks"):
        assert k in r, f"missing '{k}'"
    assert r["sharks"], "no species in output"
    for name, s in r["sharks"].items():
        v = s["presence_likelihood"]
        assert 0 <= v <= 1, f"{name}: likelihood {v}"
        assert isinstance(s["likely_habitat"], bool)
        if "range" in s:
            lo, hi = s["range"]
            assert lo <= v + 1e-9 and v <= hi + 1e-9, f"{name}: {v} outside range {s['range']}"
    return f"{len(r['sharks'])} species, mode {r['mode']}"


@check("predictor")
def t_bad_positions():
    """land and out-of-area positions return an error"""
    p = predictor()
    land = p.predict_point(-23.7, 133.9, "2030-01-15")          # Alice Springs
    outside = p.predict_point(10.0, 100.0, "2030-01-15")        # Gulf of Thailand
    assert "error" in land, "inland point got a prediction"
    assert "error" in outside, "point outside the study area got a prediction"
    return "Alice Springs and Gulf of Thailand rejected"


@check("predictor")
def t_deterministic():
    """same question, same answer"""
    p = predictor()
    a = p.predict_point(-28.0, 153.6, "2031-03-10")
    b = p.predict_point(-28.0, 153.6, "2031-03-10")
    assert a == b, "different answers"
    return "identical"


@check("predictor", slow=True)
def t_parity_observed():
    """predictor == models on training rows (observed mode)"""
    p = predictor()
    if not p.archive_days:
        raise Skip("no satellite archive")
    d = daily_data()
    d = d[d["presence"] == 1].sample(25, random_state=11)
    worst_in, worst_out = 0.0, 0.0
    name = "any" if "any" in p.daily else sorted(p.daily)[0]
    for _, row in d.iterrows():
        X, mode, _ = p.inputs([row["lat"]], [row["lon"]], row["date"])
        assert mode == "observed", f"{row['date']:%Y-%m-%d} not observed"
        diff = np.abs(X.iloc[0][feats()].values - row[feats()].values.astype(float))
        diff[feats().index("depth_m")] = 0
        worst_in = max(worst_in, np.nanmax(diff))
        a = p.daily[name]["model"].predict_proba(X[feats()])[:, 1][0]
        b = p.daily[name]["model"].predict_proba(row[feats()].to_frame().T.astype(float))[:, 1][0]
        worst_out = max(worst_out, abs(a - b))
    assert worst_in < 1e-3, f"inputs differ by {worst_in:.4f}"
    assert worst_out < 0.02, f"predictions differ by {worst_out:.4f}"
    return f"25 sightings: inputs max diff {worst_in:.1e}, prediction max diff {worst_out:.1e}"


@check("predictor")
def t_outlook_continuity():
    """outlook starts at the last known ocean and fades to typical"""
    p = predictor()
    last = p.last_known_day()
    if last is None or not len(p.fc_days) or last not in set(p.fc_days):
        raise Skip("needs a forecast file")
    rng = np.random.default_rng(1)
    idx = rng.choice(np.flatnonzero(p.clim.ocean.ravel()), 300, replace=False)
    glon, glat = np.meshgrid(p.clim.lons, p.clim.lats)
    lats, lons = glat.ravel()[idx], glon.ravel()[idx]
    known = p._forecast_values(lats, lons, last)["sst_c"].values
    near, m1, _ = p.inputs(lats, lons, last + pd.Timedelta(days=1))
    far, m2, _ = p.inputs(lats, lons, last + pd.Timedelta(days=89))
    typical_far = p.clim.sample(lats, lons, [last + pd.Timedelta(days=89)] * len(lats))["sst_c"].values
    assert m1 == m2 == "outlook", f"modes {m1}, {m2}"
    jump = np.nanmean(np.abs(near["sst_c"].values - known))
    gap_far = np.nanmean(np.abs(far["sst_c"].values - typical_far))
    anomaly = np.nanmean(np.abs(known - p.clim.sample(lats, lons, [last] * len(lats))["sst_c"].values))
    assert jump < 0.5, f"day after the forecast jumps {jump:.2f} C"
    assert gap_far < max(0.5 * anomaly, 0.3), f"90 days ahead still {gap_far:.2f} C from typical"
    return f"day +1 differs {jump:.2f} C from forecast; day +89 within {gap_far:.2f} C of typical"


@check("predictor")
def t_future_biology():
    """future predictions follow known biology"""
    p = predictor()
    msgs = []

    def score(sp, lat, lon, date):
        r = p.predict_point(lat, lon, date, [sp])
        assert "error" not in r, r.get("error")
        return list(r["sharks"].values())[0]["presence_likelihood"]
    newcastle, cairns, tas = (-32.9, 151.8), (-16.9, 145.8), (-42.1, 148.3)
    if "white" in p.daily:      # most winter white-shark records are off central NSW
        a, b = score("white", *newcastle, "2030-07-15"), score("white", *cairns, "2030-07-15")
        assert a > b, f"white shark July: NSW {a:.2f} <= Cairns {b:.2f}"
        msgs.append(f"white Jul NSW {a:.2f} > Cairns {b:.2f}")
    for sp in ("tiger", "bull"):
        if sp in p.daily:
            a, b = score(sp, *cairns, "2030-01-15"), score(sp, *tas, "2030-01-15")
            assert a > b, f"{sp}: Cairns {a:.2f} <= Tasmania {b:.2f}"
            msgs.append(f"{sp} Jan Cairns {a:.2f} > Tas {b:.2f}")
    return "; ".join(msgs)


@check("predictor")
def t_known_range():
    """no habitat predicted far outside a species' recorded range"""
    p = predictor()
    if "white" not in p.daily:
        raise Skip("no white shark model")
    glon, glat = np.meshgrid(p.clim.lons, p.clim.lats)
    tropics = p.clim.ocean & (glat > -20) & (glon > 125) & (glon < 145)     # Gulf of Carpentaria / Arafura
    lats, lons = glat[tropics][::20], glon[tropics][::20]
    df, _, mode, kind, _ = p.predict_points(lats, lons, "2030-07-15", ["white"])
    assert (df["white"].fillna(0) == 0).all(), f"white-shark habitat in the tropical north: max {df['white'].max():.2f}"
    r = p.predict_point(-15.0, 137.0, "2030-07-15", ["white"])
    assert r["sharks"]["Great White Shark"]["in_known_range"] is False
    return f"{len(lats)} Gulf/Arafura cells: white shark likelihood 0 (outside recorded range)"


@check("predictor", slow=True)
def t_grid():
    """whole-Australia map for a future date"""
    p = predictor()
    t = time.time()
    g = p.predict_grid("2030-07-15")
    secs = time.time() - t
    species = [c for c in g.columns if c in p.daily]
    assert len(g) == int(p.clim.ocean.sum()), "wrong number of cells"
    for s in species:
        v = g[s].values
        assert np.nanmin(v) >= 0 and np.nanmax(v) <= 1, f"{s} out of range"
        assert np.isfinite(v).mean() > 0.95, f"{s}: {np.isnan(v).mean():.0%} cells missing"
    models, _ = p._models_for(g.attrs["mode"])
    share = {s: float((g[s] >= models[s]["threshold"]).mean()) for s in species}
    if any(v == 0 or v > 0.6 for v in share.values()):
        raise Warn(f"suspicious habitat share: {share}")
    if secs > 90:
        raise Warn(f"slow: {secs:.0f}s for the map")
    return (f"{len(g):,} cells in {secs:.0f}s; habitat share "
            + ", ".join(f"{s} {v:.1%}" for s, v in share.items()))


@check("predictor")
def t_speed():
    """single prediction is fast"""
    p = predictor()
    t = time.time()
    for d in ("2030-01-15", "2031-06-01", "2029-11-20"):
        p.predict_point(-27.5, 153.5, d)
    secs = (time.time() - t) / 3
    if secs > 2:
        raise Warn(f"{secs:.1f}s per prediction")
    return f"{secs * 1000:.0f} ms per future prediction"


# ---------------------------------------------------------------------------
# 8. Backtest
# ---------------------------------------------------------------------------
@check("backtest")
def t_backtest():
    """honest future accuracy (trained to 2024, tested on 2025-26)"""
    path = os.path.join(BASE_DIR, "models", "backtest.csv")
    if not os.path.exists(path):
        raise Skip("run 14_backtest_future.py")
    b = pd.read_csv(path)
    typ = b[b["method"].str.startswith("Typical")].set_index("model")
    base = b[b["method"].str.startswith("Place")].set_index("model")
    msg = ", ".join(f"{m} {a:.2f}" for m, a in typ["auc"].items())
    weak = typ[typ["auc"] < 0.7]
    if not weak.empty:
        raise Warn(f"future AUC below 0.7: {weak['auc'].round(2).to_dict()}")
    worse = [m for m in typ.index if typ.loc[m, "auc"] < base.loc[m, "auc"] - 0.02]
    if worse:
        raise Warn(f"ocean climatology not better than place+season for {worse}; AUC {msg}")
    return f"future AUC (typical conditions): {msg}"


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip slow checks")
    args = ap.parse_args()
    print(f"Sharko pipeline test ({'quick' if args.quick else 'full'})\n")
    run(args.quick)

    res = pd.DataFrame(RESULTS, columns=["group", "check", "status", "detail"])
    counts = res["status"].value_counts().reindex(["PASS", "WARN", "SKIP", "FAIL"], fill_value=0)
    print("\n" + "  ".join(f"{k}: {v}" for k, v in counts.items()))
    lines = ["# Sharko Australia: pipeline test report", "",
             f"Run {pd.Timestamp.now():%Y-%m-%d %H:%M} ({'quick' if args.quick else 'full'}). "
             + ", ".join(f"{k} {v}" for k, v in counts.items()), "",
             "| group | check | result | detail |", "|---|---|---|---|"]
    lines += [f"| {r.group} | {r.check} | {r.status} | {r.detail} |" for r in res.itertuples()]
    path = os.path.join(BASE_DIR, "models", "pipeline_test_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Report -> {path}")
    sys.exit(1 if counts["FAIL"] else 0)
