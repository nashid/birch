#!/usr/bin/env python3
import argparse
import csv
import json
import statistics
import math
import itertools
from pathlib import Path
from collections import defaultdict

from scipy.stats import mannwhitneyu, spearmanr

top5_substrs = [
    "mistral-large-2407",
    "llama3-3-70b",
    "gemini-2.5-flash",
    "nova-pro",
    "o4-mini",
]

total_counts = {
    "Nucleus": 59,
    "Cluster": 185,
    "Orbit": 67,
    "Sprawl": 50,
    "Fragment": 11,
}
PROX_CLASSES = list(total_counts.keys())

def parse_args():
    p = argparse.ArgumentParser(
        description="Summarize hunk divergence and proximity for top-5 LLMs,"
                    " including Mann–Whitney U and Spearman correlation."
    )
    p.add_argument("--passed_json",   default="passed_bugs.json",
                   help="Path to passed_bugs.json")
    p.add_argument("--divergence_csv",
                   default="../../hunk_divergence_v4_bleu/total_hunk_divergence_results.csv",
                   help="CSV with bug_id,divergence")
    p.add_argument("--proximity_csv",
                   default="../../proximity_class/proximity_class.csv",
                   help="CSV with bug_id,proximity_class")
    p.add_argument("--output_csv",    default="top_5_summary.csv",
                   help="Output CSV path")
    return p.parse_args()

def load_passed(path):
    data = json.load(open(path, encoding='utf-8'))
    passed = {m.lower(): set(v.get('passed', [])) for m, v in data.items()}
    result = {}
    for sub in top5_substrs:
        bugs = set()
        for m, s in passed.items():
            if sub in m:
                bugs |= s
        # normalize bug IDs to use dashes
        result[sub] = {b.replace("_","-") for b in bugs}
    return result

def load_divergence(path):
    dmap = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            bug = row['bug_id'].strip().replace('_','-')
            try:
                dmap[bug] = float(row['divergence'])
            except ValueError:
                pass
    return dmap

def load_proximity(path):
    pmap = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            bug = row['bug_id'].strip().replace('_','-')
            pmap[bug] = row['proximity_class'].strip()
    return pmap

def summarize(bugs, divergence_map, proximity_map):
    vals = [divergence_map[b] for b in bugs if b in divergence_map]
    if vals:
        mn    = round(min(vals), 4)
        mx    = round(max(vals), 4)
        mean  = round(statistics.mean(vals), 4)
        md    = round(statistics.median(vals), 4)
        sd    = round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0
    else:
        mn = mx = mean = md = sd = 0.0

    counts  = {c: 0 for c in PROX_CLASSES}
    for b in bugs:
        cls = proximity_map.get(b)
        if cls in counts:
            counts[cls] += 1
    percents = {
        c: round(counts[c] / total_counts[c] * 100, 2)
        for c in PROX_CLASSES
    }

    return mn, mx, mean, md, sd, counts, percents

def main():
    args = parse_args()
    passed_map       = load_passed(args.passed_json)
    divergence_map   = load_divergence(args.divergence_csv)
    proximity_map    = load_proximity(args.proximity_csv)
    all_bugs         = set(divergence_map.keys())

    # Precompute Mann–Whitney p-values and Spearman stats
    mw_pvals   = {}
    spear_stats = {}
    for sub, solved in passed_map.items():
        # Mann–Whitney U: solved vs unsolved divergence
        sol_vals = [divergence_map[b] for b in solved if b in divergence_map]
        uns_vals = [divergence_map[b] for b in (all_bugs - solved) if b in divergence_map]
        if sol_vals and uns_vals:
            _, p_mw = mannwhitneyu(sol_vals, uns_vals, alternative='two-sided')
        else:
            p_mw = None
        mw_pvals[sub] = p_mw

        # Spearman: divergence vs. binary success over all bugs
        divs, succ = [], []
        for b in sorted(all_bugs):
            if b in divergence_map:
                divs.append(divergence_map[b])
                succ.append(1 if b in solved else 0)
        if len(divs) > 1 and len(set(succ)) > 1:
            rho, p_sp = spearmanr(divs, succ)
        else:
            rho, p_sp = None, None
        spear_stats[sub] = (rho, p_sp)

    # Prepare CSV
    fieldnames = [
        'model','status',
        'min_div','max_div','mean_div','median_div','std_div',
        'mw_p_value','spearman_rho'
    ] + [f'{c}_{suffix}' for c in PROX_CLASSES for suffix in ('count','pct')]

    with open(args.output_csv, 'w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for sub, solved in passed_map.items():
            # format MW p-value
            p_mw = mw_pvals.get(sub)
            p_mw_str = f"{p_mw:.2e}" if isinstance(p_mw, float) else ''
            # format Spearman stats
            rho, p_sp = spear_stats.get(sub, (None,None))
            rho_str  = f"{rho:.2f}" if isinstance(rho, float) else ''
            p_sp_str = f"{p_sp:.2e}" if isinstance(p_sp, float) else ''

            # Solved row
            mn, mx, mean, md, sd, counts, percs = summarize(
                solved, divergence_map, proximity_map
            )
            row = {
                'model': sub,
                'status': 'solved',
                'min_div': mn,
                'max_div': mx,
                'mean_div': mean,
                'median_div': md,
                'std_div': sd,
                'mw_p_value': p_mw_str,
                'spearman_rho': rho_str,
            }
            for c in PROX_CLASSES:
                row[f'{c}_count'] = counts[c]
                row[f'{c}_pct']   = percs[c]
            writer.writerow(row)

            # Unsolved row (leave stats blank)
            unsolved = all_bugs - solved
            mn, mx, mean, md, sd, counts, percs = summarize(
                unsolved, divergence_map, proximity_map
            )
            row = {
                'model': sub,
                'status': 'unsolved',
                'min_div': mn,
                'max_div': mx,
                'mean_div': mean,
                'median_div': md,
                'std_div': sd,
                'mw_p_value': '',
                'spearman_rho': '',
            }
            for c in PROX_CLASSES:
                row[f'{c}_count'] = counts[c]
                row[f'{c}_pct']   = percs[c]
            writer.writerow(row)

    print(f'✔ Wrote summary (with MW and Spearman) to {args.output_csv}')

if __name__=='__main__':
    main()
