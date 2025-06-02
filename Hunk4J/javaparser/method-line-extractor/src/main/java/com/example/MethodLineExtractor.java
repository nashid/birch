package com.example;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.Position;
import com.github.javaparser.StaticJavaParser;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import com.github.javaparser.ast.body.BodyDeclaration;
import com.github.javaparser.ast.comments.Comment;
import com.github.javaparser.ast.Node;
import java.util.LinkedHashMap;
import com.github.javaparser.ParserConfiguration;



public class MethodLineExtractor {

    // ------------------------------------------------------------------
    // Exact port of the Python  d4j_test_path_prefix
    // ------------------------------------------------------------------
    private static String testPathPrefix(String proj, int bugNum) {
        switch (proj) {
            case "Chart":               return "tests/";
            case "Closure":             return "test/";
            case "Lang":                return bugNum <= 35 ? "src/test/java/" : "src/test/";
            case "Math":                return bugNum <= 84 ? "src/test/java/" : "src/test/";
            case "Mockito":             return "test/";
            case "Time":                return "src/test/java/";
            case "Cli":                 return bugNum <= 29 ? "src/test/"      : "src/test/java/";
            case "Codec":               return bugNum <= 10 ? "src/test/"      : "src/test/java/";
            case "Collections":         return "src/test/java/";
            case "Compress":            return "src/test/java/";
            case "Csv":                 return "src/test/java/";
            case "Gson":                return "gson/src/test/java/";
            case "JacksonCore":
            case "JacksonDatabind":
            case "JacksonXml":          return "src/test/java/";
            case "Jsoup":               return "src/test/java/";
            case "JxPath":              return "src/test/";
            default:
                throw new IllegalArgumentException(
                        "Cannot find test path prefix for " + proj + bugNum);
        }
    }

    // ------------------------------------------------------------------
    // Simple POJO instead of Java 16  record
    // ------------------------------------------------------------------
    private static class BugEntry {
        final String bugName;
        final String proj;
        final int    bugNum;
        final String relFile;
        final int    spanStart;
        final int    spanEnd;
        final int    hunkId;

        BugEntry(String bugName, String proj, int bugNum,
                 String relFile, int spanStart, int spanEnd, int hunkId) {
            this.bugName   = bugName;
            this.proj      = proj;
            this.bugNum    = bugNum;
            this.relFile   = relFile;
            this.spanStart = spanStart;
            this.spanEnd   = spanEnd;
            this.hunkId    = hunkId;
        }
    }

    // ------------------------------------------------------------------
    private static final Pattern BUG_NAME_RE =
            Pattern.compile("([A-Za-z]+)_([0-9]+)");

    private static BugEntry parseEntry(JSONObject o) {
        String bugName = o.getString("bug_name");   // e.g. "Chart_2"
        Matcher m = BUG_NAME_RE.matcher(bugName);
        if (!m.matches())
            throw new IllegalArgumentException("Bad bug_name: " + bugName);

        String proj   = m.group(1);
        int bugNum    = Integer.parseInt(m.group(2));
        int    hunkId = o.getInt("hunk_id");

        return new BugEntry(
                bugName,
                proj,
                bugNum,
                o.getString("file"),               // relative to prefix
                o.getInt("start_line"),
                o.getInt("end_line"),
                hunkId
        );
    }

    private static final Map<Node, Node> parentMap = new IdentityHashMap<>();

    private static void annotateParents(Node node, Node parent) {
        if (node == null) return;
        if (parent != null) parentMap.put(node, parent);
        for (Node child : node.getChildNodes()) annotateParents(child, node);
    }

    private static int nodeDepth(Node n) {
        int d = 0;
        Set<Node> seen = new HashSet<>();
        while (n != null && parentMap.containsKey(n)) {
          if (!seen.add(n)) {
            // cycle detected – bail out
            break;
          }
          d++;
          n = parentMap.get(n);
        }
        return d;
      }

    private static Node lca(Node u, Node v) {
        Set<Node> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        while (u != null) {
            seen.add(u);
            u = parentMap.get(u);
        }
        while (v != null && !seen.contains(v)) {
            v = parentMap.get(v);
        }
        return v;
    }

    private static int astNodeDistance(Node u, Node v) {
        if (u == null || v == null){
            System.out.println("here");
             return 0;
        }
        int du = nodeDepth(u), dv = nodeDepth(v);
        Node w = lca(u, v);
        int dw = (w != null) ? nodeDepth(w) : 0;
        return du + dv - 2 * dw;
    }

