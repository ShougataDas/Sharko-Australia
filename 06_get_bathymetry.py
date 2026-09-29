"""Step 6: download seafloor depth (ETOPO, 1 arc-minute) and compute distance to coast.

No account needed (NOAA ERDDAP). Depth and distance to shore are two of the
strongest predictors of where each shark species lives.
Output: data/ocean/bathymetry.nc with variables `depth_m` (positive down, NaN on
land) and `dist_coast_km`.
"""
import os
import numpy as np
import requests
import xarray as xr
from scipy.ndimage import distance_transform_edt
from config import LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, OCEAN_DIR

url = ("https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.nc"
       f"?altitude%5B({LAT_MIN}):1:({LAT_MAX})%5D%5B({LON_MIN}):1:({LON_MAX})%5D")
raw_path = os.path.join(OCEAN_DIR, "etopo_raw.nc")
print("Downloading ETOPO bathymetry...")
with requests.get(url, stream=True, timeout=600) as r:
    r.raise_for_status()
    with open(raw_path, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)

with xr.open_dataset(raw_path) as src:   # load and release the file (Windows locks it)
    ds = src.load().rename({"latitude": "lat", "longitude": "lon"})
alt = ds["altitude"].astype("float32")
land = (alt >= 0).values

# Distance (km) from each ocean cell to the nearest land cell.
# 1 arc-minute = 1.852 km north-south; east-west shrinks with cos(latitude).
dy = 1.852
dx = 1.852 * np.cos(np.deg2rad((LAT_MIN + LAT_MAX) / 2))
dist = distance_transform_edt(~land, sampling=(dy, dx)).astype("float32")

out = xr.Dataset({
    "depth_m": (-alt).where(~land),
    "dist_coast_km": (("lat", "lon"), np.where(land, np.nan, dist)),
})
out_path = os.path.join(OCEAN_DIR, "bathymetry.nc")
out.to_netcdf(out_path)
os.remove(raw_path)
print(f"Saved {out.sizes['lat']} x {out.sizes['lon']} grid -> {out_path}")
