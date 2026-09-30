"""Step 9: train, compare and pick the best habitat model for each shark species.

For each species:
  data      its thinned sightings (presence=1) + all background points (presence=0),
            weighted so sightings and background count equally
  features  sea temperature, temperature fronts, chlorophyll, sea level, currents,
            depth, distance to coast, season  (see features.py)
            Latitude/longitude are deliberately NOT used: otherwise the model learns
            "where divers and receivers are" instead of "what conditions sharks like".

  candidates
    1. GLM         logistic regression with quadratic terms (the classic MaxEnt-style
                   species-distribution baseline)
    2. RandomForest
    3. LightGBM    gradient boosting, hyperparameters tuned with Optuna

  honest testing
    - spatial block cross-validation: Australia is cut into 2x2 degree blocks and whole
      blocks are held out, so the model is always tested on places it has never seen
    - future test: train on 2020-2024, test on 2025-2026
    metrics: ROC-AUC (0.5 = coin flip, 1 = perfect), PR-AUC, TSS (true skill statistic)

  The candidate with the best spatial-CV AUC wins and is retrained on all data.

Outputs (models/):
  <name>_model.joblib        model bundle used by 10_predict_map.py
  plots/<name>_*.png         ROC curves, feature importance (SHAP), response curves
  metrics.csv, report.md     comparison of every candidate for every species

Usage:
  python 09_train_models.py                          # tiger, bull, white
  python 09_train_models.py --species tiger whale    # pick species (short or scientific names)
  python 09_train_models.py --all                    # every species with >= 300 records
  python 09_train_models.py --trials 80              # more Optuna tuning (slower, maybe better)
  python 09_train_models.py --mode seasonal --species tiger bull white any
                                                     # long-range models on typical conditions
"""
import argparse
import os
import time
import warnings
import joblib
import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import shap
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from config import BASE_DIR, DATA_DIR
from features import FEATURES, FEATURE_LABELS

warnings.filterwarnings("ignore", category=UserWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)

MODE = "daily"                    # "daily" = real conditions of the day; "seasonal" = typical conditions
MODEL_DIR = os.path.join(BASE_DIR, "models")
PLOT_DIR = os.path.join(MODEL_DIR, "plots")
DATASETS = {"daily": "model_dataset.csv.gz", "seasonal": "model_dataset_seasonal.csv.gz"}

SPECIES = {
    "tiger": "Galeocerdo cuvier",
    "bull": "Carcharhinus leucas",
    "white": "Carcharodon carcharias",
    "whale": "Rhincodon typus",
    "greynurse": "Carcharias taurus",
    "portjackson": "Heterodontus portusjacksoni",
    "greyreef": "Carcharhinus amblyrhynchos",
    "blacktip": "Carcharhinus limbatus",
    "any": "ANY",                      # all shark species together
}
BLOCK_DEG = 2.0
N_FOLDS = 5
FUTURE_FROM_YEAR = 2025
MIN_PRESENCES = 300
SEED = 42


# ---------------------------------------------------------------------------
# Candidate models
# ---------------------------------------------------------------------------
def make_glm():
    return make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False),
                         LogisticRegression(C=0.5, max_iter=3000))


def make_rf():
    return RandomForestClassifier(n_estimators=400, min_samples_leaf=10, max_features="sqrt",
                                  n_jobs=-1, random_state=SEED)


def make_lgbm(params=None):
    base = dict(n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                reg_lambda=1.0, random_state=SEED, n_jobs=-1, verbose=-1)
    base.update(params or {})
    return lgb.LGBMClassifier(**base)


def fit(model, X, y, w):
    """Fit with balanced sample weights (works for pipelines too)."""
    if hasattr(model, "steps"):
        model.fit(X, y, **{f"{model.steps[-1][0]}__sample_weight": w})
    else:
        model.fit(X, y, sample_weight=w)
    return model


def balanced_weights(y):
    y = np.asarray(y)
    return np.where(y == 1, (y == 0).sum() / max((y == 1).sum(), 1), 1.0)


