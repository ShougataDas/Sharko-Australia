"""Step 13: training data for the long-range ("seasonal") models.

Same sightings and background points as data/model_dataset.csv.gz, but the six
changing ocean inputs are replaced by the TYPICAL conditions for that place and
week of the year (from 12_build_climatology.py). A model trained on this learns
"sharks come to this coast at this time of year" - exactly the information that is
still available for a date months or years in the future.

Depth, distance to coast and season are unchanged (they are known for any date).
Output: data/model_dataset_seasonal.csv.gz
Then train with:  python 09_train_models.py --mode seasonal
"""
import os
import pandas as pd
from climatology import Climatology
from config import DATA_DIR
from features import FEATURES, OCEAN_FEATURES

clim = Climatology(os.path.join(DATA_DIR, "climatology", "clim_all.nc"))
data = pd.read_csv(os.path.join(DATA_DIR, "model_dataset.csv.gz"), parse_dates=["date"], low_memory=False)
print(f"{len(data):,} rows; climatology years {clim.years}")

typical = clim.sample(data["lat"], data["lon"], data["date"])
seasonal = data.copy()
seasonal[OCEAN_FEATURES] = typical[OCEAN_FEATURES].values

missing = seasonal[FEATURES].isna().any(axis=1)
print(f"Dropping {missing.sum()} rows with no nearby climatology cell")
seasonal = seasonal[~missing].reset_index(drop=True)

out = os.path.join(DATA_DIR, "model_dataset_seasonal.csv.gz")
seasonal.to_csv(out, index=False, compression="gzip")
print(f"Saved {len(seasonal):,} rows -> {out}")

print("\nReal daily vs typical conditions at the same points (mean | std):")
both = data.loc[~missing]
for f in OCEAN_FEATURES:
    print(f"  {f:<11} daily {both[f].mean():8.3f} | {both[f].std():6.3f}    "
          f"typical {seasonal[f].mean():8.3f} | {seasonal[f].std():6.3f}")
