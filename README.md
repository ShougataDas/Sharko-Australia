# Sharko Australia: data pipeline

Downloads fresh (2020 to today) shark records and ocean conditions for Australian waters
(lon 110–160°E, lat 46–9°S). Settings live in `config.py`.

## Run order

```bash
pip install -r requirements.txt
python 01_get_sharks_obis.py        # OBIS: IMOS acoustic tracking, iNaturalist, BRUVS...   no account
python 02_get_sharks_gbif.py        # GBIF / Atlas of Living Australia                       no account
python 03_get_qld_shark_control.py  # Queensland Shark Control Program catches + gear         no account
python 04_merge_sharks.py           # -> data/sharks_australia.csv (cleaned, de-duplicated)
python 06_get_bathymetry.py         # depth + distance to coast (NOAA ETOPO)                  no account
copernicusmarine login              # free account: https://data.marine.copernicus.eu/register
python 05_get_ocean_data.py --dry-run   # check download size first
python 05_get_ocean_data.py             # SST, sea level + currents, chlorophyll (daily)
python 07_build_dataset.py              # -> data/model_dataset.csv.gz (model-ready, ~4 min)
python 08_check_dataset.py              # stats + sanity checks -> data/dataset_report.txt
python 09_train_models.py               # tiger, bull, white: GLM vs RandomForest vs tuned LightGBM (~5 min each)
python 09_train_models.py --species any # all-sharks model
python 10_predict_map.py --date 2026-01-15   # habitat maps -> maps/
python 11_test_models.py                # integrity, biology and unseen-region tests -> models/test_report.md
```

All scripts can be re-run safely; the data lands in `data/` (ignored by git).
Typical run times: OBIS ~1 min, GBIF ~15–20 min (slow API), QLD ~1 min, merge seconds,
bathymetry ~1 min, ocean data depends on size (run `--dry-run` first).

## Data sources

| Data | Source | Resolution |
|---|---|---|
| Shark sightings, tags, surveys | OBIS (api.obis.org), GBIF (api.gbif.org) | points |
| Shark catches at beaches | data.qld.gov.au – Shark Control Program | points (beach) |
| Sea surface temperature | Copernicus Marine – OSTIA L4 | daily, 0.05° |
| Sea level anomaly, currents | Copernicus Marine – DUACS L4 | daily, 0.125° |
| Chlorophyll-a | Copernicus Marine – GlobColour gap-free L4 | daily, 4 km |
| Depth, distance to coast | NOAA ETOPO 1 arc-minute (ERDDAP) | 1.8 km |

Please cite OBIS, GBIF, Queensland Government, Copernicus Marine Service and NOAA
in your presentation.
