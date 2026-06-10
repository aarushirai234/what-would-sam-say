import json
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def main():
    corpus = json.loads(Path("data/enriched_corpus.json").read_text())

    client = chromadb.PersistentClient(path="data/chroma_db")
    
    # Fresh collection each run
    try:
        client.delete_collection("sam_docs")
    except:
        pass
    collection = client.create_collection("sam_docs")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    total_chunks = 0

    for doc in corpus:
        chunks = chunk_text(doc["content"])
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['doc_id']}_chunk_{i:03d}"
            embedding = model.encode(chunk).tolist()
            
            metadata = {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "source_type": doc["source_type"],
                "topics": ", ".join(doc.get("topics", [])),
                "entities": ", ".join(doc.get("entities", [])),
                "summary": doc.get("summary", ""),
                "url": doc.get("url", ""),
                "chunk_index": i
            }

            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[metadata]
            )
            total_chunks += 1

        print(f"Indexed: {doc['title']} ({len(chunks)} chunks)")

    print(f"\nDone. {total_chunks} chunks indexed → data/chroma_db")

if __name__ == "__main__":
    main()