# RQ3 Results

## Best Open Source (Llama 3.3)
| Code as Examples | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| **AST, BM25** | Llama 3.3   | 64 | 76 | 232 | 0	| 372	| 17.20% |
| **Token, BM25** | Llama 3.3   | 70 | 75 | 227 | 0	| 372	| 18.82% |
| **AST, MiniLM** | Llama 3.3   | 42 | 96 | 234 | 0	| 372	| 11.29% |
| **Token, MiniLM** | Llama 3.3   | 69 | 75 | 228 | 0	| 372	| 18.55% |
| **AST, text-embedding-3-small** | Llama 3.3   | 41 | 94 | 237 | 0	| 372	| 11.02% |
| **Token, text-embedding-3-small** | Llama 3.3   | 75 | 77 | 220 | 0	| 372	| 20.16% |

## Best Closed Source (o4-mini)
| Code as Examples | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| **AST, BM25** | o4-mini   | 106 | 66 | 200 | 0	| 372	| 28.49% |
| **Token, BM25** | o4-mini   | 111 | 57 | 204 | 0	| 372	| 29.84% |
| **AST, MiniLM** | o4-mini    | 91 | 74 | 207 | 0	| 372	| 24.46% |
| **Token, MiniLM** | o4-mini   | 114 | 57 | 201 | 0	| 372	| 30.65% |
| **AST, text-embedding-3-small** | o4-mini    | 88 | 79 | 205 | 0	| 372	| 23.66% |
| **Token, text-embedding-3-small** | o4-mini    | 116 | 59 | 197 | 0	| 372	| 31.18% |
