import os
import time
import json
import logging
import re
import argparse

parser = argparse.ArgumentParser(description='Defects4J Bug Processing Script')
parser.add_argument('--work_dir', type=str, default="/tmp/work_dir",
                    help='Working directory')
parser.add_argument('--dataset_path', type=str, default="../birch/config/d4j_dataset.json",
                    help='Path to the dataset JSON file')
parser.add_argument('--baseline_dataset_path', type=str, default="../birch/config/multi_hunk.json",
                    help='Path to the alternate dataset JSON file')
parser.add_argument('--processed_file', type=str, default="processed.json",
                    help='Path to the processed bugs JSON file (will be created/updated in the same directory as the dataset file)')
parser.add_argument('--mode', type=int, choices=range(1, 5), default=4,
                    help='Mode of operation, ranging from 1 to 4')
parser.add_argument('--model', type=str, required=True,
                    help='Model to use (e.g., "gpt-4").')
parser.add_argument('--multihunk', type=str, choices=['yes', 'no'], default='no',
                    help='Use the multi-hunk dataset if "yes", otherwise use the primary dataset.')
parser.add_argument('--api_host', type=str, default=None,
                    help='API host address for connecting to an external service')
parser.add_argument('--results_path', type=str, default=None,
                    help='Optional parameter to configure results directory location. Default: ./results/mode_<MODE>_model_<MODEL>')
parser.add_argument('--project', type=str, required=True,
                    help='Defects4J project name, e.g. Lang, Chart, Closure, Math, Mockito, etc.')
parser.add_argument('--bug_id', type=str, required=True,
                    help='Defects4J bug ID, e.g. 1, 2, 3...')
parser.add_argument('--max_iterations', type=int, default=5,
                    help='Defects4J bug ID, e.g. 1, 2, 3...')
args = parser.parse_args()


dataset_path = args.dataset_path

WORK_DIR = args.work_dir
MODE = args.mode
MODEL = args.model
BASELINE = args.multihunk.lower() == 'yes'
API_HOST = args.api_host
RESULTS_PATH = args.results_path

DATASET_PATH = os.path.abspath(args.baseline_dataset_path) if BASELINE else os.path.abspath(args.dataset_path)
PROCESSED_FILE = os.path.join(os.path.dirname(DATASET_PATH), args.processed_file)

PROJECT = args.project
BUG_ID = args.bug_id
MODE = args.mode
MODEL = args.model
MAX_ITERATIONS = args.max_iterations
RESULTS_PATH = args.results_path
results_base_path = f"./results/mode_{MODE}_model_{MODEL}"
if RESULTS_PATH:
    results_base_path = RESULTS_PATH

# Derive subdirectories
PROMPT_PATH = os.path.join(results_base_path, "suggestion_prompt")
GENERATED_PATCHES_PATH = os.path.join(results_base_path, "generated_patches")
LINUX_PATCHES_PATH = os.path.join(results_base_path, "linux_patches")
TEST_RESULTS_PATH = os.path.join(results_base_path, "test_results")
COMPILE_RESULTS_PATH = os.path.join(results_base_path, "compile_results")
COMPILE_INFO_PATH = os.path.join(results_base_path, "compile_info")
TRAJECTORY_LOGS_PATH = os.path.join(results_base_path, "trajectory_logs")



from birch.utils.d4j_infra import (
    checkout_repo,
    compile_repo,
    run_test,
    write_result_csv,
    save_compile_results,
    save_test_results,
    save_processed,
    clear_work_dir
)
from birch.patch_validation import PatchValidation
from utils.feedback_loop_infra import (
    get_fix_code,
    parse_compiler_errors,
    track_compiler_error_metrics,
    save_compiler_logs,
    categorize_compiler_error,
)
from redwood.prompts.compiler_error_prompts import generate_feedback_enhanced_prompt

