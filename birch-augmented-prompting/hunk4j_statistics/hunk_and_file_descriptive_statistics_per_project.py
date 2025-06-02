#!/usr/bin/env python3
import argparse
import csv
import json
import statistics
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute per-project hunk and file statistics for multi-hunk bugs."
    )
    parser.add_argument(
        "input_json",
        nargs="?",
        default="../config/method_multihunk.json",
        help="Path to JSON file (default: ../config/method_multihunk.json)"
    )
    parser.add_argument(
        "output_csv",
        nargs="?",
        default="hunk_file_statistics_per_project.csv",
        help="Output CSV file (default: hunk_file_statistics_per_project.csv)"
    )
    return parser.parse_args()

def compute_stats(data):
    project_data = defaultdict(lambda: {"hunks": [], "files": []})

    for bug_id, entry in data.items():
        project = bug_id.split("_")[0]
        hunk_count = len(entry.get("buggy_hunks", {}))
        file_count = len(entry.get("buggy_files", {}))

        project_data[project]["hunks"].append(hunk_count)
        project_data[project]["files"].append(file_count)

    rows = []
    all_hunks, all_files = [], []
    total_bugs = 0

    for project, counts in sorted(project_data.items()):
        hunks = counts["hunks"]
        files = counts["files"]
        if not hunks:
            continue

        rows.append({
            "project": project,
            "bugs": len(hunks),
            "hunks_min": min(hunks),
            "hunks_median": statistics.median(hunks),
            "hunks_mean": round(statistics.mean(hunks), 2),
            "hunks_max": max(hunks),
            "files_min": min(files),
            "files_median": statistics.median(files),
            "files_mean": round(statistics.mean(files), 2),
            "files_max": max(files)
        })

        all_hunks.extend(hunks)
        all_files.extend(files)
        total_bugs += len(hunks)

    if all_hunks:                      
        rows.append({
            "project": "TOTAL",
            "bugs": total_bugs,
            "hunks_min": min(all_hunks),
            "hunks_median": statistics.median(all_hunks),
            "hunks_mean": round(statistics.mean(all_hunks), 2),
            "hunks_max": max(all_hunks),
            "files_min": min(all_files),
            "files_median": statistics.median(all_files),
            "files_mean": round(statistics.mean(all_files), 2),
            "files_max": max(all_files)
        })

    return rows

def write_csv(path, rows):
    fieldnames = [
        "project", "bugs",
        "hunks_min", "hunks_median", "hunks_mean", "hunks_max",
        "files_min", "files_median", "files_mean", "files_max"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def main():
    args = parse_args()
    with open(args.input_json, encoding="utf-8") as f:
        data = json.load(f)

    stats = compute_stats(data)
    write_csv(args.output_csv, stats)
    print(f"Wrote per-project hunk + file stats (plus TOTAL row) to {args.output_csv}")

if __name__ == "__main__":
    main()
