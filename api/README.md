---
title: Sharko Api
emoji: 📈
colorFrom: gray
colorTo: pink
sdk: docker
pinned: false
short_description: Project Sharko with ML models
---

# Sharko API

FastAPI backend for [Sharko](https://sharko-omega.vercel.app/). Serves shark presence and
habitat predictions for Australian waters (110-160°E, 9-46°S) using the models in
[`../ml`](../ml).

**Live:** https://midul914-sharko-api.hf.space/ (Hugging Face Space, Docker)

(The block at the top of this file is the Hugging Face Space configuration.)

## Endpoints

| Endpoint | Returns |
|---|---|
| `GET /` | status |
| `GET /predict/location?lat=&lon=&date=` | presence likelihood (all sharks) + ocean conditions for one position |
| `GET /predict/presence?date=` | GeoJSON polygons of likely shark areas (all species) |
| `GET /predict/habitat?date=&shark_name=` | GeoJSON polygons for one species: `Tiger Shark`, `Bull Shark`, `Great White Shark` |
| `GET /health` | legacy global models status |

`date` is `YYYY-MM-DD` and can be in the past or future. The predictor picks the data source
automatically (satellite for past days, the Copernicus forecast for the next ~9 days,
typical conditions for later dates). See the [main README](../README.md#future-dates).

### Examples

```
GET /predict/location?lat=-33.9&lon=151.3&date=2030-01-15
```
```json
{"coordinates": {"lat": -33.9, "lon": 151.3}, "date": "2030-01-15",
 "predictions": {"shark_presence": 0.867, "sst": 23.0, "ssh": 0.017, "chla": 0.21}}
```
`shark_presence` is 0-1, `sst` in °C, `ssh` sea level anomaly in m, `chla` chlorophyll in mg/m³.
A position on land or outside the study area returns HTTP 400 with an explanation.

```
GET /predict/habitat?date=2030-07-15&shark_name=Great%20White%20Shark
```
```json
{"success": true, "habitat_geojson_data": {"type": "FeatureCollection",
  "features": [{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [...]},
                "properties": {"cluster_id": 0}}, ...]}}
```
Species without an Australia model return `"success": false`.

## How it works

- `app.py` - the FastAPI app and routes.
- `au_predict.py` - connects the routes to `SharkoPredictor` (`ml/predictor.py`). It predicts on
  the 0.1° grid, keeps cells above each model's habitat threshold, groups them with DBSCAN
  and returns each group's outline as a GeoJSON polygon.
- The predictor (climatology, forecast, models) is loaded once at startup (~25 s).
- `index.py`, `models/`, `prediction_points.parquet`, `initial_zone_1_epsilon.geojson`,
  `sharks.json` - the earlier global prototype, still used by `/health`.

`au_predict.py` looks for the ML files in this order: the `SHARKO_ML_DIR` environment variable,
`api/au/` (deployment copy), then `../ml/` (this repository).

## Run locally

```bash
cd api
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```
Interactive docs: http://localhost:8000/docs

## Deploy to the Hugging Face Space

The Space only receives this folder, so copy the ML files in first:

```bash
python prepare_deploy.py      # copies predictor code, models and data (~250 MB) into api/au/
```
Then push the `api/` folder (with `au/`) to the Space repository. Large files (`*.joblib`,
`*.nc`) go through Git LFS on Hugging Face. `api/au/` is ignored in this GitHub repository.

To keep the 9-day forecast fresh, run `ml/15_get_forecast.py` regularly and redeploy
`data/forecast/`.

## Configuration

`.env` (not committed, see `.env.example`): `GOOGLE_API_KEY`, reserved for the AI assistant
and not needed by the prediction endpoints.