    private static List<Node> collectNodes(Node root) {
        List<Node> nodes = new ArrayList<>();
        if (root == null) return nodes;
        Deque<Node> dq = new ArrayDeque<>(); dq.add(root);
        while (!dq.isEmpty()) {
            Node n = dq.poll(); nodes.add(n);
            dq.addAll(n.getChildNodes());
        }
        return nodes;
    }

    private static Map<Node,List<Node>> buildAdjacency(Node root) {
        Map<Node,List<Node>> adj = new IdentityHashMap<>();
        // collect all nodes in a list (reuse your collectNodes)
        List<Node> all = collectNodes(root);
        // ensure every node is in the map
        for (Node n : all) {
            adj.put(n, new ArrayList<>());
        }
        // connect parent↔child
        for (Node n : all) {
            for (Node c : n.getChildNodes()) {
                adj.get(n).add(c);
                adj.get(c).add(n);
            }
        }
        return adj;
    }
    
    /** BFS from start, returns the farthest node and its distance. */
    private static Pair<Node,Integer> bfsFarthest(Node start,
            Map<Node,List<Node>> adj) {
        Deque<Node> dq = new ArrayDeque<>();
        Map<Node,Integer> dist = new IdentityHashMap<>();
        dq.add(start);
        dist.put(start, 0);
        Node far = start;
        while (!dq.isEmpty()) {
            Node u = dq.poll();
            int d = dist.get(u);
            if (d > dist.get(far)) far = u;
            for (Node v : adj.get(u)) {
                if (!dist.containsKey(v)) {
                    dist.put(v, d+1);
                    dq.add(v);
                }
            }
        }
        return new Pair<>(far, dist.get(far));
    }
    
    /** O(N) diameter via two BFS passes. */
    private static int subtreeDiameter(Node root) {
        if (root == null) return 1;
        // build adjacency graph in O(N)
        Map<Node,List<Node>> adj = buildAdjacency(root);
        // pick any node
        Node any = root;
        // first BFS to find a farthest node
        Node far = bfsFarthest(any, adj).getKey();
        // second BFS to find the diameter
        int diameter = bfsFarthest(far, adj).getValue();
        return diameter > 0 ? diameter : 1;
    }
    
    // Simple Pair holder (or use AbstractMap.SimpleEntry)
    private static class Pair<K,V> {
        private final K key;
        private final V value;
        public Pair(K k, V v) { key = k; value = v; }
        public K getKey()   { return key; }
        public V getValue() { return value; }
    }

