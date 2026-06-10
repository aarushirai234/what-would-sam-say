# 🤔 What Would Sam Say?
### (Aka) A Multimodal Content Retrieval System

A RAG (Retrieval Augmented Generation) pipeline that lets you have a conversation 
with Sam Altman — grounded entirely in his own words from blogs, talks, and podcast.

Built as a hands-on exploration of the core problems in modern content retrieval: 
multimodal ingestion, AI-generated metadata enrichment, hybrid search, and 
retrieval quality evaluation.

---

## 🎯 Why I Built This

Content retrieval is the foundational layer of any AI product. If the wrong content 
gets retrieved, the answer will be wrong — regardless of how good the language model 
is. I built this project to understand that problem hands-on: what does it take to 
ingest diverse content types, enrich them with meaningful metadata, and retrieve the 
right source reliably across different query types?

The architecture mirrors real-world content retrieval challenges: a corpus of mixed 
media (text, video, audio), AI-generated metadata that requires human review before 
indexing, hybrid search that balances meaning with exact keyword matching, and an 
eval harness that measures whether retrieval is actually working.

---

## 🏗️ Architecture
Ingestion → Enrichment → Indexing → Retrieval → Generation

### 📥 1. Ingestion layer
Three content types ingested and normalized into a single corpus schema:
- 📝 **Blog posts** — scraped from blog.samaltman.com (11 posts)
- 🎥 **YouTube transcripts** — pulled via youtube-transcript-api (3 talks)
- 🎙️ **Podcast** — downloaded and transcribed via Whisper (1 episode, ~45 mins)

Every document is normalized to the same base schema regardless of source type:
`doc_id`, `title`, `date`, `url`, `source_type`, `content`

### ✨ 2. Enrichment layer
Each document is enriched with AI-generated metadata via the Anthropic API:
- 🏷️ **Topics** — 3-5 key themes
- 👤 **Entities** — key people, companies, concepts
- 📋 **Summary** — one sentence

Critically, enriched metadata passes through an **editor-in-the-loop review step** 
before indexing — approve, edit, or reject each document's metadata. This mirrors 
production content pipelines where AI-generated metadata requires human validation 
before it becomes trusted signal.

### 🗄️ 3. Indexing layer
- Documents chunked into 500-word segments with 50-word overlap
- Each chunk embedded using `sentence-transformers` (all-MiniLM-L6-v2)
- Chunks stored in ChromaDB with embeddings + metadata persisted on disk

### 🔍 4. Retrieval layer
Hybrid search blending two signals:
- 🧠 **Semantic search (70%)** — vector similarity via ChromaDB
- 🔤 **BM25 keyword search (30%)** — exact term matching via rank-bm25

The hybrid approach outperforms pure semantic search on proper noun queries 
(named people, companies, events) where exact keyword matching matters.

### 💬 5. Generation layer
Retrieved chunks are passed as grounded context to Claude, which generates 
answers in Sam's voice. The system is instructed to acknowledge when the corpus 
doesn't contain enough information rather than hallucinate.

---

## 📊 Eval Results

We evaluate across two dimensions:
1. ✅ Has Sam genuinely spoken or written about this topic?
2. ✅ Is the right source surfaced in the top 3 results?

15 test queries across topics — startups, AI, energy, productivity — with known 
correct sources defined in advance.

| Approach | Hit Rate @3 |
|---|---|
| 🔵 Semantic only | 86.7% |
| 🟢 Hybrid (BM25 + semantic) | 100.0% |

The 13.3 point gap appears specifically on proper noun queries — "Helion Energy 
nuclear fusion", "Y Combinator Startup School 2019" — where BM25 keyword matching 
catches what pure semantic search misses.

---

## 🧠 Key Design Decisions

**🔀 Separate ingestion from enrichment**
Ingestion and enrichment fail for different reasons (network vs. model). Keeping 
them as separate pipeline stages means either can be re-run independently without 
touching the other.

**👤 Editor-in-the-loop before indexing**
AI-generated metadata isn't always right. A human review gate before indexing 
ensures only validated metadata enters the index — important in any domain where 
metadata quality affects downstream trust.

**🧩 Chunk-level metadata preservation**
Every chunk retains the metadata of its parent document. This means every retrieved 
result knows its source type, topics, entities, and summary — not just its raw text.

**⚡ Hybrid search over pure semantic**
Pure semantic search struggles with proper nouns and exact terms. Hybrid search 
combining BM25 (30%) with vector similarity (70%) closes that gap without 
sacrificing conceptual retrieval quality.

**🧪 Eval harness built in**
Retrieval quality is measured, not assumed. The eval tab in the UI runs the full 
test suite and shows per-query results with sources and scores — making quality 
visible and monitorable.

---

## ⚠️ Known Limitations

- 📛 **Blog titles not unique** — the scraper pulls generic "Sam Altman" as the title 
for some posts. In production, a metadata schema would enforce unique human-readable 
titles at ingestion.
- 📉 **No score threshold enforcement** — the system returns results even for low 
confidence scores. A production system would return "I don't have enough context" 
below a defined threshold.
- ⏰ **No freshness handling** — the corpus is static. A production retrieval system 
needs an ingestion pipeline that handles new content and re-indexes incrementally.
- 📋 **Eval ground truth is manual** — the 15 test queries and correct sources were 
defined by hand. At scale, ground truth curation needs its own workflow.
- 🗄️ **Prototype vector DB** — ChromaDB works well at this scale. At NYT-scale query 
volume, this would require evaluation of production vector databases (Pinecone, 
turbopuffer, pgvector) across latency, cost, and hybrid search support.

---

## 🛠️ Stack

| Tool | Purpose |
|---|---|
| 🤖 Anthropic API | Metadata enrichment + answer generation |
| 🗄️ ChromaDB | Vector storage and semantic search |
| 🔢 sentence-transformers | Embedding model (all-MiniLM-L6-v2) |
| 🔤 rank-bm25 | Keyword search |
| 🎙️ faster-whisper | Podcast transcription |
| 🎥 youtube-transcript-api | YouTube transcript ingestion |
| 🌐 Streamlit | UI |
| 🐍 Python 3.12 | Language |

---

## 🚀 Setup

```bash
git clone https://github.com/aarushirai234/what-would-sam-say
cd what-would-sam-say
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your Anthropic API key to `.env`:
