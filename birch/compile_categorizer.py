import os
import re
import argparse

# Error categories and their patterns
error_patterns = {
    "Syntax Errors": [
        re.compile(r"';' expected"),
        re.compile(r"unclosed string literal"),
        re.compile(r"class, interface, or enum expected"),
    ],
    "Type Errors": [
        re.compile(r"incompatible types"),
        re.compile(r"cannot find symbol"),
        re.compile(r"method is undefined for the type"),
    ],
    "Declaration Errors": [
        re.compile(r"variable might not have been initialized"),
        re.compile(r"variable is already defined in method"),
        re.compile(r"cannot resolve symbol"),
    ],
    "Reference Errors": [
        re.compile(r"cannot find symbol"),
        re.compile(r"package does not exist"),
        re.compile(r"class not found"),
    ],
    "Access Modifier Errors": [
        re.compile(r"method has private access"),
        re.compile(r"attempting to assign weaker access privileges"),
    ],
    "Linkage and Import Errors": [
        re.compile(r"cannot access package"),
        re.compile(r"package does not exist"),
        re.compile(r"class file for .+ not found"),
    ],
    "Semantic Errors": [
        re.compile(r"incompatible types"),
        re.compile(r"variable might not have been initialized"),
    ],
    "Configuration and Environment Errors": [
        re.compile(r"could not find or load main class"),
        re.compile(r"no source files"),
        re.compile(r"classpath not set correctly"),
    ],
    "Memory and Resource Errors": [
        re.compile(r"java\.lang\.OutOfMemoryError"),
        re.compile(r"java\.lang\.StackOverflowError"),
    ],
    "Runtime Errors (During Compilation)": [
        re.compile(r"Exception in thread \"main\""),
    ],
}

# Initialize counters for each category
error_counts = {category: 0 for category in error_patterns.keys()}

def categorize_error(line):
    """Categorize a single line of text based on predefined patterns."""
    for category, patterns in error_patterns.items():
        for pattern in patterns:
            if pattern.search(line):
                return category
    return None

def process_file(file_path):
    """Process a .txt file to count categorized errors, stop after the first match."""
    with open(file_path, 'r') as file:
        for line in file:
            category = categorize_error(line)
            if category:
                error_counts[category] += 1
                break  # Stop processing this file after the first match

def process_directory(directory):
    """Iterate over all .txt files in the directory and process them."""
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            process_file(file_path)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Categorize and count errors in .txt files within a directory.')
    parser.add_argument('directory', type=str, help='The path to the directory containing the .txt files')
    
    # Parse the command line arguments
    args = parser.parse_args()

    # Process the specified directory
    process_directory(args.directory)

    # Print the results
    for category, count in error_counts.items():
        print(f"{category}: {count}")

if __name__ == '__main__':
    main()