def run_birch_with_feedback(
    project,
    bug_id,
    MODE,
    MODEL,
    API_HOST,
    MAX_ITERATIONS=5
):
    
    clear_work_dir(WORK_DIR)

    trajectory_log = {
        "bug_id": f"{project}_{bug_id}",
        "resolution_status": None,  
        "duration_seconds": 0,
        "iterations": []
    }
    start_time = time.time()


    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    current_bug = f"{project}_{bug_id}"
    bug_count = dataset[current_bug]["bug_count"]

    encodings = ['utf-8', 'ISO-8859-1', 'latin-1', 'cp1252']

    total_llm_time = 0
    compile_success = False
    iteration = 0

    all_patches_applied = []

    # We'll attempt multiple compile-fix cycles up to MAX_ITERATIONS
    feedback_prompt = None  # start with the original
    accumulated_patches = []

    while iteration < MAX_ITERATIONS and not compile_success:
        iteration_start = time.time()
        
        if not checkout_repo(project, bug_id, WORK_DIR):
            logging.error(f"Failed to check out {project}-{bug_id}.")
            return
        
        iteration += 1
        logging.info(f"\n[FeedbackLoop] Iteration {iteration} for {project}-{bug_id}")

        iteration_log = {
            "iteration": iteration,
            "hunks": []
        }
        iteration_llm_time = 0
        iteration_patches = []
        for bug_num in range(bug_count - 1, -1, -1):
            patches, llm_time, prompt = get_fix_code(
                project, bug_id, bug_num, dataset, MODE, MODEL,
                PROMPT_PATH,  
                GENERATED_PATCHES_PATH,
                DATASET_PATH,
                API_HOST,
                prompt_text=feedback_prompt  
            )

            iteration_llm_time += llm_time

            hunk_log = {
                "hunk_index": bug_num,
                "input": prompt,
                "output": "\n".join(patches) if isinstance(patches, list) else str(patches),
                "latency_ms": llm_time / 1000.0
            }
            iteration_log["hunks"].append(hunk_log)

            total_llm_time += llm_time
            iteration_patches.extend(patches)

            accumulated_patches.append(patches)

            patch_validator = PatchValidation(patches)
            patch_validator.apply_patch(
                dataset[current_bug],
                os.path.join(
                    WORK_DIR, f'{project}_{bug_id}',
                    dataset[current_bug]["buggy_code"][str(bug_num)]["file"]
                ),
                encodings,
                bug_num,
                current_bug,
                LINUX_PATCHES_PATH,
                MODE
            )

        all_patches_applied.extend(iteration_patches)

        compile_start = time.time()
        compile_returncode, compile_errormsg = compile_repo(
            os.path.join(WORK_DIR, f'{project}_{bug_id}')
        )
        compile_duration = time.time() - compile_start
        compile_time = compile_duration

        if compile_returncode == 0:
            compile_success = True
            logging.info(f"[FeedbackLoop] Compile Succeeded on iteration {iteration}")
        else:
            # 4a. Compile failed => gather errors, update prompt, keep iterating
            error_details = parse_compiler_errors(compile_errormsg)

            # Save logs for this iteration (if desired)
            log_file_path = os.path.join(COMPILE_INFO_PATH, f"{project}_{bug_id}_compile_logs_iter{iteration}.json")
            save_compiler_logs(project, bug_id, error_details, iteration_patches, log_file_path)

            # Track metrics across all runs
            metrics_path = os.path.join(COMPILE_INFO_PATH,  f"{project}_{bug_id}_compiler_error_metrics.json")
            track_compiler_error_metrics(error_details, metrics_path)

            # Write partial outcome for the CSV
            write_result_csv(
                project, bug_id, compile_returncode, -1, [],
                MODE, results_base_path, total_llm_time, compile_time, 0
            )
            # Save the compile error message as well
            save_compile_results(project, bug_id, compile_errormsg, COMPILE_RESULTS_PATH)

            logging.error(f"[FeedbackLoop] Compilation failed for {project}-{bug_id} on iteration {iteration}:\n{compile_errormsg}")
            print(f"[FeedbackLoop] Compilation failed for {project}-{bug_id} on iteration {iteration}:\n{compile_errormsg}")

            # 4b. Build a new prompt with feedback
            feedback_prompt = generate_feedback_enhanced_prompt(accumulated_patches, error_details)


            # If we haven't hit max iterations, we'll do the next iteration
            if iteration < MAX_ITERATIONS:
                logging.info(f"[FeedbackLoop] Re-running with updated prompt... Iteration: {iteration+1}")
                clear_work_dir(WORK_DIR)
            else:
                logging.info(f"[FeedbackLoop] Reached MAX_ITERATIONS={MAX_ITERATIONS}, giving up.")
                clear_work_dir(WORK_DIR)
        iteration_end = time.time()
        iteration_log["time_total_iteration"] = iteration_end - iteration_start
        iteration_log["time_compilation_iteration"] = compile_time
        iteration_log["time_test_iteration"] = test_time
        iteration_log["time_llm_invocation_iteration"] = iteration_llm_time / 1000.0 
            
        trajectory_log["iterations"].append(iteration_log)
    
    # ------------------------------
    # If we exit the loop with compile_success == True, we proceed to test
    # Otherwise, we give up entirely
    # ------------------------------
    if not compile_success:
        return

    # 5. If compile succeeded, run tests once
    test_start_time = time.time()
    test_returncode, failed_tests, stdout, stderr = run_test(
        os.path.join(WORK_DIR, f'{project}_{bug_id}')
    )
    test_end_time = time.time()
    test_time = test_end_time - test_start_time

    test_pass = (test_returncode == 0 and not failed_tests)

    end_time = time.time()
    total_duration = end_time - start_time
    trajectory_log["duration_seconds"] = total_duration

    if compile_success and test_pass:
        trajectory_log["resolution_status"] = "pass"
    elif not compile_success:
        trajectory_log["resolution_status"] = "compilation_failure"
    elif compile_success and not test_pass:
        trajectory_log["resolution_status"] = "test_failure"

    # 6. Write final results
    write_result_csv(
        project, bug_id,
        0 if compile_success else -1,
        test_pass,
        failed_tests if not test_pass else [],
        MODE,
        results_base_path,
        total_llm_time,
        compile_time,
        test_time
    )
    save_test_results(project, bug_id, stdout, stderr, TEST_RESULTS_PATH)

    if not test_pass:
        logging.error(f"[FeedbackLoop] Test failures for {project}-{bug_id}:\nFailed tests: {failed_tests}")
        print(f"[FeedbackLoop] Test failures for {project}-{bug_id}:\nFailed tests: {failed_tests}")

    logs_output_path = os.path.join(TRAJECTORY_LOGS_PATH, f"{current_bug}_trajectory.json")
    os.makedirs(os.path.dirname(logs_output_path), exist_ok=True)

    with open(logs_output_path, 'w', encoding='utf-8') as log_f:
        json.dump(trajectory_log, log_f, indent=4)

    logging.info(f"Trajectory logs saved to: {logs_output_path}")




if __name__ == "__main__":
    run_birch_with_feedback(
        project=PROJECT,
        bug_id=BUG_ID,
        MODE=MODE,
        MODEL=MODEL,
        API_HOST=API_HOST,
        MAX_ITERATIONS=MAX_ITERATIONS
    )