from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import YouTubeTranscriptApi
import json
from pathlib import Path

VIDEOS = [
    {
        "id": "0lJKucu6HJc",
        "title": "How to Succeed with a Startup - Sam Altman, Stanford",
        "url": "https://www.youtube.com/watch?v=0lJKucu6HJc"
    },
    {
        "id": "i3d1asTrWUQ",
        "title": "Sam Altman - Y Combinator Startup School 2019",
        "url": "https://www.youtube.com/watch?v=i3d1asTrWUQ"
    },
    {
        "id": "xXCBz_8hM9w",
        "title": "Sam Altman at Sequoia - AI and the Future",
        "url": "https://www.youtube.com/watch?v=xXCBz_8hM9w"
    }
]

def fetch_transcript(video):
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video["id"])
        full_text = " ".join([t.text for t in transcript])
        return {
            "id": video["id"],
            "title": video["title"],
            "url": video["url"],
            "source_type": "youtube",
            "date": "unknown",
            "content": full_text
        }
    except Exception as e:
        print(f"Failed: {video['title']} — {e}")
        return None

def main():
    output_path = Path("data/transcripts.json")
    output_path.parent.mkdir(exist_ok=True)

    results = []
    for video in VIDEOS:
        print(f"Fetching: {video['title']}")
        result = fetch_transcript(video)
        if result:
            results.append(result)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. Fetched {len(results)} transcripts → data/transcripts.json")

if __name__ == "__main__":
    main()