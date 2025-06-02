# Experiments - RQ2

| Mode | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| Baseline | Llama 3.3   | 39 | 90 | 240 | 0 |372  | 10.57% |
| AST-based examples, BM25 |  Llama 3.3   | 45    | 82           | 245                 | 0          | 372       | 12.10%    |
| AST-based examples, MiniLM|  Llama 3.3   | 32    | 81           | 259                 | 0          | 372       | 8.60%    |
| Code as token, BM25 |  Llama 3.3   | 53    | 85           | 234                 | 0          | 372       | 14.25%    |
| Code as token, MiniLM |  Llama 3.3   | 50    | 73           | 249                 | 0          | 372       | 13.44%    |
| AST-based examples, BM25, feedback loop |  Llama 3.3   | 54    | 78           | 240                 | 0          | 372       | 14.51%    |
| AST-based examples, MiniLM, feedback loop |  Llama 3.3   | 47    | 87           | 238                 | 0          | 372       | 12.63%    |
| Code as token, BM25, feedback loop |  Llama 3.3   | 53    | 81           | 238                 | 0          | 372       | 14.25%    |
| Code as token, MiniLM, feedback loop |  Llama 3.3   | 58    | 81           | 233                 | 0          | 372       | 15.59%    |


