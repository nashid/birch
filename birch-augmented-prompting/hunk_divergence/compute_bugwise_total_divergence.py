import argparse
import csv
from collections import defaultdict
from pathlib import Path

def parse_args():
    ap = argparse.ArgumentParser(description="Aggregate hunk divergence per bug")
    ap.add_argument("--pairwise",
                    default="pairwise_hunk_divergence_results.csv",
                    help="Pair-wise distance table")
    ap.add_argument("--total",
                    default="total_hunk_divergence_results.csv",
                    help="Override file with bug_id,hunk_count,divergence")
    ap.add_argument("--out",
                    default="bugwise_average_divergence.csv",
                    help="Output CSV")
    return ap.parse_args()

def load_pairwise(path: Path):
    """
    Returns dict[bug_id] -> accumulator with sums and pair count.
    """
    acc = defaultdict(lambda: {
        "lexical": 0.0,
        "ast": 0.0,
        "file": 0.0,
        "pairs": 0
    })

    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            bid = row["bug_id"]
            acc[bid]["lexical"] += float(row["lexical_distance"])
            acc[bid]["ast"]     += float(row["ast_distance"])
            acc[bid]["file"]    += float(row["package_distance"])
            acc[bid]["pairs"]   += 1
    return acc

def load_total_divergence(path: Path):
    over = {}
    if not path.exists():
        return over
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            over[r["bug_id"]] = (int(r["hunk_count"]), float(r["divergence"]))
    return over

def load_total_divergence(path: Path):
    """
    Returns dict[bug_id] -> (hunk_count, divergence)
    """
    overrides = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            overrides[row["bug_id"]] = (
                int(row["hunk_count"]),
                float(row["divergence"])
            )
    return overrides

def main():
    args = parse_args()

    pairwise = load_pairwise(Path(args.pairwise))
    overrides = load_total_divergence(Path(args.total))

    out_f = Path(args.out)
    with out_f.open("w", newline="") as f_out:
        w = csv.writer(f_out)
        w.writerow([
            "bug_id", "hunk_count", "pair_count",
            "avg_lexical", "avg_ast", "avg_file", "avg_divergence"
        ])

        for bug_id in sorted(pairwise):
            sums = pairwise[bug_id]
            pair_cnt = sums["pairs"]

            n = int((1 + (1 + 8*pair_cnt) ** 0.5) / 2) if pair_cnt else 1
            denom = n*(n-1)/2 if n > 1 else 1

            avg_lex = sums["lexical"] / denom
            avg_ast = sums["ast"]     / denom
            avg_file= sums["file"]    / denom
            avg_div = None  

            if bug_id in overrides:
                n_override, div_override = overrides[bug_id]
                avg_div = div_override
                n = n_override
            else:
                avg_div = (avg_lex + avg_ast + avg_file) / 3.0

            w.writerow([
                bug_id, n, pair_cnt,
                round(avg_lex, 6),
                round(avg_ast, 6),
                round(avg_file, 6),
                round(avg_div, 6)
            ])

    print(f"[done] Saved {out_f}")

if __name__ == "__main__":
    main()
