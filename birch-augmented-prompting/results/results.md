# RQ2 Table
# Enclosing Scope

| Mode | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| Birch | Llama 3.3   | 22 | 30 | 303 | 17	| 372	| 5.91% |
| Retrieval based (AST-based examples, BM25, without feedback loop) | Llama 3.3  | 25    | 36           | 310                 | 1          | 372       | 6.74%    |
| Redwood (AST-based examples, BM25, with feedback loop)|  Llama 3.3   | 46    | 88           | 238                 | 0          | 372       | 12.37%   

# Method Scope

| Mode | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| Birch | Llama 3.3   | 39 | 90 | 240 | 0 |372	| 10.57% |
| Redwood (AST-based examples, BM25, without feedback loop)|  Llama 3.3   | 45    | 82           | 245                 | 0          | 372       | 12.10%    |
| Retrieval based (Src-based examples, MiniLM embedding, without feedback loop) |  Llama 3.3   | 50    | 73           | 249                 | 0          | 372       | 13.44%    |
| Retrieval based (Src-based examples, BM25, without feedback loop) |  Llama 3.3   | 53    | 85           | 234                 | 0          | 372       | 14.25%    |
| Redwood (AST-based examples, MiniLM embedding, without feedback loop) |  Llama 3.3   | 32    | 81           | 259                 | 0          | 372       | 8.60%    |
| Redwood (AST-based examples, BM25, with feedback loop)|  Llama 3.3   | 54    | 78           | 240                 | 0          | 372       | 14.51%    |
| Retrieval based (Src-based examples, MiniLM embedding, with feedback loop) |  Llama 3.3   | 58    | 81           | 233                 | 0          | 372       | 15.59%    |
| Retrieval based (Src-based examples, BM25, with feedback loop) |  Llama 3.3   | 53    | 81           | 238                 | 0          | 372       | 14.25%    |
| Redwood (AST-based examples, MiniLM embedding, with feedback loop) |  Llama 3.3   | 47    | 87           | 238                 | 0          | 372       | 12.63%    |

# RQ3 Table
# Enclosing Scope

| Enclosing Scope | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| Method | Llama 3.3   | 39 | 90 | 240 | 0	| 372	| 10.47% |
| Block | Llama 3.3   | 24 | 51 | 297 | 0	| 372	| 6.45% |
| Class | Llama 3.3   | 7 | 26 | 337 | 2	| 372	| 1.89% |
| File | Llama 3.3   | 6 | 10 | 356 | 0	| 372	| 1.61% |

| Enclosing Scope | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| Method | Llama 3.3   | 41 | 62 | 269 | 0	| 372	| 11.02% |
| Class | Llama 3.3   | 30 | 78 | 197 | 67	| 372	| 8.06% |
| File | Llama 3.3   | 39 | 95 | 163 | 70	| 372	| 10.48% |

- **Solution 1:**
- Results after forcing  LLM to return complete Class and File level code:

| Enclosing Scope | Model | Pass | Test Failure | Compilation Failure | LLM Failure | Total Bugs | Accuracy |
|------|-------|------|--------------|---------------------|------------|-----------|----------|
| Class | Llama 3.3   | 28 | 87 | 203 | 49	| 372	| 7.53% |
| File | Llama 3.3   | 39 | 102 | 170 | 61	| 372	| 1.61% |

- **Solution 2:**
  1. We prompt the LLM with full Class/File scopes with Few-Shot Prompting.  
  2. The LLM returns only the correct method/scope that contains the buggy lines.
  3. We obtain the correct code by the LLM, and apply it to the corresponding buggy method/scope.
  4. Few-Shot Example:
  ```
  ** Our Current Prompt **
  ** Study the examples below and generate a single corrected Java code snippet that incorporates any needed changes following its format: **
  // Buggy
  package mypkg;
  import a.b;
  
  public class Example {
      public void foo() {
          <START_BUG>
          buggy line
          <END_BUG>
      }
  }

  // Fixed
    public void foo() {
          // corrected line
    }
