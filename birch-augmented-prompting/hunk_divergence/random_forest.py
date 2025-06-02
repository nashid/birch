#!/usr/bin/env python3
import argparse
import csv
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr
from sklearn.model_selection import (
    StratifiedKFold, GridSearchCV, cross_val_score, train_test_split
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score


RQ2_MODELS  = ["o4-mini","nova-pro","gemini-2.5-flash","mistral-large-2407","llama3-3-70b"]
PROX_CLASSES = ["Nucleus","Cluster","Orbit","Sprawl","Fragment"]

def parse_args():
    p = argparse.ArgumentParser(
        description="Analyze which divergence & proximity features drive RQ2 repair success"
    )
    p.add_argument("--avg_csv",    default="bugwise_average_divergence.csv",
                   help="CSV with bug_id,avg_lexical,avg_ast,avg_file,…")
    p.add_argument("--prox_csv",   default="../proximity_class/proximity_class.csv",
                   help="CSV with bug_id,proximity_class")
    p.add_argument("--passed_json", default="../results/rq2/passed_bugs.json",
                   help="RQ2 passed_bugs.json")
    return p.parse_args()

def load_avg_distances(path: str):
    d = {}
    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for col in ("avg_lexical","avg_ast","avg_file"):
            if col not in rdr.fieldnames:
                raise ValueError(f"Missing column {col!r} in {path}")
        for row in rdr:
            bid = row["bug_id"].strip().replace("_","-")
            d[bid] = (float(row["avg_lexical"]),
                      float(row["avg_ast"]),
                      float(row["avg_file"]))
    return d

def load_proximity(path: str):
    p = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row["bug_id"].strip().replace("_","-")
            p[bid] = row["proximity_class"].strip()
    return p

def load_passed(path: str):
    data = json.load(open(path, encoding="utf-8"))
    mapping = {m:set() for m in RQ2_MODELS}
    for full_k, entry in data.items():
        kl = full_k.lower()
        for model in RQ2_MODELS:
            if model in kl:
                solved = {b.replace("_","-") for b in entry.get("passed",[])}
                mapping[model].update(solved)
    return mapping

def build_feature_matrix(avg_dist, passed_map, prox_map):
    # Include every bug we have avg_dist for
    rows = []
    all_bugs = sorted(avg_dist.keys())
    for b in all_bugs:
        lex, ast, fl = avg_dist[b]
        prox = prox_map.get(b, "UNKNOWN")
        label = int(any(b in s for s in passed_map.values()))
        rows.append({"bug":b, "avg_lexical":lex, "avg_ast":ast,
                     "avg_file":fl, "proximity_class":prox, "label":label})
    df = pd.DataFrame(rows)
    return df

def main():
    args = parse_args()
    avg_dist   = load_avg_distances(args.avg_csv)
    prox_map   = load_proximity(args.prox_csv)
    passed_map = load_passed(args.passed_json)

    df = build_feature_matrix(avg_dist, passed_map, prox_map)

    print("=== Spearman ρ vs. success ===")
    features = ["avg_lexical","avg_ast","avg_file"] + PROX_CLASSES
    prox_ohe = pd.get_dummies(df["proximity_class"]).reindex(columns=PROX_CLASSES, fill_value=0)
    X_prox   = prox_ohe.values
    for col in ["avg_lexical","avg_ast","avg_file"]:
        rho,p = spearmanr(df[col], df["label"])
        print(f"  {col:12s}  ρ = {rho:.3f}, p = {p:.1e}")
    for i,cls in enumerate(PROX_CLASSES):
        rho,p = spearmanr(X_prox[:,i], df["label"])
        print(f"  prox_{cls:9s}  ρ = {rho:.3f}, p = {p:.1e}")

    print("\n=== Median distances by success ===")
    print(df.groupby("label")[["avg_lexical","avg_ast","avg_file"]].median())

    X_num = df[["avg_lexical","avg_ast","avg_file"]].values
    X     = np.hstack([X_num, X_prox])
    y     = df["label"].values
    feat_names = ["avg_lexical","avg_ast","avg_file"] + [f"prox_{c}" for c in PROX_CLASSES]

    X_tr,X_te,y_tr,y_te = train_test_split(X,y, stratify=y, test_size=0.2, random_state=42)
    rf = RandomForestClassifier(class_weight="balanced", n_estimators=200, random_state=42)
    rf.fit(X_tr, y_tr)
    importances = rf.feature_importances_
    imp_df = pd.DataFrame({"feature":feat_names,"importance":importances})
    imp_df = imp_df.sort_values("importance", ascending=False).reset_index(drop=True)
    print("\n=== RandomForest feature importances ===")
    print(imp_df.to_string(index=False))

    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    inner = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth":    [None, 10, 20],
    }

    # Store importances for every outer fold
    importances_cv = np.zeros((outer.get_n_splits(), len(feat_names)))
    roc_auc_cv     = np.zeros(outer.get_n_splits())

    for fold, (train_idx, test_idx) in enumerate(outer.split(X, y), start=1):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        # Grid-search *inside* the current fold
        base_rf = RandomForestClassifier(class_weight="balanced",
                                         random_state=42)
        grid = GridSearchCV(
            base_rf, param_grid, cv=inner, scoring="roc_auc", n_jobs=-1
        ).fit(X_tr, y_tr)

        best_rf = grid.best_estimator_

        # ROC-AUC on the held-out fold
        roc_auc_cv[fold-1] = roc_auc_score(y_te, best_rf.predict_proba(X_te)[:, 1])
        # Permutation importance on the held-out fold
        perm = permutation_importance(
            best_rf, X_te, y_te,
            n_repeats=30, random_state=42, n_jobs=-1
        )
        importances_cv[fold-1] = perm.importances_mean

        print(f"[fold {fold}] best params → {grid.best_params_}")

    # Aggregate across folds
    imp_df = (
        pd.DataFrame({
            "feature":     feat_names,
            "mean_imp":    importances_cv.mean(axis=0),
            "std_imp":     importances_cv.std(axis=0),
        })
        .sort_values("mean_imp", ascending=False)
        .reset_index(drop=True)
    )

    print("\n=== CV permutation importances ===")
    print(imp_df.to_string(index=False))
    print("\n=== Outer-fold ROC-AUC ===")
    print(" per-fold:", np.round(roc_auc_cv, 3))
    print(f" mean   = {roc_auc_cv.mean():.3f}")
    print(f" std    = {roc_auc_cv.std():.3f}")

if __name__=="__main__":
    main()
