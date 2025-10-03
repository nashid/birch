import javalang
import json
import os
import difflib
from birch.utils.d4j_json_utils import find_enclosing_block

def read_java_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def P(file_path):
    java_code = read_java_file(file_path)
    if java_code is None:
        return None

    try:
        tree = javalang.parse.parse(java_code)
        return tree
    except javalang.parser.JavaSyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return None

def ExtractBuggySubtree(AST, start_line, end_line, tolerance=5):
    buggy_subtrees = []

    if AST is None:
        return buggy_subtrees

    # Performs in-order traversal with line number support to extract buggy sub-tree
    for path, node in AST:
        if hasattr(node, 'position') and node.position:
            node_line = node.position[0]  # Get the line number of the node

            if start_line <= node_line <= end_line:
                buggy_subtrees.append(node)

            # Check for specific edge cases such as global variables and function end brackets
            if isinstance(node, javalang.tree.FieldDeclaration):  # Global variable declaration
                if node_line < start_line:  # Global variables often appear before the function
                    buggy_subtrees.append(node)
            
            if isinstance(node, javalang.tree.MethodDeclaration):  # Function declaration (includes end bracket)
                # Method declaration might be at the end of the function
                if start_line <= node_line <= end_line:
                    buggy_subtrees.append(node)

    return buggy_subtrees


def generate_metadata(file_path, bug_id, hunk_index, buggy_code, fixed_code):
    return {
        'file_path': file_path,
        'bug_id': bug_id,
        'hunk_index': hunk_index,
        'buggy_code': buggy_code,
        'fixed_code': fixed_code
    }


def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    return dataset

def load_fixed_index(javaparser_json_path):
    raw = json.load(open(javaparser_json_path, encoding="utf-8"))
    # normalize into flat list of entries
    entries = raw if isinstance(raw, list) else [
        e for v in raw.values() if isinstance(v, dict) and "entries" in v for e in v["entries"]
    ]
    index = {}
    for ent in entries:
        key = (
            ent.get("bug_name"),
            ent.get("file"),
            ent.get("span_start"),
            ent.get("span_end"),
        )
        if None not in key:
            index[key] = ent
    return index

def construct_file_hunk_mappings(D, work_dir, fixed_code_dir, javaparser_json_path):
    file_hunk_mappings = []
    fixed_index = load_fixed_index(javaparser_json_path)
    
    for bug_id, bug_data in D.items():
        project_name, bug_num = bug_id.split("_")
        bug_num = int(bug_num)

        if "buggy_hunks" in bug_data:
            for hunk_index, hunk_data in bug_data["buggy_hunks"].items():
                rel_path = hunk_data["file"]
                full_path = os.path.join(work_dir, f"{project_name}_{bug_num}", rel_path)
                key_path = os.path.join(f"{project_name}_{bug_num}", rel_path)
                start_line = hunk_data["start_line"]
                end_line   = hunk_data["end_line"]

                buggy_code_entry = bug_data.get("buggy_code", {}).get(str(hunk_index), {})
                buggy_code = buggy_code_entry.get("code", "")
                if not buggy_code.strip():
                    continue

                bc_start_line = buggy_code_entry.get("start_line")
                bc_end_line   = buggy_code_entry.get("end_line")

                if bc_start_line is None or bc_end_line is None:
                    bc_start_line = hunk_data["start_line"]
                    bc_end_line   = hunk_data["end_line"]

                if bc_start_line > bc_end_line:
                    bc_start_line, bc_end_line = bc_end_line, bc_start_line
                
                fixed_code = ""
                key = (bug_id, key_path, start_line, end_line)
                ent = fixed_index.get(key)
                if ent:
                    fixed_file = os.path.join(fixed_code_dir, f"{project_name}_{bug_num}", rel_path)
                    lines = []
                    try:
                        with open(fixed_file, encoding="utf-8", errors="replace") as f:
                            for i, ln in enumerate(f, start=1):
                                if ent["start_line"] <= i <= ent["end_line"]:
                                    lines.append(ln.rstrip("\n"))
                    except FileNotFoundError:
                        lines = []
                    fixed_code = "\n".join(lines)
                else:
                    fixed_code_file_path = os.path.join(
                        fixed_code_dir, f"{project_name}_{bug_num}", rel_path
                    )
                    fixed_code = find_exact_fixed_code(
                        buggy_code,
                        buggy_code,
                        bc_start_line,
                        bc_end_line,
                        fixed_code_file_path
                    )

                if start_line > end_line:
                    start_line, end_line = end_line, start_line

                file_hunk_mappings.append({
                    "bug_id":     bug_id,
                    "file_path":  full_path,
                    "start_line": start_line,
                    "end_line":   end_line,
                    "hunk_index": hunk_index,
                    "buggy_code": buggy_code,
                    "fixed_code": fixed_code
                })

    
    return file_hunk_mappings



