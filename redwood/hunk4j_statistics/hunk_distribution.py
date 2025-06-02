#!/usr/bin/env python3
import json
import argparse
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Markdown table for multi-hunk bug distribution."
    )
    parser.add_argument(
        "json_file",
        help="Path to JSON file of multi-hunk entries"
    )
    return parser.parse_args()

# Active bugs per project from Defects4J 2.0.1
ACTIVE_BUGS = {
    "Chart": 26,
    "Cli": 39,
    "Closure": 174,
    "Codec": 18,
    "Collections": 4,
    "Compress": 47,
    "Csv": 16,
    "Gson": 18,
    "JacksonCore": 26,
    "JacksonDatabind": 112,
    "JacksonXml": 6,
    "Jsoup": 93,
    "JxPath": 22,
    "Lang": 64,
    "Math": 106,
    "Mockito": 38,
    "Time": 26,
}

PROJECT_ORDER = [
    "Chart", "Cli", "Closure", "Codec", "Collections", "Compress",
    "Csv", "Gson", "JacksonCore", "JacksonDatabind", "JacksonXml",
    "Jsoup", "JxPath", "Lang", "Math", "Mockito", "Time"
]

def load_entries(path):
    with open(path) as f:
        return json.load(f)


def compute_stats(entries):
    stats = defaultdict(lambda: {"multi": 0, "hunks": 0})
    for key, entry in entries.items():
        project = key.split("_")[0]
        stats[project]["multi"] += 1
        buggy_hunks = entry.get("buggy_hunks", {})
        stats[project]["hunks"] += len(buggy_hunks)
    return stats


def emit_markdown_table(stats):
    print("| Project | Total Multi-Hunk | % Multi-Hunk | Avg. Hunks per Bug |")
    print("|---------|------------------:|-------------:|-------------------:|")

    total_multi = 0
    total_hunks = 0

    for proj in PROJECT_ORDER:
        multi = stats.get(proj, {}).get("multi", 0)
        hunks = stats.get(proj, {}).get("hunks", 0)
        active = ACTIVE_BUGS.get(proj, 0)
        pct = (multi / active * 100) if active else 0
        avg = (hunks / multi) if multi else 0
        total_multi += multi
        total_hunks += hunks
        print(f"| {proj} | {multi} | {pct:.1f}% | {avg:.1f} |")

    total_active = sum(ACTIVE_BUGS.values())
    total_pct = (total_multi / total_active * 100) if total_active else 0
    total_avg = (total_hunks / total_multi) if total_multi else 0
    print("| **Total** | **{}** | **{:.1f}%** | **{:.1f}** |".format(
        total_multi, total_pct, total_avg
    ))


def main():
    args = parse_args()
    entries = load_entries(args.json_file)
    stats = compute_stats(entries)
    emit_markdown_table(stats)

if __name__ == '__main__':
    main()