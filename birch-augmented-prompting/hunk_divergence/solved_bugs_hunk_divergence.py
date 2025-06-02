import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict

RQ_FOLDERS = ["rq2", "rq3", "rq4", "rq5"]

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="For every model run, sum the divergence of the bugs it fixed."
    )
    p.add_argument(
        "--results_dir", default="../results",
        help="Directory containing rq2 … rq5 sub-folders (default: ../results)",
    )
    p.add_argument(
        "--divergence_csv", default="total_hunk_divergence_results.csv",
        help="CSV with bug_id,hunk_count,divergence (default: total_hunk_divergence_results.csv)",
    )
    p.add_argument(
        "--output_csv", default="model_average_divergence.csv",
        help="Output CSV path (default: model_divergence_totals.csv)",
    )
    return p.parse_args()

def load_divergence_map(csv_path: Path) -> dict[str, float]:
    """Return bug_id → divergence."""
    div_map: dict[str, float] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bug = row["bug_id"].strip().replace("_", "-") 
            try:
                div_map[bug] = float(row["divergence"])
            except ValueError:
                print(f"[WARN] Non-numeric divergence for {bug} – skipping.")
    return div_map

def process_model(
    rq_name: str,
    model_name: str,
    passed_bugs: list[str],
    divergence: dict[str, float],
) -> dict[str, float]:
    total_div = 0.0
    bug_count = 0

    for bug in passed_bugs:
        d = divergence.get(bug)
        if d is None:
            continue
        total_div += d
        bug_count += 1

    avg_div = total_div / bug_count if bug_count else 0.0

    return {
        "model": f"{rq_name}/{model_name}",
        "total_bugs": bug_count,
        "total_divergence": round(total_div, 4),
        "avg_divergence": round(avg_div, 4),
    }

def main() -> None:
    args = parse_args()
    root = Path(args.results_dir).resolve()
    divergence_map = load_divergence_map(Path(args.divergence_csv).resolve())

    rows: list[dict[str, float]] = []

    for rq in RQ_FOLDERS:
        json_path = root / rq / "passed_bugs.json"
        if not json_path.is_file():
            print(f"[WARN] {json_path} not found – skipping.")
            continue

        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)

        for model_name, entry in data.items():
            passed = entry.get("passed", [])
            rows.append(process_model(rq, model_name, passed, divergence_map))

    rows.sort(key=lambda r: r["model"])

    fieldnames = ["model", "total_bugs", "total_divergence", "avg_divergence"]
    with Path(args.output_csv).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✔ Divergence totals written to {args.output_csv}")

if __name__ == "__main__":
    main()
