# Module Overview

This folder contains three Python scripts for running Defects4J bug‐repair experiments. Each script implements a different “mode” of operation and accepts a largely overlapping set of command‐line arguments. Below is a brief description of each script, along with a consolidated list of their command‐line flags, defaults, and usage examples.

## 1. Feedback‐Loop

**Purpose**
When a patch candidate compiles but fails tests, this script invokes a feedback loop to re‐generate/repair until either the tests pass or a maximum number of iterations is reached.

**Key Difference**
• Runs only if test cases compile successfully yet fail.
• Uses the “feedback loop” mechanism to submit new repair attempts.

### Command‐Line Arguments

```text
--work_dir                 Path to a workspace where project checkouts go  
                           (default: "/tmp/work_dir")

--dataset_path             Path to the primary dataset JSON
                           (default: "../birch/config/d4j_dataset.json")

--baseline_dataset_path    Path to an alternate (multi‐hunk) dataset JSON
                           (default: "../birch/config/multi_hunk.json")

--processed_file           Filename for writing/updating processed‐bugs info 
                           (default: "processed.json")

--mode                     Integer [1–4]. 4 = feedback‐loop mode.
                           (default: 4)

--model                    Model name (e.g. "gpt-4" or "o4-mini")  
                           **(required)**  

--multihunk                "yes" or "no": whether to use the multi‐hunk dataset
                           (default: "no")

--api_host                 API host address (if using a self-hosted LLM)  
                           (default: None)

--results_path             Where to write output (defaults to `./results/mode_<MODE>_model_<MODEL>`)

--project                  Defects4J project (e.g. "Lang", "Chart", "Closure", …)  
                           **(required)**  

--bug_id                   Defects4J bug ID (e.g. "1", "2", "3", …)  
                           **(required)**  

--max_iterations           Maximum number of feedback‐loop iterations  
                           (default: 5)
```

### Example Invocation

```bash
python d4j_code_repair_feedback_loop.py \
  --model=gpt-4 \
  --project=Math \
  --bug_id=23 \
  --multihunk=no \
  --max_iterations=5
```

## 2. Feedback with Retriveal Based Example Selection

**Purpose**
This script runs the regular (non–feedback‐loop) repair pipeline. It submits one patch‐generation request per iteration. On test failures, it retrieves a similar example from a chosen retrieval strategy, then continues. On compilation failures, it reports the compile error and halts or moves to the next bug.

**Key Differences**
• No feedback loop for compilation failures—just report the compile error.
• May retrieve similar examples on test failures (depending on “mode”).

### Command‐Line Arguments

```text
--work_dir                    Path to a workspace for project checkouts  
                              (default: "/tmp/work_dir")

--dataset_path                Path to the primary dataset JSON  
                              (default: "../birch/config/d4j_dataset.json")

--baseline_dataset_path       Path to “method” multi-hunk dataset JSON  
                              (default: "./config/method_multihunk.json")

--baseline_block_dataset_path Path to “block” multi-hunk dataset JSON  
                              (default: "./config/block_multihunk.json")

--baseline_class_dataset_path Path to “class” multi-hunk dataset JSON  
                              (default: "./config/class_multihunk.json")

--baseline_file_dataset_path  Path to “file” multi-hunk dataset JSON  
                              (default: "./config/files_multihunk.json")

--processed_file              Filename for processed‐bugs JSON  
                              (default: "processed.json")

--mode                        Integer [1–4].  
                              4 = standard (Redwood) mode  
                              (default: 4)

--model                       Model name (e.g. "gpt-4" or "o4-mini")  
                              **(required)**  

--multihunk                   "yes" or "no": whether to use the multi-hunk dataset  
                              (default: "yes")

--api_host                    API host address (if using a self-hosted LLM)  
                              (default: None)

--results_path                Where to write output  
                              (default: `./results/mode_<MODE>_model_<MODEL>`)

--project                     Defects4J project (e.g. "Lang", "Chart", "Closure", …)  
                              **(required)**  

--bug_id                      Defects4J bug ID (e.g. "1", "2", "3", …)  
                              **(required)**  

--max_iterations              Maximum iterations before giving up  
                              (default: 3)

--method                      Retrieval strategy to use when “mode=4”:
                              • "ast"      — use AST retrieval  
                              • "rag"      — use RAG retrieval  
                              • "emb-ast"  — embedding + AST  
                              • "emb-rag"  — embedding + RAG  
                              • "ada-ast"  — ADA embeddings + AST  
                              • "ada-rag"  — ADA embeddings + RAG  
                              (default: "rag")

--checkout_dir                Path to the directory where you clone projects  
                              (default: `~/WORK_DIR`)

--fixed_dir                   Path to store projects after fixing  
                              (default: `~/WORK_DIR_FIXED`)

--fixed_json                  Path to JSON containing “fixed” context (e.g. enclosing‐method AST)  
                              (default: "./config/enclosing_method_context_javaparser_fixed.json")

--scope                        Granularity of repair: "block", "method", "class", or "file"  
                              (default: "method")
```

