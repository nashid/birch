import os
import json
import argparse
from utils.d4j_infra import write_result_csv, checkout_repo, run_test, compile_repo, get_fix_code, save_test_results, save_compile_results, clear_work_dir, extract_projects_and_bugs, load_processed, save_processed
from patch_validation import PatchValidation
from calculate_results import analyze_results
import logging
import time
from redwood.utils.tokens_counter import count_tokens

parser = argparse.ArgumentParser(description='Defects4J Bug Processing Script')
parser.add_argument('--defects4j_home', type=str, default="/Users/danielding/Desktop/defects4j", help='Path to the Defects4J home directory')
parser.add_argument('--work_dir', type=str, default="/tmp/work_dir", help='Working directory')
parser.add_argument('--dataset_path', type=str, default="./config/d4j_dataset.json", help='Path to the dataset JSON file')
parser.add_argument('--baseline_dataset_path', type=str, default="../redwood/config/method_multihunk.json", help='Path to the alternate dataset JSON file')
parser.add_argument('--baseline_block_dataset_path', type=str, default="../redwood/config/block_multihunk.json", help='Path to the alternate dataset JSON file')
parser.add_argument('--baseline_class_dataset_path', type=str, default="../redwood/config/class_multihunk.json", help='Path to the alternate dataset JSON file')
parser.add_argument('--baseline_file_dataset_path', type=str, default="../redwood/config/files_multihunk.json", help='Path to the alternate dataset JSON file')
parser.add_argument('--processed_file', type=str, default="processed.json", help='Path to the processed bugs JSON file (will be created/updated in the same directory as the dataset file)')
parser.add_argument('--mode', type=int, choices=range(1, 5), default=1, help='Mode of operation, ranging from 1 to 4')
parser.add_argument('--model', type=str, required=True, help='Model to use')
parser.add_argument('--multihunk', type=str, choices=['yes', 'no'], default='no', help='Run with multihunk dataset if "yes", otherwise use the primary dataset')
parser.add_argument('--scope', type=str, choices=['block', 'method', 'class', 'file'], default='method', help='Choose the appropriate scope you want to run the experiment with')
parser.add_argument('--api_host', type=str, default=None, help='API host address for connecting to an external service')
parser.add_argument('--results_path', type=str, default=None, help='Optional parameter to configure results directory location. Default location is results/ under this directory.')

args = parser.parse_args()

DEFECTS4J_HOME = args.defects4j_home
WORK_DIR = args.work_dir
MODE = args.mode
MODEL = args.model
BASELINE = args.multihunk.lower() == 'yes'
API_HOST = args.api_host
RESULTS_PATH = args.results_path
SCOPE = args.scope

if BASELINE:
    if SCOPE == 'block':
        DATASET_PATH = os.path.abspath(args.baseline_block_dataset_path)
    elif SCOPE == 'class':
        DATASET_PATH = os.path.abspath(args.baseline_class_dataset_path)
    elif SCOPE == 'file':
        DATASET_PATH = os.path.abspath(args.baseline_file_dataset_path)
    else:
        DATASET_PATH = os.path.abspath(args.baseline_dataset_path)
else:
    DATASET_PATH = os.path.abspath(args.dataset_path)

PROCESSED_FILE = os.path.join(os.path.dirname(DATASET_PATH), args.processed_file)

results_base_path = f"./results/mode_{MODE}_model_{MODEL}"
if RESULTS_PATH:
    results_base_path = RESULTS_PATH


PROMPT_PATH = os.path.join(results_base_path, "suggestion_prompt")
GENERATED_PATCHES_PATH = os.path.join(results_base_path, "generated_patches")
LINUX_PATCHES_PATH = os.path.join(results_base_path, "linux_patches")
TEST_RESULTS_PATH = os.path.join(results_base_path, "test_results")
COMPILE_RESULTS_PATH = os.path.join(results_base_path, "compile_results")
TRAJECTORY_LOGS_PATH = os.path.join(results_base_path, "trajectory_logs")

