import os
import json
import faiss
import pickle
import argparse
import numpy as np

from sentence_transformers import SentenceTransformer

from redwood.algorithms.ast_algorithm import BuildFullASTDataset, load_dataset, P

from redwood.algorithms.bm25_algorithm import TokenizeStructure

def embed_text_sliding_window(embed_model, text: str,
                              window_size: int = 256,
                              overlap: int = 64) -> np.ndarray:
    words = text.split()
    n = len(words)
    # fast path
    if n <= window_size:
        emb = embed_model.encode(text, show_progress_bar=False)
        return np.array(emb, dtype="float32")

    # build sliding windows
    chunks = []
    start = 0
    while start < n:
        end = min(start + window_size, n)
        chunks.append(" ".join(words[start:end]))
        if end == n:
            break
        start += window_size - overlap

    # embed all chunks in batch
    embs = embed_model.encode(chunks, show_progress_bar=False)
    embs = np.array(embs, dtype="float32")
    # mean-pool
    return embs.mean(axis=0)


def BuildEmbeddingDatabase(
    dataset_ast,
    model_name='all-MiniLM-L6-v2',
    exclude_bug_ids=None,
    emb_db_path="embedding_db.index",
    window_size: int = 512,
    overlap: int = 64
):
    print(f"Loading embedding model: {model_name}")
    embed_model = SentenceTransformer(model_name)

    embeddings = []
    metadata_entries = []

    for subtree, metadata in dataset_ast:
        bug_id = metadata["bug_id"]
        print(bug_id)
        if exclude_bug_ids and bug_id in exclude_bug_ids:
            print(f"Skipping {bug_id} due to filtering.")
            continue

        buggy_code = metadata.get("buggy_code", "").strip()
        if not buggy_code:
            print(f"Warning: Empty buggy_code for bug_id={bug_id}, skipping.")
            continue

        snippet_embedding = embed_text_sliding_window(
            embed_model, buggy_code, window_size, overlap
        )
        embeddings.append(snippet_embedding)

        ast_tokens = TokenizeStructure(subtree)
        metadata["ast_tokens"] = ast_tokens

        metadata_entries.append(metadata)

    if not embeddings:
        print("No valid embeddings created. Check dataset or filtering.")
        return

    # Build the Faiss index
    embeddings_array = np.vstack(embeddings)
    dim = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_array)

    print(f"Storing {len(embeddings_array)} embedding vectors in FAISS (dimension={dim}).")
    faiss.write_index(index, emb_db_path)
    print(f"FAISS embedding database stored at {emb_db_path}.")

    meta_path = os.path.splitext(emb_db_path)[0] + "_metadata.pkl"
    with open(meta_path, "wb") as f:
        pickle.dump(metadata_entries, f)
    print(f"Saved embedding metadata to {meta_path}.")


def QueryEmbeddingDatabaseEmb(
    query_buggy_code,
    k=5,
    model_name='all-MiniLM-L6-v2',
    db_path="embedding_db.index",
    query_bug_id=None,
    query_hunk_index=None,
    window_size: int = 512,
    overlap: int = 64
):
    embed_model = SentenceTransformer(model_name)

    query_embedding = embed_text_sliding_window(
        embed_model, query_buggy_code, window_size, overlap
    )[None, :]

    index = faiss.read_index(db_path)
    meta_path = os.path.splitext(db_path)[0] + "_metadata.pkl"
    with open(meta_path, "rb") as f:
        metadata_entries = pickle.load(f)

    distances, indices = index.search(query_embedding, k)
    results = []

    for i, idx in enumerate(indices[0]):
        meta = metadata_entries[idx]
        dist = distances[0][i]

        if (query_bug_id is not None
            and query_hunk_index is not None
            and meta.get("bug_id") == str(query_bug_id)
            and meta.get("hunk_index") == str(query_hunk_index)
        ):
            continue

        results.append((meta, dist))

    return results


def QueryEmbeddingDatabaseEmbAST(
    query_subtree,
    k=5,
    model_name='all-MiniLM-L6-v2',
    db_path="embedding_db.index",
    query_bug_id=None,
    query_hunk_index=None,
    window_size: int = 512,
    overlap: int = 64
):
    query_tokens = TokenizeStructure(query_subtree)
    if not query_tokens:
        print("Warning: Empty tokenized AST for the query subtree!")
        return []

    query_str = " ".join(query_tokens)
    embed_model = SentenceTransformer(model_name)

    query_emb = embed_text_sliding_window(
        embed_model, query_str, window_size, overlap
    ).astype("float32")[None, :]

    index = faiss.read_index(db_path)
    meta_path = os.path.splitext(db_path)[0] + "_metadata.pkl"
    with open(meta_path, "rb") as f:
        metadata_entries = pickle.load(f)

    distances, indices = index.search(query_emb, k)
    results = []

    for i, idx in enumerate(indices[0]):
        meta = metadata_entries[idx]
        dist = distances[0][i]

        if (query_bug_id is not None
            and query_hunk_index is not None
            and meta.get("bug_id") == str(query_bug_id)
            and meta.get("hunk_index") == str(query_hunk_index)
        ):
            continue

        results.append((meta, dist))

    return results


def main():
    parser = argparse.ArgumentParser(description="Defects4J Embedding Database Builder")

    parser.add_argument("--dataset_path", type=str, default="../config/method_multihunk.json",
                        help="Path to the dataset JSON file.")
    parser.add_argument("--work_dir", type=str, default=os.path.expanduser("~/WORK_DIR"),
                        help="Path to the working directory where bug projects are stored.")
    parser.add_argument("--fixed_dir", type=str, default=os.path.expanduser("~/WORK_DIR_FIXED"),
                        help="Path to the directory containing fixed projects.")
    parser.add_argument("--fixed_json", type=str, default="../config/enclosing_method_context_javaparser_fixed.json",
                        help="Path to the dataset JSON file")
    parser.add_argument("--exclude_bugs", nargs="*", default=[],
                        help="List of bug IDs to exclude from the database.")
    parser.add_argument("--model_name", type=str, default="all-MiniLM-L6-v2",
                        help="Sentence Transformers model for code embeddings.")
    parser.add_argument("--emb_db_path", type=str, default="embedding_db.index",
                        help="Where to store the FAISS embedding database.")
    args = parser.parse_args()

    # 1) Load the dataset JSON
    dataset = load_dataset(args.dataset_path)

    # 2) Build the AST dataset
    dataset_ast = BuildFullASTDataset(dataset, P, args.work_dir, args.fixed_dir, args.fixed_json)

    # 3) Convert the set of exclude_bugs to a set
    exclude_set = set(args.exclude_bugs) if args.exclude_bugs else None

    # 4) Build the embedding database
    BuildEmbeddingDatabase(
        dataset_ast,
        model_name=args.model_name,
        exclude_bug_ids=exclude_set,
        emb_db_path=args.emb_db_path
    )

if __name__ == "__main__":
    main()
