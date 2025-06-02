#!/usr/bin/env python3
"""
Comprehensive sanity check for AST-helper functions used in hunk_divergence.py
Requires only javalang and the helpers themselves.
"""
import importlib.util, pathlib, tempfile, textwrap, random, itertools, sys

# ---------------------------------------------------------------------- sample Java (Java-8 compliant)
SAMPLE_JAVA = textwrap.dedent("""\
    package demo.ast;
    import java.util.*;
    import java.util.function.Function;

    public class Sample {
        enum State { NEW, IN_PROGRESS, DONE }

        static class Box<T> {
            private final T v;
            Box(T v){this.v=v;}
            <R> R map(Function<? super T,? extends R> f){return f.apply(v);}
        }

        public static void main(String[] a)throws Exception{
            Scanner sc=new Scanner(System.in);
            String s=sc.nextLine().trim().toLowerCase();
            State st;
            switch(s){
                case "new": st=State.NEW; break;
                case "progress": st=State.IN_PROGRESS; break;
                case "done":
                case "ok": st=State.DONE; break;
                default: throw new IllegalArgumentException();
            }
            Box<State> b=new Box<>(st);
            b.map(Enum::name);
            System.out.println("done");
        }
    }
""")

tmpdir = pathlib.Path(tempfile.mkdtemp())
java_file = tmpdir / "Sample.java"
java_file.write_text(SAMPLE_JAVA, encoding="utf-8")

# ---------------------------------------------------------------------- import helpers
HELPER_PATH = pathlib.Path("hunk_divergence.py").resolve()
spec = importlib.util.spec_from_file_location("helpers", HELPER_PATH)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

build_ast        = helpers.build_ast_tree
annotate_parents = helpers.annotate_parents
_node_depth      = helpers._node_depth
_lca             = helpers._lca
distance         = helpers.ASTNodeDistance
diameter         = helpers.subtree_diameter
collect_nodes    = helpers.collect_nodes
_parent_map      = helpers._parent_map

# ---------------------------------------------------------------------- 1. parse
tree = build_ast(java_file.read_text())
assert tree is not None, "❌ build_ast_tree returned None"

# ---------------------------------------------------------------------- 2. annotate parents
_parent_map.clear()
annotate_parents(tree)

nodes = collect_nodes(tree)
assert nodes, "❌ collect_nodes returned empty list"

for n in nodes:
    if n is not tree:
        assert n in _parent_map, f"❌ parent missing for node {n}"

# depths
for n in nodes:
    if n is tree:
        assert _node_depth(n) == 0
    else:
        p = _parent_map[n]
        assert _node_depth(n) == _node_depth(p) + 1

# ---------------------------------------------------------------------- 3. distances & LCA
dia = diameter(tree)
all_pairs = list(itertools.combinations(nodes, 2))
max_seen = 0

for u, v in random.sample(all_pairs, min(200, len(all_pairs))):
    d_uv = distance(u, v)
    max_seen = max(max_seen, d_uv)

    # non-negativity & symmetry
    assert d_uv >= 0
    assert d_uv == distance(v, u)

    # lca property
    w = _lca(u, v)
    assert w is not None
    assert d_uv == distance(u, w) + distance(v, w)

# triangle inequality on 100 random triples
for _ in range(100):
    a, b, c = random.sample(nodes, 3)
    assert distance(a, c) <= distance(a, b) + distance(b, c)

# diameter check (exhaustive)
exhaustive_max = 0
for u, v in all_pairs:
    exhaustive_max = max(exhaustive_max, distance(u, v))
assert dia == exhaustive_max, "❌ subtree_diameter mismatch"

print("\033[92mALL AST TESTS PASSED\033[0m")