    // ------------------------------------------------------------------
    public static void main(String[] args) throws Exception {

        /* ---------- CLI usage check ---------- */
        if (args.length < 1) {
            System.err.println(
                "Usage: java MethodLineExtractor <bugs.json> [workDir] [output.json]\n\n" +
                "  bugs.json  : input file.  Accepted forms:\n" +
                "      • JSONArray  [ {...}, {...} ]\n" +
                "      • JSONObject { \"Chart_2\": {...}, \"Lang_47\": {...} }\n" +
                "  workDir    : directory with checked‑out bugs   (default: ~/WORK_DIR)\n" +
                "  output.json: results file                      (default: method_lines.json)\n");
            System.exit(1);
        }
    
        Path bugsJson   = Paths.get(args[0]);
        Path workDir    = args.length >= 2
                          ? Paths.get(args[1])
                          : Paths.get(System.getProperty("user.home"), "WORK_DIR");
        Path outputJson = args.length >= 3
                          ? Paths.get(args[2])
                          : Paths.get("method_lines.json");
    
        /* ---------- load JSON, accept array or object ---------- */
        String jsonText = readFileUtf8(bugsJson).trim();
        JSONArray inArr = new JSONArray();                       // flat work list

        if (jsonText.startsWith("[")) {                          // top‑level array
            JSONArray raw = new JSONArray(jsonText);
            for (int i = 0; i < raw.length(); i++) {
                inArr.put(raw.getJSONObject(i));
            }

        } else if (jsonText.startsWith("{")) {                   // object of bugs
            JSONObject bigObj = new JSONObject(jsonText);
            for (String bugName : bigObj.keySet()) {
                JSONObject val = bigObj.getJSONObject(bugName);

                Matcher m = BUG_NAME_RE.matcher(bugName);
                if (!m.matches())
                    throw new IllegalArgumentException("Bad bug_name: " + bugName);

                String proj = m.group(1);
                int bugNum  = Integer.parseInt(m.group(2));

                if (val.has("file")) {
                    // single‑hunk layout
                    val.put("bug_name", bugName);
                    inArr.put(val);

                } else if (val.has("hunks") || val.has("buggy_hunks")) {
                    // multi‑hunk layout: either  JSON array  or  numbered object
                    if (val.has("hunks")) {
                        JSONArray hunks = val.getJSONArray("hunks");
                        for (int j = 0; j < hunks.length(); j++) {
                            JSONObject h = hunks.getJSONObject(j);
                            addHunk(inArr, buildEntryFromHunk(bugName, proj, bugNum, h));
                        }
                    } else { // "buggy_hunks" as { "0": {...}, "1": {...} }
                        JSONObject hunksObj = val.getJSONObject("buggy_hunks");
                        for (String hk : hunksObj.keySet()) {
                            JSONObject h = hunksObj.getJSONObject(hk);
                            h.put("hunk_id", Integer.parseInt(hk));
                            addHunk(inArr, buildEntryFromHunk(bugName, proj, bugNum, h));
                        }
                    }

                } else {
                    throw new IllegalArgumentException(
                            "No file/hunks in bug entry " + bugName);
                }
            }

        } else {
            throw new IllegalArgumentException("Unrecognised JSON top‑level value");
        }
        /* ---------- end JSON loading ---------- */
    
        JSONArray membersResults = new JSONArray();
        JSONArray typesResults   = new JSONArray();
        JavaParser parser        = new JavaParser();

        for (int i = 0; i < inArr.length(); i++) {
            BugEntry be = parseEntry(inArr.getJSONObject(i));

            // locate source file
            Path bugDir   = workDir.resolve(be.bugName);
            Path javaPath = bugDir.resolve(be.relFile).normalize();
            if (!Files.exists(javaPath)) {
                String prefix = testPathPrefix(be.proj, be.bugNum);
                javaPath = bugDir.resolve(prefix).resolve(be.relFile).normalize();
            }
            if (!Files.exists(javaPath)) {
                System.err.printf("⚠ file missing: %s%n", javaPath);
                continue;
            }

            // make path effectively final for lambdas
            final Path pathForEntry = javaPath;
            ParseResult<CompilationUnit> pr = parser.parse(pathForEntry);
            Optional<CompilationUnit> maybeCu = pr.getResult();
            if (!maybeCu.isPresent()) {
                throw new RuntimeException("Parse failed: " + pathForEntry);
            }
            CompilationUnit cu = maybeCu.get();

            // ─── methods ──────────────────────────────────────────────────────────
            List<BodyDeclaration<?>> matchedMembers = new ArrayList<>();

            // collect matching methods
            cu.findAll(MethodDeclaration.class).forEach(m -> {
                Optional<Position> ob = m.getBegin();
                Optional<Position> oe = m.getEnd();
                if (ob.isPresent() && oe.isPresent()) {
                    int s = ob.get().line, t = oe.get().line;
                    if (!(t < be.spanStart || s > be.spanEnd)) {
                        matchedMembers.add(m);
                    }
                }
            });

            // collect matching constructors
            cu.findAll(ConstructorDeclaration.class).forEach(ctor -> {
                Optional<Position> ob = ctor.getBegin();
                Optional<Position> oe = ctor.getEnd();
                if (ob.isPresent() && oe.isPresent()) {
                    int s = ob.get().line, t = oe.get().line;
                    if (!(t < be.spanStart || s > be.spanEnd)) {
                        matchedMembers.add(ctor);
                    }
                }
            });

            if (!matchedMembers.isEmpty()) {
                if (matchedMembers.size() > 1) {
                    System.out.printf("⚠ %s spans %d members%n", be.bugName, matchedMembers.size());
                }
                // compute overall span
                int minStart = Integer.MAX_VALUE, maxEnd = Integer.MIN_VALUE;
                // pick first member for name and javadoc
                BodyDeclaration<?> first = matchedMembers.get(0);
                String memberType, name, javadoc = null;
                Optional<Position> fb = first.getBegin(), fe = first.getEnd();
                if (fb.isPresent() && fe.isPresent()) {
                    minStart = fb.get().line;
                    maxEnd   = fe.get().line;
                }
                if (first instanceof MethodDeclaration) {
                    MethodDeclaration md = (MethodDeclaration) first;
                    memberType = "method";
                    name = md.getNameAsString();
                    javadoc = md.getJavadocComment().map(Comment::toString).orElse(null);
                } else {
                    ConstructorDeclaration cd = (ConstructorDeclaration) first;
                    memberType = "constructor";
                    name = cd.getNameAsString();
                    javadoc = cd.getJavadocComment().map(Comment::toString).orElse(null);
                }
                // update min/max across all
                for (BodyDeclaration<?> member : matchedMembers) {
                    Position b = member.getBegin().get();
                    Position e = member.getEnd().get();
                    minStart = Math.min(minStart, b.line);
                    maxEnd   = Math.max(maxEnd,   e.line);
                }

                JSONObject out = new JSONObject();
                out.put("bug_name",    be.bugName);
                out.put("file",        pathForEntry.toString());
                out.put("member_type", memberType);
                out.put("name",        name);
                out.put("javadoc",     javadoc);
                out.put("start_line",  minStart);
                out.put("end_line",    maxEnd);
                out.put("span_start",  be.spanStart);
                out.put("span_end",    be.spanEnd);
                membersResults.put(out);
            }

            // ─── classes & interfaces ─────────────────────────────────────────────
            cu.findAll(com.github.javaparser.ast.body.ClassOrInterfaceDeclaration.class)
            .forEach(typeDecl -> {
                Optional<Position> b = typeDecl.getBegin();
                Optional<Position> e = typeDecl.getEnd();
                if (!b.isPresent() || !e.isPresent()) return;
                int s = b.get().line, t = e.get().line;
                if (s <= be.spanStart && t >= be.spanEnd) {
                    String javadoc = typeDecl
                        .getJavadocComment()
                        .map(com.github.javaparser.ast.comments.Comment::toString)
                        .orElse(null);
                    JSONObject out = new JSONObject();
                    out.put("bug_name",    be.bugName);
                    out.put("file",        pathForEntry.toString());
                    out.put("type",        typeDecl.isInterface() ? "interface" : "class");
                    out.put("name",        typeDecl.getNameAsString());
                    out.put("javadoc",     javadoc);
                    out.put("start_line",  s);
                    out.put("end_line",    t);
                    out.put("span_start",  be.spanStart);
                    out.put("span_end",    be.spanEnd);
                    typesResults.put(out);
                }
            });
        }
        

        ParserConfiguration cfg = new ParserConfiguration()
            .setAttributeComments(false)   // optional
            .setStoreTokens(true);         // <— this is the key
        StaticJavaParser.setConfiguration(cfg);
        Map<String, Map<String, List<BugEntry>>> groupMap = new LinkedHashMap<>();
        for (int i = 0; i < inArr.length(); i++) {
            BugEntry be = parseEntry(inArr.getJSONObject(i));
            Map<String, List<BugEntry>> fileMap = groupMap.get(be.bugName);
            if (fileMap == null) {
                fileMap = new LinkedHashMap<>();
                groupMap.put(be.bugName, fileMap);
            }
            List<BugEntry> list = fileMap.get(be.relFile);
            if (list == null) {
                list = new ArrayList<>();
                fileMap.put(be.relFile, list);
            }
            list.add(be);
        }
        JSONObject astMetrics = new JSONObject();
        for (Map.Entry<String, Map<String, List<BugEntry>>> bugEntry : groupMap.entrySet()) {
            String bugName = bugEntry.getKey();
            JSONObject filesObj = new JSONObject();
            for (Map.Entry<String, List<BugEntry>> fileEntry : bugEntry.getValue().entrySet()) {
                String relFile = fileEntry.getKey();
                List<BugEntry> hunks = fileEntry.getValue();
                Path javaPath = workDir.resolve(bugName).resolve(relFile).normalize();
                ParseResult<CompilationUnit> pr = parser.parse(javaPath);
                if (!pr.getResult().isPresent()) continue;
                CompilationUnit cu = StaticJavaParser.parse(javaPath);
                parentMap.clear(); annotateParents(cu, null);
                int treeDiam = subtreeDiameter(cu);
                List<Node> roots = new ArrayList<>();
                List<Integer> hunkIds = new ArrayList<>();
                for (BugEntry be : hunks) {
                    List<Node> enclosing = new ArrayList<>();
                    for (Node n : cu.findAll(Node.class)) {
                        if (!n.getRange().isPresent()) continue;
                        int ns = n.getRange().get().begin.line;
                        int ne = n.getRange().get().end.line;
                        // only nodes whose range *fully covers* the buggy span
                        if (ns <= be.spanStart && ne >= be.spanEnd) {
                            enclosing.add(n);
                        }
                    }

                    Node rootNode;
                    if (!enclosing.isEmpty()) {
                        // pick the one with the smallest span (end−start)
                        rootNode = enclosing.get(0);
                        int bestSpan = rootNode.getRange().get().end.line
                                    - rootNode.getRange().get().begin.line;
                        for (Node cand : enclosing) {
                            int span = cand.getRange().get().end.line
                                    - cand.getRange().get().begin.line;
                            if (span < bestSpan) {
                                bestSpan = span;
                                rootNode = cand;
                            }
                        }
                    } else {
                        rootNode = cu;
                    }
                    roots.add(rootNode);
                    hunkIds.add(be.hunkId);
                }
                JSONObject pairObj = new JSONObject();
                for (int a = 0; a < roots.size(); a++) {
                    for (int b = a + 1; b < roots.size(); b++) {
                        int d = astNodeDistance(roots.get(a), roots.get(b));
                        int hA = hunkIds.get(a);
                        int hB = hunkIds.get(b);
                        pairObj.put(hA + "_" + hB, d);
                    }
                }
                JSONObject fileObj = new JSONObject();
                fileObj.put("diameter", treeDiam);
                fileObj.put("pairs", pairObj);
                filesObj.put(relFile, fileObj);
            }
            astMetrics.put(bugName, filesObj);
        }

        // write out two JSON files
        writeFileUtf8(outputJson, membersResults.toString(4));
        System.out.printf("Saved %d member entries → %s%n",
                membersResults.length(), outputJson.toAbsolutePath());

        // write classes+interfaces
        Path typesOut = outputJson.getParent()
            .resolve(outputJson.getFileName().toString().replaceFirst("\\.json$", "_types.json"));
        writeFileUtf8(typesOut, typesResults.toString(4));
        System.out.printf("Saved %d type entries   → %s%n",
                typesResults.length(), typesOut.toAbsolutePath());
        Path astOut = outputJson.getParent().resolve(
            outputJson.getFileName().toString().replaceFirst("\\.json$", "_ast.json")
        );
        writeFileUtf8(astOut, astMetrics.toString(4));
        System.out.printf("Saved AST metrics → %s%n", astOut);
    }

