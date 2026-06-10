import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

BASE_URL = "https://blog.samaltman.com"

POSTS = [
    "the-merge",
    "how-to-be-successful",
    "abundant-intelligence",
    "the-gentle-singularity",
    "three-observations",
    "productivity",
    "startup-advice",
    "energy",
    "what-i-wish-someone-had-told-me",
    "the-strength-of-being-misunderstood",
    "idea-generation",
]

def scrape_post(slug):
    url = f"{BASE_URL}/{slug}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed: {url}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Title
    title = soup.find("h1")
    title_text = title.get_text(strip=True) if title else slug

    # Date
    date_tag = soup.find("time")
    date_text = date_tag.get_text(strip=True) if date_tag else "unknown"

    # Body content
    body = soup.find("div", class_="post-content") or soup.find("article")
    if not body:
        print(f"No body found for {slug}")
        return None

    paragraphs = body.find_all("p")
    content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])

    return {
        "id": slug,
        "title": title_text,
        "date": date_text,
        "url": url,
        "source_type": "blog",
        "content": content
    }

def main():
    output_path = Path("data/blogs.json")
    output_path.parent.mkdir(exist_ok=True)

    results = []
    for slug in POSTS:
        print(f"Scraping: {slug}")
        post = scrape_post(slug)
        if post:
            results.append(post)
        time.sleep(1)  # polite crawling

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. Scraped {len(results)} posts → data/blogs.json")

if __name__ == "__main__":
    main()