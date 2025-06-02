from __future__ import annotations
import argparse, csv, json, itertools
from pathlib import Path
from typing import Dict, List, Optional, Tuple      # ← added Tuple

import difflib
import javalang


_parent_map: Dict[javalang.ast.Node, javalang.ast.Node] = {}

# ----------------------------------------------------------------------
#  Utilities for AST distances
# ----------------------------------------------------------------------
def annotate_parents(node: javalang.ast.Node,
                     parent: Optional[javalang.ast.Node] = None) -> None:
    if not isinstance(node, javalang.ast.Node):
        return
    if parent is not None:
        _parent_map[node] = parent
    for child in node.children:
        if isinstance(child, list):
            for c in child:
                annotate_parents(c, node)
        else:
            annotate_parents(child, node)

def _node_depth(n: Optional[javalang.ast.Node]) -> int:
    d = 0
    while n in _parent_map:
        d += 1
        n = _parent_map[n]
    return d

def _lca(u: Optional[javalang.ast.Node],
         v: Optional[javalang.ast.Node]) -> Optional[javalang.ast.Node]:
    seen = set()
    x = u
    while x is not None:
        seen.add(x)
        x = _parent_map.get(x)
    y = v
    while y is not None and y not in seen:
        y = _parent_map.get(y)
    return y

def ASTNodeDistance(u: Optional[javalang.ast.Node],
                    v: Optional[javalang.ast.Node]) -> int:
    if u is None or v is None:
        return 0
    du = _node_depth(u)
    dv = _node_depth(v)
    w  = _lca(u, v)
    dw = _node_depth(w) if w is not None else 0
    return du + dv - 2 * dw

def collect_nodes(root: Optional[javalang.ast.Node]) -> List[javalang.ast.Node]:
    if root is None:
        return []
    return [n for _, n in root]

def subtree_diameter(root: Optional[javalang.ast.Node]) -> int:
    nodes = collect_nodes(root)
    if len(nodes) < 2:
        return 1
    diam = 0
    for u, v in itertools.combinations(nodes, 2):
        diam = max(diam, ASTNodeDistance(u, v))
    return diam or 1

# ----------------------------------------------------------------------
#  Package helpers
# ----------------------------------------------------------------------
def PackageDistance(pkg_i: str, pkg_j: str) -> int:
    seg_i = [s for s in pkg_i.split(".") if s]
    seg_j = [s for s in pkg_j.split(".") if s]
    common = 0
    for a, b in zip(seg_i, seg_j):
        if a == b:
            common += 1
        else:
            break
    return (len(seg_i) - common) + (len(seg_j) - common)

def extract_package(lines: List[str], file_path: Path) -> str:
    for ln in lines[:50]:
        ln = ln.strip()
        if ln.startswith("package "):
            return ln[len("package "):].rstrip(";").strip()
    # fallback: derive from path
    parts = list(file_path.with_suffix("").parts)
    if "src" in parts:
        parts = parts[parts.index("src") + 1 : -1]
    else:
        parts = parts[:-1]
    return ".".join(parts)

# ----------------------------------------------------------------------
#  AST construction
# ----------------------------------------------------------------------
def build_ast_tree(src: str) -> Optional[javalang.ast.Node]:
    try:
        return javalang.parse.parse(src)
    except Exception:
        return None

# ----------------------------------------------------------------------
#  Hunk extraction
# ----------------------------------------------------------------------
def make_hunks_for_bug(bug_entry: Dict, checkout_root: Path) -> List[Dict]:
    hunks: List[Dict] = []
    file_tree_map: Dict[str, Optional[javalang.ast.Node]] = {} 
    for h in bug_entry.get("buggy_hunks", {}).values():
        file_rel, start, end = h["file"], h["start_line"], h["end_line"]
        fp = checkout_root / file_rel
        if not fp.exists():
            alt = checkout_root.joinpath(*file_rel.split("/")[1:])
            fp = alt if alt.exists() else None
        if not fp:
            hunks.append(dict(file="MISSING_FILE", pkg="", ast_tree=None, code=""))
            continue

        src_lines = fp.read_text(errors="ignore").splitlines()
        pkg  = extract_package(src_lines, fp)
        tree = build_ast_tree("\n".join(src_lines))
        file_tree_map[str(fp)] = tree
        if tree:
            annotate_parents(tree)

        # pick the LCA of all nodes whose positions fall in [start, end]
        subtree_root = tree
        if tree:
            buggy_nodes: List[javalang.ast.Node] = []
            for _, node in tree:
                pos = getattr(node, "position", None)
                if pos and start <= pos[0] <= end:
                    buggy_nodes.append(node)
            if buggy_nodes:
                root = buggy_nodes[0]
                for n in buggy_nodes[1:]:
                    root = _lca(root, n)
                subtree_root = root

        hunks.append({
            "file": str(fp),
            "pkg":  pkg,
            "ast_tree": subtree_root,
            "code": "\n".join(src_lines[start - 1 : end]),
        })
    return hunks, file_tree_map

# ----------------------------------------------------------------------
#  Repo-wide max package distance cache
# ----------------------------------------------------------------------
_pkg_cache: Dict[Path, int] = {}

_IGNORE_DIR_TOKENS = {"src", "main", "java", "test", "resources"}

