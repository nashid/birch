import os
import json
import difflib
import argparse

def parse_patch_file(patch_file_path):
    """
    Returns a dict {hunk_index: {"buggy_lines": [...], "fixed_lines": [...]} }
    where hunk_index increments per '@@' block in the patch file.
    """
    hunk_data = {}
    current_hunk = 0
    buggy_lines = []
    fixed_lines = []
    in_hunk = False

    with open(patch_file_path, 'r', encoding='utf-8') as pf:
        for line in pf:
            if line.startswith("@@"):
                # Store the previous hunk if we were in one
                if in_hunk:
                    hunk_data[current_hunk] = {
                        "buggy_lines": buggy_lines,
                        "fixed_lines": fixed_lines
                    }
                    current_hunk += 1
                # Reset
                buggy_lines = []
                fixed_lines = []
                in_hunk = True
                continue

            if in_hunk:
                # Removed (buggy) lines
                if line.startswith("+") and not line.startswith("+++"):
                    buggy_lines.append(line[1:].rstrip("\n"))
                # Added (fixed) lines
                elif line.startswith("-") and not line.startswith("---"):
                    fixed_lines.append(line[1:].rstrip("\n"))
                # else: context lines or patch metadata

    # Capture the final hunk if in_hunk was True
    if in_hunk:
        hunk_data[current_hunk] = {
            "buggy_lines": buggy_lines,
            "fixed_lines": fixed_lines
        }

    return hunk_data

def main():
    parser = argparse.ArgumentParser(description="Compute pairwise patch-line similarity for multi-hunk bugs.")
    parser.add_argument('--defects4j_home', type=str, default=os.path.expanduser("~/Desktop/defects4j"),
                        help='Path to the Defects4J home directory')
    parser.add_argument('--json_path', type=str, default="../birch/config/multi_hunk.json",
                        help='Path to the multi-hunk JSON file')
    args = parser.parse_args()

    defects4j_home = args.defects4j_home

    # We will categorize results by these four groups
    # (or anything else your JSON might hold, if relevant).
    # We track:
    #   total = total # of pairwise comparisons
    #   low_range = # of comparisons with 0 < sim < 0.5
    stats = {
        "single_file_two_hunks":    {"total":0, "zero":0, "low_range":0, "sub_range":0, "mid_range":0, "high_range":0, "identical":0},
        "single_file_three_hunks":  {"total":0, "zero":0, "low_range":0, "sub_range":0, "mid_range":0, "high_range":0, "identical":0},
        "multi_file_two_hunks":     {"total":0, "zero":0, "low_range":0, "sub_range":0, "mid_range":0, "high_range":0, "identical":0},
        "multi_file_three_hunks":   {"total":0, "zero":0, "low_range":0, "sub_range":0, "mid_range":0, "high_range":0, "identical":0},
    }

    data = json.load(open(args.json_path, "r", encoding="utf-8"))

    # We'll store raw pairwise results if desired (optional)
    pairwise_results = []

    for bug_id, bug_info in data.items():
        htype = bug_info.get("hunk_type", "")

        # If "single_file_four_or_more_hunks" or "multi_file_four_or_more_hunks", skip
        if htype in ("single_file_four_or_more_hunks", "multi_file_four_or_more_hunks"):
            continue

        # If htype not in our stats dict, skip or create an entry dynamically:
        if htype not in stats:
            continue

        # Derive patch file path from bug_id (e.g., "Chart_25" => project="Chart", bug_num="25")
        try:
            project, bug_num_str = bug_id.split("_")
        except ValueError:
            print(f"Cannot parse bug_id '{bug_id}' (expected PROJECT_bugID). Skipping.")
            continue

        patch_file_path = os.path.join(
            defects4j_home,
            "framework",
            "projects",
            project,
            "patches",
            f"{bug_num_str}.src.patch"
        )

        if not os.path.exists(patch_file_path):
            print(f"No patch file found at {patch_file_path}, skipping {bug_id}.")
            continue

        # Parse the patch to get hunks_data
        hunks_data = parse_patch_file(patch_file_path)

        # If the patch has >= 4 hunks, skip it
        if len(hunks_data) >= 4:
            continue
        # If there's 1 or 0 hunks, no pair to compare
        if len(hunks_data) < 2:
            continue

        # Pairwise comparisons
        hunk_indices = sorted(hunks_data.keys())
        for i in range(len(hunk_indices)):
            for j in range(i+1, len(hunk_indices)):
                hi = hunk_indices[i]
                hj = hunk_indices[j]
                buggy_i = hunks_data[hi]["buggy_lines"]
                fixed_i = hunks_data[hi]["fixed_lines"]
                buggy_j = hunks_data[hj]["buggy_lines"]
                fixed_j = hunks_data[hj]["fixed_lines"]

                # Combine
                hunk_i = buggy_i + fixed_i
                hunk_j = buggy_j + fixed_j

                combined_sim = difflib.SequenceMatcher(None, hunk_i, hunk_j).ratio()

                # Update raw results (optional)
                pairwise_results.append((bug_id, hi, hj, combined_sim, htype))

                # Update stats
                stats[htype]["total"] += 1
                if combined_sim == 0:
                    stats[htype]["zero"] += 1
                elif combined_sim > 0 and combined_sim < 0.25:
                    stats[htype]["low_range"] += 1
                elif combined_sim >= 0.25 and combined_sim < 0.5:
                    stats[htype]["sub_range"] += 1
                elif combined_sim >= 0.5 and combined_sim < 0.75:
                    stats[htype]["mid_range"] += 1
                elif combined_sim >= 0.75 and combined_sim < 1:
                    stats[htype]["high_range"] += 1
                elif combined_sim == 1:
                    stats[htype]["identical"] += 1


    # Optionally, write pairwise results to CSV
    # (if you want the raw data)
    out_csv = "hunk_similarity_raw.csv"
    with open(out_csv, "w", encoding="utf-8") as out:
        out.write("bug_id,hunk_i,hunk_j,combined_sim,hunk_type\n")
        for (bug_id, hi, hj, sim, htype) in pairwise_results:
            out.write(f"{bug_id},{hi},{hj},{sim:.4f},{htype}\n")

    # Now print the summary table
    # e.g., columns: Hunk Type, Total, 0<difflib<0.5
    print("\nFinal Summary\n")
    print(f"{'Hunk Type':35s} {'Total':>5s} {'diff = 0':>10s} {'0<diff<=0.25':>10s} {'0.25<=diff<0.5':>10s} {'0.5<=diff<0.75':>10s} {'diff>=0.75':>10s}{'diff=1':>10s}")
    for htype in stats.keys():
        total = stats[htype]["total"]
        zero = stats[htype]["zero"]
        low = stats[htype]["low_range"]
        sub = stats[htype]["sub_range"]
        mid = stats[htype]["mid_range"]
        high = stats[htype]["high_range"]
        identical = stats[htype]["identical"]
        # Build a nicer label if you want:
        # "single_file_two_hunks" => "Single File - Two Hunks Bugs"
        # but you can do it in a dictionary if you prefer
        if total == 0:
            continue
        # Simple alignment:
        print(f"{htype:35s} {total:5d}{zero:10d}{low:10d}{sub:10d}{mid:10d}{high:10d}{identical:10d}")

    print(f"\nDone. Raw pairwise results written to {out_csv}.")

if __name__ == "__main__":
    main()
