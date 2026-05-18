import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import os

URL = "https://ottawa.ca/en/city-hall/city-news/newsroom"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": "https://www.google.com/",
}


def fetch_items():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []

    # Try to find news links — ottawa.ca uses anchor tags with full article paths
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)

        # Filter to links that look like newsroom articles
        if "/newsroom/" not in href or not title or len(title) < 10:
            continue

        if href.startswith("/"):
            href = "https://ottawa.ca" + href

        items.append({"title": title, "link": href})

    # Deduplicate by link
    seen = set()
    unique = []
    for item in items:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)

    return unique[:20]


def build_rss(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "City of Ottawa Newsroom"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "News releases, advisories and announcements from the City of Ottawa"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    for item in items:
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = item["title"]
        ET.SubElement(entry, "link").text = item["link"]
        ET.SubElement(entry, "guid", isPermaLink="true").text = item["link"]

    return ET.tostring(rss, encoding="unicode", xml_declaration=False)


def main():
    print("Fetching Ottawa newsroom...")
    items = fetch_items()
    print(f"Found {len(items)} items")

    rss_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + build_rss(items)

    os.makedirs("docs", exist_ok=True)
    with open("docs/feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)

    print("Written to docs/feed.xml")


if __name__ == "__main__":
    main()
