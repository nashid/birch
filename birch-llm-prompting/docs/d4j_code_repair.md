# BIRCH Code Repair Program

## Purpose of the Script
This script is designed to automate the process of generating, applying, and testing fixes for bugs in the Defects4J dataset using various large language models (LLMs). It builds different types of prompts based on the input mode, sends them to an LLM to suggest fixes, applies the fix, and then compiles and tests the modified code to verify if the LLM-produced fix resolves the bug.

## Command-line Parameters
The script accepts several command-line parameters:

- **--mode** : Specifies the level of information included in the prompt provided to the LLM. Available modes are:
    - **1** : Only the buggy code.
    - **2** : Buggy code + bug markers indicating the start and end points of the bug.
    - **3** : Mode 2 + a description of the bug.
    - **4** : Mode 3 + test code + the error message associated with the bug.

- **--model** : Specifies the LLM model to be prompted. Please type in the full model name. For example:
    - **gpt-4o-2024-08-06** : GPT-4o model.
    - **ollama/llama3.1:405b** : Locally hosted Llama 3.1 model.
    - **claude-3-5-sonnet-20240620**:  Claude 3.5 Sonnet model.

- **--multihunk** : Determines whether to run the multi-hunk or all set of bugs:
    - **yes** : Runs baseline numbers for all 372 multi-hunk bugs in the Defects4J dataset.
    - **no** (default) : Runs for all 835 active bugs in the Defects4J dataset.

- **--api_host** : Specifies the API host for using open-source Ollama models, such as a locally hosted API, without relying on AWS Bedrock.
    - **None** (default)

- **--results_path** : Optional parameter to specify location of the directory containing the results.
    - **None** (default). Default output will have the results stored under `results/` in this repo.

## Concrete Example of Input and Output

### Sample Command
For invoking `GPT-4o` and other API-Based Proprietary Models:

`python d4j_code_repair.py --mode 4 --model gpt-4o-2024-08-06 --multihunk yes`

For invoking `Ollama Llama 3.1` and other Locally Hosted Open-Source Models:

`python d4j_code_repair.py --mode 4 --model ollama/llama3.1:405b --multihunk yes --api_host "http://localhost:11434"`

This command runs the program using mode 4 (buggy code + bug markers + bug description + test code + error message) with the GPT-4o model on all active bugs in the Defects4J dataset.

### Expected Output

```
Checking out c7a581e5 to /tmp/work_dir/Time_26............................. OK
Init local repository...................................................... OK
Tag post-fix revision...................................................... OK
Fix broken build........................................................... OK
Run post-checkout hook..................................................... OK
Excluding broken/flaky tests............................................... OK
Excluding broken/flaky tests............................................... OK
Excluding broken/flaky tests............................................... OK
Initialize fixed program version........................................... OK
Apply patch................................................................ OK
Initialize buggy program version........................................... OK
Diff c7a581e5:218a7fe9..................................................... OK
Apply patch................................................................ OK
Tag pre-fix revision....................................................... OK
Check out program version: Time-26b........................................ OK
Completion obtained
Completion obtained
Completion obtained
Completion obtained
Completion obtained
Completion obtained
Completion obtained
Completion obtained
```
