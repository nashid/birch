# Defects4J Dataset Description

## Purpose of the Script
The script `d4j_json_creator.py` is designed to process and structure relevant information from the Defects4J dataset, including buggy code, test errors, and bug descriptions, to aid in generating code fixes using large language models (LLMs). The script collects the necessary data, formats it, and prepares it for patch generation and evaluation.

## Description of the Script
The script processes various entries from the Defects4J dataset and provides them in a structured format for use in other components of the Defects4J code repair process. The key entries are:

- **"buggy_code"**:
    - Contains the method or code block surrounding the buggy lines.
    - Main component used to prompt the LLM for a fix.
  
- **"buggy_hunk"**:
    - Contains the actual lines modified in the buggy files, mined from Defects4J's default patches.
    - `<START_BUG>` and `<END_BUG>` markers are inserted around the buggy lines to indicate what needs fixing.
  
- **"delineated_bug"**:
    - Contains the buggy code with the `<START_BUG>` and `<END_BUG>` markers inserted around the buggy hunks.
    - Used in support of buggy code to generate better fixes from the LLM.
  
- **"triggered_test"**:
    - Information about tests that fail due to the buggy code.
    - Includes "test_code" (the source code of failed tests) and "clean_err_msg" (the error message produced after the test fails).
  
- **"bug_description"**:
    - A description of the bug, mined from the URL provided by the `defects4j info` command.
    - Used to provide context and generate better patches.
  
- **"buggy_files", "bug_count"**:
    - Lists buggy files and the number of bugs in a project.
    - Used in patch application logic.
  
- **"hunk_type"**:
    - Categorizes the bug based on lines, hunks, and files.
  
- **"hunk_mapping"**:
    - Maps buggy lines to their corresponding code in the buggy code block.

## Prerequisite to Running the Program
1. **Ensure Java 8 is installed and running**: The code requires `java8` to be installed and running on your machine.
2. **Clone and set up the Defects4J home directory**:
    - Fork the Defects4J repository from `https://github.com/rjust/defects4j` and clone it to your desired directory.
    - Update the following line in the script with the correct path to your defects4j directory:
      ```python
      parser.add_argument('--defects4j_home', type=str, default=os.path.expanduser("~/Desktop/defects4j"), help='Path to the Defects4J home directory')
      ```
3. **Check out all active bugs**:
    - Modify the `defects4j_checkout.sh` script to point to your `DEFECTS4J_HOME` and `WORK_DIR` paths.
    - Run the script using:
      ```bash
      ./defects4j_checkout.sh
      ```
    - Update the following line in the script with your own working directory:
      ```python
      parser.add_argument('--work_dir', type=str, default=os.path.expanduser("~/WORK_DIR"), help='Working directory for output files')
      ```
4. **Ensure all required libraries are installed**.


## Files under Defects4J Dataset
- **`d4j_dataset.json`**:
    - A dataset containing relevant information for all 835 active bugs in the Defects4J dataset.
  
- **`multi_hunk.json`**:
    - A dataset with information for the 372 multi-hunk bugs.

| File                  | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `d4j_dataset.json`     | Contains relevant information for all 835 entries in the Defects4J dataset. |
| `multi_hunk.json`      | Contains information on the multi-hunk bugs for more specific patching.      |

## Concrete Example of Input and Output

### Sample Command
`python d4j_json_creator.py --work_dir <WORKING_DIRECTORY> --defects4j_home <DEFECTS4J_HOME_DIRECTORY> --output_dir <OUTPUT_DIRECTORY>`
`<WORKING_DIRECTORY>` should be the location of the directory you checked out all the D4J bugs to.
`<DEFECTS4J_HOME_DIRECTORY>` should be the location of your local D4J home directory.
`<OUTPUT_DIRECTORY>` should be the desired output location of your dataset file.
This command will create the dataset files based on your defects4j directory and working directory.d4

### Expected Output
```
Chart-2
Chart-4
Chart-14
...
Time-26
```
