from faster_whisper import WhisperModel
import json
from pathlib import Path

def main():
    print("Loading Whisper model...")
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("Transcribing podcast (this will take a few minutes)...")
    segments, info = model.transcribe("data/podcast.mp3", beam_size=5)

    full_text = " ".join([segment.text for segment in segments])

    result = {
        "id": "lex_fridman_367",
        "title": "Lex Fridman Podcast #367 - Sam Altman",
        "url": "https://www.youtube.com/watch?v=L_Guz73e6fw",
        "source_type": "podcast",
        "date": "2023-03-25",
        "content": full_text
    }

    Path("data/podcast.json").write_text(json.dumps(result, indent=2))
    print(f"Done. Transcribed → data/podcast.json")
    print(f"Total characters: {len(full_text)}")

if __name__ == "__main__":
    main()