def SerializeSubtree(subtree):
    serialized = []

    for node in subtree:
        node_info = {
            "type": type(node).__name__,
            "attributes": {attr: getattr(node, attr) for attr in dir(node) if not attr.startswith("__") and not callable(getattr(node, attr))}
        }
        serialized.append(node_info)

    return serialized

def extract_code_from_file(file_path, start_line, end_line):
    """
    Extracts the code from the specified file between start_line and end_line.
    """
    try:
        # Attempt to read the file using UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # If UTF-8 fails, try reading the file with ISO-8859-1 encoding
        try:
            with open(file_path, 'r', encoding='ISO-8859-1') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            # If both encodings fail, raise a descriptive error
            raise ValueError(f"Unable to decode the file {file_path} using both UTF-8 and ISO-8859-1 encodings.")
    
    return lines[start_line - 1:end_line]

def get_diff(buggy_code, fixed_code):
    """
    Generates a diff between the buggy and fixed code.
    Returns the unified diff as a list of lines.
    """
    diff = difflib.unified_diff(buggy_code.splitlines(), fixed_code.splitlines())
    return list(diff)

def apply_diff_to_buggy_code(buggy_code, diff):
    """
    Applies the generated diff to the buggy code and returns the fixed code.
    This approach works directly with the diff and buggy code strings.
    Combines both unchanged buggy code and new fixed code lines.
    """
    # Split the buggy code into lines
    buggy_lines = buggy_code.splitlines()
    
    # Initialize the result lines (the final fixed code)
    fixed_code_lines = []

    # Loop through the diff and apply the changes to the buggy code
    for line in diff:
        if line.startswith(" "):  # Lines that are unchanged in the buggy code
            fixed_code_lines.append(line[2:])  # Remove the leading " " and keep the line
        elif line.startswith("+"):  # Lines that are added in the fixed code
            fixed_code_lines.append(line[2:])  # Remove the leading "+ " and add the line
    
    # After processing the diff, return the combined fixed code
    fixed_code = "\n".join(fixed_code_lines)
    
    return fixed_code


def find_exact_fixed_code(buggy_code, fixed_code, start_line, end_line, fixed_code_file_path):
    """
    Finds the exact fixed code by aligning the buggy and fixed code using diffing.
    Applies the diff to the buggy code and returns the fixed code in the same format.
    """
    # Get the code lines from the fixed file based on the buggy line range
    fixed_code_range = extract_code_from_file(fixed_code_file_path, start_line, end_line)
    
    # Generate the diff between the buggy code and the fixed code
    diff = get_diff(buggy_code, ''.join(fixed_code_range))
    
    # Apply the diff to the buggy code to generate the fixed code
    fixed_code = apply_diff_to_buggy_code(buggy_code, diff)

    return fixed_code


def BuildFullASTDataset(D, P, work_dir, fixed_dir, fixed_json):
    D_AST = []
    file_hunk_mappings = construct_file_hunk_mappings(D, work_dir, fixed_dir, fixed_json)

    for mapping in file_hunk_mappings:
        bug_id = mapping["bug_id"]
        file_path = mapping["file_path"]
        start_line = mapping["start_line"]
        end_line = mapping["end_line"]
        hunk_index = mapping["hunk_index"]
        buggy_code = mapping.get("buggy_code", "") 
        fixed_code = mapping.get("fixed_code", "")

        AST = P(file_path) 
        buggy_subtree = ExtractBuggySubtree(AST, start_line, end_line) 

        metadata = generate_metadata(file_path, bug_id, hunk_index, buggy_code, fixed_code)

        D_AST.append((buggy_subtree, metadata))
    
    return D_AST


