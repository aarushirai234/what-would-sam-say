import streamlit as st
import anthropic
import sys
from pathlib import Path
from dotenv import load_dotenv
import base64
import datetime

load_dotenv()
sys.path.append(str(Path(__file__).parent))

from retrieval.search import hybrid_search, semantic_search
from evals.eval import TEST_QUERIES

client = anthropic.Anthropic()

st.set_page_config(
    page_title="What Would Sam Say?",
    page_icon="💬",
    layout="wide"
)

st.markdown("""
<style>
.source-bubble {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    margin: 3px 3px 3px 0;
}
.blog    { background-color: #e8f4f8; color: #1a6b8a; }
.youtube { background-color: #fde8e8; color: #c0392b; }
.podcast { background-color: #e8f8e8; color: #1a8a4a; }
[data-testid="stSidebar"] { background-color: #f7f7f5; }
.stat-pill {
    display: inline-block;
    background: #ececea;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    color: #666;
    margin-top: 0.5rem;
}
/* Push suggestions to bottom above chat input */
.suggestion-container {
    position: fixed;
    bottom: 80px;
    left: 260px;
    right: 0;
    padding: 0 2rem;
    z-index: 10;
}
</style>
""", unsafe_allow_html=True)

def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

sam_img = get_image_base64("assets/sam.jpg")

# ─── SESSION STATE ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "eval_rows" not in st.session_state:
    st.session_state.eval_rows = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "ask"
if "prefill_query" not in st.session_state:
    st.session_state.prefill_query = ""
if "query_log" not in st.session_state:
    st.session_state.query_log = []

# ─── SIDEBAR ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style='text-align:center; padding: 1.2rem 0 1rem 0'>
            <img src="data:image/jpeg;base64,{sam_img}"
                 style="width:86px;height:86px;border-radius:50%;
                        object-fit:cover;border: 2px solid #e0e0de;"/>
            <h3 style='margin: 0.7rem 0 0.2rem 0; font-size:1rem'>
                What Would Sam Say?
            </h3>
            <p style='color:#888; font-size:0.75rem; margin:0 0 0.4rem 0'>
                Grounded in Sam's blogs,<br/>talks & podcast
            </p>
            <span class="stat-pill">15 sources · 83 chunks indexed</span>
        </div>
        <hr style='margin: 0.8rem 0; opacity:0.15'/>
    """, unsafe_allow_html=True)

    ask_type  = "primary"   if st.session_state.active_tab == "ask"  else "secondary"
    eval_type = "primary"   if st.session_state.active_tab == "eval" else "secondary"

    if st.button("💬  Ask Sam", use_container_width=True, type=ask_type):
        st.session_state.active_tab = "ask"
        st.rerun()

    if st.button("📊  Eval", use_container_width=True, type=eval_type):
        st.session_state.active_tab = "eval"
        st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='opacity:0.15; margin:0 0 0.8rem 0'/>",
                unsafe_allow_html=True)

    if st.button("🗑  Clear conversation", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ─── ASK SAM ──────────────────────────────────────────────────────
SUGGESTED = [
    "What do you think about nuclear energy?",
    "How do I generate good startup ideas?",
    "What advice would you give first-time founders?",
    "What was it like building OpenAI?",
]

if st.session_state.active_tab == "ask":
    st.markdown("<h2 style='margin-bottom:0.1rem'>Ask Sam</h2>",
                unsafe_allow_html=True)
    st.caption("Answers grounded in Sam's blogs, talks, and podcast.")
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Render conversation history
    for msg in st.session_state.messages:
        avatar = f"data:image/jpeg;base64,{sam_img}" \
            if msg["role"] == "assistant" else "🙋"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if "sources" in msg:
                st.markdown(msg["sources"], unsafe_allow_html=True)

    # Suggested chips — only when no conversation yet
    if not st.session_state.messages:
        st.markdown("<div style='height:8rem'></div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for i, suggestion in enumerate(SUGGESTED):
            with cols[i % 2]:
                if st.button(suggestion, key=f"chip_{i}",
                             use_container_width=True):
                    st.session_state.prefill_query = suggestion
                    st.rerun()

    # Handle prefilled query from chip click
    if st.session_state.prefill_query:
        query = st.session_state.prefill_query
        st.session_state.prefill_query = ""
    else:
        query = None

    chat_input = st.chat_input("Ask Sam anything...")
    if chat_input:
        query = chat_input

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="🙋"):
            st.markdown(query)

        with st.chat_message("assistant",
                             avatar=f"data:image/jpeg;base64,{sam_img}"):
            with st.spinner("Sam is thinking..."):
                docs, metas, scores = hybrid_search(query, n_results=3)

                context = ""
                for i, (doc, meta) in enumerate(zip(docs, metas)):
                    context += f"Source {i+1} [{meta['source_type']}]: {doc[:500]}\n\n"

                prompt = f"""You are Sam Altman. Answer the following question \