def _logical_package(path: Path) -> List[str]:
    parts = list(path.with_suffix("").parts)[:-1]  # drop file name
    return [p for p in parts if p not in _IGNORE_DIR_TOKENS]

def _dir_distance(p1: List[str], p2: List[str]) -> int:
    common = 0
    for a, b in zip(p1, p2):
        if a == b:
            common += 1
        else:
            break
    return (len(p1) - common) + (len(p2) - common)

def max_package_distance_for_repo(root: Path) -> int:
    if root in _pkg_cache:
        return _pkg_cache[root]

    # 1. collect logical package vectors for every *.java file
    pkgs: List[List[str]] = []
    for java in root.rglob("*.java"):
        try:
            # keep every file; ignore undecodable bytes
            java.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass  # still include the path; the package comes from the path itself
        pkgs.append(_logical_package(java))

    # 2. compute pairwise max distance
    best = 0
    for a, b in itertools.combinations(pkgs, 2):
        best = max(best, _dir_distance(a, b))

    # 3. store ≥1 so later division never zero-divides
    _pkg_cache[root] = best or 1
    return _pkg_cache[root]

# ----------------------------------------------------------------------
#  Divergence computation
# ----------------------------------------------------------------------
def compute_metrics_for_bug(
    hunks: List[Dict],
    file_tree_map,
    max_pkg: int
) -> Tuple[float, List[List]]:
    n = len(hunks)
    if n < 2:
        return 0.0, []

    MaxASTDist: Dict[str, int] = {}
    hunks_by_file: Dict[str, List[int]] = {}
    for idx, h in enumerate(hunks):
        hunks_by_file.setdefault(h["file"], []).append(idx)

    for f in hunks_by_file:
        tree = file_tree_map.get(f)           # use first, guaranteed parse OK
        if tree:
            annotate_parents(tree)
            MaxASTDist[f] = subtree_diameter(tree)
        else:                                 # should be rare
            # fall back to max distance among hunk roots
            idxs = hunks_by_file[f]
            MaxASTDist[f] = max(
                ASTNodeDistance(hunks[i]["ast_tree"], hunks[j]["ast_tree"])
                for i, j in itertools.combinations(idxs, 2)
            ) or 1

    total_score, total_max = 0.0, 0.0
    pair_rows: List[List] = []

    for i, j in itertools.combinations(range(n), 2):
        hi, hj = hunks[i], hunks[j]

        D_lex = 1.0 - difflib.SequenceMatcher(None, hi["code"], hj["code"]).ratio()

        if hi["file"] == hj["file"]:
            gamma   = 1.0
            raw_ast = ASTNodeDistance(hi["ast_tree"], hj["ast_tree"])
            diam = MaxASTDist[hi["file"]]
            D_ast = raw_ast / diam
            D_dir   = 0.0
        else:
            gamma   = 2.0
            D_ast   = 1.0
            pkgd    = PackageDistance(hi["pkg"], hj["pkg"])
            D_dir   = pkgd / max_pkg

        pairDiv = D_lex * (D_ast + gamma * D_dir)

        maxDiv  = 1.0 + gamma

        normalized = pairDiv / maxDiv

        total_score += pairDiv
        total_max   += maxDiv

        pair_rows.append([
            i, j,
            f"{D_lex:.4f}",
            f"{D_ast:.4f}",
            f"{D_dir:.4f}",
            f"{normalized:.4f}",
        ])

    divergence = total_score / total_max
    return divergence, pair_rows

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute Hunk-Divergence & emit per-bug and per-pair CSVs"
    )
    parser.add_argument("--json",     default="../config/method_multihunk.json")
    parser.add_argument("--work-dir", default="~/WORK_DIR")
    parser.add_argument("--out",      default="total_hunk_divergence_results.csv")
    parser.add_argument("--pair-out", default="pairwise_hunk_divergence_results.csv")
    args = parser.parse_args()

    data      = json.load(open(args.json, encoding="utf-8"))
    work_root = Path(args.work_dir).expanduser()

    per_bug_rows, per_pair_rows = [], []

    for bug_id, entry in data.items():
        proj, num = bug_id.split("_")
        checkout  = work_root / f"{proj}_{num}"
        hunks, tree_map = make_hunks_for_bug(entry, checkout)
        if len(hunks) < 2:
            continue

        max_pkg   = max_package_distance_for_repo(checkout)
        div, pairs = compute_metrics_for_bug(hunks, tree_map, max_pkg)

        per_bug_rows.append([bug_id, len(hunks), f"{div:.4f}"])
        for row in pairs:
            per_pair_rows.append([bug_id] + row)

        print(f"{bug_id:12s}  ({len(hunks)} hunks)  divergence = {div:.4f}")

    # write CSVs ---------------------------------------------------------
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["bug_id", "hunk_count", "divergence"])
        w.writerows(per_bug_rows)

    with open(args.pair_out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "bug_id", "hunk_i", "hunk_j",
            "lexical_distance", "ast_distance",
            "package_distance", "pair_divergence"
        ])
        w.writerows(per_pair_rows)

    print(f"\n✓ per-bug  → {args.out}")
    print(f"✓ per-pair → {args.pair_out}")

if __name__ == "__main__":
    main()
