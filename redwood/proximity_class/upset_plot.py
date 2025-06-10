#!/usr/bin/env python3
import argparse
import json
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- Configuration ---
TOP5 = [
    "mistral-large-2407",
    "llama3-3",
    "gemini-2.5",
    "nova-pro",
    "o4-mini",
]
DISPLAY_NAMES = {
    "mistral-large-2407": "mistral-2407",
    "llama3-3":           "llama3-3",
    "gemini-2.5":         "gemini-2.5",
    "nova-pro":           "nova-pro",
    "o4-mini":            "o4-mini",
}

PROX_CLASSES = ["Nucleus","Cluster","Orbit","Sprawl","Fragment"]
CLASS_COLORS = {
    "Nucleus":  "#1f77b4",
    "Cluster":  "#aec7e8",
    "Orbit":    "#ff7f0e",
    "Sprawl":   "#ffbb78",
    "Fragment": "#2ca02c"
}

# --- CLI parsing ---
def parse_args():
    p = argparse.ArgumentParser(
        description="Custom UpSet‐style plot of top‐5 LLMs by spatial proximity"
    )
    p.add_argument(
        "--passed", default="../results/rq2/passed_bugs.json",
        help="Path to passed_bugs.json"
    )
    p.add_argument(
        "--proximity", default="proximity_class.csv",
        help="Path to proximity_class.csv"
    )
    return p.parse_args()

# --- Data loaders ---
def load_passed(path:str) -> dict[str,set[str]]:
    data = json.load(open(path, encoding="utf-8"))
    mapping: dict[str,set[str]] = {}
    for model_name, entry in data.items():
        ml = model_name.lower()
        for sub in TOP5:
            if sub in ml:
                mapping.setdefault(sub, set()).update(
                    bug.replace("_","-") for bug in entry.get("passed", [])
                )
    return mapping

def load_proximity(path:str) -> dict[str,str]:
    prox = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bug = row["bug_id"].strip().replace("_","-")
            prox[bug] = row["proximity_class"].strip()
    return prox

# --- Build membership DataFrame ---
def build_df(passed_map:dict[str,set[str]], prox_map:dict[str,str]) -> pd.DataFrame:
    all_bugs = set().union(*passed_map.values())
    recs = []
    for bug in sorted(all_bugs):
        rec = { sub: (bug in passed_map.get(sub,())) for sub in TOP5 }
        rec["prox"] = prox_map.get(bug, "UNKNOWN")
        recs.append((bug, rec))
    return pd.DataFrame.from_dict({b:r for b,r in recs}, orient="index")

# --- Main plotting ---
def main():
    args       = parse_args()
    passed_map = load_passed(args.passed)
    prox_map   = load_proximity(args.proximity)
    df         = build_df(passed_map, prox_map)

    # build the 5‐digit pattern string
    df["pattern"] = df[TOP5].apply(
        lambda r: "".join("1" if r[sub] else "0" for sub in TOP5), axis=1
    )

    # pivot to counts
    pivot = df.pivot_table(
        index="pattern", columns="prox", aggfunc="size", fill_value=0
    ).reindex(columns=PROX_CLASSES, fill_value=0)
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=True)

    patterns        = pivot.index.to_list()
    counts_by_class = pivot[PROX_CLASSES].to_numpy()  # (n_patterns × 5)
    totals          = pivot["total"].to_numpy()
    n_patterns      = len(patterns)

    # get dominant class per pattern → for connector color
    dominant = [ PROX_CLASSES[np.argmax(row)] for row in counts_by_class ]
    colors   = [ CLASS_COLORS[c] for c in dominant ]

    # --- start plotting ---
    fig = plt.figure(figsize=(12,8))
    gs  = fig.add_gridspec(2,1, height_ratios=(4,1), hspace=0.05)

    # Top: stacked bar + annotations
    ax0    = fig.add_subplot(gs[0])
    x      = np.arange(n_patterns)
    bottom = np.zeros(n_patterns)
    for i, cls in enumerate(PROX_CLASSES):
        vals = counts_by_class[:,i]
        bars = ax0.bar(x, vals, bottom=bottom, color=CLASS_COLORS[cls], label=cls)

        # annotate each segment
        for xi, v in enumerate(vals):
            if v > 0:
                y = bottom[xi] + v/2
                ax0.text(
                    xi, y, str(int(v)),
                    ha="center", va="center",
                    fontsize=10, color="white"
                )
        bottom += vals

    # annotate total above
    for xi, tot in zip(x, totals):
        ax0.text(xi, tot + 0.5, str(int(tot)), ha="center", fontsize=14)

    ax0.set_ylabel("Intersection size", fontsize=14)
    ax0.set_xticks([])
    ax0.legend(title="Proximity class", ncol=len(PROX_CLASSES), title_fontsize=12,  fontsize=14)

    # Bottom: dot‐matrix + connectors
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    for xi, pat in enumerate(patterns):
        ys = [i for i,ch in enumerate(pat) if ch=="1"]
        if not ys:
            continue
        # connector
        ax1.vlines(xi, min(ys), max(ys), color=colors[xi], linewidth=2)
        # dots
        ax1.scatter([xi]*len(ys), ys, color=colors[xi], s=40)

    ax1.set_yticks(range(len(TOP5)))
    ax1.set_yticklabels([DISPLAY_NAMES[sub] for sub in TOP5], fontsize=12)
    ax1.invert_yaxis()
    ax1.set_xlim(-0.5, n_patterns-0.5)
    ax1.set_xticks([])
    # ax1.set_xlabel("Model combinations")
    # ax1.set_ylabel("Model", labelpad=10)

    # adjust margins so nothing gets clipped
    fig.subplots_adjust(top=0.92, bottom=0.08, left=0.15, right=0.95)
    # plt.suptitle(
    #     "Bugs solved by Top-5 Models\nstacked by Spatial Proximity",
    #     fontsize=14, fontweight="bold"
    # )
    plt.tight_layout()
    plt.show()

if __name__=="__main__":
    main()
