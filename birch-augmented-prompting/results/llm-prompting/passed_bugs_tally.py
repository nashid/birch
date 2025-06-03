import argparse
import json
import sys
from pathlib import Path

PROPRIETARY_SUBSTRS = [
    "gemini-2.5-flash",
    "o4-mini",
    "gpt-4.1",
    "nova-pro",
]

OPEN_SOURCE_SUBSTRS = [
    "mistral-large-2407",
    "mistral-large-2402",
    "mistral-7b-instruct",
    "mixtral-8x7b-instruct",
    "llama3-1-405b",
    "llama3-2-90b",
    "llama3-3-70b",
]

TOP5_SUBSTRS = [
    "mistral-large-2407",  # open-source
    "llama3-3-70b",        # open-source
    "gemini-2.5-flash",    # proprietary
    "nova-pro",            # proprietary
    "o4-mini",             # proprietary
]

def main():
    parser = argparse.ArgumentParser(
        description="Summarise bug coverage stats from passed_bugs.json"
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        type=Path,
        default=Path(__file__).parent / "passed_bugs.json",
        help="Path to passed_bugs.json (default: ./passed_bugs.json)"
    )
    args = parser.parse_args()

    try:
        raw = json.load(args.json_file.open())
    except Exception as e:
        sys.exit(f"Error reading JSON: {e}")

    passed = {
        model.lower(): set(entry.get("passed", []))
        for model, entry in raw.items()
    }

    all_bugs = set().union(*passed.values())

    def union_by_substrings(subs):
        result = set()
        for sub in subs:
            for model_name, bugs in passed.items():
                if sub in model_name:
                    result.update(bugs)
        return result

    open_bugs = union_by_substrings(OPEN_SOURCE_SUBSTRS)
    prop_bugs = union_by_substrings(PROPRIETARY_SUBSTRS)
    top5_bugs = union_by_substrings(TOP5_SUBSTRS)

    top5_open_bugs = union_by_substrings([s for s in TOP5_SUBSTRS if s in OPEN_SOURCE_SUBSTRS])
    top5_prop_bugs = union_by_substrings([s for s in TOP5_SUBSTRS if s in PROPRIETARY_SUBSTRS])

    Z = len(all_bugs)
    X = len(open_bugs)
    Y = len(prop_bugs)
    M = len(top5_bugs)
    N = len(top5_open_bugs)
    O = len(top5_prop_bugs)

    # Output
    print("Summary of solved Defects4J bugs")
    print("=" * 40)
    print(f"All 11 models: Z = {Z}")
    print(f"  ├─ open-source aggregate (X):      {X}")
    print(f"  └─ proprietary aggregate (Y):     {Y}\n")
    print("Top-5 models subset:")
    print(f"  total (M):                         {M}")
    print(f"  ├─ open-source subset (N):        {N}")
    print(f"  └─ proprietary subset (O):         {O}")

if __name__ == "__main__":
    main()