import json
import re
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup

DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

def _mk(event_id: Any) -> str:
    """Build a human-visit-able event URL from an eventId."""
    return f"https://sportsbook.draftkings.com/event/{event_id}"

def _dedupe(events: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for e in events:
        key = e.get("link") or e.get("teams")
        if key and key not in seen:
            seen.add(key)
            out.append(e)
    return out

def _from_next_data(html: str) -> List[Dict[str, str]]:
    """
    DraftKings NFL page is a Next.js app. Event data usually lives inside:
      <script id="__NEXT_DATA__" type="application/json">...</script>
    We parse it and walk common paths to find events.
    """
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not tag or not tag.string:
        return []

    try:
        data = json.loads(tag.string)
    except Exception:
        return []

    # Typical structure (can evolve): props.pageProps.dehydratedState.queries[*].state.data
    # Look across queries to find any object with "events" list or "eventGroup"
    events: List[Dict[str, str]] = []

    def harvest(obj):
        # look for key "events" that is a list of dicts containing eventId/name/teams
        evs = obj.get("events")
        if isinstance(evs, list):
            for ev in evs:
                name = ev.get("name") or ev.get("eventName") or ""
                # if name like 'Jets vs Patriots' that's perfect
                eid = ev.get("eventId") or ev.get("providerEventId") or ev.get("id")
                if eid:
                    events.append({"teams": name or f"event {eid}", "link": _mk(eid)})

    try:
        # Walk likely paths safely
        props = (data.get("props") or {}).get("pageProps") or {}
        dehydrated = (props.get("dehydratedState") or {}).get("queries") or []
        for q in dehydrated:
            state = q.get("state") or {}
            # Some versions: state['data']; others: state['data']['eventGroup']
            dat = state.get("data") or {}
            if isinstance(dat, dict):
                harvest(dat)
                # Sometimes nested under eventGroup
                eg = dat.get("eventGroup") or {}
                if isinstance(eg, dict):
                    harvest(eg)
            # Occasionally the query result lives under state['data']['featured'] etc.
            for k, v in dat.items() if isinstance(dat, dict) else []:
                if isinstance(v, dict):
                    harvest(v)
    except Exception:
        # Be permissive; if structure shifts, we'll fall back to regex/anchors next.
        pass

    return _dedupe(events)

def _from_regex(html: str) -> List[Dict[str, str]]:
    events = []
    for href in set(re.findall(r'href="(/event/[^"]+)"', html)):
        link = f"https://sportsbook.draftkings.com{href}"
        # No team names from regex; use the tail as a label
        label = href.split("/event/")[-1].replace("-", " ").split("?")[0][:80]
        events.append({"teams": label, "link": link})
    return _dedupe(events)

def _from_anchors(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/event/" in href:
            link = f"https://sportsbook.draftkings.com{href}"
            teams = a.get_text(strip=True) or "NFL event"
            events.append({"teams": teams, "link": link})
    return _dedupe(events)

def fetch_events() -> Dict[str, Any]:
    """
    Returns: {"status": "success"|"error", "events_found": int, "events": [...]}
    """
    try:
        r = requests.get(DK_URL, headers={"User-Agent": UA}, timeout=12)
        r.raise_for_status()
    except Exception as e:
        return {"status": "error", "error": str(e), "events_found": 0, "events": []}

    html = r.text

    # Strategy A: Next.js JSON
    events = _from_next_data(html)
    # Strategy B: Regex fallback
    if not events:
        events = _from_regex(html)
    # Strategy C: Anchor fallback
    if not events:
        events = _from_anchors(html)

    return {"status": "success", "events_found": len(events), "events": events}


if __name__ == "__main__":
    print(json.dumps(fetch_events(), indent=2))
