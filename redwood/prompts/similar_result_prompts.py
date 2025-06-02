import os
import toml
from jinja2 import Template


def _load_prompt_template(toml_path: str, key: str) -> str:
    """
    Load a Jinja2 template string from a TOML file, given the section key.
    """
    if not os.path.isfile(toml_path):
        raise FileNotFoundError(f"Prompt-configuration file not found: {toml_path}")

    data = toml.load(toml_path)
    if key not in data or "template" not in data[key]:
        raise KeyError(f"Key '{key}.template' not found in {toml_path}")

    return data[key]["template"]


def generate_algorithm_enhanced_prompt(similar_examples, base_prompt):
    """
    Builds a few-shot prompt (no prior feedback) with similar examples.
    """
    toml_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "prompt_configurations",
        "prompts_retrieval.toml",
    )

    template_str = _load_prompt_template(toml_file_path, "prompt_few_shot")
    template = Template(template_str)

    context = {
        "base_prompt": base_prompt,
        "similar_examples": similar_examples,  # list[{buggy_code, fixed_code}]
    }
    return template.render(context)


def generate_algorithm_enhanced_prompt_feedback(similar_examples, last_code):
    """
    Builds a few-shot *feedback* prompt that shows the model's last attempt.
    """
    toml_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "prompt_configurations",
        "prompts_retrieval.toml",
    )

    template_str = _load_prompt_template(toml_file_path, "prompt_few_shot_feedback")
    template = Template(template_str)

    context = {
        "last_code": last_code,
        "similar_examples": similar_examples,  # list[{buggy_code, fixed_code}]
    }
    return template.render(context)
