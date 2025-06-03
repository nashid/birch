import json

# Load JSON data from file
with open("passed_bugs.json", "r") as file:
    data = json.load(file)

# Define model keys
model_keys = [
    "us.meta.llama3-3-70b-instruct-v1:0",
    "mistral.mistral-large-2407-v1:0",
    "us.amazon.nova-pro-v1:0",
    "mode_4_model_gemini-2.5-flash-preview-04-17",
    "mode_4_model_gpt-4.1-2025-04-14",
    "mode_4_model_o4-mini-2025-04-16"
]

# Collect unique passed bugs
unique_bugs = set()
for key in model_keys:
    unique_bugs.update(data.get(key, {}).get("passed", []))

# Output result
print(f"Total unique passed bugs: {len(unique_bugs)}")
