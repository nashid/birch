#!/bin/bash

# Script: create_archive.sh
# Purpose: Archives specified files and directories safely for phase 2 deliverables

# Define the archive name with dynamic date and hardcoded version
DATE=$(date +%Y%m%d)
OUTPUT_ARCHIVE="birch_${DATE}.tar.gz"

# Top-level directory for archive contents
HUNK_DIR="birch"

# Directories to include in the archive
INCLUDE_DIRS=(
    "config"
    "docs"
    "llm"
    "prompt_configurations"
    "prompts"
    "utils"
    "results"
    "images"
)

# Additional files to include from the home directory
HOME_FILES=(
    ".gitignore"
    "README.md"
    "calculate_results.py"
    "compile_categorizer.py"
    "d4j_code_repair.py"
    "d4j_json_creator.py"
    "defects4j_checkout.sh"
    "llm-code-repair-env.yml"
    "patch_validation.py"
    "d4j_repair_ollama.sh"
    "create_archive.sh"
)

# Files or directories to exclude
EXCLUDE_ITEMS=(
    "docs/vm_setup.md"
    "sow"
    "**/__pycache__"
)

# Temporary directory for safe processing
TMP_DIR=$(mktemp -d)

# Ensure cleanup on exit
trap "rm -rf $TMP_DIR" EXIT

# Create the top-level directory inside the temporary directory
mkdir -p "$TMP_DIR/$HUNK_DIR"

# Copy directories into the hunk directory
echo "Copying directories..."
for dir in "${INCLUDE_DIRS[@]}"; do
    cp -r "$dir" "$TMP_DIR/$HUNK_DIR/" 2>/dev/null || echo "Warning: Directory $dir not found and will be skipped."
done

# Copy additional home files into the hunk directory
echo "Copying home files..."
for file in "${HOME_FILES[@]}"; do
    cp "$file" "$TMP_DIR/$HUNK_DIR/" 2>/dev/null || echo "Warning: File $file not found and will be skipped."
done

# Exclude unwanted files or directories
echo "Excluding specified items..."
for exclude in "${EXCLUDE_ITEMS[@]}"; do
    find "$TMP_DIR/$HUNK_DIR" -path "$TMP_DIR/$HUNK_DIR/$exclude" -exec rm -rf {} + 2>/dev/null
done

# Create the tar.gz archive
echo "Creating archive..."
tar -czvf "$OUTPUT_ARCHIVE" -C "$TMP_DIR" "$HUNK_DIR"

# Confirm completion
if [ $? -eq 0 ]; then
    echo "Archive $OUTPUT_ARCHIVE created successfully."
else
    echo "Error creating archive. Please check the output above."
    exit 1
fi
