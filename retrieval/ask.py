import sys
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parent.parent))

from retrieval.search import hybrid_search

client = anthropic.Anthropic()

def answer(query):
    docs, metas, scores = hybrid_search(query, n_results=3)

    context = ""
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        context += f"Source {i+1} [{meta['source_type']}]: {doc[:500]}\n\n"

    prompt = f"""You are Sam Altman. Answer the following question based only on the provided sources below. 
Respond in first person, in Sam's direct and thoughtful voice. 
If the sources don't contain enough information to answer, say so honestly.

Question: {query}

Sources:
{context}

Answer as Sam:"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"\nSam says:\n")
    print(message.content[0].text)
    print("\nSources used:")
    for i, meta in enumerate(metas):
        print(f"  {i+1}. [{meta['source_type']}] {meta['title']} (score: {scores[i]:.3f})")
    print("-" * 50 + "\n")

def main():
    print("=== What Would Sam Say? ===")
    print("Ask Sam Altman anything based on his blogs, talks, and podcast.")
    print("Type 'quit' to exit.\n")

    while True:
        query = input("Your question: ").strip()
        if query.lower() == "quit":
            break
        if not query:
            continue
        answer(query)

if __name__ == "__main__":
    main()