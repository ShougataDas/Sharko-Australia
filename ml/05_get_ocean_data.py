"""Step 5: download daily ocean conditions for Australia from Copernicus Marine.

Needs a free Copernicus Marine account. Log in once with:
    copernicusmarine login

Variables (all daily, gap-filled):
  sst  - sea surface temperature, OSTIA 0.05 deg        (Kelvin -> convert to C later)
  ssh  - sea level anomaly + geostrophic currents, 0.125 deg (eddies and fronts)
  chl  - chlorophyll-a, GlobColour gap-free 4 km          (food web / productivity)

Each variable uses the "MY" (reprocessed, best quality) dataset for older dates and
the "NRT" (near real time, a few days old) dataset for the latest months.
One NetCDF file per variable per year -> data/ocean/<var>_<year>.nc

Usage:
    python 05_get_ocean_data.py --dry-run          # show download sizes only
    python 05_get_ocean_data.py                    # download everything
    python 05_get_ocean_data.py --vars sst --years 2025 2026
"""
import argparse
import os
from datetime import date
import copernicusmarine as cm
from config import LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, START_DATE, OCEAN_DIR

SOURCES = {
    "sst": {"variables": ["analysed_sst"],
            "datasets": ["METOFFICE-GLO-SST-L4-REP-OBS-SST", "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2"]},
    "ssh": {"variables": ["sla", "adt", "ugos", "vgos"],
            "datasets": ["cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D",
                         "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"]},
    "chl": {"variables": ["CHL"],
            "datasets": ["cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D",
                         "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D"]},
}

ap = argparse.ArgumentParser()
ap.add_argument("--vars", nargs="+", default=list(SOURCES), choices=list(SOURCES))
ap.add_argument("--years", nargs="+", type=int,
                default=list(range(int(START_DATE[:4]), date.today().year + 1)))
ap.add_argument("--dry-run", action="store_true", help="only print estimated sizes")
args = ap.parse_args()

if not cm.login(check_credentials_valid=True):
    raise SystemExit("Not logged in. Create a free account at "
                     "https://data.marine.copernicus.eu/register then run:  copernicusmarine login")

total_mb = 0.0
for var in args.vars:
    src = SOURCES[var]
    for year in args.years:
        # The MY dataset covers older years; the NRT dataset fills in the most recent months.
        for kind, dataset_id in zip(("my", "nrt"), src["datasets"]):
            fname = f"{var}_{year}_{kind}.nc"
            if os.path.exists(os.path.join(OCEAN_DIR, fname)):
                print(f"exists, skipping: {fname}")
                continue
            try:
                res = cm.subset(
                    dataset_id=dataset_id,
                    variables=src["variables"],
                    minimum_longitude=LON_MIN, maximum_longitude=LON_MAX,
                    minimum_latitude=LAT_MIN, maximum_latitude=LAT_MAX,
                    start_datetime=f"{year}-01-01T00:00:00",
                    end_datetime=f"{year}-12-31T23:59:59",
                    coordinates_selection_method="inside",   # clip to what the dataset has
                    output_directory=OCEAN_DIR,
                    output_filename=fname,
                    dry_run=args.dry_run,
                    disable_progress_bar=args.dry_run,
                )
                size = res.file_size or 0
                total_mb += size
                print(f"{'would download' if args.dry_run else 'downloaded'} {fname}: "
                      f"{size:,.0f} MB")
            except Exception as e:
                # Normal when e.g. the NRT dataset has no data for an older year
                print(f"no data for {fname}: {str(e).splitlines()[0][:150] if str(e) else type(e).__name__}")

print(f"\nTotal: {total_mb / 1024:,.1f} GB")
