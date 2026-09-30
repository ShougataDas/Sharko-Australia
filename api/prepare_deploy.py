"""Copy the files the API needs from ../ml into api/au/ before deploying.

The Hugging Face Space only receives the api/ folder, so it cannot see ../ml.
This copies the predictor code, the trained models and the small data files
(~250 MB) into api/au/, which au_predict.py uses automatically when present.

Usage (from the api/ folder):
    python prepare_deploy.py
Then push api/ (including au/) to the Space. api/au/ is ignored by the GitHub repo.
"""
import glob
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.join(os.path.dirname(HERE), "ml")
DEST = os.path.join(HERE, "au")

FILES = [
    "config.py", "features.py", "climatology.py", "predictor.py",
    "data/sharks_australia.csv",                 # known-range check
    "data/ocean/bathymetry.nc",                  # depth + distance to coast
    "data/climatology/clim_all.nc",              # typical conditions (future dates)
    "data/forecast/forecast.nc",                 # next ~9 days (refresh with ml/15_get_forecast.py)
    "data/forecast/bias.nc",
]
FILES += [os.path.relpath(p, ML) for p in glob.glob(os.path.join(ML, "models", "*_model.joblib"))]
FILES += [os.path.relpath(p, ML) for p in glob.glob(os.path.join(ML, "models", "seasonal", "*_model.joblib"))]

total = 0
for rel in FILES:
    src, dst = os.path.join(ML, rel), os.path.join(DEST, rel)
    if not os.path.exists(src):
        raise SystemExit(f"Missing {src} - build it with the ml/ pipeline first")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    total += os.path.getsize(dst)
    print(f"  {rel}")
print(f"Copied {len(FILES)} files ({total / 1e6:.0f} MB) -> {DEST}")
