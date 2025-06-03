# RQ2 Plots: Summarizing and Visualizing Plots for Model Families

This directory contains scripts and data used to generate visualizations for the RQ2 analysis of passed bug fixes across different model families.

## Contents

- `llm_bug_passed_mapping.csv`: CSV file mapping LLMs to passed bug IDs.
- `summarize_passed_instances.py`: Python script that processes the CSV and generates summary data.
- `venn_diagram.r`: R script that creates a Venn diagram to visualize overlaps in passed bug fixes across LLM configurations.
- `venn_llm_4_sets.png`: Output image of the generated Venn diagram.

## How to Generate the Plots

1. **Run the Python summarization script:**

   ```bash
   python3 summarize_passed_instances.py
   ```
   
2. **Generate the Venn diagram using R:**

   ```bash
   Rscript venn_diagram.r
   ```   
This will produce `venn_llm_model_families.png`, illustrating overlaps in successful bug resolutions across model families.

