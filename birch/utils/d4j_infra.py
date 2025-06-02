import os
import subprocess
import csv
import json
from llm.llm_api_call import invoke_llm
from llm.invoke_gemini_flash_no_reasoning import invoke_gemini
from prompts.prompt import generate_prompt
from dotenv import load_dotenv
from llm.models import Models
import logging

def clear_work_dir(work_dir):
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
        return
    
    os.system(f'rm -rf {work_dir}/*')

def extract_projects_and_bugs(dataset_path):
    with open(dataset_path, 'r') as file:
        data = json.load(file)
        
    projects_bugs = []
    for key in data.keys():
        project, bug_id = key.split('_')
        projects_bugs.append((project, int(bug_id)))
    
    return projects_bugs

def strip_code_block(content):
    lines = content.split('\n')
    if lines[0].strip().startswith("```") and lines[-1].strip().startswith("```"):
        return '\n'.join(lines[1:-1]).strip()
    return content.strip()

def write_result_csv(project, bug_id, compile_result, test_result, failed_tests, mode, results_base_path, llm_time, compile_time, test_time):
    results_file_path = os.path.abspath(os.path.join(results_base_path, f"test_results_mode_{mode}.csv"))
    file_exists = os.path.isfile(results_file_path)
    with open(results_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['bug', 'pass', 'test_fail', 'compile_fail', 'failed_tests', 'llm_time', 'compile_time', 'test_time'])
        
        # Determine pass, test_fail, and compile_fail
        pass_status = 'Yes' if test_result == 1 and compile_result == 0 else 'No'
        test_fail = 'Yes' if pass_status == 'No' and compile_result == 0 else 'No'
        compile_fail = 'Yes' if compile_result != 0 else 'No'
        
        writer.writerow([
            f'{project}-{bug_id}', 
            pass_status, 
            test_fail, 
            compile_fail, 
            '; '.join(failed_tests), 
            f'{llm_time:.2f}', 
            f'{compile_time:.2f}', 
            f'{test_time:.2f}'
        ])

    logging.info(f"Results written for {project}-{bug_id}: Pass: {pass_status}, Test Fail: {test_fail}, Compile Fail: {compile_fail}, Failed Tests: {failed_tests}, LLM Time: {llm_time:.2f}, Compile Time: {compile_time:.2f}, Test Time: {test_time:.2f}")

def save_test_results(project, bug_id, stdout, stderr, TEST_RESULT_PATH):
    result_dir = os.path.join(TEST_RESULT_PATH,"{project}_{bug_id}_failed_tests")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    stdout_path = os.path.join(result_dir, f'{project}_{bug_id}_stdout.txt')
    stderr_path = os.path.join(result_dir, f'{project}_{bug_id}_stderr.txt')

    with open(stdout_path, 'w') as f:
        f.write(stdout)
    with open(stderr_path, 'w') as f:
        f.write(stderr)

    logging.info(f"Test results saved for {project}-{bug_id}: stdout -> {stdout_path}, stderr -> {stderr_path}")

def save_compile_results(project, bug_id, stdout, COMPILE_RESULTS_PATH):
    if not os.path.exists(COMPILE_RESULTS_PATH):
        os.makedirs(COMPILE_RESULTS_PATH)

    stdout_path = os.path.join(COMPILE_RESULTS_PATH, f'{project}_{bug_id}_stdout.txt')

    with open(stdout_path, 'w') as f:
        f.write(stdout)

    logging.info(f"Test results saved for {project}-{bug_id}: stdout -> {stdout_path}")

def concatenate_trigger_test_info(json_file_path, current_bug):
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

    if "triggered_tests" not in data[current_bug]:
        print("No 'triggered_tests' key found in the JSON data.")
        return None, None

    test_info_list = []

    for test_id, test_info in data[current_bug]["triggered_tests"].items():
        test_code = test_info.get("test_code", "")
        clean_err_msg = test_info.get("clean_err_msg", "")
        test_info_list.append((test_code, clean_err_msg))

    return test_info_list

