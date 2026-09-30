"""Step 14: honest test of FUTURE prediction ("backtest").

We pretend it is the end of 2024 and predict every real 2025-2026 shark sighting,
using only information that would have been available at that time:

  A. Typical conditions   (seasonal model)  climatology built from 2020-2024 only.
                                            This is what the app does for dates
                                            months/years ahead (e.g. 2030).
  B. Outlook, N days ahead                  typical conditions + the unusual part of
                                            the conditions observed N days earlier,
                                            fading with time (damped persistence).
                                            Used for dates a few weeks ahead.
  C. Place + season only  (baseline)        depth, distance to coast, season - no
                                            ocean data. Shows what ocean data adds.
  D. Real conditions      (upper bound)     the actual 2025-26 satellite conditions,
                                            which nobody knows in advance. This is
                                            the best any ocean forecast could achieve.

All models are trained on 2020-2024 and tested on 2025-2026 (sightings + background).
Metrics: AUC (0.5 random ... 1 perfect) and "caught" = share of real sightings that
fall inside the predicted habitat (threshold chosen on 2020-2024 only).

Output: models/backtest_report.md, models/plots/backtest_future.png
"""
import importlib
import os
import sys
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from climatology import Climatology
from config import BASE_DIR, DATA_DIR
from features import FEATURES, OCEAN_FEATURES, add_ocean_features

warnings.filterwarnings("ignore")
tm = importlib.import_module("09_train_models")        # reuse training helpers

MODEL_DIR = os.path.join(BASE_DIR, "models")
PLOT_DIR = os.path.join(MODEL_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)
TEST_FROM = 2025
LEADS = [7, 14, 30, 60, 90]
SPECIES = [("tiger", "Galeocerdo cuvier"), ("bull", "Carcharhinus leucas"),
           ("white", "Carcharodon carcharias"), ("any", "ANY")]
STATIC = ["depth_m", "dist_coast_km", "day_sin", "day_cos"]

data = pd.read_csv(os.path.join(DATA_DIR, "model_dataset.csv.gz"), parse_dates=["date"], low_memory=False)
clim = Climatology(os.path.join(DATA_DIR, "climatology", "clim_backtest.nc"))
if not clim.years.endswith(str(TEST_FROM - 1)):
    sys.exit(f"clim_backtest.nc covers {clim.years}; it must end in {TEST_FROM - 1}")
print(f"Climatology used for the backtest: {clim.years} (no 2025-26 information)")

# Typical conditions for every row, from 2020-2024 only
typical = clim.sample(data["lat"], data["lon"], data["date"])
seasonal = data.copy()
seasonal[OCEAN_FEATURES] = typical[OCEAN_FEATURES].values
keep = seasonal[FEATURES].notna().all(axis=1)
data, seasonal = data[keep].reset_index(drop=True), seasonal[keep].reset_index(drop=True)
test_mask = (data["year"] >= TEST_FROM).values

# Outlook features: typical(t) + persistence(L) * (observed(t-L) - typical(t-L))
print(f"\nBuilding outlook inputs for {test_mask.sum():,} test rows at leads {LEADS} days...")
outlook = {}
test_rows = data.loc[test_mask, ["date", "lat", "lon"]]
for lead in LEADS:
    past = test_rows.assign(date=test_rows["date"] - pd.Timedelta(days=lead))
    observed = add_ocean_features(past, verbose=False)
    typ_past = clim.sample(past["lat"], past["lon"], past["date"])
    feats = seasonal.loc[test_mask].copy()
    for f in OCEAN_FEATURES:
        anomaly = observed[f].values - typ_past[f].values
        anomaly = np.where(np.isfinite(anomaly), anomaly, 0.0)       # unknown -> assume typical
        feats[f] = feats[f].values + clim.persistence_factor(f, lead) * anomaly
    outlook[lead] = feats
    print(f"  lead {lead:>3} days: remaining anomaly factor sst {clim.persistence_factor('sst_c', lead):.2f}, "
          f"chl {clim.persistence_factor('chl_log10', lead):.2f}, sla {clim.persistence_factor('sla_m', lead):.2f}")


def params_for(name, mode):
    path = os.path.join(MODEL_DIR, "seasonal" if mode == "seasonal" else "", f"{name}_model.joblib")
    if os.path.exists(path):
        return joblib.load(path).get("lgbm_params", {})
    return joblib.load(os.path.join(MODEL_DIR, f"{name}_model.joblib")).get("lgbm_params", {})


