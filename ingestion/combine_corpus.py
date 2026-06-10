import json
from pathlib import Path

def main():
    blogs = json.loads(Path("data/blogs.json").read_text())
    transcripts = json.loads(Path("data/transcripts.json").read_text())
    podcast = json.loads(Path("data/podcast.json").read_text())

    # podcast is a single dict, wrap in list
    corpus = blogs + transcripts + [podcast]

    # Add a unique doc_id to each
    for i, doc in enumerate(corpus):
        doc["doc_id"] = f"doc_{i:03d}"

    Path("data/corpus.json").write_text(json.dumps(corpus, indent=2))
    print(f"Done. Combined corpus: {len(corpus)} documents → data/corpus.json")
    print(f"  Blogs: {len(blogs)}")
    print(f"  Transcripts: {len(transcripts)}")
    print(f"  Podcast: 1")

if __name__ == "__main__":
    main()