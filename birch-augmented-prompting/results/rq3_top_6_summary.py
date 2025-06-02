#!/usr/bin/env python3
import argparse
import csv
import json
import statistics
from pathlib import Path
from collections import defaultdict

from scipy.stats import mannwhitneyu, spearmanr

RQ_MODELS = {
    "rq3": [
        "ada-rag_mode_4_model_o4-mini-2025-04-16",
        "ada-rag_us.meta.llama3-3-70b-instruct-v1:0",
    ],
    "rq4": [
        "file_mode_4_model_o4-mini-2025-04-16",
        "file_us.meta.llama3-3-70b-instruct-v1:0",
    ],
    "rq5": [
        "mode_4_model_o4-mini-2025-04-16",
        "us.meta.llama3-3-70b-instruct-v1:0",
    ],
}

TOTAL_COUNTS = {
    "Nucleus":  59,
    "Cluster": 185,
    "Orbit":    67,
    "Sprawl":   50,
    "Fragment": 11,
}
PROX_CLASSES = list(TOTAL_COUNTS.keys())

def parse_args():
    p = argparse.ArgumentParser(
        description="Summarise RQ3-5 models like RQ2 did, adding Spearman’s ρ and p-value."
    )
    p.add_argument(
        "--results_dir",
        default="../results",
        help="Parent folder containing rq3/, rq4/, rq5/ subdirs"
    )
    p.add_argument(
        "--divergence_csv",
        default="../hunk_divergence_v4_bleu/total_hunk_divergence_results.csv",
        help="CSV with columns bug_id, divergence"
    )
    p.add_argument(
        "--proximity_csv",
        default="../proximity_class/proximity_class.csv",
        help="CSV with columns bug_id, proximity_class"
    )
    p.add_argument(
        "--output_csv",
        default="augmented_top_6_strategy.csv",
        help="Where to write the 6×2 summary rows"
    )
    return p.parse_args()

def load_passed(results_dir: Path) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for rq, keys in RQ_MODELS.items():
        path = results_dir / rq / "passed_bugs.json"
        if not path.is_file():
            print(f"[WARN] Missing {path}; skipping")
            continue
        data = json.load(open(path, encoding="utf-8"))
        for model_key in keys:
            bugs = data.get(model_key, {}).get("passed", [])
            # normalize bug IDs to use hyphens
            mapping[model_key] = {b.replace("_","-") for b in bugs}
    return mapping

def load_divergence(path: Path) -> dict[str, float]:
    d = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row["bug_id"].strip().replace("_","-")
            try:
                d[bid] = float(row["divergence"])
            except ValueError:
                pass
    return d

def load_proximity(path: Path) -> dict[str, str]:
    p = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bid = row["bug_id"].strip().replace("_","-")
            p[bid] = row["proximity_class"].strip()
    return p

def summarize(bugs: set[str],
              divergence_map: dict[str, float],
              proximity_map: dict[str, str]
             ):
    vals = [divergence_map[b] for b in bugs if b in divergence_map]
    if vals:
        mn   = round(min(vals),   4)
        mx   = round(max(vals),   4)
        mean = round(statistics.mean(vals),   4)
        md   = round(statistics.median(vals), 4)
        sd   = round(statistics.stdev(vals),  4) if len(vals) > 1 else 0.0
    else:
        mn = mx = mean = md = sd = 0.0

    # count per proximity class
    counts = {c:0 for c in PROX_CLASSES}
    for b in bugs:
        cls = proximity_map.get(b)
        if cls in counts:
            counts[cls] += 1

    # convert to percentages
    percents = {
        c: round(counts[c] / TOTAL_COUNTS[c] * 100, 2)
        for c in PROX_CLASSES
    }

    return mn, mx, mean, md, sd, counts, percents

def main():
    args         = parse_args()
    results_dir  = Path(args.results_dir)
    passed_map   = load_passed(results_dir)
    divergence   = load_divergence(Path(args.divergence_csv))
    proximity    = load_proximity(Path(args.proximity_csv))
    all_bugs     = set(divergence.keys())

    # 1) Mann–Whitney U p-values
    mw_pvals = {}
    # 2) Spearman ρ and p-values across all bugs
    spear_stats = {}

    for model_key, solved in passed_map.items():
        # Mann–Whitney U on solved vs unsolved subsets
        sol = [divergence[b] for b in solved if b in divergence]
        uns = [divergence[b] for b in (all_bugs - solved) if b in divergence]
        mw_p = None
        if sol and uns:
            _, mw_p = mannwhitneyu(sol, uns, alternative="two-sided")
        mw_pvals[model_key] = mw_p

        # Spearman correlation between divergence and 0/1 success
        divs, succ = [], []
        for b in all_bugs:
            if b in divergence:
                divs.append(divergence[b])
                succ.append(1 if b in solved else 0)
        rho = sp_p = None
        if len(divs) > 1 and len(set(succ)) > 1:
            rho, sp_p = spearmanr(divs, succ)
        spear_stats[model_key] = (rho, sp_p)

    # prepare CSV
    fieldnames = (
        ["model","status",
         "min_div","max_div","mean_div","median_div","std_div",
         "p_value","spearman_rho"]
      + [f"{cls}_{s}" for cls in PROX_CLASSES for s in ("count","pct")]
    )

    outp = Path(args.output_csv)
    with outp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for model_key, solved in passed_map.items():
            # format the two tests
            mw_p  = mw_pvals.get(model_key)
            mw_str = f"{mw_p:.2e}" if isinstance(mw_p, float) else ""
            rho, sp_p = spear_stats[model_key]
            rho_str = f"{rho:.2f}"   if isinstance(rho, float) else ""
            sp_str  = f"{sp_p:.2e}"  if isinstance(sp_p, float) else ""

            # --- solved row ---
            mn, mx, mean, md, sd, counts, percs = summarize(solved, divergence, proximity)
            row = {
                "model": model_key,
                "status": "solved",
                "min_div":    mn,
                "max_div":    mx,
                "mean_div":   mean,
                "median_div": md,
                "std_div":    sd,
                "p_value":        mw_str,
                "spearman_rho":      rho_str,
            }
            for cls in PROX_CLASSES:
                row[f"{cls}_count"] = counts[cls]
                row[f"{cls}_pct"]   = percs[cls]
            writer.writerow(row)

            # --- unsolved row (no p-values) ---
            unsolved = all_bugs - solved
            mn, mx, mean, md, sd, counts, percs = summarize(unsolved, divergence, proximity)
            row = {
                "model": model_key,
                "status": "unsolved",
                "min_div":    mn,
                "max_div":    mx,
                "mean_div":   mean,
                "median_div": md,
                "std_div":    sd,
                "p_value":        "",
                "spearman_rho":      "",
            }
            for cls in PROX_CLASSES:
                row[f"{cls}_count"] = counts[cls]
                row[f"{cls}_pct"]   = percs[cls]
            writer.writerow(row)

    print(f"✔ Summary (with Spearman’s ρ) at {outp.resolve()}")

if __name__ == "__main__":
    main()