def tss_best(y, p):
    fpr, tpr, thr = roc_curve(y, p)
    k = np.argmax(tpr - fpr)
    return tpr[k] - fpr[k], thr[k]


def spatial_folds(y, groups):
    """Assign whole 2x2 degree blocks to folds so every fold gets a fair share of sightings.

    Sightings are very clustered (a few blocks hold most of them), so random block
    splits can leave a test fold with no sightings. Blocks are dealt out greedily,
    biggest first, to the fold with the fewest sightings (then fewest rows) so far.
    """
    rng = np.random.default_rng(SEED)
    stats = pd.DataFrame({"g": groups.values, "y": y.values}).groupby("g")["y"].agg(["sum", "size"])
    stats = stats.sample(frac=1, random_state=SEED).sort_values(["sum", "size"], ascending=False,
                                                                 kind="stable")
    fold_pos, fold_n = np.zeros(N_FOLDS), np.zeros(N_FOLDS)
    assign = {}
    for g, (pos, n) in stats.iterrows():
        order = np.lexsort((rng.random(N_FOLDS), fold_n, fold_pos))
        f = order[0]
        assign[g] = f
        fold_pos[f] += pos
        fold_n[f] += n
    fold_of = groups.map(assign).values
    return [(np.flatnonzero(fold_of != f), np.flatnonzero(fold_of == f)) for f in range(N_FOLDS)]


def spatial_cv(make_model, X, y, groups):
    """Out-of-fold predictions with whole 2x2 degree blocks held out."""
    oof = np.zeros(len(y))
    fold_auc = []
    for tr, te in spatial_folds(y, groups):
        m = fit(make_model(), X.iloc[tr], y.iloc[tr], balanced_weights(y.iloc[tr]))
        oof[te] = m.predict_proba(X.iloc[te])[:, 1]
        fold_auc.append(roc_auc_score(y.iloc[te], oof[te]))
    return oof, np.array(fold_auc)


def tune_lgbm(X, y, groups, n_trials):
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 150, 1200, step=50),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 8, 128, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 12),
            "min_child_samples": trial.suggest_int("min_child_samples", 20, 300, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 10, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 10, log=True),
        }
        _, aucs = spatial_cv(lambda: make_lgbm(params), X, y, groups)
        return aucs.mean()

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    return study.best_params, study.best_value


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def plot_roc(name, title, y, oofs):
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for label, p in oofs.items():
        fpr, tpr, _ = roc_curve(y, p)
        ax.plot(fpr, tpr, label=f"{label} (AUC {roc_auc_score(y, p):.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="random guess")
    ax.set(xlabel="False positive rate", ylabel="True positive rate",
           title=f"{title}\nspatial cross-validation (unseen regions)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, f"{name}_roc.png"), dpi=150)
    plt.close(fig)


def explain(name, title, model, model_name, X, y):
    """SHAP for tree models, permutation importance otherwise. Returns importance table."""
    sample = X.sample(min(3000, len(X)), random_state=SEED)
    labels = [FEATURE_LABELS[c] for c in X.columns]
    if model_name == "LightGBM":
        sv = shap.TreeExplainer(model).shap_values(sample)
        sv = sv[1] if isinstance(sv, list) else sv
        imp = pd.Series(np.abs(sv).mean(0), index=X.columns)
        plt.figure()
        shap.summary_plot(sv, sample, feature_names=labels, show=False, max_display=10)
        plt.title(f"{title}: what drives the prediction (SHAP)", fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, f"{name}_shap.png"), dpi=150)
        plt.close()
    else:
        r = permutation_importance(model, sample, y.loc[sample.index], scoring="roc_auc",
                                   n_repeats=5, random_state=SEED, n_jobs=-1)
        imp = pd.Series(r.importances_mean, index=X.columns)

    imp = imp.sort_values()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh([FEATURE_LABELS[c] for c in imp.index], imp.values, color="#2a7fb8")
    ax.set(title=f"{title}: feature importance ({model_name})", xlabel="importance")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, f"{name}_importance.png"), dpi=150)
    plt.close(fig)

    # Response curves: how suitability changes with each of the top 6 features
    top = list(imp.index[::-1][:6])
    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    PartialDependenceDisplay.from_estimator(
        model, sample, top, ax=axes.ravel(), grid_resolution=40,
        percentiles=(0.02, 0.98), kind="average")
    for ax, c in zip(axes.ravel(), top):
        ax.set_xlabel(FEATURE_LABELS[c])
        if c in ("depth_m", "dist_coast_km"):   # most sightings are in the first few km / metres
            ax.set_xscale("log")
        ax.set_ylabel("habitat suitability")
    fig.suptitle(f"{title}: response curves", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, f"{name}_response.png"), dpi=150)
    plt.close(fig)
    return imp[::-1]


