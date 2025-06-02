import argparse
import csv
import re
from pathlib import Path
from typing import Tuple, Literal


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sum tokens (and cost) in suggestion_prompt/ and "
                    "generated_patches/ for every model directory."
    )
    p.add_argument(
        "--results_dir",
        default="/Users/danielding/Desktop/hunk-results/paper-empirical-study",
        help="Root directory that contains rq2-baseline/, rq3-retrieval/, "
             "rq4-context-scope/, rq5-feedback-loop/ (default: ../results)",
    )
    p.add_argument(
        "--output_csv",
        default="run_token_counts.csv",
        help="Output CSV path (default: run_token_counts.csv)",
    )
    p.add_argument(
        "--encoding",
        default="cl100k_base",
        help="tiktoken encoding (default: cl100k_base). "
             "Ignored if tiktoken not installed.",
    )
    return p.parse_args()

try:
    import tiktoken

    def get_token_count(text: str, enc_name: str = "cl100k_base") -> int:
        enc = tiktoken.get_encoding(enc_name)
        return len(enc.encode(text))

except ModuleNotFoundError:
    print("[WARN] tiktoken not installed; falling back to whitespace tokeniser.")

    def get_token_count(text: str, enc_name: str | None = None) -> int:  
        return len(re.findall(r"\S+", text))


RQ_PATHS = [
    ("rq2-baseline",      "rq2"),
    ("rq3-retrieval",     "rq3"),
    ("rq4-context-scope", "rq4"),
    ("rq5-feedback-loop", "rq5"),
]

BEDROCK_UNIT = 1_000
OTHER_UNIT   = 1_000_000

PRICING: list[tuple[str, Tuple[float, float, int]]] = [
    # Bedrock models
    ("nova-pro",           (0.0008,  0.0032, BEDROCK_UNIT)),
    ("llama3-3-70b",       (0.00072, 0.00036, BEDROCK_UNIT)),
    ("llama3-2-90b",       (0.00072, 0.00036, BEDROCK_UNIT)),
    ("llama3-1-405b",      (0.0024,  0.0012,  BEDROCK_UNIT)),
    ("mistral-7b",         (0.00015, 0.0,     BEDROCK_UNIT)),
    ("mixtral-8x7b",       (0.00045, 0.0,     BEDROCK_UNIT)),
    ("mistral-large-2402", (0.004,   0.0,     BEDROCK_UNIT)),
    ("mistral-large-2407", (0.002,   0.0015,  BEDROCK_UNIT)),
    # Non-Bedrock models
    ("gemini-2.5-flash",   (0.15,    0.60,    OTHER_UNIT)),
    ("gpt-4.1",            (2.0,     8.0,     OTHER_UNIT)),
    ("o4-mini",            (1.10,    4.40,    OTHER_UNIT)),
]

def lookup_pricing(model_dir_name: str) -> Tuple[float, float, int]:
    name = model_dir_name.lower()
    for substr, (in_price, out_price, unit) in PRICING:
        if substr in name:
            return in_price, out_price, unit
    print(f"[WARN] Pricing not found for '{model_dir_name}' - cost set to $0.")
    return 0.0, 0.0, 1


def count_tokens_in_folder(folder: Path, enc_name: str) -> int:
    total = 0
    if not folder.is_dir():
        return 0
    for txt in folder.glob("*.txt"):
        try:
            text = txt.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = txt.read_text(encoding="latin-1", errors="ignore")
        total += get_token_count(text, enc_name)
    return total


def main() -> None:
    args = parse_args()
    root = Path(args.results_dir).resolve()

    rows: list[dict[str, float | int]] = []

    for outer_dir, rq in RQ_PATHS:
        rq_dir = root / outer_dir / rq
        if not rq_dir.is_dir():
            print(f"[WARN] {rq_dir} missing - skipping.")
            continue

        for model_dir in rq_dir.iterdir():
            if not model_dir.is_dir():
                continue

            prompt_dir = model_dir / "suggestion_prompt"
            patch_dir  = model_dir / "generated_patches"

            input_tok  = count_tokens_in_folder(prompt_dir, args.encoding)
            output_tok = count_tokens_in_folder(patch_dir, args.encoding)
            total_tok  = input_tok + output_tok

            in_price, out_price, unit = lookup_pricing(model_dir.name)

            input_cost  = (input_tok  / unit) * in_price
            output_cost = (output_tok / unit) * out_price
            total_cost  = input_cost + output_cost

            rows.append({
                "model":         f"{outer_dir}/{rq}/{model_dir.name}",
                "input_tokens":  input_tok,
                "output_tokens": output_tok,
                "total_tokens":  total_tok,
                "input_cost":    round(input_cost,  4),
                "output_cost":   round(output_cost, 4),
                "total_cost":    round(total_cost, 4),
            })

    rows.sort(key=lambda r: r["model"])

    fieldnames = [
        "model",
        "input_tokens", "output_tokens", "total_tokens",
        "input_cost",   "output_cost",   "total_cost",
    ]

    with Path(args.output_csv).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✔ Token counts and costs written to {args.output_csv}")


if __name__ == "__main__":
    main()
