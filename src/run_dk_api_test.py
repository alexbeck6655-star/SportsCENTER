# src/run_dk_api_test.py
"""
DraftKings NFL API probe
- Tries a handful of known/public DK JSON endpoints
- Uses browser-y headers to avoid 403s
- Prints what worked + a small sample so you can see real data
- Also saves the first successful JSON to out/dk_api_snapshot.json
"""

from __future__ import annotations
import json, os, sys, time
from typing import Any, Dict, Optional

import requests

HEADERS = {
    # Look like a normal browser
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://sportsbook.draftkings.com/",
    "Origin": "https://sportsbook.draftkings.com",
    "Connection": "keep-alive",
}

# A small set of **likely** endpoints DK uses for NFL.
# We’ll try each, stop at the first that returns good JSON.
CANDIDATES = [
    # Scoreboard-ish (often works without auth)
    {
        "name": "scoreboards v1 nfl",
        "url": "https://api.draftkings.com/scoreboards/v1/nfl",
        "parse_hint": "scoreboards",
    },
    # Odds by league → gamelines (league id can vary by locale; 88808 is a common NFL group)
    {
        "name": "odds v1 gamelines (league 88808)",
        "url": "https://api.draftkings.com/odds/v1/leagues/88808/offers/gamelines",
        "parse_hint": "offers",
    },
    # “Sites” eventgroups (US book site; returns eventGroups with categories/markets)
    {
        "name": "sites US-SB eventgroups (88808)",
        "url": "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/88808?format=json",
        "parse_hint": "eventGroup",
    },
]

OUT_DIR = "out"
OUT_JSON = os.path.join(OUT_DIR, "dk_api_snapshot.json")


def fetch_json(url: str, headers: Dict[str, str], timeout: int = 15) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        print(f"[HTTP] {r.status_code} {url}")
        if r.status_code != 200:
            return None
        # Try to parse JSON directly
        try:
            return r.json()
        except Exception:
            # Some endpoints return JSON with incorrect content-type -> try manual load
            return json.loads(r.text)
    except Exception as e:
        print(f"[ERR] request failed: {e}")
        return None


def summarize_payload(name: str, hint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Try to summarize a few common shapes DK uses.
    Returns a small dict we’ll print for the logs.
    """
    summary = {"endpoint": name, "keys": list(payload.keys())[:8]}

    # Common shapes
    if hint == "scoreboards":
        # Look for games / events
        games = payload.get("games") or payload.get("events") or []
        summary["items_found"] = len(games)
        samples = []
        for g in games[:3]:
            # Try a few common fields
            title = g.get("name") or g.get("eventName") or g.get("description")
            home = g.get("homeTeam") or g.get("home_team") or g.get("home")
            away = g.get("awayTeam") or g.get("away_team") or g.get("away")
            samples.append({"title": title, "home": str(home), "away": str(away)})
        summary["sample"] = samples
        return summary

    if hint == "offers":
        offers = payload.get("offers") or payload.get("events") or []
        summary["items_found"] = len(offers)
        summary["sample"] = list(offers[:1])  # these objects are large
        return summary

    if hint == "eventGroup":
        # sites/US-SB/api/v5/eventgroups/88808?format=json
        eg = payload.get("eventGroup") or {}
        events = eg.get("events") or []
        summary["items_found"] = len(events)
        # Sample a couple of event names
        summary["sample"] = [{"name": e.get("name"), "id": e.get("eventId")} for e in events[:3]]
        return summary

    # Fallback
    summary["items_found"] = 0
    return summary


def main() -> None:
    print("DK API Probe starting…")
    os.makedirs(OUT_DIR, exist_ok=True)

    for cand in CANDIDATES:
        name, url, hint = cand["name"], cand["url"], cand["parse_hint"]
        print(f"\n[TRY] {name}")
        payload = fetch_json(url, HEADERS)
        if not payload:
            print("[MISS] No JSON / non-200")
            continue

        summary = summarize_payload(name, hint, payload)
        print("[HIT] Summary:")
        print(json.dumps(summary, indent=2))

        # Save the first success for inspection
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        print(f"[SAVED] {OUT_JSON} (first 1MB shown in logs below if needed)\n")

        # Print a tiny peek at the raw JSON in logs (don’t flood output)
        raw = json.dumps(payload)[:1_000_000]
        print(f"[RAW PREVIEW] {raw[:1000]}…")

        print("\n✅ DK API Probe finished successfully.")
        return

    print("\n❌ No DK JSON endpoint returned usable data. "
          "If you see 403s, we may need different headers or a region-specific endpoint.")
    sys.exit(1)


if __name__ == "__main__":
    main()
