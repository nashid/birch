#!/usr/bin/env python3
import argparse
import csv
import json
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Extract per-hunk info from JSON and save to CSV.")
    parser.add_argument(
        "input_json",
        nargs='?',
        default="../config/method_multihunk.json",
        help="Path to JSON file (default: ../config/method_multihunk.json)"
    )
    parser.add_argument(
        "output_csv",
        nargs='?',
        default="hunk_level_data.csv",
        help="Output CSV file (default: hunk_level_data.csv)"
    )
    return parser.parse_args()

def extract_hunks_from_json(json_data):
    all_hunks = []
    for bug_id, entry in json_data.items():
        hunk_list = entry.get("buggy_hunks", {})
        for hunk_index, (file_path, _) in enumerate(hunk_list.items()):
            all_hunks.append({
                "bug_id": bug_id,
                "file_path": file_path,
                "hunk_index": hunk_index
            })
    return all_hunks

def write_csv(output_path, all_hunks):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["bug_id", "file_path", "hunk_index"])
        writer.writeheader()
        for row in all_hunks:
            writer.writerow(row)

def main():
    args = parse_args()
    with open(args.input_json, encoding="utf-8") as f:
        data = json.load(f)

    all_hunks = extract_hunks_from_json(data)
    write_csv(args.output_csv, all_hunks)

    print(f"Extracted {len(all_hunks)} hunks from JSON.")
    print(f"Saved to {args.output_csv}")

if __name__ == "__main__":
    main()