# ---------------------------------------------------------------------------
# Train one species
# ---------------------------------------------------------------------------
def train_species(name, scientific, data, n_trials):
    title = "All sharks" if scientific == "ANY" else f"{scientific} ({name})"
    if MODE == "seasonal":
        title += " - seasonal"
    pres = data[data["presence"] == 1]
    if scientific != "ANY":
        pres = pres[pres["species"] == scientific]
    if len(pres) < MIN_PRESENCES:
        print(f"\n### {title}: only {len(pres)} records (< {MIN_PRESENCES}), skipped")
        return []
    df = pd.concat([pres, data[data["presence"] == 0]]).reset_index(drop=True)
    X, y = df[FEATURES], df["presence"]
    groups = (np.floor(df["lat"] / BLOCK_DEG).astype(int).astype(str) + "_"
              + np.floor(df["lon"] / BLOCK_DEG).astype(int).astype(str))
    print(f"\n### {title}: {len(pres):,} sightings + {(y == 0).sum():,} background, "
          f"{groups.nunique()} spatial blocks")

    t = time.time()
    best_params, best_cv = tune_lgbm(X, y, groups, n_trials)
    print(f"  Optuna: {n_trials} trials, best spatial-CV AUC {best_cv:.3f} ({time.time() - t:.0f}s)")

    candidates = {
        "GLM": make_glm,
        "RandomForest": make_rf,
        "LightGBM": lambda: make_lgbm(best_params),
    }
    future_train = df["year"] < FUTURE_FROM_YEAR
    rows, oofs = [], {}
    for cname, make in candidates.items():
        oof, aucs = spatial_cv(make, X, y, groups)
        oofs[cname] = oof
        tss, _ = tss_best(y, oof)
        m = fit(make(), X[future_train], y[future_train], balanced_weights(y[future_train]))
        p_future = m.predict_proba(X[~future_train])[:, 1]
        row = {
            "species": title, "model": cname,
            "spatial_auc": aucs.mean(), "spatial_auc_std": aucs.std(),
            "spatial_pr_auc": average_precision_score(y, oof), "spatial_tss": tss,
            "future_auc": roc_auc_score(y[~future_train], p_future),
            "n_presences": len(pres), "selected": False,
        }
        rows.append(row)
        print(f"  {cname:<13} spatial AUC {row['spatial_auc']:.3f} ± {row['spatial_auc_std']:.3f} | "
              f"PR-AUC {row['spatial_pr_auc']:.3f} | TSS {tss:.3f} | future AUC {row['future_auc']:.3f}")

    best = max(rows, key=lambda r: r["spatial_auc"])
    best["selected"] = True
    print(f"  -> best: {best['model']}")
    plot_roc(name, title, y, oofs)

    # Retrain the winner on everything; pick the yes/no threshold that maximises TSS
    final = fit(candidates[best["model"]](), X, y, balanced_weights(y))
    _, threshold = tss_best(y, oofs[best["model"]])
    importance = explain(name, title, final, best["model"], X, y)
    print("  top drivers: " + ", ".join(FEATURE_LABELS[c] for c in importance.index[:4]))

    joblib.dump({
        "model": final, "model_name": best["model"], "features": FEATURES,
        "species": scientific, "short_name": name, "title": title, "mode": MODE,
        "threshold": float(threshold), "metrics": best,
        "lgbm_params": best_params, "importance": importance.to_dict(),
        "n_presences": len(pres), "n_background": int((y == 0).sum()),
        "trained": pd.Timestamp.now().isoformat(timespec="seconds"),
        "data_range": (str(df["date"].min())[:10], str(df["date"].max())[:10]),
    }, os.path.join(MODEL_DIR, f"{name}_model.joblib"))
    return rows


