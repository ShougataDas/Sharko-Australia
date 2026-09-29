"""Step 11: test the trained models (run after 09_train_models.py).

Test groups
  1. Integrity    (FAIL if broken)  model file loads, uses the right features in the
                                    right order, outputs probabilities in [0, 1], gives
                                    the same answer twice, is not constant
  2. Biology      (WARN if wrong)   does the model behave like the real animal?
                                    e.g. deep open ocean scores lower than the shelf,
                                    white sharks prefer cool water, tiger/bull warm water
  3. New regions  (WARN if weak)    the model is re-trained without one whole region of
                                    Australia (West / North / South / East) and tested on
                                    it: can it predict a coastline it has never seen?
  4. New records  (info)            sightings dated after the model's training data
                                    (appear after you re-download data with steps 1-4)

Exit code is 1 if any integrity test fails, so this can be used as an automated check.

Usage:
  python 11_test_models.py                    # test every model in models/
  python 11_test_models.py --species white    # test one model
Report: models/test_report.md
"""
import argparse
import glob
import os
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from config import BASE_DIR, DATA_DIR
from features import FEATURES, add_ocean_features

warnings.filterwarnings("ignore")
MODEL_DIR = os.path.join(BASE_DIR, "models")
SEED = 42
MIN_REGION_PRESENCES = 30
GOOD_AUC = 0.70

# Regions of Australia by longitude / latitude
REGIONS = {
    "West (WA)": lambda d: d["lon"] < 129,
    "North (NT, Gulf, Torres Strait)": lambda d: (d["lon"] >= 129) & (d["lat"] > -20),
    "South (SA, Vic, Tas, Bass Strait)": lambda d: (d["lon"] >= 129) & (d["lat"] <= -20) & (d["lon"] < 145),
    "East (Qld, NSW)": lambda d: (d["lon"] >= 145) & (d["lat"] <= -20),
}

# What we know about each species' biology: (feature, higher value, lower value, description)
# The model should give higher suitability at the first value than the second.
BIOLOGY = {
    "Galeocerdo cuvier": [("sst_c", 27, 15, "tiger sharks prefer warm (27°C) over cold (15°C) water")],
    "Carcharhinus leucas": [("sst_c", 27, 15, "bull sharks prefer warm (27°C) over cold (15°C) water")],
    "Carcharodon carcharias": [("sst_c", 18, 29, "white sharks prefer cool (18°C) over tropical (29°C) water")],
    "Rhincodon typus": [("sst_c", 28, 16, "whale sharks prefer warm (28°C) over cold (16°C) water")],
    "Heterodontus portusjacksoni": [("sst_c", 18, 29, "Port Jackson sharks prefer cool (18°C) water")],
}

results = []


def record(model, group, test, status, detail):
    results.append({"model": model, "group": group, "test": test, "status": status, "detail": detail})
    icon = {"PASS": "ok  ", "FAIL": "FAIL", "WARN": "warn", "INFO": "info"}[status]
    print(f"  [{icon}] {group}: {test} - {detail}")


def species_rows(data, species):
    pres = data[data["presence"] == 1]
    return pres if species == "ANY" else pres[pres["species"] == species]


# ---------------------------------------------------------------------------
def test_integrity(name, b, data):
    g = "integrity"
    missing = [k for k in ("model", "features", "species", "threshold", "metrics") if k not in b]
    if missing:
        record(name, g, "bundle contents", "FAIL", f"missing keys {missing}")
        return False
    record(name, g, "bundle contents", "PASS", f"{b['model_name']}, trained {b.get('trained', '?')}")

    ok = b["features"] == FEATURES
    record(name, g, "feature list & order", "PASS" if ok else "FAIL",
           "matches features.py" if ok else f"model {b['features']} != features.py {FEATURES}")
    if not ok:
        return False

    X = data[FEATURES].sample(2000, random_state=SEED)
    p1 = b["model"].predict_proba(X)[:, 1]
    p2 = b["model"].predict_proba(X)[:, 1]
    in_range = np.isfinite(p1).all() and p1.min() >= 0 and p1.max() <= 1
    record(name, g, "outputs are probabilities", "PASS" if in_range else "FAIL",
           f"range {p1.min():.3f} to {p1.max():.3f}")
    record(name, g, "deterministic", "PASS" if np.allclose(p1, p2) else "FAIL",
           "same input -> same output" if np.allclose(p1, p2) else "predictions changed between runs")
    varied = p1.std() > 0.01
    record(name, g, "not constant", "PASS" if varied else "FAIL", f"std of predictions {p1.std():.3f}")
    thr_ok = 0 < b["threshold"] < 1
    record(name, g, "threshold valid", "PASS" if thr_ok else "FAIL", f"{b['threshold']:.3f}")

    # Sightings should on average score above background (sanity, in-sample)
    pres = species_rows(data, b["species"])
    bg = data[data["presence"] == 0]
    ps = b["model"].predict_proba(pres[FEATURES])[:, 1].mean()
    pb = b["model"].predict_proba(bg[FEATURES])[:, 1].mean()
    record(name, g, "sightings score above background", "PASS" if ps > pb else "FAIL",
           f"mean {ps:.2f} vs {pb:.2f}")
    return in_range and varied and thr_ok


