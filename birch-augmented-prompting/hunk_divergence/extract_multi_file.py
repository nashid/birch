import argparse
import json
import pandas as pd
from pathlib import Path


def parse_args():
    ap = argparse.ArgumentParser(description="Extract multi-file bugs")
    ap.add_argument("--div_csv", default="bugwise_average_divergence.csv",
                    help="CSV with bug_id,…,avg_divergence")
    ap.add_argument("--meta_json", default="../config/method_multihunk.json",
                    help="JSON file that contains hunk_type per bug")
    ap.add_argument("--out_csv", default="multifile_bugwise_average_divergence.csv",
                    help="Where to save the filtered table")
    return ap.parse_args()


def collect_multi_file_bug_ids(meta_path: Path) -> set[str]:
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    multi_ids = {bug_id
                 for bug_id, entry in meta.items()
                 if entry.get("hunk_type", "").startswith("multi_file_")}
    return multi_ids


def main():
    args = parse_args()

    mf_ids = collect_multi_file_bug_ids(Path(args.meta_json))
    print(f"[info] multi-file bugs found in JSON: {len(mf_ids)}")

    df = pd.read_csv(args.div_csv)

    df_mf = df[df["bug_id"].isin(mf_ids)].reset_index(drop=True)
    print(f"[info] rows kept in CSV: {len(df_mf)}")

    df_mf.to_csv(args.out_csv, index=False)
    print(f"[done] written to {args.out_csv}")


if __name__ == "__main__":
    main()