def process_bug(project, bug_id, MODE, MODEL, processed):
    clear_work_dir(WORK_DIR)

    trajectory_log = {
        "bug_id": f"{project}_{bug_id}",
        "resolution_status": None,  
        "duration_seconds": 0,
        "hunks": []
    }

    start_time = time.time()


    dataset_path = DATASET_PATH
    dataset = json.load(open(dataset_path, "r"))

    current_bug = f"{project}_{bug_id}"
    bug_count = dataset[current_bug]["bug_count"]

    if not checkout_repo(project, bug_id, WORK_DIR):
        return

    llm_error = False

    encodings = ['utf-8', 'ISO-8859-1', 'latin-1', 'cp1252']

    total_llm_time = 0
    for bug_num in range(bug_count - 1, -1, -1):
        patches, llm_invocation_time, prompt = get_fix_code(project, bug_id, bug_num, dataset, MODE, MODEL, PROMPT_PATH, GENERATED_PATCHES_PATH, DATASET_PATH, API_HOST, SCOPE)
        if patches is None:
            llm_error = True
            continue
        input_tokens = count_tokens(prompt)
        output = "\n".join(patches) if isinstance(patches, list) else str(patches)
        output_tokens = count_tokens(output)
        hunk_log = {
                "hunk_index": bug_num,
                "input": prompt,
                "output": "\n".join(patches) if isinstance(patches, list) else str(patches),
                "latency_ms": llm_invocation_time / 1000.0,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        trajectory_log["hunks"].append(hunk_log)
        patch_validation = PatchValidation(patches)
        
        patch_validation.apply_patch(dataset[current_bug], os.path.join(WORK_DIR, f'{project}_{bug_id}', dataset[current_bug]["buggy_code"][str(bug_num)]["file"]), encodings, bug_num, current_bug, LINUX_PATCHES_PATH, MODE)
    total_llm_time += llm_invocation_time

    compile_start_time = time.time()
    compile_returncode, compile_errormsg = compile_repo(os.path.join(WORK_DIR, f'{project}_{bug_id}'))
    compile_end_time = time.time()
    compile_time = compile_end_time - compile_start_time if compile_returncode == 0 else 0

    if compile_returncode != 0:
        write_result_csv(project, bug_id, compile_returncode, -1, [], MODE, results_base_path, total_llm_time, compile_time, 0)
        save_compile_results(project, bug_id, compile_errormsg, COMPILE_RESULTS_PATH)
        logging.error(f"Compilation failed for {project}-{bug_id}:\n{compile_errormsg}")
        print(f"Compilation failed for {project}-{bug_id}:\n{compile_errormsg}")
        processed[str(MODE)].append(current_bug)
        save_processed(processed, PROCESSED_FILE)
        end_time = time.time()
        total_duration = end_time - start_time
        trajectory_log["duration_seconds"] = total_duration
        if llm_error:
            trajectory_log["resolution_status"] = "llm_failure"
        else:
            trajectory_log["resolution_status"] = "compile_failure"
        logs_output_path = os.path.join(TRAJECTORY_LOGS_PATH, f"{current_bug}_trajectory.json")
        os.makedirs(os.path.dirname(logs_output_path), exist_ok=True)

        with open(logs_output_path, 'w', encoding='utf-8') as log_f:
            json.dump(trajectory_log, log_f, indent=4)

        logging.info(f"Trajectory logs saved to: {logs_output_path}")
        return

    test_start_time = time.time()
    test_returncode, failed_tests, stdout, stderr = run_test(os.path.join(WORK_DIR, f'{project}_{bug_id}'))
    test_end_time = time.time()
    test_time = test_end_time - test_start_time

    test_pass = test_returncode == 0 and len(failed_tests) == 0

    write_result_csv(project, bug_id, compile_returncode, test_pass, failed_tests, MODE, results_base_path, total_llm_time, compile_time, test_time)
    save_test_results(project, bug_id, stdout, stderr, TEST_RESULTS_PATH)

    if not test_pass:
        logging.error(f"Test failures for {project}-{bug_id}:\nFailed tests: {failed_tests}")
        print(f"Test failures for {project}-{bug_id}:\nFailed tests: {failed_tests}")

    # Add processed bug to the processed list
    processed[str(MODE)].append(current_bug)
    save_processed(processed, PROCESSED_FILE)

    end_time = time.time()
    total_duration = end_time - start_time
    trajectory_log["time_compilation_iteration"] = compile_time
    trajectory_log["time_test_iteration"] = test_time
    trajectory_log["duration_seconds"] = total_duration

    if llm_error:
        trajectory_log["resolution_status"] = "llm_failure"
    else:
        if test_pass:
            trajectory_log["resolution_status"] = "pass"
        else:
            trajectory_log["resolution_status"] = "test_failure"

    logs_output_path = os.path.join(TRAJECTORY_LOGS_PATH, f"{current_bug}_trajectory.json")
    os.makedirs(os.path.dirname(logs_output_path), exist_ok=True)

    with open(logs_output_path, 'w', encoding='utf-8') as log_f:
        json.dump(trajectory_log, log_f, indent=4)

    logging.info(f"Trajectory logs saved to: {logs_output_path}")

if __name__ == "__main__":
    processed = load_processed(PROCESSED_FILE)
    PROJECTS = extract_projects_and_bugs(DATASET_PATH)

    unprocessed_projects = [entry for entry in PROJECTS if f"{entry[0]}_{entry[1]}" not in processed[str(MODE)]]

    if not unprocessed_projects:
        # Clear processed.json if all bugs are processed
        save_processed({str(i): [] for i in range(1, 5)}, PROCESSED_FILE)
        print("All bugs have been processed. Processed file cleared.")
    else:
        for entry in unprocessed_projects:
            project, bug_id = entry
            bug_id = int(bug_id)
            process_bug(project, bug_id, MODE, MODEL, processed)
        input_csv = os.path.abspath(os.path.join(results_base_path, f"test_results_mode_{MODE}.csv"))
        output_csv = os.path.abspath(os.path.join(results_base_path, f"test_statistics_mode_{MODE}.csv"))
        analyze_results(input_csv, output_csv)