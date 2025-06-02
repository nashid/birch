#!/usr/bin/env python3
import json, argparse, re, csv, statistics, math
from itertools import combinations
from pathlib import PurePosixPath
from typing import List

def longest_common_prefix(a: List[str], b: List[str]) -> int:
    depth = 0
    for x, y in zip(a, b):
        if x == y:
            depth += 1
        else:
            break
    return depth

class Hunk:
    __slots__ = ("file", "method", "pkg")
    def __init__(self, file_path: str, method: str, pkg: List[str]):
        self.file = file_path
        self.method = method
        self.pkg = pkg

SIG_RE = re.compile(r"\b(?:public|protected|private)?\s+[\w<>\[\]]+\s+(\w+)\s*\(")

def extract_method(code: str) -> str:
    for ln in code.splitlines():
        if (m := SIG_RE.search(ln.strip())):
            return m.group(1)
    return "<unknown>"

def build_hunks(entry: dict):
    mapping: dict[tuple[str,int,int], str] = {}
    for mid, hlist in entry.get("hunk_mapping", {}).items():
        for m in hlist:
            key = (m["file"], m["start_line"], m["end_line"])
            mapping[key] = mid

    hunks: list[Hunk] = []
    for h in entry.get("buggy_hunks", {}).values():
        f       = h.get("file", "")
        hs      = h.get("start_line", 0)
        he      = h.get("end_line", 0)
        method  = mapping.get((f, hs, he), "<unknown>")

        pkg = list(PurePosixPath(f).parts[1:-1]) if "/" in f else []
        hunks.append(Hunk(f, method, pkg))

    return hunks


def SF(H):
    return len({h.file for h in H}) == 1

def SM(H):
    return len({h.method for h in H}) == 1

def SP(H):
    return len({tuple(h.pkg) for h in H}) == 1

def LCP_min(H):
    return 0 if len(H) < 2 else min(longest_common_prefix(a.pkg, b.pkg) for a, b in combinations(H, 2))


def classify(H, cutoff):
    if SF(H):
        return "Nucleus" if SM(H) else "Cluster"
    if SP(H):
        return "Orbit"
    return "Sprawl" if LCP_min(H) > cutoff else "Fragment"


def main():
    ap = argparse.ArgumentParser(description="Spatial proximity classification")
    ap.add_argument("input_json")
    ap.add_argument("output_csv")
    ap.add_argument("--threshold", type=int, help="Override LCP cutoff for Sprawl")
    args = ap.parse_args()

    data = json.load(open(args.input_json, encoding="utf-8"))

    pkg_depths = []
    for entry in data.values():
        H = build_hunks(entry)
        pkg_depths.extend(len(h.pkg) for h in H)

    median_depth = statistics.median(pkg_depths) if pkg_depths else 0
    default_cutoff = math.floor(median_depth / 2)
    cutoff = args.threshold if args.threshold is not None else default_cutoff

    print(f"Median package depth = {median_depth}; cutoff = {cutoff}")

    rows = [("bug_id", "proximity_class")]
    for bug_id, entry in data.items():
        rows.append((bug_id, classify(build_hunks(entry), cutoff)))

    with open(args.output_csv, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    print(f"Wrote {len(rows)-1} rows → {args.output_csv}")

if __name__ == "__main__":
    main()
