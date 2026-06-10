import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from retrieval.search import semantic_search, hybrid_search

TEST_QUERIES = [
    {
        "query": "Helion Energy nuclear fusion investment",
        "expected_source": "energy",
        "expected_type": "blog"
    },
    {
        "query": "how to be successful in life and career",
        "expected_source": "how-to-be-successful",
        "expected_type": "blog"
    },
    {
        "query": "what is the merge between humans and AI",
        "expected_source": "the-merge",
        "expected_type": "blog"
    },
    {
        "query": "YC startup advice for founders",
        "expected_source": "startup-advice",
        "expected_type": "blog"
    },
    {
        "query": "idea generation for startups",
        "expected_source": "idea-generation",
        "expected_type": "blog"
    },
    {
        "query": "Sam Altman productivity tips delegation",
        "expected_source": "productivity",
        "expected_type": "blog"
    },
    {
        "query": "superintelligence AGI digital intelligence",
        "expected_source": "abundant-intelligence",
        "expected_type": "blog"
    },
    {
        "query": "gentle singularity AI transition",
        "expected_source": "the-gentle-singularity",
        "expected_type": "blog"
    },
    {
        "query": "three observations about AI progress",
        "expected_source": "three-observations",
        "expected_type": "blog"
    },
    {
        "query": "misunderstood by others strength conviction",
        "expected_source": "the-strength-of-being-misunderstood",
        "expected_type": "blog"
    },
    {
        "query": "Stanford lecture how to succeed with a startup",
        "expected_source": "0lJKucu6HJc",
        "expected_type": "youtube"
    },
    {
        "query": "Y Combinator startup school 2019 advice",
        "expected_source": "i3d1asTrWUQ",
        "expected_type": "youtube"
    },
    {
        "query": "Sequoia AI future technology talk",
        "expected_source": "xXCBz_8hM9w",
        "expected_type": "youtube"
    },
    {
        "query": "Lex Fridman interview Sam Altman OpenAI",
        "expected_source": "lex_fridman_367",
        "expected_type": "podcast"
    },
    {
        "query": "OpenAI GPT model training compute scaling",
        "expected_source": "lex_fridman_367",
        "expected_type": "podcast"
    },
]

def evaluate(search_fn, label, k=3):
    hits = 0
    misses = []

    for test in TEST_QUERIES:
        docs, metas, _ = search_fn(test["query"], n_results=k)
        
        hit = any(
            test["expected_source"] in meta.get("doc_id", "") or
            test["expected_source"] in meta.get("url", "") or
            meta.get("source_type") == test["expected_type"]
            for meta in metas
        )

        if hit:
            hits += 1
        else:
            misses.append(test["query"])

    hit_rate = hits / len(TEST_QUERIES) * 100
    print(f"\n{label}")
    print(f"  Hit rate @{k}: {hits}/{len(TEST_QUERIES)} = {hit_rate:.1f}%")
    if misses:
        print(f"  Misses:")
        for m in misses:
            print(f"    - {m}")
    return hit_rate

def main():
    print("=== Retrieval Eval ===")
    print(f"Total test queries: {len(TEST_QUERIES)}")

    semantic_score = evaluate(semantic_search, "Semantic only", k=3)
    hybrid_score = evaluate(hybrid_search, "Hybrid (BM25 + semantic)", k=3)

    print(f"\n=== Summary ===")
    print(f"  Semantic @3:  {semantic_score:.1f}%")
    print(f"  Hybrid @3:    {hybrid_score:.1f}%")
    delta = hybrid_score - semantic_score
    if delta > 0:
        print(f"  Hybrid wins by {delta:.1f} points")
    elif delta < 0:
        print(f"  Semantic wins by {abs(delta):.1f} points")
    else:
        print(f"  Tied")

if __name__ == "__main__":
    main()