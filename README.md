# Sharko Australia

Predicts shark habitat around Australia (tiger, bull, white and all sharks) from
satellite ocean data and 2020–2026 shark records.

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

All scripts can be re-run safely.
Typical run times: OBIS ~1 min, GBIF ~15–20 min (slow API), QLD ~1 min, merge seconds,
bathymetry ~1 min, ocean data depends on size (run `--dry-run` first).

## What's in this repo

| Folder | Contents |
|---|---|
| `data/` | shark records (raw + merged), model dataset, dataset report |
| `data/ocean/` | `bathymetry.nc` only; the daily ocean files (~20 GB) are not included - recreate them with `05_get_ocean_data.py` |
| `models/` | trained models (`*_model.joblib`), comparison (`report.md`, `metrics.csv`), tests (`test_report.md`), plots |
| `maps/` | example habitat maps for 15 Jan 2026 |

The trained models and `data/model_dataset.csv.gz` work without the ocean files; only
`07_build_dataset.py`, `10_predict_map.py` and the new-records test need them.

## Model results

Spatial AUC = tested on 2x2° regions the model never saw (0.5 random, 0.8 good, 0.9 excellent).

| Model | Best algorithm | Spatial AUC | Top drivers |
|---|---|---|---|
| Bull shark | LightGBM | 0.93 | depth, sea temperature, distance to coast |
| All sharks | Random forest | 0.90 | distance to coast, depth, sea level |
| Tiger shark | LightGBM | 0.89 | depth, distance to coast, sea level, temperature |
| White shark | LightGBM | 0.81 | sea level, depth, temperature |

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
