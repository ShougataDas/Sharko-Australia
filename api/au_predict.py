"""Adapter between the Australia predictor (au/predictor.py) and the existing API response
shapes in app.py. Keeps /predict/presence, /predict/habitat and /predict/location returning
exactly the same JSON structure the frontend already consumes.
"""
import os
import sys

import geojson
import numpy as np
from shapely.geometry import MultiPoint
from sklearn.cluster import DBSCAN

_HERE = os.path.dirname(os.path.abspath(__file__))


def _find_ml_dir():
    """Where the Australia predictor, models and data live.

    1. SHARKO_ML_DIR environment variable, if set
    2. api/au/  - deployment copy made by prepare_deploy.py (Hugging Face Space)
    3. ../ml/   - the ML folder of the GitHub repo (local development)
    """
    candidates = [os.environ.get("SHARKO_ML_DIR"), os.path.join(_HERE, "au"),
                  os.path.join(os.path.dirname(_HERE), "ml")]
    for path in candidates:
        if path and os.path.exists(os.path.join(path, "predictor.py")):
            return path
    raise FileNotFoundError("Sharko ML folder not found: set SHARKO_ML_DIR or run prepare_deploy.py")


AU_DIR = _find_ml_dir()
if AU_DIR not in sys.path:
    sys.path.insert(0, AU_DIR)

from predictor import SharkoPredictor  # noqa: E402

# shark_name (as sent by the frontend / listed in sharks.json) -> AU model short name.
# Only species with a real trained Australia model are listed here.
SPECIES_MAP = {
    "tiger shark": "tiger",
    "bull shark": "bull",
    "great white shark": "white",
}

# DBSCAN runs on the predictor's regular 0.1-degree grid (~11 km spacing), not sparse
# random points, so epsilon must be just over that spacing (diagonal neighbours are
# ~0.14 degrees apart) rather than the old value tuned for sparse global sampling.
CLUSTER_EPS_DEG = 0.15
CLUSTER_MIN_SAMPLES = 4

_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = SharkoPredictor(base_dir=AU_DIR)
    return _predictor


def _threshold_for(predictor, short_name, mode_kind):
    models = predictor.daily if mode_kind == "daily" else predictor.seasonal
    return models[short_name]["threshold"]


def _cluster_to_geojson(points_lonlat, epsilon=CLUSTER_EPS_DEG, min_samples=CLUSTER_MIN_SAMPLES):
    """DBSCAN + convex hull per cluster, same feature shape as the legacy clustering step."""
    if len(points_lonlat) == 0:
        return None

    labels = DBSCAN(eps=epsilon, min_samples=min_samples).fit(points_lonlat).labels_
    unique_labels = set(labels)
    unique_labels.discard(-1)

    features = []
    for label in unique_labels:
        cluster_points = points_lonlat[labels == label]
        if len(cluster_points) < 3:
            continue
        hull = MultiPoint(cluster_points).convex_hull
        features.append(geojson.Feature(geometry=hull, properties={"cluster_id": int(label)}))

    if not features:
        return None
    return geojson.FeatureCollection(features)


def predict_presence_geojson(date):
    """Generic ('any species') presence zones across Australian waters."""
    predictor = get_predictor()
    df = predictor.predict_grid(date, species=["any"])
    threshold = _threshold_for(predictor, "any", df.attrs["model_kind"])
    hot = df.loc[df["any"] >= threshold, ["lon", "lat"]].to_numpy()
    return _cluster_to_geojson(hot)


def predict_habitat_geojson(date, shark_name):
    """Species-specific habitat zones. Returns None if the species has no trained AU model."""
    short_name = SPECIES_MAP.get((shark_name or "").strip().lower())
    if short_name is None:
        return None
    predictor = get_predictor()
    df = predictor.predict_grid(date, species=[short_name])
    threshold = _threshold_for(predictor, short_name, df.attrs["model_kind"])
    hot = df.loc[df[short_name] >= threshold, ["lon", "lat"]].to_numpy()
    return _cluster_to_geojson(hot)


def predict_location(lat, lon, date):
    """Single-point prediction, reshaped into the legacy /predict/location response shape.

    Returns (payload, error). error is set (payload is None) when the point is on land,
    has no ocean data, or falls outside the Australia study area (110-160E / 9-46S).
    """
    predictor = get_predictor()
    result = predictor.predict_point(lat, lon, date, species=["any"])
    if "error" in result:
        return None, result["error"]

    any_shark = result["sharks"]["Any shark"]
    oc = result["ocean_conditions"]
    payload = {
        "coordinates": {"lat": lat, "lon": lon},
        "date": result["date"],
        "predictions": {
            "shark_presence": any_shark["presence_likelihood"],
            "sst": oc["sea_temperature_c"],
            "ssh": oc["sea_level_anomaly_m"],
            "chla": oc["chlorophyll_mg_m3"],
        },
    }
    return payload, None
