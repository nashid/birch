# Defects4J Code‑Repair Scripts

This repository contains several small drivers that wrap our core repair engine in different evaluation modes.

| Script                                 | What it demonstrates                                                                                                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **`d4j_code_repair_feedback_loop.py`** | *Feedback only* — runs the repair loop with automatic test‑suite feedback but **without** prompting for similar examples or enlarged context. |
| **`d4j_code_repair_redwood.py`**       | *Best examples ✚ Best enclosing scope ✚ Feedback* — combines the three extensions below into a single end‑to‑end experiment.                  |

## Extensions implemented

1. **Best examples** – selects the top‑$3$ demonstrations from our curated patch‐pair pool and injects them into the system prompt before each generation step.
2. **Best enclosing scope** – expands the input context for every hunk to the smallest AST scope that fully contains the buggy lines (method, constructor, or field initializer), giving the LM richer semantic cues.
3. **Feedback loop** – after each candidate patch is compiled and tested, the failing‑test diagnostics are converted into natural‑language feedback and appended to the conversation; the LM can then refine its next patch.

> ⚠️ `d4j_code_repair_feedback_loop.py` implements only **3**; `d4j_code_repair_redwood.py` implements **1 + 2 + 3**.
