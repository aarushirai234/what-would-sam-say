import json
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from pathlib import Path

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("sam_docs")

def get_all_chunks():
    results = collection.get(include=["documents", "metadatas"])
    return results["documents"], results["metadatas"]

def semantic_search(query, n_results=5):
    embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results["documents"][0], results["metadatas"][0], results["distances"][0]

def hybrid_search(query, n_results=5, semantic_weight=0.7, bm25_weight=0.3):
    # Semantic search
    embedding = model.encode(query).tolist()
    semantic_results = collection.query(
        query_embeddings=[embedding],
        n_results=20,
        include=["documents", "metadatas", "distances"]
    )
    semantic_docs = semantic_results["documents"][0]
    semantic_ids = semantic_results["ids"][0]
    semantic_distances = semantic_results["distances"][0]

    # Normalize semantic scores (distance → similarity)
    max_dist = max(semantic_distances) if semantic_distances else 1
    semantic_scores = {
        sid: 1 - (dist / max_dist)
        for sid, dist in zip(semantic_ids, semantic_distances)
    }

    # BM25 search over same candidate set
    tokenized_corpus = [doc.lower().split() for doc in semantic_docs]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_raw = bm25.get_scores(query.lower().split())

    # Normalize BM25 scores
    max_bm25 = max(bm25_raw) if max(bm25_raw) > 0 else 1
    bm25_scores = {
        sid: score / max_bm25
        for sid, score in zip(semantic_ids, bm25_raw)
    }

    # Combine scores
    combined = {}
    for sid in semantic_ids:
        combined[sid] = (
            semantic_weight * semantic_scores.get(sid, 0) +
            bm25_weight * bm25_scores.get(sid, 0)
        )

    # Sort and return top n
    top_ids = sorted(combined, key=combined.get, reverse=True)[:n_results]

    # Fetch full metadata for top results
    final = collection.get(ids=top_ids, include=["documents", "metadatas"])
    return final["documents"], final["metadatas"], [combined[i] for i in top_ids]

if __name__ == "__main__":
    print("=== Hybrid Search Demo ===\n")

    # Query where hybrid beats pure semantic
    query = "Helion Energy nuclear fusion investment"
    print(f"Query: '{query}'\n")

    print("--- Semantic only ---")
    docs, metas, distances = semantic_search(query, n_results=3)
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        print(f"{i+1}. [{meta['source_type']}] {meta['title']}")
        print(f"   {doc[:120]}...\n")

    print("--- Hybrid (BM25 + semantic) ---")
    docs, metas, scores = hybrid_search(query, n_results=3)
    for i, (doc, meta, score) in enumerate(zip(docs, metas, scores)):
        print(f"{i+1}. [{meta['source_type']}] {meta['title']} (score: {score:.3f})")
        print(f"   {doc[:120]}...\n")