def evaluate(train_X, train_y, groups, test_sets, params):
    """Train on 2020-24 (threshold from spatial CV on 2020-24), score each test set."""
    make = lambda: tm.make_lgbm(params)
    oof, _ = tm.spatial_cv(make, train_X, train_y, groups)
    _, thr = tm.tss_best(train_y, oof)
    model = tm.fit(make(), train_X, train_y, tm.balanced_weights(train_y))
    out = {}
    for label, (X, y) in test_sets.items():
        p = model.predict_proba(X[train_X.columns])[:, 1]
        out[label] = {"auc": roc_auc_score(y, p), "caught": (p[y == 1] >= thr).mean(),
                      "false_alarm": (p[y == 0] >= thr).mean()}
    return out


rows = []
for name, sci in SPECIES:
    is_sp = (data["presence"] == 0) | (sci == "ANY") | (data["species"] == sci)
    idx = np.flatnonzero(is_sp.values)
    tr = idx[~test_mask[idx]]
    te = idx[test_mask[idx]]
    y = data["presence"]
    n_test = int(y.iloc[te].sum())
    print(f"\n### {name}: train {int(y.iloc[tr].sum()):,} sightings (2020-24), "
          f"test {n_test:,} sightings (2025-26)")
    groups = (np.floor(data["lat"] / tm.BLOCK_DEG).astype(int).astype(str) + "_"
              + np.floor(data["lon"] / tm.BLOCK_DEG).astype(int).astype(str))
    yt = y.iloc[te].values

    # D. upper bound: real conditions
    real = evaluate(data.loc[tr, FEATURES], y.iloc[tr], groups.iloc[tr],
                    {"Real conditions (upper bound)": (data.loc[te, FEATURES], yt)}, params_for(name, "daily"))
    # A + B. seasonal model: typical conditions, and outlooks at each lead
    te_pos = np.searchsorted(np.flatnonzero(test_mask), te)       # position of te rows in the outlook tables
    tests = {f"Outlook {lead} days ahead": (outlook[lead].iloc[te_pos][FEATURES], yt) for lead in LEADS}
    tests["Typical conditions (months/years ahead)"] = (seasonal.loc[te, FEATURES], yt)
    seas = evaluate(seasonal.loc[tr, FEATURES], y.iloc[tr], groups.iloc[tr], tests, params_for(name, "seasonal"))
    # C. baseline
    base = evaluate(data.loc[tr, STATIC], y.iloc[tr], groups.iloc[tr],
                    {"Place + season only (baseline)": (data.loc[te, STATIC], yt)}, params_for(name, "daily"))

    for label, m in {**real, **seas, **base}.items():
        rows.append({"model": name, "method": label, "test_sightings": n_test, **m})
        print(f"  {label:<42} AUC {m['auc']:.3f} | caught {m['caught']:.0%} | false alarm {m['false_alarm']:.0%}")

res = pd.DataFrame(rows)
res.to_csv(os.path.join(MODEL_DIR, "backtest.csv"), index=False)

# Plot: AUC vs how far ahead
fig, ax = plt.subplots(figsize=(7.5, 4.8))
x_typ = 180
for name, _ in SPECIES:
    r = res[res["model"] == name].set_index("method")["auc"]
    xs = LEADS + [x_typ]
    ys = [r[f"Outlook {l} days ahead"] for l in LEADS] + [r["Typical conditions (months/years ahead)"]]
    line, = ax.plot(xs, ys, "o-", label=name)
    ax.axhline(r["Real conditions (upper bound)"], color=line.get_color(), ls=":", lw=1)
    ax.axhline(r["Place + season only (baseline)"], color=line.get_color(), ls="--", lw=0.8, alpha=0.6)
ax.set_xticks(LEADS + [x_typ])
ax.set_xticklabels([str(l) for l in LEADS] + ["months-\nyears"])
ax.set(xlabel="How far ahead the prediction is made (days)", ylabel="AUC on 2025-26 sightings",
       title="Predicting 2025-26 sharks using only data up to 2024\n"
             "dotted = real conditions (upper bound), dashed = place + season only")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(PLOT_DIR, "backtest_future.png"), dpi=150)

# Report
lines = ["# Sharko Australia: future-prediction backtest", "",
         f"Trained on 2020-{TEST_FROM - 1}, tested on {TEST_FROM}-2026 real sightings, using only information "
         "available at the end of 2024. AUC: 0.5 = random, 0.7 = fair, 0.8 = good, 0.9 = excellent. "
         "Caught = share of real sightings inside the predicted habitat; false alarm = share of background "
         "points flagged as habitat.", ""]
for name, grp in res.groupby("model", sort=False):
    lines += [f"## {name} ({grp['test_sightings'].iloc[0]} test sightings)", "",
              "| method | AUC | caught | false alarm |", "|---|---|---|---|"]
    lines += [f"| {r.method} | {r.auc:.3f} | {r.caught:.0%} | {r.false_alarm:.0%} |" for r in grp.itertuples()]
    lines.append("")
with open(os.path.join(MODEL_DIR, "backtest_report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nSaved {os.path.join(MODEL_DIR, 'backtest_report.md')} and plots/backtest_future.png")