### Example Invocation

```bash
python d4j_code_repair_feedback_loop.py \
  --model=o4-mini \
  --project=Closure \
  --bug_id=47 \
  --multihunk=yes \
  --mode=4 \
  --method=emb-rag \
  --max_iterations=3 \
  --scope=class
```

## 3. Retrieval-Based Similar Example Selection

**Purpose**
Runs a single pass (no feedback loop) to compare different retrieval algorithms (e.g. “ada-rag” vs “emb-rag” vs “rag”). Useful to generate one patch per bug from each strategy, and measure differences.

**Key Differences**
• No feedback loop on compilation failure—script simply reports “compilation error.”
• Compares multiple retrieval algorithms in one run.

### Command‐Line Arguments

```text
--work_dir                    Path to a workspace for project checkouts  
                              (default: "/tmp/work_dir")

--dataset_path                Path to the primary dataset JSON  
                              (default: "../birch/config/d4j_dataset.json")

--baseline_dataset_path       Path to “method” multi-hunk dataset JSON  
                              (default: "./config/method_multihunk.json")

--baseline_block_dataset_path Path to “block” multi-hunk dataset JSON  
                              (default: "./config/block_multihunk.json")

--baseline_class_dataset_path Path to “class” multi-hunk dataset JSON  
                              (default: "./config/class_multihunk.json")

--baseline_file_dataset_path  Path to “file” multi-hunk dataset JSON  
                              (default: "./config/files_multihunk.json")

--processed_file              Filename for processed‐bugs JSON  
                              (default: "processed.json")

--mode                        Integer [1–4].  
                              4 = algorithm comparison (no feedback loop)  
                              (default: 4)

--model                       Model name (e.g. "gpt-4" or "o4-mini")  
                              **(required)**  

--multihunk                   "yes" or "no": whether to use the multi-hunk dataset  
                              (default: "yes")

--api_host                    API host address (if using a self-hosted LLM)  
                              (default: None)

--results_path                Where to write output  
                              (default: `./results/mode_<MODE>_model_<MODEL>`)

--project                     Defects4J project (e.g. "Lang", "Chart", "Closure", …)  
                              **(required)**  

--bug_id                      Defects4J bug ID (e.g. "1", "2", "3", …)  
                              **(required)**  

--max_iterations              Maximum per‐algorithm generation attempts  
                              (default: 3)

--method                      Which retrieval algorithm to run (choose exactly one):
                              • "ast"      — AST‐only retrieval  
                              • "rag"      — RAG retrieval  
                              • "emb-ast"  — embedding + AST  
                              • "emb-rag"  — embedding + RAG  
                              • "ada-ast"  — ADA embeddings + AST  
                              • "ada-rag"  — ADA embeddings + RAG  
                              (default: "rag")

--checkout_dir                Path to the directory where you clone projects  
                              (default: `~/WORK_DIR`)

--fixed_dir                   Path to store projects after fixing  
                              (default: `~/WORK_DIR_FIXED`)

--fixed_json                  Path to JSON containing “fixed” context (e.g. enclosing‐method AST)  
                              (default: "./config/enclosing_method_context_javaparser_fixed.json")

--scope                        Granularity of repair: "block", "method", "class", or "file"  
                              (default: "method")
```

### Example Invocation

```bash
python d4j_repair_algorithm.py \
   --mode=4 \
  --multihunk=yes \
  --method=ada-ast \
```
