#!/usr/bin/env python3
import argparse
import csv
import json

def parse_args():
    parser = argparse.ArgumentParser(description="Count number of hunks per bug from a JSON file.")
    parser.add_argument(
        "input_json",
        nargs='?',
        default="../config/method_multihunk.json",
        help="Path to JSON file (default: ../config/method_multihunk.json)"
    )
    parser.add_argument(
        "output_csv",
        nargs='?',
        default="num_hunks_per_bug.csv",
        help="Output CSV file (default: num_hunks_per_bug.csv)"
    )
    return parser.parse_args()

def count_hunks_per_bug(data):
    rows = []
    for bug_id, entry in data.items():
        hunk_count = len(entry.get("buggy_hunks", {}))
        rows.append({
            "bug_id": bug_id,
            "num_hunks": hunk_count
        })
    return rows

def write_csv(output_path, rows):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["bug_id", "num_hunks"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def main():
    args = parse_args()
    with open(args.input_json, encoding="utf-8") as f:
        data = json.load(f)

    rows = count_hunks_per_bug(data)
    write_csv(args.output_csv, rows)

    print(f"Saved hunk counts for {len(rows)} bugs to {args.output_csv}")

if __name__ == "__main__":
    main()
