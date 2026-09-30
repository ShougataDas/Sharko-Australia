# 🦈 Sharko: predicting shark presence around Australia

**Live site:** https://sharko-omega.vercel.app/  

Sharko predicts **how likely a shark is at any position around Australia on any date**, past,
next week or years ahead. It learns from 29,000+ real shark sightings (2020-2026) and daily
satellite measurements of the ocean (temperature, plankton, sea height, currents), then shows
the predicted hotspots on an interactive map.


---

## How it fits together

```
 ┌──────────────────────── ml/ (Python) ────────────────────────┐
 │ OBIS, GBIF, QLD Shark Control  ─┐                            │
 │ Copernicus satellites (daily) ──┼─> dataset -> models ─┐     │
 │ NOAA seafloor depth ────────────┘                      │     │
 │ climatology (typical ocean) + Copernicus forecast ─────┴─> predictor.py
 └──────────────────────────────────────────────────────────────┘
                                   │  predict(lat, lon, date)
                     ┌─────────────▼─────────────┐
                     │  api/  FastAPI            │  Hugging Face Space
                     │  /predict/presence        │
                     │  /predict/habitat         │
                     │  /predict/location        │
                     └─────────────┬─────────────┘
                                   │  GeoJSON / JSON
                     ┌─────────────▼─────────────┐
                     │  frontend/  React + Vite  │  Vercel
                     │  story, map, AI assistant │
                     └───────────────────────────┘
```

## Repository structure

| Folder | What it is | Details |
|---|---|---|
| [`ml/`](ml/) | Data download, dataset building, model training, testing and the `predictor.py` used by the API | [ml/README.md](ml/README.md) |
| [`ml/data/`](ml/data/) | Shark records, model datasets, ocean climatology, latest forecast, seafloor depth | |
| [`ml/models/`](ml/models/) | Trained models (daily + long-range `seasonal/`), reports, plots, test results | |
| [`api/`](api/) | FastAPI backend deployed as a Hugging Face Space | [api/README.md](api/README.md) |
| [`frontend/`](frontend/) | React + TypeScript website deployed on Vercel | [frontend/README.md](frontend/README.md) |

## What the model uses and returns

**Input:** a position (latitude, longitude) and a date.

The model looks at 10 conditions at that place and day:

| Condition | Source |
|---|---|
| Sea temperature, temperature fronts | satellite (OSTIA) |
| Chlorophyll (plankton, start of the food chain) | satellite (GlobColour) |
| Sea level anomaly, sea height, current speed | satellite altimetry (DUACS) |
| Depth, distance to coast | NOAA ETOPO seafloor map |
| Season | the date |

**Output:** for each species (tiger, bull, great white, any shark) a **presence likelihood from
0 to 1**, a yes/no "likely habitat", and for long-range dates a range (cooler vs warmer year).
The API turns the whole-Australia grid into GeoJSON polygons for the map.

### Future dates

Nobody has measured a future ocean, so the conditions are estimated differently depending on
how far ahead the date is:

| Mode | When | Ocean conditions from |
|---|---|---|
| observed | past dates | real satellite measurements of that day |
| forecast | next ~9 days | Copernicus ocean forecast, bias-corrected to satellite |
| outlook | up to 3 months after the last known day | typical conditions + today's unusual conditions, fading with time |
| typical | further ahead (e.g. 2030) | typical conditions for that place and week (2020-2026 average) |

Each species is only predicted within 500 km of where it has actually been recorded.

## Results

**Tested on regions the model never saw** (spatial cross-validation, AUC: 0.5 = random, 1 = perfect):

| Model | Daily | Long-range (seasonal) |
|---|---|---|
| Bull shark | 0.93 | 0.94 |
| All sharks | 0.90 | 0.90 |
| Tiger shark | 0.89 | 0.88 |
| Great white shark | 0.81 | 0.82 |

**Predicting the future** (trained on 2020-2024 only, predicting the real 2025-2026 sightings
with typical conditions, as the app does for far-future dates):

| Model | AUC | Real sightings caught |
|---|---|---|
| Tiger | 0.98 | 99% |
| Bull | 0.98 | 100% |
| Great white | 0.93 | 91% |
| All sharks | 0.95 | 95% |

The future test uses sightings at places already seen in training, so the spatial numbers
above are the more cautious measure. Full reports:
[model comparison](ml/models/report.md) ·
[backtest](ml/models/backtest_report.md) ·
[model tests](ml/models/test_report.md) ·
[pipeline tests (28/28 pass)](ml/models/pipeline_test_report.md)

## Quick start

**Ask the model directly (Python):**
```bash
cd ml
pip install -r requirements.txt
python predictor.py -33.9 151.3 2030-01-15
```

**Run the API locally** (uses the models in `ml/`):
```bash
cd api
pip install -r requirements.txt
uvicorn app:app --port 8000
```
Then open http://localhost:8000/predict/location?lat=-33.9&lon=151.3&date=2030-01-15

**Run the website locally:**
```bash
cd frontend
npm install
cp .env.example .env      # add your Mapbox public token
npm run dev
```

**Rebuild everything from scratch:** follow the numbered scripts in [ml/README.md](ml/README.md)
(downloads ~20 GB of satellite data; a free Copernicus Marine account is needed).

## Data sources

| Data | Source |
|---|---|
| Shark sightings, tagging, camera surveys | [OBIS](https://obis.org), [GBIF / Atlas of Living Australia](https://www.gbif.org) |
| Shark catches at beaches | [Queensland Shark Control Program](https://www.data.qld.gov.au) |
| Sea temperature, sea level, currents, chlorophyll, forecasts | [Copernicus Marine Service](https://marine.copernicus.eu) |
| Seafloor depth | [NOAA ETOPO](https://www.ncei.noaa.gov/products/etopo-global-relief-model) |

## Limitations

- 86% of sightings come from the east coast, where most divers, tags and drumlines are, so
  predictions for Western Australia and the north are less certain.
- More than ~10 days ahead, nobody can predict eddies or storms: long-range answers describe
  where sharks *usually* are at that time of year.
- The score is how well the conditions match where the species is usually found, not a
  guarantee that a shark is there.

## Not in this repository

- The daily satellite archive (~20 GB) - recreate with `ml/05_get_ocean_data.py`.
- `api/au/` - a copy of the ML files for deployment, made with `api/prepare_deploy.py`.
- Secrets (`.env` files): see each folder's `.env.example`.