# ---------------------------------------------------------------------------
def test_biology(name, b, data):
    g = "biology"
    pres = species_rows(data, b["species"])
    base = pres[FEATURES].median().to_frame().T      # a "typical" place this species is seen

    def score(**changes):
        row = base.copy()
        for k, v in changes.items():
            row[k] = v
        return float(b["model"].predict_proba(row[FEATURES])[:, 1][0])

    typical = score()
    record(name, g, "typical sighting spot", "PASS" if typical >= b["threshold"] else "WARN",
           f"suitability {typical:.2f} (threshold {b['threshold']:.2f}) at median conditions: "
           f"{base['sst_c'].iloc[0]:.1f}°C, {base['depth_m'].iloc[0]:.0f} m deep, "
           f"{base['dist_coast_km'].iloc[0]:.1f} km offshore")

    if b["species"] != "Rhincodon typus":   # whale sharks do use deep water
        deep = score(depth_m=4000, dist_coast_km=300)
        record(name, g, "deep open ocean less suitable", "PASS" if deep < typical else "WARN",
               f"4000 m deep, 300 km offshore -> {deep:.2f} vs {typical:.2f}")

    for feat, hi, lo, desc in BIOLOGY.get(b["species"], []):
        p_hi, p_lo = score(**{feat: hi}), score(**{feat: lo})
        record(name, g, desc, "PASS" if p_hi > p_lo else "WARN", f"{p_hi:.2f} vs {p_lo:.2f}")


# ---------------------------------------------------------------------------
def test_new_regions(name, b, data):
    g = "new region"
    pres = species_rows(data, b["species"])
    bg = data[data["presence"] == 0]
    df = pd.concat([pres, bg]).reset_index(drop=True)
    y = df["presence"].values
    aucs = []
    for region, in_region in REGIONS.items():
        test = in_region(df).values
        n_pos = int(y[test].sum())
        if n_pos < MIN_REGION_PRESENCES:
            record(name, g, region, "INFO", f"only {n_pos} sightings there - not tested")
            continue
        model = clone(b["model"])
        w = np.where(y[~test] == 1, (y[~test] == 0).sum() / max(y[~test].sum(), 1), 1.0)
        if hasattr(model, "steps"):
            model.fit(df.loc[~test, FEATURES], y[~test], **{f"{model.steps[-1][0]}__sample_weight": w})
        else:
            model.fit(df.loc[~test, FEATURES], y[~test], sample_weight=w)
        p = model.predict_proba(df.loc[test, FEATURES])[:, 1]
        auc = roc_auc_score(y[test], p)
        found = (p[y[test] == 1] >= b["threshold"]).mean()
        aucs.append(auc)
        record(name, g, region, "PASS" if auc >= GOOD_AUC else "WARN",
               f"AUC {auc:.3f} on {n_pos} sightings never seen in training; "
               f"{found:.0%} of them inside predicted habitat")
    if aucs:
        record(name, g, "average over regions", "PASS" if np.mean(aucs) >= GOOD_AUC else "WARN",
               f"AUC {np.mean(aucs):.3f}")


# ---------------------------------------------------------------------------
def test_new_records(name, b, sightings):
    g = "new records"
    end = pd.Timestamp(b["data_range"][1])
    new = sightings[sightings["date"] > end]
    if b["species"] != "ANY":
        new = new[new["species"] == b["species"]]
    if len(new) < 10:
        record(name, g, "sightings after training data", "INFO",
               f"{len(new)} sightings after {end:%Y-%m-%d} - re-run steps 1-4 later to get more")
        return
    feats = add_ocean_features(new[["date", "lat", "lon"]], verbose=False).dropna(subset=FEATURES)
    if feats.empty:
        record(name, g, "sightings after training data", "INFO", "no ocean data yet for those dates")
        return
    p = b["model"].predict_proba(feats[FEATURES])[:, 1]
    inside = (p >= b["threshold"]).mean()
    record(name, g, f"{len(feats)} new sightings", "PASS" if inside >= 0.5 else "WARN",
           f"{inside:.0%} fall inside predicted habitat (mean suitability {p.mean():.2f})")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--species", nargs="+", help="model short names (default: all in models/)")
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(MODEL_DIR, "*_model.joblib")))
    if args.species:
        paths = [p for p in paths if os.path.basename(p).replace("_model.joblib", "") in args.species]
    if not paths:
        sys.exit("No models found. Run 09_train_models.py first.")

    data = pd.read_csv(os.path.join(DATA_DIR, "model_dataset.csv.gz"), parse_dates=["date"], low_memory=False)
    sightings = pd.read_csv(os.path.join(DATA_DIR, "sharks_australia.csv"), parse_dates=["date"])

    for path in paths:
        name = os.path.basename(path).replace("_model.joblib", "")
        b = joblib.load(path)
        print(f"\n=== {b.get('title', name)} ===")
        if test_integrity(name, b, data):
            test_biology(name, b, data)
            test_new_regions(name, b, data)
            test_new_records(name, b, sightings)

    res = pd.DataFrame(results)
    summary = res.groupby(["model", "status"]).size().unstack(fill_value=0)
    print("\n=== SUMMARY ===")
    print(summary.to_string())

    lines = ["# Sharko Australia: model test report", "",
             "Integrity = FAIL if broken. Biology / new region = WARN if the model disagrees with "
             "known biology or predicts an unseen region poorly (AUC < 0.7).", ""]
    for model, grp in res.groupby("model", sort=False):
        lines += [f"## {model}", "", "| group | test | result | detail |", "|---|---|---|---|"]
        lines += [f"| {r.group} | {r.test} | {r.status} | {r.detail} |" for r in grp.itertuples()]
        lines.append("")
    with open(os.path.join(MODEL_DIR, "test_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReport saved -> {os.path.join(MODEL_DIR, 'test_report.md')}")

    n_fail = (res["status"] == "FAIL").sum()
    print("RESULT: " + ("all integrity tests passed" if n_fail == 0 else f"{n_fail} test(s) FAILED"))
    sys.exit(1 if n_fail else 0)
