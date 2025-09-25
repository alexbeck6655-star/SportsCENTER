import requests
import re
import json
from bs4 import BeautifulSoup

DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"

def fetch_events():
    """
    Fetch NFL events from DraftKings by parsing the embedded dehydratedState JSON.
    Returns a list of {teams, link} dicts.
    """
    try:
        r = requests.get(DK_URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Could not fetch DK page: {e}")
        return []

    # Search for the dehydratedState JSON blob
    match = re.search(r'"dehydratedState":({.*?}),"app"', r.text)
    if not match:
        print("[WARN] Could not find dehydratedState JSON in HTML")
        return []

    try:
        data = json.loads(match.group(1))
    except Exception as e:
        print(f"[ERROR] Could not parse JSON: {e}")
        return []

    events = []
    for item in data.get("apolloState", {}).values():
        if isinstance(item, dict) and item.get("__typename") == "Event":
            name = item.get("name")
            url = item.get("eventUrl")
            if name and url:
                events.append({"teams": name, "link": f"https://sportsbook.draftkings.com{url}"})

    print(f"[INFO] Found {len(events)} events")
    return events

