# src/books/dk_probe.py
from __future__ import annotations
import time
import typing as t
import requests
from bs4 import BeautifulSoup

NFL_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"

HEADERS = {
    # light, generic desktop UA + sec headers help avoid some bot walls
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}

def quick_probe(url: str = NFL_URL, timeout: float = 12.0) -> dict:
    """
    Fetch the DK NFL page and return a small status dict.
    Also extracts simple HTML facts (title, link counts) to prove parsing works.
    """
    t0 = time.time()
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    elapsed_ms = int((time.time() - t0) * 1000)

    ok = (r.status_code == 200 and r.text and "DraftKings" in r.text)
    info: dict[str, t.Any] = {
        "status": r.status_code,
        "elapsed_ms": elapsed_ms,
        "html_len": len(r.text),
        "marker": ("DraftKings" in r.text),
        "url": url,
        "parsed": {},
    }

    if ok:
        info["parsed"] = _parse_landing_snapshot(r.text)

    return info

def _parse_landing_snapshot(html: str) -> dict:
    """
    Super-lightweight HTML inspection:
      - page <title>
      - number of links
      - count of 'event-ish' links (paths that look like game/event pages)
      - a few sample links so we can see we're grabbing real anchors
    NOTE: DK renders most odds client-side; with plain requests we won't see prices yet.
    This is just to confirm we can navigate/parse safely.
    """
    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.get_text(strip=True) if soup.title else "")

    links = [a.get("href") for a in soup.find_all("a", href=True)]
    # normalize relative links to help us eyeball them
    norm_links: list[str] = []
    for href in links:
        if not href:
            continue
        if href.startswith("//"):
            norm_links.append("https:" + href)
        elif href.startswith("/"):
            norm_links.append("https://sportsbook.draftkings.com" + href)
        else:
            norm_links.append(href)

    # very rough filter for “looks like a game/event/team page”
    eventish = [
        u for u in norm_links
        if any(p in u for p in ["/event/", "/game/", "/leagues/football/nfl/"])
    ]

    return {
        "title": title,
        "total_links": len(norm_links),
        "eventish_links": len(eventish),
        "sample_eventish": eventish[:5],
    }
