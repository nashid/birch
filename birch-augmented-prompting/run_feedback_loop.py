import subprocess
import json
import os
import argparse
from birch.utils.d4j_infra import extract_projects_and_bugs

parser = argparse.ArgumentParser(description='Defects4J Bug Processing Script')
parser.add_argument('--dataset_path', type=str, default="../birch/config/multi_hunk.json",
                    help='Path to the dataset JSON file')
args = parser.parse_args()

DATASET = args.dataset_path

def main():
    # Path to your JSON config file
    dataset_path = DATASET

    # Read (project, bug_id) pairs from JSON
    projects_and_bugs = extract_projects_and_bugs(dataset_path)

    # Loop over each bug and run the script
    for project, bug_id in projects_and_bugs:
        command = f"python d4j_code_repair_redwood.py --model bedrock/us.meta.llama3-3-70b-instruct-v1:0 --project {project} --bug_id {bug_id}"
        print(f"Executing: {command}")
        subprocess.run(command, shell=True)

if __name__ == "__main__":
    main()
