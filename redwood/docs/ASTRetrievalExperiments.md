# Defects4J AST Vector Database

This repository provides functionality to build a vector database for storing and querying Abstract Syntax Tree (AST) representations of buggy code extracted from the **Defects4J dataset**. The database is built using **FAISS** for efficient nearest neighbor search, and BM25 is used for additional ranking.

## **Installation**
Ensure you have the necessary dependencies installed:

```bash
pip install faiss-cpu numpy scikit-learn
```

For BM25 support:
```bash
pip install rank-bm25
```

For parsing Java ASTs:
```bash
pip install javalang
```

---

## **Usage**
### **1. Build the Vector Database**
Run the following command to process the dataset, extract ASTs, and store them in FAISS:

```bash
python vector_database.py
```

This command will:
- Parse all Java files in the dataset.
- Extract ASTs for buggy hunks.
- Convert ASTs to tokenized structures.
- Store the vectors in **FAISS**.
- Exclude bugs **Chart_3** and **Lang_2** from indexing.

#### **Optional Arguments**:
| Argument          | Description |
|------------------|-------------|
| `--dataset_path` | Path to the Defects4J dataset JSON file *(default: ./birch/config/multi_hunk.json)* |
| `--work_dir` | Path to the directory where bug projects are stored *(default: /Users/danielding/WORK_DIR/)* |
| `--exclude_bugs` | List of bug IDs to exclude from the database |

---

### **2. Query the Vector Database**
To search for the most similar ASTs for a given bug:

```bash
python vector_database.py --query_bug_id Chart_2 --top_k 5
```

This command will:
- Tokenize the AST of **Chart_2**.
- Retrieve the top **5** most similar ASTs from the FAISS database.
- Rank them using **BM25** for improved search quality.

#### **Optional Arguments**:
| Argument          | Description |
|------------------|-------------|
| `--query_bug_id` | Bug ID to query from the vector database |
| `--top_k` | Number of similar ASTs to retrieve *(default: 5)* |

---

## **How It Works**
1. **BuildFullASTDataset:** Extracts ASTs from Java files.
2. **TokenizeStructure:** Converts ASTs into structured tokens.
3. **BuildVectorDatabase:**
   - Converts ASTs into TF-IDF vectors.
   - Stores vectors in FAISS for fast retrieval.
   - Saves metadata for bug tracking.
4. **QueryVectorDatabase:**
   - Tokenizes the query AST.
   - Retrieves the closest matches using FAISS.
   - Ranks results using BM25.

---

## **Example Output**
```
Top-k Similar Subtrees:
Bug ID: Lang_10, File: /Users/danielding/WORK_DIR/Lang_10/src/org/apache/commons/lang/StringUtils.java, Score: 0.89
Bug ID: Chart_7, File: /Users/danielding/WORK_DIR/Chart_7/source/org/jfree/chart/plot/Plot.java, Score: 0.85
```

#### **3. Running the Repair Program with Algorithms
Run the following commands:
`python d4j_code_repair.py --mode 4 --model bedrock/meta.llama3-1-405b-instruct-v1:0 --multihunk yes`
