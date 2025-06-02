#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path
from collections import defaultdict

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarise unique solves by each key model and by all five.")
    p.add_argument("--solved_json",   default="../results/rq2/passed_bugs.json",
                   help="Path to rq2/passed_bugs.json")
    p.add_argument("--divergence_csv", default="../hunk_divergence_v4_bleu/total_hunk_divergence_results.csv",
                   help="CSV with bug_id,hunk_count,divergence")
    p.add_argument("--proximity_csv",  default="../proximity_class/proximity_class.csv",
                   help="CSV with bug_id,proximity_class")
    p.add_argument("--out_dir",        default=".", help="Output folder")
    return p.parse_args()

KEY_SUBSTR = {
    "mistral-large-2407",  # llama-3.2
    "llama3-3-70b",        # llama-3.3
    "gemini-2.5-flash",    # gemini 2.5 flash
    "nova-pro",            # gpt-4.1
    "o4-mini",             # o4-mini
}

def load_divergence(path: Path) -> dict[str, float]:
    mapping = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bug = row["bug_id"].strip().replace("_", "-")
            try:
                mapping[bug] = float(row["divergence"])
            except ValueError:
                pass
    return mapping

def load_proximity(path: Path) -> dict[str, str]:
    mapping = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bug = row["bug_id"].strip().replace("_", "-")
            mapping[bug] = row["proximity_class"].strip()
    return mapping

def write_csv(path: Path, bugs: set[str],
              divergence: dict[str, float],
              proximity: dict[str, str]) -> None:
    rows = []
    prox_counts = defaultdict(int)
    div_sum = 0.0
    div_cnt = 0

    for bug in sorted(bugs):
        div = divergence.get(bug)
        prox = proximity.get(bug, "UNKNOWN")
        if div is not None:
            div_sum += div
            div_cnt += 1
        prox_counts[prox] += 1
        rows.append({
            "bug_id": bug,
            "divergence": f"{div:.4f}" if div is not None else "",
            "proximity_class": prox,
        })

    avg_div = div_sum / div_cnt if div_cnt else 0.0
    total_row = {
        "bug_id": "TOTAL",
        "divergence": f"{avg_div:.4f}",
        "proximity_class": "; ".join(f"{k}:{v}" for k, v in prox_counts.items()),
    }
    rows.append(total_row)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["bug_id", "divergence", "proximity_class"])
        w.writeheader()
        w.writerows(rows)
    print(f"✔ Wrote {len(rows)-1} bug rows (+ TOTAL) to {path.name}")

def sanitize(name: str) -> str:
    # replace non-alphanum with underscore
    return re.sub(r'[^0-9A-Za-z]+', '_', name)

def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    divergence = load_divergence(Path(args.divergence_csv))
    proximity  = load_proximity(Path(args.proximity_csv))

    with Path(args.solved_json).open(encoding="utf-8") as f:
        raw = json.load(f)

    solved = {m.lower(): set(entry.get("passed", [])) for m, entry in raw.items()}

    # build per-key-model sets
    key_sets: dict[str, set[str]] = {sub: set() for sub in KEY_SUBSTR}
    for model_name, bugs in solved.items():
        for sub in KEY_SUBSTR:
            if sub in model_name:
                key_sets[sub].update(bugs)

    # compute and write uniques for each key model
    for sub, bugset in key_sets.items():
        others = set().union(*(key_sets[o] for o in KEY_SUBSTR if o != sub))
        unique = bugset - others
        fname = f"only_{sanitize(sub)}.csv"
        write_csv(out_dir / fname, unique, divergence, proximity)

    # compute and write intersection of all five
    all_five = set.intersection(*(s for s in key_sets.values()))
    write_csv(out_dir / "all_five_models.csv", all_five, divergence, proximity)

if __name__ == "__main__":
    main()
