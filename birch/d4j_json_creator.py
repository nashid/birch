import os
import argparse
import json
from utils.d4j_json_utils import get_bug_report_info, get_buggy_lines, get_failing_tests, extract_test_method_content, determine_bug_type, d4j_path_prefix, d4j_test_path_prefix, get_buggy_files, extract_hunks_from_file, load_existing_buggy_code, explicit_delineation, classify_single_hunk, decide_bug_scope
from utils.general_utils import read_file_content

PROJECTS = {
    "Chart": list(range(1, 27)),
    "Cli": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
    "Closure": list(range(1, 63)) + list(range(65, 93)) + list(range(94, 177)),
    "Codec": list(range(1, 19)),
    "Collections": list(range(25, 29)),
    "Compress": list(range(1, 48)),
    "Csv": list(range(1, 17)),
    "Gson": list(range(1, 19)),
    "JacksonCore": list(range(1, 27)),
    "JacksonDatabind": list(range(1, 113)),
    "JacksonXml": list(range(1, 7)),
    "Jsoup": list(range(1, 94)),
    "JxPath": list(range(1, 23)),
    "Lang": [1, 3] + list(range(4, 66)),
    "Math": list(range(1, 107)),
    "Mockito": list(range(1, 39)),
    "Time": list(range(1, 21)) + list(range(22, 28)),
}

def process_bugs(projects, work_dir, defects4j_home, output_dir, json_files_path, mode):
    hunks_data = {}
    json_files = [
        os.path.join(json_files_path, 'defects4j-sf.json'),
        os.path.join(json_files_path, 'defects4j-mf.json')
    ]
    for project, bug_ids in projects.items():
        for bug_id in bug_ids:
            project_bug = f"{project}_{bug_id}"
            print(project_bug)
            patch_file_path = os.path.join(defects4j_home, f'framework/projects/{project}/patches/{bug_id}.src.patch')
            
            buggy_files = get_buggy_files(project, bug_id)
            buggy_lines = get_buggy_lines(patch_file_path)
            buggy_files_data = {f'{idx}': file for idx, file in enumerate(buggy_files)}

            triggered_tests = get_failing_tests(project, bug_id)
            
            bug_report_url, bug_description = get_bug_report_info(project, bug_id)

            hunks = []
            hunk_mapping = {}
            buggy_codes = []
            bug_counter = 0
            for buggy_file in buggy_files:
                original_file_path = os.path.join(work_dir, f'{project_bug}', buggy_file)
                try:
                    original_content = read_file_content(original_file_path)
                except IOError as e:
                    print(f"Failed to read file {original_file_path}: {e}")
                    continue

                localized_content = original_content.split('\n')
                buggy_lines_list = buggy_lines.get(buggy_file, [])
                processed_ranges = []
                
                file_hunks, file_buggy_code, file_hunk_mapping, bug_counter = extract_hunks_from_file(localized_content, buggy_lines_list, buggy_file, processed_ranges, bug_counter, buggy_codes, mode, project_bug)
                hunks.extend(file_hunks)
                for key, value in file_hunk_mapping.items():
                    if key not in hunk_mapping:
                        hunk_mapping[key] = value
                    elif value:  # Only update if the new value is not an empty list
                        hunk_mapping[key].extend(value)
            
            delineated_codes = explicit_delineation(buggy_codes, hunk_mapping)

            hunk_scopes = []
            for h in hunks:
                rel_path = h["file"]
                abs_path = os.path.join(work_dir, f"{project_bug}", rel_path)

                try:
                    file_lines = read_file_content(abs_path).splitlines()
                except IOError:
                    print(f"Failed to read file {original_file_path}: {e}")

                start0 = h["start_line"]
                end0   = h["end_line"] + 1

                h_scope = classify_single_hunk(file_lines, start0, end0, project_bug)
                hunk_scopes.append(h_scope)

            bug_scope = decide_bug_scope(hunk_scopes)

            if project_bug not in hunks_data:
                hunks_data[project_bug] = {}
            if 'buggy_hunks' not in hunks_data[project_bug]:
                hunks_data[project_bug]['buggy_hunks'] = {}
            for i, hunk in enumerate(hunks):
                hunks_data[project_bug]['buggy_hunks'][f'{i}'] = hunk

            if 'buggy_code' not in hunks_data[project_bug]:
                hunks_data[project_bug]['buggy_code'] = {}
            for i, buggy_code in enumerate(buggy_codes):
                hunks_data[project_bug]['buggy_code'][f'{i}'] = buggy_code

            if 'delineated_bug' not in hunks_data[project_bug]:
                hunks_data[project_bug]['delineated_bug'] = {}
            for i, delineated_code in enumerate(delineated_codes):
                hunks_data[project_bug]['delineated_bug'][f'{i}'] = delineated_code

            hunks_data[project_bug]["contained_scope"] = bug_scope

            hunks_data[project_bug]['bug_count'] = len(buggy_codes)

            d4j_prefix = d4j_test_path_prefix(project, int(bug_id))
            triggered_tests_data = {}
            for idx, (test_path, test_method, clean_err_msg) in enumerate(triggered_tests):
                test_file_path = os.path.join(work_dir, f"{project_bug}", d4j_prefix, *test_path.split(".")) + ".java"
                try:
                    test_content = read_file_content(test_file_path)
                except IOError as e:
                    print(f"Failed to read file {original_file_path}: {e}")
                    continue
                if test_content:
                    method_content = extract_test_method_content(test_content, test_method)
                    if method_content:
                        triggered_tests_data[f'{idx}'] = {
                            'test_path': test_path,
                            'test_method': test_method,
                            'test_code': method_content,
                            'clean_err_msg': clean_err_msg
                        }

            bug_type = determine_bug_type(project, bug_id, defects4j_home)

            hunks_data[project_bug]['triggered_tests'] = triggered_tests_data
            hunks_data[project_bug]['buggy_files'] = buggy_files_data
            hunks_data[project_bug]['bug_report'] = {
                'url': bug_report_url,
                'bug_description': bug_description
            }
            hunks_data[project_bug]['hunk_type'] = bug_type
            hunks_data[project_bug]['hunk_mapping'] = hunk_mapping

    with open(os.path.join(output_dir, 'd4j_dataset.json'), 'w', encoding='utf-8') as json_file:
        json.dump(hunks_data, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Defects4J bugs and create buggy files with localized bug markers.')
    parser.add_argument('--work_dir', type=str, default=os.path.expanduser("~/WORK_DIR"), help='Working directory for output files')
    parser.add_argument('--defects4j_home', type=str, default=os.path.expanduser("~/Desktop/defects4j"), help='Path to the Defects4J home directory')
    parser.add_argument('--output_dir', type=str, default=os.path.join(os.getcwd(), 'config'), help='Output directory for processed bug files')
    parser.add_argument('--json_files_path', type=str, default=os.path.join(os.getcwd(), 'config'), help='Path to the JSON files containing existing buggy code')
    parser.add_argument('--mode', type=str, choices=['block', 'method', 'class', 'file'], default='method')

    args = parser.parse_args()

    process_bugs(PROJECTS, args.work_dir, args.defects4j_home, args.output_dir, args.json_files_path, args.mode)
