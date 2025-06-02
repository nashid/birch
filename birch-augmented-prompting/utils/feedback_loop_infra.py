import os
import subprocess
import csv
import json
from birch.llm.llm_api_call import invoke_llm
from birch.prompts.prompt import generate_prompt
from birch.utils.d4j_infra import concatenate_trigger_test_info, strip_code_block
from redwood.prompts.compiler_error_prompts import generate_feedback_enhanced_prompt
from dotenv import load_dotenv
from birch.llm.models import Models
import logging
import re

def get_fix_code(project, bug_id, bug_num, dataset, mode, model, PROMPT_PATH, GENERATED_PATCHES_PATH, MF_DATASET_PATH, API_HOST, scope,  FEEDBACK, last_code, error_details, prompt_text=None):
    current_bug = f"{project}_{bug_id}"
    if current_bug not in dataset:
        print(f"No buggy function found for {current_bug}")
        return None

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
    print(dataset[current_bug]["bug_report"])
    bug_description_title = dataset[current_bug]["bug_report"]["title"]
    bug_description = dataset[current_bug]["bug_report"]["bug_description"]

    test_info_list = concatenate_trigger_test_info(MF_DATASET_PATH, current_bug)
    test_info_str = "\n".join(
        [
            f"This code is buggy because of the following `{len(test_info_list)}` test case failure. "
            "Test code and corresponding error messages will be shown below.\n "
            f"Here is test code {i+1}:\n{test_code}\nand its corresponding error message:\n{error_msg}\n"
            for i, (test_code, error_msg) in enumerate(test_info_list)
        ]
    )

    system_prompt = "You are a Java expert tasked with code repair. Provide only the corrected code."
    if FEEDBACK:
        prompt = generate_feedback_enhanced_prompt(last_code, error_details)
    else:
        prompt = generate_prompt(buggy_code, delineated_bug, javadoc, bug_description_title, bug_description, test_info_str, mode, bug_type, scope)

    if "mixtral" in model.lower():
        # Reference: https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1#instruction-format
        prompt = f"[INST]\n{prompt}[/INST]"
    elif 'llama' in model.lower():
        # Reference: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_1/#prompt-template
        prompt = f"<|start_header_id|>user<|end_header_id|>\n{prompt}<|end_of_text|>"
        system_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}"
    elif 'qwen' in model.lower():
        # Reference: https://huggingface.co/TheBloke/Qwen-7B-Chat-GPTQ#prompt-template-chatml
        prompt = f"<|im_start|>user\n{prompt}<|im_end|>"
        system_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>"

    if not os.path.exists(PROMPT_PATH):
        os.makedirs(PROMPT_PATH)
    suggestion_prompt_file_path = os.path.join(PROMPT_PATH, f'{current_bug}_prompt_{mode}.txt')

    with open(suggestion_prompt_file_path, 'a', encoding='utf-8') as file:
        file.write(prompt)
        file.write("\n\n")

    fixed_code, inference_time = invoke_llm(model, system_prompt, prompt, API_HOST)
    if fixed_code is None:
        return None

    fixed_code = strip_code_block(fixed_code)

    if not os.path.exists(GENERATED_PATCHES_PATH):
        os.makedirs(GENERATED_PATCHES_PATH)
    generated_patches_file_path = os.path.join(
        GENERATED_PATCHES_PATH, f'{current_bug}_generated_patches_{mode}.txt'
    )
    with open(generated_patches_file_path, 'a', encoding='utf-8') as file:
        file.write(fixed_code)
        file.write("\n")

    return fixed_code, inference_time, prompt


def parse_compiler_errors(compiler_output):
    """
    Parse compiler output and extract file names, line numbers, and error messages,
    as well as the category of the error. Also store the entire raw compiler output
    as a separate entry so we can feed it to the LLM.
    """
    error_details = []

    # Capture the entire raw compiler output in one dictionary entry
    # so we can pass it along in the prompt.
    error_details.append({
        'file': None,
        'line': None,
        'message': compiler_output.strip(),
        'category': 'raw_compiler_output'
    })

    lines = compiler_output.split('\n')
    for line in lines:
        # Look for lines containing 'error:'
        if 'error:' in line.lower():
            match = re.search(r'^(.*?):(\d+):\s+(.*)', line)
            if match:
                file_path, line_num, msg = match.groups()
                category = categorize_compiler_error(msg)
                error_details.append({
                    'file': file_path.strip(),
                    'line': line_num.strip(),
                    'message': msg.strip(),
                    'category': category
                })
            else:
                # If the regex does not match, we still keep the line as an error
                category = categorize_compiler_error(line)
                error_details.append({
                    'file': None,
                    'line': None,
                    'message': line.strip(),
                    'category': category
                })
    return error_details

def save_compiler_logs(project, bug_id, error_details, patches, log_file_path):
    """
    Store compiler error details + the patches that caused them
    in a JSON file *exactly* at `log_file_path`.
    """
    log_data = {
        'project': project,
        'bug_id': bug_id,
        'errors': error_details,
        'modified_hunks': patches
    }

    # Ensure the directory for `log_file_path` exists (avoid FileNotFoundError).
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    with open(log_file_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4)

def track_compiler_error_metrics(error_details, metrics_path):
    """
    Track the frequency of specific error types across multiple bugs.
    """
    # Load or initialize metrics
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
    else:
        metrics = {}

    # Known categories
    categories = [
        "syntax_error", 
        "type_error", 
        "undefined_reference", 
        "dependency_issue", 
        "flow_control_issue", 
        "other_error"
    ]
    # Ensure each is present in 'metrics'
    for cat in categories:
        if cat not in metrics:
            metrics[cat] = 0

    for err in error_details:
        cat = err['category']

        # Skip 'raw_compiler_output' entries
        if cat == 'raw_compiler_output':
            continue

        if cat not in metrics:
            cat = "other_error"

        metrics[cat] += 1

    # Save
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)



def categorize_compiler_error(msg):
    """
    Given a compiler error message, classify it into one of several categories:
    - syntax_error
    - type_error
    - undefined_reference
    - dependency_issue
    - flow_control_issue
    - other_error

    You can expand or refine these conditions to match your environment.
    """
    msg_lower = msg.lower()

    # Syntax Errors: e.g., "illegal start of type", "expected" token, etc.
    # (You may add more specific triggers if needed.)
    if ("syntax error" in msg_lower or 
        "illegal start" in msg_lower or 
        "expected" in msg_lower):
        return "syntax_error"

    # Type Errors: e.g., "incompatible types", "bad operand type"
    if ("incompatible types" in msg_lower or
        "bad operand type" in msg_lower or
        "cannot convert" in msg_lower):
        return "type_error"

    # Undefined References: e.g., "cannot find symbol"
    if "cannot find symbol" in msg_lower:
        return "undefined_reference"

    # Dependency Issues: e.g., "package does not exist", "cannot access"
    if ("package does not exist" in msg_lower or
        "cannot access" in msg_lower):
        return "dependency_issue"

    # Flow Control Issues: e.g., "unreachable statement", "infinite loop" (less common in javac logs)
    if "unreachable statement" in msg_lower:
        return "flow_control_issue"

    # If nothing else matches
    return "other_error"
