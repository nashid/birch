import json, argparse, csv, statistics


def main():
    ap = argparse.ArgumentParser(description="Multi-file multi-hunk stats → CSV")
    ap.add_argument("input_json")
    ap.add_argument("output_csv")
    args = ap.parse_args()

    data = json.load(open(args.input_json, encoding="utf-8"))
    rows = [("bug_id", "hunk_count", "file_count")]
    file_counts = []
    hunk_counts = []

    for bug_id, entry in data.items():
        hunk_count = len(entry.get("buggy_hunks", {}))
        file_count = len(entry.get("buggy_files", {}))
        if hunk_count > 1 and file_count > 1:
            rows.append((bug_id, hunk_count, file_count))
            file_counts.append(file_count)
            hunk_counts.append(hunk_count)

    with open(args.output_csv, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)

    if file_counts:
        print(f"Qualifying bugs: {len(hunk_counts)}")
        print(f"hunks per bug  →  min={min(hunk_counts)}, max={max(hunk_counts)}, "
              f"mean={statistics.mean(hunk_counts):.2f}, median={statistics.median(hunk_counts)}")
        print(f"files per bug  →  min={min(file_counts)}, max={max(file_counts)}, "
              f"mean={statistics.mean(file_counts):.2f}, median={statistics.median(file_counts)}")
    else:
        print("No multi-file multi-hunk bugs found.")
    print(f"CSV written to {args.output_csv}")

if __name__ == "__main__":
    main()