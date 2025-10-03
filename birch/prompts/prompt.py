import os
import toml
from jinja2 import Template

def load_prompts_from_toml(toml_file_path):
    with open(toml_file_path, 'r', encoding='utf-8') as file:
        return toml.load(file)

def generate_prompt(buggy_code, delineated_bug, javadoc, bug_description_title, bug_description, test_info_str, prompt_type, bug_type, scope):
    toml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'prompt_configurations', 'prompts.toml'
    )
    toml_path = os.path.abspath(toml_path)
    prompts = load_prompts_from_toml(toml_path)

    prompt_key_map = {
        '1': 'prompt_buggy_code',
        '2': 'prompt_delineation',
        '3': 'prompt_description_delineation',
    }

    if str(prompt_type) in ('1', '2', '3'):
        prompt_key = prompt_key_map[str(prompt_type)]
    elif str(prompt_type) == '4':
        # choose based on scope
        if scope == 'method':
            prompt_key = 'prompt_description_delineation_test_information'
        elif scope == 'class':
            prompt_key = 'prompt_description_delineation_test_information_class'
        elif scope == 'file':
            prompt_key = 'prompt_description_delineation_test_information_file'
        else:
            raise ValueError(f"Invalid scope for prompt_type 4: {scope}")
    else:
        raise ValueError(f"Invalid prompt type: {prompt_type}")

    template_str = prompts[prompt_key]['template']
    template = Template(template_str)

    prompt_headers = {
        "single_line_bug":            "Single-line bugs require fixes at a single location.",
        "single_hunk_3_or_more_lines":"Single-file, one-hunk bugs need edits at one location.",
        "single_file_two_hunks":      "Single-file, multi-hunk bugs need edits at multiple locations within the same file. Multiple prompts may be used to address each hunk separately.",
        "single_file_three_hunks":    "Single-file, multi-hunk bugs need edits at multiple locations within the same file. Multiple prompts may be used to address each hunk separately.",
        "single_file_four_or_more_hunks":"Single-file, multi-hunk bugs need edits at multiple locations within the same file. Multiple prompts may be used to address each hunk separately.",
        "multi_file_two_hunks":       "Multi-file, multi-hunk bugs need edits across multiple files and locations. Multiple prompts may be used to address each hunk separately.",
        "multi_file_three_hunks":     "Multi-file, multi-hunk bugs need edits across multiple files and locations. Multiple prompts may be used to address each hunk separately.",
        "multi_file_four_or_more_hunks":"Multi-file, multi-hunk bugs need edits across multiple files and locations. Multiple prompts may be used to address each hunk separately.",
        "multi_file_multi_hunk":      "Multi-file, multi-hunk bugs need edits across multiple files and locations. Multiple prompts may be used to address each hunk separately."
    }
    prompt_header = prompt_headers[bug_type]

    context = {
        'prompt_header':         prompt_header,
        'buggy_code':            buggy_code,
        'javadoc':               javadoc,
        'delineated_bug':        delineated_bug,
        'bug_description_title': bug_description_title,
        'bug_description':       bug_description,
        'test_info_str':         test_info_str
    }
    return template.render(context)