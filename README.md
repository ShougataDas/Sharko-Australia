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
# --- future-date prediction ---
python 12_build_climatology.py          # typical conditions per place + week -> data/climatology/ (~8 min)
python 13_build_seasonal_dataset.py     # training data on typical conditions
python 09_train_models.py --mode seasonal --species tiger bull white any   # long-range models -> models/seasonal/
python 14_backtest_future.py            # honest future test: train to 2024, predict 2025-26 -> models/backtest_report.md
python 15_get_forecast.py               # Copernicus ocean forecast, next ~9 days (run daily)
python 16_test_pipeline.py              # end-to-end test of everything -> models/pipeline_test_report.md
python predictor.py -33.9 151.3 2030-01-15   # shark presence likelihood for any position + date
```

All scripts can be re-run safely.
Typical run times: OBIS ~1 min, GBIF ~15–20 min (slow API), QLD ~1 min, merge seconds,
bathymetry ~1 min, ocean data depends on size (run `--dry-run` first).

## Predicting a future date

`predictor.py` answers "how likely is a shark at this position on this date?" for any date.
The 10 model inputs are built according to how far ahead the date is:

| Mode | When | Ocean inputs from | Model |
|---|---|---|---|
| observed | past date, archive on disk | real satellite data of that day | daily |
| forecast | next ~9 days | Copernicus ocean forecast, bias-corrected to satellite | daily |
| outlook | up to 90 days after the last known day | typical conditions + today's unusual part, fading with time | seasonal |
| typical | further ahead (e.g. 2030) | typical conditions for that place and week (2020-2026) | seasonal |

Depth, distance to coast and season are always known exactly. Long-range answers include a
range (cooler / warmer year). Each species is only predicted within 500 km of where it has
been recorded (2020-2026).

```python
from predictor import SharkoPredictor
p = SharkoPredictor()
p.predict_point(-33.9, 151.3, "2030-01-15")   # JSON-ready dict per species
p.predict_grid("2030-01-15")                  # whole-Australia map (0.1 deg)
```

## What's in this repo

| Folder | Contents |
|---|---|
| `data/` | shark records (raw + merged), model dataset, dataset report |
| `data/climatology/` | typical conditions (`clim_all.nc`) and the 2020-2024 version for the backtest |
| `data/forecast/` | latest bias-corrected ocean forecast (`forecast.nc`) and its correction (`bias.nc`) |
| `data/ocean/` | `bathymetry.nc` only; the daily ocean files (~20 GB) are not included - recreate them with `05_get_ocean_data.py` |
| `models/` | daily models (`*_model.joblib`), long-range models (`seasonal/`), comparison (`report.md`, `metrics.csv`), tests (`test_report.md`), plots |
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
