import argparse
import csv
import sys
from collections import defaultdict
import statistics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Average hunk divergence for each proximity class."
    )
    p.add_argument(
        "--divergence_csv",
        default="../hunk_divergence_v4_bleu/total_hunk_divergence_results.csv",
        help="CSV containing bug_id,hunk_count,divergence "
             "(default: ../hunk_divergence_v4_crystalbleu/total_hunk_divergence_results.csv)",
    )
    p.add_argument(
        "--proximity_csv",
        default="proximity_class.csv",
        help="CSV containing bug_id,proximity_class (default: proximity_class.csv)",
    )
    p.add_argument(
        "--output_csv",
        default="proximity_class_avg_hunk_divergence.csv",
        help="Output CSV path (default: proximity_class_avg_hunk_divergence.csv)",
    )
    return p.parse_args()


def load_divergences(path: str) -> dict[str, float]:
    divergences = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bug = row["bug_id"].strip()
            try:
                divergences[bug] = float(row["divergence"])
            except ValueError:
                print(f"[WARN] Non-numeric divergence for {bug}; skipping.", file=sys.stderr)
    return divergences


def load_proximity_classes(path: str) -> dict[str, str]:
    classes = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            classes[row["bug_id"].strip()] = row["proximity_class"].strip()
    return classes


def compute_averages(divergences: dict[str, float],
                     prox_classes: dict[str, str]
                    ) -> dict[str, float]:
    import statistics
    from collections import defaultdict

    values_by_class: dict[str, list[float]] = defaultdict(list)
    for bug, divergence in divergences.items():
        cls = prox_classes.get(bug)
        if cls is not None:
            values_by_class[cls].append(divergence)

    return {
        cls: statistics.mean(vals) if vals else 0.0
        for cls, vals in values_by_class.items()
    }


def write_output(path: str, averages: dict[str, float]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["proximity_class", "avg_hunk_divergence"])
        for cls, avg in sorted(averages.items()):
            writer.writerow([cls, f"{avg:.4f}"])


def main() -> None:
    args = parse_args()

    divergences = load_divergences(args.divergence_csv)
    prox_classes = load_proximity_classes(args.proximity_csv)
    averages = compute_averages(divergences, prox_classes)

    write_output(args.output_csv, averages)
    print(f"✔ Averages written to {args.output_csv}")


if __name__ == "__main__":
    main()
