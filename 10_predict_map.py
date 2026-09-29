"""Step 10: map predicted shark habitat around Australia for any date.

Uses the real ocean conditions of that day (same features as training, via
features.py) and the models saved by 09_train_models.py.

Output (maps/):
  <species>_<date>.png   suitability map, with that species' real sightings from
                         +-15 days drawn on top (a visual check of the model)
  <species>_<date>.nc    the suitability grid, for use in other tools / web apps

Usage:
  python 10_predict_map.py                                  # tiger, bull, white; latest day
  python 10_predict_map.py --date 2026-01-15
  python 10_predict_map.py --species white any --date 2025-07-01
  python 10_predict_map.py --res 0.05                        # sharper map (slower)
"""
import argparse
import glob
import os
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from config import BASE_DIR, DATA_DIR, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
from features import FEATURES, add_ocean_features, available_days, load_bathymetry

MODEL_DIR = os.path.join(BASE_DIR, "models")
MAP_DIR = os.path.join(BASE_DIR, "maps")
os.makedirs(MAP_DIR, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--species", nargs="+", default=["tiger", "bull", "white"],
                help="model short names, i.e. models/<name>_model.joblib")
ap.add_argument("--date", help="YYYY-MM-DD (default: latest day with ocean data)")
ap.add_argument("--res", type=float, default=0.1, help="map resolution in degrees")
args = ap.parse_args()

days = available_days("chl")      # chlorophyll is usually the last variable to arrive
date = pd.Timestamp(args.date) if args.date else days[-1]
if date not in set(days):
    raise SystemExit(f"No ocean data for {date:%Y-%m-%d}. Available: {days[0]:%Y-%m-%d} to "
                     f"{days[-1]:%Y-%m-%d}. Run 05_get_ocean_data.py to update.")

models = {}
for name in args.species:
    path = os.path.join(MODEL_DIR, f"{name}_model.joblib")
    if not os.path.exists(path):
        found = [os.path.basename(p).replace("_model.joblib", "")
                 for p in glob.glob(os.path.join(MODEL_DIR, "*_model.joblib"))]
        raise SystemExit(f"No model '{name}'. Available: {', '.join(found)}. Train with 09_train_models.py")
    models[name] = joblib.load(path)

# --- Grid of ocean cells -----------------------------------------------------
lats = np.arange(LAT_MIN + args.res / 2, LAT_MAX, args.res)
lons = np.arange(LON_MIN + args.res / 2, LON_MAX, args.res)
glon, glat = np.meshgrid(lons, lats)
bathy = load_bathymetry()
depth_on_grid = bathy["depth_m"].sel(lat=xr.DataArray(glat.ravel()), lon=xr.DataArray(glon.ravel()),
                                     method="nearest").values
ocean = np.isfinite(depth_on_grid)
cells = pd.DataFrame({"date": date, "lat": glat.ravel()[ocean], "lon": glon.ravel()[ocean]})
print(f"Computing ocean conditions for {date:%Y-%m-%d} on {len(cells):,} ocean cells...")
cells = add_ocean_features(cells, bathy, verbose=False)
valid = cells[FEATURES].notna().all(axis=1)

sightings = pd.read_csv(os.path.join(DATA_DIR, "sharks_australia.csv"), parse_dates=["date"])
near = sightings[(sightings["date"] - date).abs() <= pd.Timedelta(days=15)]

# --- Predict + plot ----------------------------------------------------------
n = len(models)
fig, axes = plt.subplots(1, n, figsize=(6.2 * n, 5.4), squeeze=False)
for ax, (name, b) in zip(axes[0], models.items()):
    p = np.full(len(cells), np.nan)
    p[valid.values] = b["model"].predict_proba(cells.loc[valid, b["features"]])[:, 1]
    grid = np.full(glat.size, np.nan)
    grid[ocean] = p
    grid = grid.reshape(glat.shape)

    xr.Dataset({"suitability": (("lat", "lon"), grid.astype("float32"))},
               coords={"lat": lats, "lon": lons},
               attrs={"species": b["title"], "date": f"{date:%Y-%m-%d}", "model": b["model_name"],
                      "threshold": b["threshold"]}
               ).to_netcdf(os.path.join(MAP_DIR, f"{name}_{date:%Y-%m-%d}.nc"))

    ax.set_facecolor("#d9d4c7")   # land
    im = ax.pcolormesh(lons, lats, grid, cmap="magma", vmin=0, vmax=1, shading="auto")
    ax.contour(lons, lats, np.nan_to_num(grid), levels=[b["threshold"]], colors="cyan", linewidths=0.6)
    sp = near if b["species"] == "ANY" else near[near["species"] == b["species"]]
    ax.scatter(sp["lon"], sp["lat"], s=6, c="#00e5ff", edgecolors="k", linewidths=0.3,
               label=f"real sightings ±15 days ({len(sp)})")
    m = b["metrics"]
    ax.set(xlim=(LON_MIN, LON_MAX), ylim=(LAT_MIN, LAT_MAX), aspect=1.15,
           title=f"{b['title']}\n{date:%d %b %Y} · {b['model_name']} · "
                 f"spatial AUC {m['spatial_auc']:.2f}")
    ax.legend(loc="lower left", fontsize=7)
    fig.colorbar(im, ax=ax, shrink=0.8, label="habitat suitability")
    hot = np.nanmean(grid >= b["threshold"]) * 100
    print(f"  {b['title']}: {hot:.1f}% of ocean cells above the habitat threshold "
          f"({b['threshold']:.2f}); {len(sp)} real sightings within ±15 days")

fig.suptitle("Sharko: predicted shark habitat (cyan line = likely-habitat threshold)", fontsize=11)
fig.tight_layout()
out = os.path.join(MAP_DIR, f"{'_'.join(models)}_{date:%Y-%m-%d}.png")
fig.savefig(out, dpi=150)
print(f"Saved map -> {out}")
