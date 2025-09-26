# src/books/dk_events.py
from __future__ import annotations

import json
import re
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"


def _headers() -> dict:
    # Be explicit so DK gives us the normal HTML
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        # Don’t send cookies; we want the public page
    }


def _try_parse_embedded_json(html: str) -> list[dict]:
    """
    Many DK pages embed a big JSON blob. Common markers to search:
      - 'dehydratedState'
      - '__NEXT_DATA__'
      - 'window.__APOLLO_STATE__'
    This routine tries to find a JSON-looking block and extract 'events' within it.
    If nothing reliable is found, return [].
    """
    # 1) Look for <script id="__NEXT_DATA__"> ... JSON ...
    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            data = json.loads(m.group(1))
            # Try some common paths where events live
            # This is intentionally defensive — we just collect anything that looks like an event.
            events: list[dict] = []
            def walk(obj):
                if isinstance(obj, dict):
                    # If it looks like an event-ish object, keep it
                    keys = set(obj.keys())
                    if ("eventId" in obj or "eventIdEncoded" in obj) and ("name" in obj or "eventName" in obj):
                        name = obj.get("name") or obj.get("eventName") or ""
                        if isinstance(name, str) and name:
                            events.append({"teams": name, "link": None})
                    for v in obj.values():
                        walk(v)
                elif isinstance(obj, list):
                    for v in obj:
                        walk(v)
            walk(data)
            # De-dup by 'teams'
            uniq = {}
            for e in events:
                key = e["teams"]
                uniq[key] = e
            return list(uniq.values())
        except Exception:
            pass

    # 2) Look for a window.* style assignment with a large JSON
    m = re.search(r'window\.__[A-Z0-9_]+__\s*=\s*(\{.*?\});\s*</script>', html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            events: list[dict] = []
            def walk(obj):
                if isinstance(obj, dict):
                    keys = set(obj.keys())
                    if ("eventId" in obj or "eventIdEncoded" in obj) and ("name" in obj or "eventName" in obj):
                        name = obj.get("name") or obj.get("eventName") or ""
                        if isinstance(name, str) and name:
                            events.append({"teams": name, "link": None})
                    for v in obj.values():
                        walk(v)
                elif isinstance(obj, list):
                    for v in obj:
                        walk(v)
            walk(data)
            uniq = {}
            for e in events:
                key = e["teams"]
                uniq[key] = e
            return list(uniq.values())
        except Exception:
            pass

    # 3) Sometimes the term “dehydratedState” is present in a bare script tag
    if "dehydratedState" in html:
        # Grab the first {...} that follows the marker — very defensive.
        m = re.search(r'dehydratedState.*?({.*})', html, re.DOTALL)
        if m:
            blob = m.group(1)
            # Try to trim to a valid JSON object boundary
            # This is a cheap heuristic; if it fails we’ll just return [] and let fallback handle it.
            last_brace = blob.rfind("}")
            if last_brace > 0:
                blob = blob[: last_brace + 1]
            try:
                data = json.loads(blob)
                events: list[dict] = []
                def walk(obj):
                    if isinstance(obj, dict):
                        keys = set(obj.keys())
                        if ("eventId" in obj or "eventIdEncoded" in obj) and ("name" in obj or "eventName" in obj):
                            name = obj.get("name") or obj.get("eventName") or ""
                            if isinstance(name, str) and name:
                                events.append({"teams": name, "link": None})
                        for v in obj.values():
                            walk(v)
                    elif isinstance(obj, list):
                        for v in obj:
                            walk(v)
                walk(data)
                uniq = {}
                for e in events:
                    key = e["teams"]
                    uniq[key] = e
                return list(uniq.values())
            except Exception:
                pass

    return []


def _fallback_link_scan(html: str, base_url: str) -> list[dict]:
    """
    If JSON parsing fails, scan anchors for event-like links.
    """
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    anchors = soup.find_all("a", href=True)
    for a in anchors:
        href = a["href"]
        text = (a.get_text() or "").strip()
        # DraftKings event pages often live under /event/ or include 'game' or 'matchup'
        if re.search(r"/event/|/game/|/matchup", href, re.IGNORECASE):
            # Basic sanity: something that looks like "Team at Team" or "Team vs Team"
            if re.search(r"\b(at|vs)\b", text, re.IGNORECASE) and len(text) <= 80:
                events.append({
                    "teams": re.sub(r"\s+", " ", text),
                    "link": urljoin(base_url, href),
                })

    # De-dup by link (prefer link because titles can repeat)
    uniq = {}
    for e in events:
        key = e["link"] or e["teams"]
        uniq[key] = e
    return list(uniq.values())


def fetch_events(debug: bool = True) -> List[Dict]:
    """
    Returns a list of {teams: 'Jets vs Patriots', link: 'https://...'}.
    Tries embedded JSON first, then falls back to link-scan.
    """
    r = requests.get(DK_URL, headers=_headers(), timeout=12)
    r.raise_for_status()

    html = r.text
    if debug:
        title = BeautifulSoup(html, "html.parser").title.string if BeautifulSoup(html, "html.parser").title else ""
        print(f"[INFO] DK title: {title!r}, html_length={len(html)}")

    # 1) Try JSON
    events = _try_parse_embedded_json(html)
    if debug:
        print(f"[INFO] JSON-parse events found: {len(events)}")

    # 2) Fallback if needed
    if not events:
        events = _fallback_link_scan(html, DK_URL)
        if debug:
            print(f"[INFO] Fallback link-scan events found: {len(events)}")

    return events