    /**
     * Build a BugEntry from a single hunk object (multi‑hunk JSON layout).
     */
    private static BugEntry buildEntryFromHunk(
        String bugName, String proj, int bugNum, JSONObject hunk) {
        
        int hunkId = hunk.getInt("hunk_id");

        String relFile =
                hunk.has("file")      ? hunk.getString("file")      :
                hunk.has("file_name") ? hunk.getString("file_name") :
                hunk.has("file_path") ? hunk.getString("file_path") :
                null;

        if (relFile == null)
            throw new IllegalArgumentException("Missing file key in hunk for " + bugName);
        
        int start = hunk.getInt("start_line");
        int end   = hunk.getInt("end_line");

        return new BugEntry(bugName, proj, bugNum, relFile, start, end, hunkId);
    }
    private static void addHunk(JSONArray arr, BugEntry be) {
        JSONObject obj = new JSONObject();
        obj.put("bug_name",   be.bugName);
        obj.put("file",       be.relFile);
        obj.put("start_line", be.spanStart);
        obj.put("end_line",   be.spanEnd);
        obj.put("hunk_id",    be.hunkId);
        arr.put(obj);
    }

      
    

    // ------------------------------------------------------------------
    // Utility methods for Java 8 (UTF‑8 safe)
    private static String readFileUtf8(Path p) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = Files.newBufferedReader(p, StandardCharsets.UTF_8)) {
            String line;
            while ((line = br.readLine()) != null) sb.append(line).append('\n');
        }
        return sb.toString();
    }

    private static void writeFileUtf8(Path p, String text) throws IOException {
        Files.write(p, text.getBytes(StandardCharsets.UTF_8));
    }
}