def write_report(metrics):
    lines = ["# Sharko Australia: model comparison", "",
             "Spatial AUC = tested on 2x2 degree regions the model never saw. "
             f"Future AUC = trained on 2020-{FUTURE_FROM_YEAR - 1}, tested on {FUTURE_FROM_YEAR}-2026. "
             "AUC 0.5 = random, 0.7 = fair, 0.8 = good, 0.9 = excellent.", ""]
    cols = ["species", "model", "spatial_auc", "spatial_pr_auc", "spatial_tss", "future_auc", "n_presences"]
    tbl = metrics[cols].copy()
    tbl["model"] = np.where(metrics["selected"].astype(bool),
                            "**" + tbl["model"] + "** (best)", tbl["model"])
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * len(cols))
    for _, r in tbl.iterrows():
        lines.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r) + " |")
    with open(os.path.join(MODEL_DIR, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--species", nargs="+", default=["tiger", "bull", "white"],
                    help="short names (" + ", ".join(SPECIES) + ") or scientific names")
    ap.add_argument("--all", action="store_true", help=f"every species with >= {MIN_PRESENCES} records")
    ap.add_argument("--trials", type=int, default=40, help="Optuna trials per species")
    ap.add_argument("--mode", choices=list(DATASETS), default="daily",
                    help="daily: real conditions (models/); seasonal: typical conditions for "
                         "long-range dates (models/seasonal/, needs 13_build_seasonal_dataset.py)")
    args = ap.parse_args()

    MODE = args.mode
    if MODE == "seasonal":
        MODEL_DIR = os.path.join(BASE_DIR, "models", "seasonal")
        PLOT_DIR = os.path.join(MODEL_DIR, "plots")
    os.makedirs(PLOT_DIR, exist_ok=True)
    data = pd.read_csv(os.path.join(DATA_DIR, DATASETS[MODE]), parse_dates=["date"],
                       low_memory=False)
    if args.all:
        counts = data[data["presence"] == 1]["species"].value_counts()
        reverse = {v: k for k, v in SPECIES.items()}
        targets = [(reverse.get(s, s.lower().replace(" ", "_")), s)
                   for s in counts[counts >= MIN_PRESENCES].index]
    else:
        targets = []
        for s in args.species:
            if s.lower() in SPECIES:
                targets.append((s.lower(), SPECIES[s.lower()]))
            else:
                targets.append((s.lower().replace(" ", "_"), s))

    print(f"Training {len(targets)} model(s): " + ", ".join(n for n, _ in targets))
    all_rows = []
    for name, sci in targets:
        all_rows += train_species(name, sci, data, args.trials)

    if all_rows:
        new = pd.DataFrame(all_rows)
        path = os.path.join(MODEL_DIR, "metrics.csv")
        if os.path.exists(path):   # keep results for species not retrained this run
            old = pd.read_csv(path)
            new = pd.concat([old[~old["species"].isin(new["species"])], new], ignore_index=True)
        new.to_csv(path, index=False)
        write_report(new)
        print(f"\nSaved models, plots and report -> {MODEL_DIR}")
        best = new[new["selected"].astype(bool)]
        print(best[["species", "model", "spatial_auc", "future_auc"]].round(3).to_string(index=False))
