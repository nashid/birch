import math
from collections import Counter, defaultdict
import javalang

class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        self.term_doc_freq = self.compute_term_doc_freq()

    def compute_term_doc_freq(self):
        doc_freq = defaultdict(int)
        for doc in self.corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_freq[term] += 1
        return doc_freq

    def score(self, query, document, doc_length):
        score = 0.0
        doc_counter = Counter(document)
        for term in query:
            if term in self.term_doc_freq:
                idf = math.log(
                    (len(self.corpus) - self.term_doc_freq[term] + 0.5)
                    / (self.term_doc_freq[term] + 0.5)
                    + 1
                )
                term_freq = doc_counter[term]
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * doc_length / self.avg_doc_length
                )
                score += idf * (numerator / denominator)
        return score

    def get_top_k(self, query, k):
        scores = []
        for idx, document in enumerate(self.corpus):
            doc_length = self.doc_lengths[idx]
            score = self.score(query, document, doc_length)
            scores.append((idx, score))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        return scores[:k]

def TokenizeStructure(ast_tree):
    if not ast_tree:
        print("Warning: Received empty AST tree for tokenization!")
        return []

    tokens = []

    def traverse(node):
        if isinstance(node, javalang.tree.Node):
            node_type = type(node).__name__
            tokens.append(node_type)  # Store node type as a token

            # Traverse child attributes
            for attr in dir(node):
                if not attr.startswith("_") and attr not in ["position", "annotations", "documentation"]:
                    value = getattr(node, attr)
                    if isinstance(value, (javalang.tree.Node, list)):
                        traverse(value)

        elif isinstance(node, list):  # If node is a list of children
            for item in node:
                traverse(item)

    traverse(ast_tree)  # Start traversal

    if not tokens:
        print("Warning: Tokenization resulted in an empty list!")

    return tokens



def RetrieveTopK(Q, DAST, k):
    query_tokens = TokenizeStructure(Q)
    print("Query Tokens:", query_tokens)
    for entry in DAST:
        print(f"DAST Entry {entry['id']} Tokens:", entry["tokens"])

    dataset_tokens = [entry["tokens"] for entry in DAST]

    bm25 = BM25(dataset_tokens)

    print("Term-Document Frequencies:", bm25.term_doc_freq)

    print("Average Document Length:", bm25.avg_doc_length)


    top_k = bm25.get_top_k(query_tokens, k)

    top_k_examples = [(DAST[idx], score) for idx, score in top_k]
    print(top_k_examples)
    return top_k_examples


if __name__ == "__main__":
    # Example query AST
    # GPT Generated example to test functionality
    query_ast = {
        "type": "IfStmt",
        "condition": {"type": "BinOp"},
        "body": [{"type": "ReturnStmt", "value": {"type": "BinOp"}}],
    }

    # Example DAST (demonstration dataset)
    DAST = [
        {"id": 1, "tokens": ["IfStmt", "Condition", "BinOp", "ReturnStmt", "BinOp"]},
        {"id": 2, "tokens": ["ForStmt", "Condition", "BinOp", "Body", "BinOp"]},
    ]

    # Top-k results
    k = 2
    top_k_results = RetrieveTopK(query_ast, DAST, k)

    print("Top-k Results:")
    for result, score in top_k_results:
        print(f"Example ID: {result['id']}, Score: {score}")
