#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict


RQ_FOLDERS   = ["rq2", "rq3", "rq4", "rq5"]
PROX_CLASSES = ["Nucleus", "Cluster", "Orbit", "Sprawl", "Fragment"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compute per-class pass percentages and counts for each model."
    )
    p.add_argument(
        "--results_dir",
        default="../results",
        help="Directory containing rq2 … rq5 sub-folders (default: ../results)",
    )
    p.add_argument(
        "--proximity_csv",
        default="proximity_class.csv",
        help="CSV with bug_id,proximity_class (default: proximity_class.csv)",
    )
    p.add_argument(
        "--output_csv",
        default="model_proximity_pass_percentages.csv",
        help="Output CSV path (default: model_proximity_pass_percentages.csv)",
    )
    return p.parse_args()


def load_proximity_map(csv_path: Path) -> tuple[dict[str, str], dict[str, int]]:
    """Returns (bug→class mapping, totals per class)."""
    bug2class: dict[str, str] = {}
    totals = defaultdict(int)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bug = row["bug_id"].strip().replace("_", "-")
            cls = row["proximity_class"].strip()
            bug2class[bug] = cls
            totals[cls] += 1

    for cls in PROX_CLASSES:
        totals.setdefault(cls, 0)

    return bug2class, totals


def process_model(
    rq_name: str,
    model_name: str,
    passed_bugs: list[str],
    bug2class: dict[str, str],
    totals: dict[str, int],
) -> dict[str, float]:
    counts = defaultdict(int)
    for bug in passed_bugs:
        cls = bug2class.get(bug)
        if cls:
            counts[cls] += 1

    # build the row
    row: dict[str, float] = {"model": f"{rq_name}/{model_name}"}
    for cls in PROX_CLASSES:
        denom = totals[cls]
        pct   = (counts[cls] / denom * 100) if denom else 0.0
        row[cls]        = round(pct, 2)      # percentage column
        row[f"{cls}_abs"] = counts[cls]      # absolute count column
    return row


def main() -> None:
    args = parse_args()
    results_root = Path(args.results_dir).resolve()
    bug2class, totals = load_proximity_map(Path(args.proximity_csv).resolve())

    rows: list[dict[str, float]] = []

    for rq in RQ_FOLDERS:
        json_path = results_root / rq / "passed_bugs.json"
        if not json_path.is_file():
            print(f"[WARN] {json_path} not found, skipping.")
            continue

        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)

        for model_name, entry in data.items():
            passed_bugs = entry.get("passed", [])
            rows.append(
                process_model(rq, model_name, passed_bugs, bug2class, totals)
            )

    pct_cols  = PROX_CLASSES
    abs_cols  = [f"{cls}_abs" for cls in PROX_CLASSES]
    fieldnames = ["model"] + pct_cols + abs_cols

    with Path(args.output_csv).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted(rows, key=lambda x: x["model"]):
            writer.writerow(r)

    print(f"✔ Results with percentages and absolute counts written to {args.output_csv}")


if __name__ == "__main__":
    main()
