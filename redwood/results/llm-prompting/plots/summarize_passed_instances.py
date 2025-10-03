import json
import csv

# Load JSON data
with open("../passed_bugs.json", "r") as f:
    data = json.load(f)

# Mapping of full IDs to clean labels
model_name_map = {
    "us.meta.llama3-3-70b-instruct-v1:0": "Llama3.3",
    "mistral.mistral-large-2407-v1:0": "Mistral-2407",
    "us.amazon.nova-pro-v1:0": "Nova-pro",
    "mode_4_model_o4-mini-2025-04-16": "o4-mini",
    "mode_4_model_gemini-2.5-flash-preview-04-17": "Gemini-2.5"
}

# Build rows: (LLM label, BUG_ID)
rows = []
for full_id, short_name in model_name_map.items():
    if full_id in data:
        for bug_id in data[full_id].get("passed", []):
            rows.append((short_name, bug_id))

# Write to CSV
with open("llm_bug_passed_mapping.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["LLM", "BUG_ID"])
    writer.writerows(rows)

print("Saved to llm_bug_passed_mapping.csv")
