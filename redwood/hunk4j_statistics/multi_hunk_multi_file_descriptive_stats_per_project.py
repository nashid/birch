#!/usr/bin/env python3
import json
import argparse
import csv
import statistics
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(description="Per-project descriptive statistics for multi-file multi-hunk bugs → CSV")
    parser.add_argument(
        "input_json",
        nargs='?',
        default="../config/method_multihunk.json",
        help="Path to JSON input (default: ../config/method_multihunk.json)"
    )
    parser.add_argument(
        "output_csv",
        nargs='?',
        default="multi_file_multi_hunk_descriptive_statistics.csv",
        help="Output CSV file (default: multi_file_multi_hunk_descriptive_statistics.csv)"
    )
    return parser.parse_args()

def compute_project_stats(data):
    project_data = defaultdict(lambda: {"hunks": [], "files": []})
    all_files = []

    for bug_id, entry in data.items():
        hunk_count = len(entry.get("buggy_hunks", {}))
        file_count = len(entry.get("buggy_files", {}))

        if hunk_count > 1 and file_count > 1:
            project = bug_id.split("_")[0]
            project_data[project]["hunks"].append(hunk_count)
            project_data[project]["files"].append(file_count)
            all_files.append(file_count)

    project_stats = []
    for project, counts in project_data.items():
        f = counts["files"]
        if f:
            project_stats.append({
                "project": project,
                "bugs": len(f),
                "files_min": min(f),
                "files_median": f"{statistics.median(f):.2f}",
                "files_mean": f"{statistics.mean(f):.2f}",
                "files_max": max(f)
            })

    global_stats = {
        "total_bugs": len(all_files),
        "global_min": min(all_files),
        "global_median": f"{statistics.median(all_files):.2f}",
        "global_mean": f"{statistics.mean(all_files):.2f}",
        "global_max": max(all_files),
    }

    return project_stats, global_stats

def write_csv(path, stats):
    fields = [
        "project", "bugs",
        "files_min", "files_median", "files_mean", "files_max"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(stats)

def main():
    args = parse_args()
    with open(args.input_json, encoding="utf-8") as f:
        data = json.load(f)
    stats, global_stats = compute_project_stats(data)
    write_csv(args.output_csv, stats)

    print(f"Descriptive statistics written to {args.output_csv}")
    print("\n=== Global File Statistics Across All Bugs ===")
    print(f"Total Bugs: {global_stats['total_bugs']}")
    print(f"Min Files: {global_stats['global_min']}")
    print(f"Median Files: {global_stats['global_median']}")
    print(f"Mean Files: {global_stats['global_mean']}")
    print(f"Max Files: {global_stats['global_max']}")

if __name__ == "__main__":
    main()
