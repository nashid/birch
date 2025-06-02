import os
import toml
from jinja2 import Template

def load_prompts_from_toml(toml_file_path):
    with open(toml_file_path, 'r', encoding='utf-8') as file:
        return toml.load(file)

def generate_feedback_enhanced_prompt(last_code, error_details):
    # Path to your TOML file (unchanged)
    toml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'prompt_configurations', 'prompts_feedback.toml'
    )
    toml_path = os.path.abspath(toml_path)
    prompts = load_prompts_from_toml(toml_path)

    # Load your template
    prompt_key = 'prompt_with_last_code_and_errors'
    template_str = prompts[prompt_key]['template']
    template = Template(template_str)

    # We still categorize errors as before
    categorized_errors = {
        'syntax_errors': [],
        'runtime_errors': [],
        'logic_errors': [],
        'other_errors': []
    }

    # NEW: We'll keep a variable for the full compiler output
    full_compiler_output = ""

    for err in error_details:
        category = err.get('category', 'unknown')
        message = err.get('message', 'unknown')

        if category == 'raw_compiler_output':
            # Store the entire raw output separately
            full_compiler_output = message
            continue

        # Otherwise, handle syntax/runtime/logic/other
        if 'syntax' in category.lower():
            categorized_errors['syntax_errors'].append(f"- [Category: {category}] {message}")
        elif 'runtime' in category.lower():
            categorized_errors['runtime_errors'].append(f"- [Category: {category}] {message}")
        elif 'logic' in category.lower():
            categorized_errors['logic_errors'].append(f"- [Category: {category}] {message}")
        else:
            categorized_errors['other_errors'].append(f"- [Category: {category}] {message}")

    # Convert lists to strings
    prompt_config = {
        'syntax_errors': "\n".join(categorized_errors['syntax_errors']),
        'runtime_errors': "\n".join(categorized_errors['runtime_errors']),
        'logic_errors': "\n".join(categorized_errors['logic_errors']),
        'other_errors': "\n".join(categorized_errors['other_errors'])
    }

    # Prepare the template context
    context = {
        'last_code': last_code,
        'syntax_errors': prompt_config['syntax_errors'],
        'runtime_errors': prompt_config['runtime_errors'],
        'logic_errors': prompt_config['logic_errors'],
        'other_errors': prompt_config['other_errors'],

        # Insert the raw compiler output
        'full_compiler_output': full_compiler_output
    }

    return template.render(context)

