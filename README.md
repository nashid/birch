# BIRCH

This repository contains two main experiments:

1. **LLM-Only Experiment**  
   All code for the LLM-only study can be found in the  
   [`birch_llm_prompting`](./birch_llm_prompting) folder.

2. **Prompt Augmentations**  
   All code for the prompt-augmentation experiments can be found in the  
   [`birch_augmented_prompting`](./birch_augmented_prompting) folder.

## Project Structure
```
.
├── Hunk4J
│   ├── README.md
│   ├── code                          # Python scripts for JSON/metadata creation
│   │   └── utils                     # Helper utilities
│   ├── dataset                       # Multi-hunk metadata JSON files
│   ├── javaparser                    # JavaParser-based AST context extractor
│   │   └── method-line-extractor
│   └── patches                       # Raw `.patch` files for bugs
│
├── birch-llm-prompting
│   ├── README.md                     # LLM-only repair workflow instructions
│   ├── llm                           # LLM API wrappers and model definitions
│   ├── prompt_configurations         # Prompt templates (e.g., `prompts.toml`)
│   ├── prompts                       # Python prompt generators
│   ├── utils                         # Defects4J and LLM helper utilities
│   └── scripts …                     # Scripts for checkout, repair, validation, and result summarization
│
├── birch-augmented-prompting
│   ├── README.md                     # Augmented-technique workflow instructions
│   ├── algorithms                    # Similar-example retrieval, AST/embedding algorithms, etc.
│   ├── hunk4j_statistics             # Scripts & CSVs for multi-hunk descriptive statistics
│   ├── hunk_divergence               # Divergence computation & analysis (Python, R, plots, CSVs)
│   ├── proximity_class               # Spatial-proximity classification tools & plots
│   ├── prompt_configurations         # TOML configs for feedback/retrieval prompts
│   ├── prompts                       # Python modules for compiler-error & similar-result prompts
│   ├── results                       # Results for all experiments with `passed_bugs.json` and summaries
│   ├── solved_bugs_statistics        # CSV reports of which bugs each LLM solved (per scope)
│   └── utils                         # Feedback-loop and general utilities
│
├── images                            # Repository-wide image assets (e.g., birch-image.png)
└── README.md                         # (this file)
```