based only on the provided sources below.
Respond in first person, in Sam's direct, thoughtful, and concise voice.
Keep your answer to 3-4 sentences maximum.
If the sources don't contain enough information to answer, say so honestly \
— do not make things up.

Question: {query}

Sources:
{context}

Answer as Sam:"""

                message = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = message.content[0].text
                st.markdown(answer)

                # Source bubbles — no scores shown to user
                bubbles = "<div style='margin-top:8px'>"
                for meta in metas:
                    stype = meta.get("source_type", "unknown")
                    title = meta.get("title", "Unknown")
                    bubbles += (
                        f'<span class="source-bubble {stype}">'
                        f'{stype.upper()} · {title}</span>'
                    )
                bubbles += "</div>"
                st.markdown(bubbles, unsafe_allow_html=True)

                # Log to eval query log (with scores, for eval tab)
                st.session_state.query_log.append({
                    "Question": query,
                    "Top source": f"[{metas[0].get('source_type','').upper()}] "
                                  f"{metas[0].get('title','')}",
                    "Score": f"{scores[0]:.3f}",
                    "Topics": metas[0].get("topics", "—"),
                    "Time": datetime.datetime.now().strftime("%H:%M:%S")
                })

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": bubbles
        })
        st.rerun()

# ─── EVAL ─────────────────────────────────────────────────────────
elif st.session_state.active_tab == "eval":
    st.markdown("<h2 style='margin-bottom:0.1rem'>Retrieval Eval</h2>",
                unsafe_allow_html=True)

    st.markdown("""
    We evaluate the retrieval system powering Ask Sam, which combines semantic search with BM25 keyword matching to find the most relevant sources from our indexed collection of Sam's writings and talks.
                
    The score shown reflects how confident the system is in each result. It is calculated by combining two signals:
    1. How similar the meaning of the source is to the question (70% weight)
    2. How many of the exact words in the question appear in the source (30% weight)

    A score above 0.5 indicates a strong match. A score below 0.35 suggests Sam likely hasn't spoken about this topic — and rather than making something up, the system should say so.
                
    Our offline eval consisted of a sample of 15 questions across different topics — startups, AI, energy, productivity — and for each one, we defined the correct responses and sources.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Semantic @3", "86.7%")
    with col2:
        st.metric("Hybrid @3", "100.0%", delta="+13.3 pts")
    with col3:
        st.metric("Test queries", "15")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if st.button("▶  Run eval", type="primary", use_container_width=True):
        rows = []
        progress = st.progress(0, text="Running eval...")

        for i, test in enumerate(TEST_QUERIES):
            s_docs, s_metas, s_scores = semantic_search(test["query"], n_results=3)
            h_docs, h_metas, h_scores = hybrid_search(test["query"], n_results=3)

            def is_hit(metas, test):
                return any(
                    test["expected_source"] in meta.get("doc_id", "") or
                    test["expected_source"] in meta.get("url", "") or
                    meta.get("source_type") == test["expected_type"]
                    for meta in metas
                )

            s_hit = is_hit(s_metas, test)
            h_hit = is_hit(h_metas, test)
            top = h_metas[0] if h_metas else {}

            rows.append({
                "Query":      test["query"],
                "Semantic":   "✓" if s_hit else "✗",
                "Hybrid":     "✓" if h_hit else "✗",
                "Top source": f"[{top.get('source_type','').upper()}] "
                              f"{top.get('title','')}",
                "Score":      f"{h_scores[0]:.3f}" if h_scores else "—",
                "Topics":     top.get("topics", "—"),
            })
            progress.progress(
                (i + 1) / len(TEST_QUERIES),
                text=f"Query {i+1}/{len(TEST_QUERIES)}..."
            )

        st.session_state.eval_rows = rows
        progress.empty()

    if st.session_state.eval_rows:
        st.dataframe(
            st.session_state.eval_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Query":      st.column_config.TextColumn(width="large"),
                "Semantic":   st.column_config.TextColumn(width="small"),
                "Hybrid":     st.column_config.TextColumn(width="small"),
                "Top source": st.column_config.TextColumn(width="medium"),
                "Score":      st.column_config.TextColumn(width="small"),
                "Topics":     st.column_config.TextColumn(width="large"),
            }
        )
    else:
        st.info("Click '▶ Run eval' to see per-query results with sources and scores.")

    # ── Live query log ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Live query log")
    st.caption("Every question asked in Ask Sam, logged in real time.")

    if st.session_state.query_log:
        st.dataframe(
            st.session_state.query_log,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Question":   st.column_config.TextColumn(width="large"),
                "Top source": st.column_config.TextColumn(width="medium"),
                "Score":      st.column_config.TextColumn(width="small"),
                "Topics":     st.column_config.TextColumn(width="large"),
                "Time":       st.column_config.TextColumn(width="small"),
            }
        )
    else:
        st.info("No live queries yet — ask Sam something to see them logged here.")