from __future__ import annotations
import argparse, csv, json, itertools
from pathlib import Path
from typing import Dict, List, Optional, Tuple     

import difflib
import javalang
import os


_parent_map: Dict[javalang.ast.Node, javalang.ast.Node] = {}

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

def build_ast_tree(src: str) -> Optional[javalang.ast.Node]:
    try:
        return javalang.parse.parse(src)
    except Exception:
        return None

def make_hunks_for_bug(bug_id: str, bug_entry: Dict, checkout_root: Path, patch_root: Path):
    hunks, file_tree_map = [], {}
    patch_file = patch_root / f"{bug_id}.src.patch"
    patch_hunks = parse_patch_file(patch_file) if patch_file.exists() else {}
    for local_idx, (h) in enumerate(bug_entry.get("buggy_hunks", {}).values()):
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

        plines = []
        if local_idx in patch_hunks:
            ph = patch_hunks[local_idx]
            plines = ph["buggy"] + ph["fixed"]

        hunks.append({
            "file": str(fp),
            "pkg":  pkg,
            "ast_tree": subtree_root,
            "patch_lines": plines,         
        })
    return hunks, file_tree_map

_pkg_cache: Dict[Path, int] = {}

_IGNORE_DIR_TOKENS = {"src", "main", "java", "test", "resources"}

def _logical_package(path: Path) -> List[str]:
    parts = list(path.with_suffix("").parts)[:-1] 
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

    pkgs: List[List[str]] = []
    for java in root.rglob("*.java"):
        try:
            java.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass 
        pkgs.append(_logical_package(java))

    best = 0
    for a, b in itertools.combinations(pkgs, 2):
        best = max(best, _dir_distance(a, b))

    _pkg_cache[root] = best or 1
    return _pkg_cache[root]

def parse_patch_file(patch_path: Path):
    out, idx, buggy, fixed, in_hunk = {}, 0, [], [], False
    with patch_path.open(encoding="utf-8") as pf:
        for line in pf:
            if line.startswith("@@"):
                if in_hunk:
                    out[idx] = {"buggy": buggy, "fixed": fixed}
                    idx += 1
                buggy, fixed, in_hunk = [], [], True
                continue
            if not in_hunk:
                continue
            if line.startswith("+") and not line.startswith("+++"):
                fixed.append(line[1:].rstrip("\n"))
            elif line.startswith("-") and not line.startswith("---"):
                buggy.append(line[1:].rstrip("\n"))
    if in_hunk:
        out[idx] = {"buggy": buggy, "fixed": fixed}
    return out


def compute_metrics_for_bug(
    hunks: List[Dict],
    file_tree_map: Dict[str, Optional[javalang.ast.Node]],
) -> Tuple[float, List[List]]:
    n = len(hunks)
    if n < 2:
        return 0.0, []

    MaxASTDist: Dict[str, int] = {}
    hunks_by_file: Dict[str, List[int]] = {}
    for idx, h in enumerate(hunks):
        hunks_by_file.setdefault(h["file"], []).append(idx)

    for f, idxs in hunks_by_file.items():
        tree = file_tree_map.get(f)
        if tree:
            annotate_parents(tree)
            MaxASTDist[f] = subtree_diameter(tree)
        else:
            MaxASTDist[f] = max(
                ASTNodeDistance(hunks[i]["ast_tree"], hunks[j]["ast_tree"])
                for i, j in itertools.combinations(idxs, 2)
            ) or 1

    total_score, total_max = 0.0, 0.0
    pair_rows: List[List] = []

    for i, j in itertools.combinations(range(n), 2):
        hi, hj = hunks[i], hunks[j]

        D_lex = 1.0 - difflib.SequenceMatcher(None, hi["patch_lines"], hj["patch_lines"]).ratio()

        if hi["file"] == hj["file"]:
            gamma   = 0.0
            raw_ast = ASTNodeDistance(hi["ast_tree"], hj["ast_tree"])
            diam    = MaxASTDist[hi["file"]]
            D_ast   = raw_ast / diam
            D_dir   = 0.0
        else:
            gamma = 2.0
            D_ast = 1.0     
            D_dir = 1.0    

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
    parser.add_argument('--defects4j_home', type=str, default=os.path.expanduser("~/Desktop/defects4j"),
                        help='Path to the Defects4J home directory')
    parser.add_argument("--out",      default="total_hunk_divergence_results.csv")
    parser.add_argument("--pair-out", default="pairwise_hunk_divergence_results.csv")
    args = parser.parse_args()

    data      = json.load(open(args.json, encoding="utf-8"))
    work_root = Path(args.work_dir).expanduser()

    per_bug_rows, per_pair_rows = [], []

    for bug_id, entry in data.items():
        proj, num = bug_id.split("_")
        checkout  = work_root / f"{proj}_{num}"
        patch_root = Path(args.defects4j_home, "framework", "projects", proj, "patches")
        hunks, tree_map = make_hunks_for_bug(num, entry, checkout, patch_root)
        if len(hunks) < 2:
            continue

        div, pairs = compute_metrics_for_bug(hunks, tree_map)

        per_bug_rows.append([bug_id, len(hunks), f"{div:.4f}"])
        for row in pairs:
            per_pair_rows.append([bug_id] + row)

        print(f"{bug_id:12s}  ({len(hunks)} hunks)  divergence = {div:.4f}")

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
