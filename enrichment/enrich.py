import json
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

def generate_metadata(doc):
    prompt = f"""You are a metadata tagging system. Analyze the following content and return ONLY a JSON object with no preamble or markdown backticks.

Content title: {doc['title']}
Source type: {doc['source_type']}
Content (first 1000 chars): {doc['content'][:1000]}

Return this exact JSON structure:
{{
    "topics": ["topic1", "topic2", "topic3"],
    "entities": ["entity1", "entity2", "entity3"],
    "summary": "one sentence summary"
}}

Return ONLY the JSON object. No explanation, no markdown, no backticks."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # Strip markdown backticks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def editor_review(doc, metadata):
    print("\n" + "="*60)
    print(f"DOCUMENT: {doc['title']}")
    print(f"SOURCE:   {doc['source_type']}")
    print(f"\nAI-GENERATED METADATA:")
    print(f"  Topics:   {', '.join(metadata['topics'])}")
    print(f"  Entities: {', '.join(metadata['entities'])}")
    print(f"  Summary:  {metadata['summary']}")
    print("="*60)
    print("\n[A]pprove  [E]dit  [R]eject")
    choice = input("Your choice: ").strip().lower()

    if choice == "a":
        return metadata, "approved"
    elif choice == "r":
        return None, "rejected"
    elif choice == "e":
        print("\nEditing topics (comma separated, press enter to keep current):")
        topics_input = input(f"  Topics [{', '.join(metadata['topics'])}]: ").strip()
        if topics_input:
            metadata['topics'] = [t.strip() for t in topics_input.split(",")]

        print("Editing entities (comma separated, press enter to keep current):")
        entities_input = input(f"  Entities [{', '.join(metadata['entities'])}]: ").strip()
        if entities_input:
            metadata['entities'] = [e.strip() for e in entities_input.split(",")]

        print("Editing summary (press enter to keep current):")
        summary_input = input(f"  Summary [{metadata['summary']}]: ").strip()
        if summary_input:
            metadata['summary'] = summary_input

        return metadata, "edited"
    else:
        print("Invalid choice, approving by default.")
        return metadata, "approved"

def main():
    corpus = json.loads(Path("data/corpus.json").read_text())
    enriched = []

    print(f"Starting enrichment for {len(corpus)} documents...")
    print("You will review each document's AI-generated metadata before it gets indexed.\n")

    for doc in corpus:
        print(f"\nGenerating metadata for: {doc['title']}")
        try:
            metadata = generate_metadata(doc)
            reviewed_metadata, status = editor_review(doc, metadata)

            if status == "rejected":
                print(f"Skipped: {doc['title']}")
                continue

            enriched_doc = {**doc, **reviewed_metadata, "review_status": status}
            enriched.append(enriched_doc)
            print(f"✓ {status.capitalize()}: {doc['title']}")

        except Exception as e:
            print(f"Error processing {doc['title']}: {e}")
            continue

    Path("data/enriched_corpus.json").write_text(json.dumps(enriched, indent=2))
    print(f"\nDone. {len(enriched)} documents enriched → data/enriched_corpus.json")

if __name__ == "__main__":
    main()