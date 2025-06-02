import os
import json
import faiss
import pickle
import argparse
import numpy as np

import litellm, numpy as np, tiktoken

from redwood.algorithms.ast_algorithm import BuildFullASTDataset, load_dataset, P
from redwood.algorithms.bm25_algorithm import TokenizeStructure

# Ensure your key is set in the environment:
litellm.api_key = os.getenv("OPENAI_API_KEY")


ENC = tiktoken.get_encoding("cl100k_base")

def _num_tokens(text: str) -> int:
    return len(ENC.encode(text))

def get_litellm_embedding(text: str,
                          model_name: str = "text-embedding-3-small",
                          max_tokens: int = 8192,
                          chunk_overlap: int = 512) -> np.ndarray:
    if _num_tokens(text) <= max_tokens:
        resp = litellm.embedding(model=model_name, input=text)
        return np.array(resp["data"][0]["embedding"], dtype="float32")

    # Otherwise split on whitespace into ~max_tokens pieces
    words = text.split()
    chunks, cur = [], []
    cur_tokens = 0
    for w in words:
        t = _num_tokens(w)  # usually 1
        # +1 for the space we lost in split()
        if cur_tokens + t + 1 > max_tokens - chunk_overlap and cur:
            chunks.append(" ".join(cur))
            cur, cur_tokens = [], 0
        cur.append(w)
        cur_tokens += t + 1
    if cur:
        chunks.append(" ".join(cur))

    # Embed each chunk
    vecs = []
    for ch in chunks:
        resp = litellm.embedding(model=model_name, input=ch)
        vecs.append(resp["data"][0]["embedding"])
    # Mean‑pool
    return np.mean(np.array(vecs, dtype="float32"), axis=0)



def BuildAdaDatabase(
    dataset_ast,
    model_name: str = 'text-embedding-3-small',
    exclude_bug_ids=None,
    emb_db_path: str = "ada_db.index",
):
    print(f"Using LiteLLM embedding model: {model_name}")

    embeddings = []
    metadata_entries = []

    for subtree, metadata in dataset_ast:
        bug_id = metadata["bug_id"]
        print(f"Embedding bug: {bug_id}")

        if exclude_bug_ids and bug_id in exclude_bug_ids:
            print(f"  ↳ Skipping {bug_id} due to exclude list.")
            continue

        buggy_code = metadata.get("buggy_code", "").strip()
        if not buggy_code:
            print(f"  ↳ Warning: Empty buggy_code for {bug_id}, skipping.")
            continue

        snippet_embedding = get_litellm_embedding(buggy_code, model_name)
        embeddings.append(snippet_embedding)

        ast_tokens = TokenizeStructure(subtree)
        metadata["ast_tokens"] = ast_tokens
        metadata_entries.append(metadata)

    if not embeddings:
        print("No embeddings were created. Check your dataset or filters.")
        return

    embeddings_array = np.vstack(embeddings)
    dim = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings_array)

    print(f"Storing {len(embeddings_array)} vectors in FAISS index (dim={dim}).")
    faiss.write_index(index, emb_db_path)
    print(f"FAISS index saved to {emb_db_path}.")

    meta_path = os.path.splitext(emb_db_path)[0] + "_metadata.pkl"
    with open(meta_path, "wb") as f:
        pickle.dump(metadata_entries, f)
    print(f"Saved metadata to {meta_path}.")


def QueryAdaDatabaseEmb(
    query_buggy_code: str,
    k: int = 5,
    model_name: str = 'text-embedding-3-small',
    db_path: str = "ada_db.index",
    query_bug_id=None,
    query_hunk_index=None
):
    query_embedding = get_litellm_embedding(query_buggy_code, model_name)[None, :]

    index = faiss.read_index(db_path)
    meta_path = os.path.splitext(db_path)[0] + "_metadata.pkl"
    with open(meta_path, "rb") as f:
        metadata_entries = pickle.load(f)

    distances, indices = index.search(query_embedding, k)
    results = []

    for rank, idx in enumerate(indices[0]):
        meta = metadata_entries[idx]
        dist = float(distances[0][rank])

        if (query_bug_id is not None
            and query_hunk_index is not None
            and meta.get("bug_id") == str(query_bug_id)
            and meta.get("hunk_index") == str(query_hunk_index)
        ):
            continue

        results.append((meta, dist))

    return results


def QueryAdaDatabaseEmbAST(
    query_subtree,
    k: int = 5,
    model_name: str = 'text-embedding-3-small',
    db_path: str = "ada_db.index",
    query_bug_id=None,
    query_hunk_index=None
):
    query_tokens = TokenizeStructure(query_subtree)
    if not query_tokens:
        print("Warning: Empty AST tokens for query.")
        return []

    query_str = " ".join(query_tokens)
    query_emb = get_litellm_embedding(query_str, model_name)[None, :]

    index = faiss.read_index(db_path)
    meta_path = os.path.splitext(db_path)[0] + "_metadata.pkl"
    with open(meta_path, "rb") as f:
        metadata_entries = pickle.load(f)

    distances, indices = index.search(query_emb, k)
    results = []

    for rank, idx in enumerate(indices[0]):
        meta = metadata_entries[idx]
        dist = float(distances[0][rank])

        if (query_bug_id is not None
            and query_hunk_index is not None
            and meta.get("bug_id") == str(query_bug_id)
            and meta.get("hunk_index") == str(query_hunk_index)
        ):
            continue

        results.append((meta, dist))

    return results


def main():
    parser = argparse.ArgumentParser(description="Build/query a Defects4J embedding DB via LiteLLM")
    parser.add_argument("--dataset_path", type=str, default="../config/method_multihunk.json",
                        help="Path to the dataset JSON file.")
    parser.add_argument("--work_dir", type=str, default=os.path.expanduser("~/WORK_DIR"),
                        help="Root directory of checked-out buggy projects.")
    parser.add_argument("--fixed_dir", type=str, default=os.path.expanduser("~/WORK_DIR_FIXED"),
                        help="Root directory of checked-out fixed projects.")
    parser.add_argument("--fixed_json", type=str, default="../config/enclosing_method_context_javaparser_fixed.json",
                        help="Path to the fixed-code javaparser JSON.")
    parser.add_argument("--exclude_bugs", nargs="*", default=[],
                        help="List of bug IDs to exclude from embedding build.")
    parser.add_argument("--model_name", type=str, default="text-embedding-3-small",
                        help="LiteLLM embedding model name.")
    parser.add_argument("--emb_db_path", type=str, default="ada_db.index",
                        help="Output path for the FAISS index.")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset_path)
    dataset_ast = BuildFullASTDataset(dataset, P,
                                      args.work_dir,
                                      args.fixed_dir,
                                      args.fixed_json)

    exclude_set = set(args.exclude_bugs) if args.exclude_bugs else None
    BuildAdaDatabase(
        dataset_ast,
        model_name=args.model_name,
        exclude_bug_ids=exclude_set,
        emb_db_path=args.emb_db_path
    )


if __name__ == "__main__":
    main()
