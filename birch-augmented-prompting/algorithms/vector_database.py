import os
import json
import faiss
import pickle
import argparse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from redwood.algorithms.bm25_algorithm import BM25, TokenizeStructure  
from redwood.algorithms.ast_algorithm import BuildFullASTDataset, load_dataset, P 

def BuildVectorDatabase(dataset_ast, exclude_bug_ids=None, db_path="vector_db.index"):
    vectorizer = TfidfVectorizer()
    vector_db_path = "vector_db.index"
    
    tokenized_structures = []   
    metadata_entries = []       

    for subtree, metadata in dataset_ast:
        bug_id = metadata["bug_id"]
        print(bug_id)
        file_path = metadata["file_path"]  # File path is included, buggy code can be found here

        if exclude_bug_ids and bug_id in exclude_bug_ids:
            print(f"Skipping {bug_id} due to filtering.")
            continue

        # Retrieve the 'buggy_code' directly from the metadata
        buggy_code = metadata.get('buggy_code', '')  # Make sure to get 'buggy_code' from metadata

        # Tokenize the structure to create a vector representation
        tokenized_structure = TokenizeStructure(subtree)
        if not tokenized_structure:
            print(f"Warning: Empty tokenized structure for {bug_id}, skipping.")
            continue

        tokenized_str = " ".join(tokenized_structure)
        tokenized_structures.append(tokenized_str)
        
        # Add the extracted buggy code to the metadata
        metadata['buggy_code'] = buggy_code  # Ensure the buggy code is stored in metadata
        
        metadata_entries.append((tokenized_structure, metadata))

    if not tokenized_structures:
        print("No valid data to store in FAISS. Check dataset and filtering conditions.")
        return

    vectorized = vectorizer.fit_transform(tokenized_structures).toarray()

    max_length = max(len(v) for v in vectorized)  
    padded_vectors = np.array([np.pad(v, (0, max_length - len(v)), 'constant') for v in vectorized])

    print(f"Storing {len(padded_vectors)} vectors in FAISS.")

    dimension = padded_vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(padded_vectors)

    faiss.write_index(index, vector_db_path)
    print(f"FAISS database stored at {vector_db_path}.")

    # Save the updated metadata, which now includes the buggy code
    with open("vector_metadata.pkl", "wb") as f:
        pickle.dump(metadata_entries, f)

    with open("vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    print("Fitted vectorizer saved at vectorizer.pkl.")




def QueryVectorDatabase(query_subtree, k=5, query_bug_id=None, query_hunk_index=None, db_path="vector_db.index"):
    with open("vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    index = faiss.read_index(db_path)

    with open("vector_metadata.pkl", "rb") as f:
        metadata_store = pickle.load(f)

    query_tokens = TokenizeStructure(query_subtree)
    if not query_tokens:
        print("⚠️ Warning: Tokenization resulted in an empty list!")
        return []
    query_string = " ".join(query_tokens)
    query_vector = vectorizer.transform([query_string]).toarray().astype('float32')

    distances, indices = index.search(query_vector, k)

    faiss_results = []
    for i, idx in enumerate(indices[0]):
        metadata = metadata_store[idx][1]  # Get the metadata part (bug information)
        # Skip the results that match the query_bug_id
        if query_bug_id and metadata.get('bug_id') == str(query_bug_id) and metadata.get('hunk_index') == str(query_hunk_index):
            continue
        faiss_results.append((metadata, distances[0][i]))

    # If BM25 corpus is empty, return early
    corpus_tokens = [entry[0] for entry in metadata_store if entry[0]]
    if not corpus_tokens:
        print("Warning: BM25 corpus is empty!")
        return faiss_results

    bm25 = BM25(corpus_tokens)

    top_k_bm25 = bm25.get_top_k(query_tokens, k)

    combined_results = [
        (faiss_metadata, faiss_score + bm25_score)
        for ((faiss_metadata, faiss_score), (bm25_idx, bm25_score)) in zip(faiss_results, top_k_bm25)
    ]

    combined_results = sorted(combined_results, key=lambda x: x[1], reverse=True)

    return combined_results

def QueryVectorDatabaseRAG(query_buggy_code, k=5, metadata_path="vector_metadata.pkl", query_bug_id=None, query_hunk_index=None):
    with open(metadata_path, "rb") as f:
        metadata_store = pickle.load(f)  

    corpus = []
    for _, meta in metadata_store:
        buggy_code_snippet = meta.get("buggy_code", "") or ""
        corpus.append(buggy_code_snippet)

    tokenized_corpus = [snippet.split() for snippet in corpus]

    bm25 = BM25(tokenized_corpus)

    query_tokens = query_buggy_code.split()

    top_k_bm25 = bm25.get_top_k(query_tokens, k)

    results = []
    for doc_idx, score in top_k_bm25:
        meta = metadata_store[doc_idx][1]  
        if (query_bug_id is not None and query_hunk_index is not None and meta.get("bug_id") == str(query_bug_id) and meta.get("hunk_index") == str(query_hunk_index)):
            continue

        results.append((meta, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results






if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Defects4J AST Vector Database")

    parser.add_argument("--dataset_path", type=str, default="../config/method_multihunk.json",
                        help="Path to the dataset JSON file")
    parser.add_argument("--work_dir", type=str, default=os.path.expanduser("~/WORK_DIR"),
                        help="Path to the working directory where bug projects are stored")
    parser.add_argument("--fixed_dir", type=str, default=os.path.expanduser("~/WORK_DIR_FIXED"),
                        help="Path to the working directory where bug projects are stored")
    parser.add_argument("--fixed_json", type=str, default="../config/enclosing_method_context_javaparser_fixed.json",
                        help="Path to the dataset JSON file")
    parser.add_argument("--query_bug_id", type=str, help="Bug ID to query from the vector database")
    parser.add_argument("--exclude_bugs", nargs="*", default=[], help="List of bug IDs to exclude from the database")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top similar ASTs to retrieve")

    args = parser.parse_args()

    if args.query_bug_id is not None and args.query_bug_id not in args.exclude_bugs:
        args.exclude_bugs.append(args.query_bug_id)

    dataset = load_dataset(args.dataset_path)

    dataset_ast = BuildFullASTDataset(dataset, P, args.work_dir, args.fixed_dir, args.fixed_json)

    BuildVectorDatabase(dataset_ast, exclude_bug_ids=set(args.exclude_bugs))

    query_ast = None
    for subtree, metadata in dataset_ast:
        if metadata["bug_id"] == args.query_bug_id:
            query_ast = subtree
            break

    if query_ast is None:
        print(f"Error: Query bug ID {args.query_bug_id} not found in dataset.")
        exit(1)

    top_results = QueryVectorDatabase(query_ast, k=args.top_k)

    print("\nTop-k Similar Subtrees:")
    for metadata, score in top_results:
        print(f"Bug ID: {metadata['bug_id']}, File: {metadata['file_path']}, Score: {score}")
