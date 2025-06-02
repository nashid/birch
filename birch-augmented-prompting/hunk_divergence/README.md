# README: Patch Divergence Scores and Repair Outcomes

## Files

### `bugwise_average_divergence.csv`
- **Path:** [`birch/redwood/hunk_divergence_v4_bleu/bugwise_average_divergence.csv`](https://github.com/testcue/birch/blob/main/redwood/hunk_divergence_v4_bleu/bugwise_average_divergence.csv)
- **Description:** Contains the average hunk divergence scores for each bug.
- **Format:** CSV with multiple columns for divergence components, it also contains the `avg_divergence`, i.e.:
  - `bug_id`: Unique identifier for each bug (e.g., `Chart_10`)
  - `avg_divergence`: Average divergence score

### `passed_bugs.json`
- **Path:** [`birch/redwood/results/rq2/passed_bugs.json`](https://github.com/testcue/birch/blob/main/redwood/results/rq2/passed_bugs.json)
- **Description:** Lists the bugs successfully repaired by each model configuration evaluated in our study.
- **Format:** JSON object where keys are model/prompt configuration names and values are lists of bug IDs they successfully repaired.

## Scripts
- [llm_divergence_faceted_violin_plot.py](plots/llm_divergence_faceted_violin_plot.py)
  - Install Dependencies
    - `conda install pandas`
    - `conda install seaborn`
  - Run `python llm_divergence_faceted_violin_plot.py`