def get_fix_code(project, bug_id, bug_num, dataset, mode, model, PROMPT_PATH, GENERATED_PATCHES_PATH, MF_DATASET_PATH, API_HOST, scope):
    current_bug = f"{project}_{bug_id}"
    buggy_code_entry = dataset[current_bug]["buggy_code"][str(bug_num)]
    buggy_code = buggy_code_entry["code"]
    bug_type = dataset[current_bug]["hunk_type"]
    hunk_mapping = dataset[current_bug].get("hunk_mapping", {})

    buggy_hunks = []
    for hunk in hunk_mapping.get(str(bug_num), []):
        buggy_hunks.append(hunk["code"])

    delineated_bug_entry = dataset[current_bug]["delineated_bug"][str(bug_num)]
    delineated_bug = delineated_bug_entry["code"]
    if scope == "file":
        javadoc = ""
    else:
        javadoc = delineated_bug_entry["javadoc"]
    concatenated_hunks = "\n".join(buggy_hunks)
    bug_description_title = dataset[current_bug]["bug_report"]["title"]
    bug_description = dataset[current_bug]["bug_report"]["bug_description"]
    test_info_list = concatenate_trigger_test_info(MF_DATASET_PATH, current_bug)
    test_info_str = "\n".join([f"This code is buggy because of the following `{len(test_info_list)}` test case failure. Test code and corresponding error messages is shown below.\nHere is test code {i+1}:\n{test_code}\nand its corresponding error message:\n{error_msg}\n"
                               for i, (test_code, error_msg) in enumerate(test_info_list)])
    
    system_prompt = "You are a Java expert tasked with code repair. Provide only the corrected code."
    
    if current_bug in dataset:
        prompt = generate_prompt(buggy_code, delineated_bug, javadoc, bug_description_title, bug_description, test_info_str, mode, bug_type, scope)
        # All mixtral models have "mistral." as prefix. Thus, "mistral" covers for all mistral and mixtral models.
        if "mistral" in model.lower():
            #Reference: https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1#instruction-format
            prompt = f"[INST]\n{prompt}[/INST]"
        elif 'llama' in model.lower():
            #Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/#prompt-template
            prompt = f"<|start_header_id|>user<|end_header_id|>\n{prompt}<|end_of_text|>"
            system_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}"
        elif 'qwen' in model.lower():
            #Reference: https://huggingface.co/TheBloke/Qwen-7B-Chat-GPTQ#prompt-template-chatml
            prompt = f"<|im_start|>user\n{prompt}<|im_end|>"
            system_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>"


        if not os.path.exists(PROMPT_PATH):
            os.makedirs(PROMPT_PATH)
        suggestion_prompt_file_path = os.path.join(PROMPT_PATH, f'{current_bug}_prompt_{mode}.txt')
        with open(suggestion_prompt_file_path, 'a', encoding='utf-8') as file:
            file.write(prompt)

        if model == "gemini-2.5-flash-preview-04-17":
            fixed_code, inference_time = invoke_gemini(model, system_prompt, prompt, API_HOST)
        else:
            fixed_code, inference_time = invoke_llm(model, system_prompt, prompt, API_HOST)
        
        if fixed_code is None:
            return None, inference_time, prompt
        fixed_code = strip_code_block(fixed_code)

        if not os.path.exists(GENERATED_PATCHES_PATH):
            os.makedirs(GENERATED_PATCHES_PATH)
        generated_patches_file_path = os.path.join(GENERATED_PATCHES_PATH, f'{current_bug}_generated_patches_{mode}.txt')
        with open(generated_patches_file_path, 'a', encoding='utf-8') as file:
            file.write(fixed_code)
            file.write("\n")
        return fixed_code, inference_time, prompt
    else:
        print(f"No buggy function found for {current_bug}")
        return None

    
def compile_repo(repo_dir_path):
    compile_proc = subprocess.run(
        ['defects4j', 'compile'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=repo_dir_path)
    
    compile_error_lines = compile_proc.stderr.decode('utf-8').split('\n')[2:]
    compile_error_lines = [
        e for e in compile_error_lines if '[javac] [' not in e]
    compile_error_lines = [e for e in compile_error_lines if '[javac]' in e]
    compile_error_lines = [
        e for e in compile_error_lines if 'warning:' not in e]
    compile_error_lines = [
        e for e in compile_error_lines if '[javac] Note:' not in e]
    compile_error_lines = [
        e for e in compile_error_lines if 'compiler be upgraded.' not in e]
    compile_error_msg = '\n'.join(compile_error_lines)
    
    if compile_proc.returncode != 0:
        logging.error(f"Compilation failed for repo {repo_dir_path} with errors: {compile_error_msg}")
    else:
        logging.info(f"Compilation succeeded for repo {repo_dir_path}")

    return compile_proc.returncode, compile_error_msg

def run_test(repo_dir_path):
    '''Returns failing test number and test details.'''
    test_process = subprocess.run(['defects4j', 'test'],
                                  capture_output=True, cwd=repo_dir_path)
    captured_stdout = test_process.stdout.decode()
    captured_stderr = test_process.stderr.decode()

    if len(captured_stdout) == 0:
        logging.error(f"No output from test execution for repo {repo_dir_path}")
        return -1, [], captured_stdout, captured_stderr
    else:
        stdout_lines = captured_stdout.split('\n')
        try:
            failed_test_num = int(stdout_lines[0].removeprefix('Failing tests: '))
            failed_tests = [e.strip(' - ') for e in stdout_lines[1:] if len(e) > 1]
            assert len(failed_tests) == failed_test_num
        except Exception as e:
            logging.error(f"Error parsing test results for repo {repo_dir_path}: {e}")
            return -1, [], captured_stdout, captured_stderr

        if failed_test_num > 0:
            logging.error(f"Test failures for repo {repo_dir_path}: {failed_tests}")
        else:
            logging.info(f"All tests passed for repo {repo_dir_path}")

        return 0, failed_tests, captured_stdout, captured_stderr

def checkout_repo(project, bug_id, work_dir):
    try:
        subprocess.run(['defects4j', 'checkout', '-p', project, '-v', f'{bug_id}b', '-w', f'{work_dir}/{project}_{bug_id}'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Checkout failed for {project}-{bug_id}: {e}")
        return False
    
def load_processed(PROCESSED_FILE):
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    else:
        # Create an empty structure and save it
        processed = {str(i): [] for i in range(1, 5)}
        save_processed(processed, PROCESSED_FILE)
        return processed

def save_processed(processed, PROCESSED_FILE):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(processed, f, indent=4)
