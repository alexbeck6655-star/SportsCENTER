import requests, json
from bs4 import BeautifulSoup

DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"

def fetch_events():
    try:
        r = requests.get(DK_URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return {"status": "error", "error": str(e), "events": []}

    soup = BeautifulSoup(r.text, "html.parser")
    script = soup.find("script", string=lambda s: s and "DEHYDRATED_STATE" in s)
    if not script:
        print("[WARN] Could not find dehydratedState JSON in HTML")
        return {"status": "success", "events_found": 0, "events": []}

    try:
        # Extract JSON part from script contents
        json_text = script.string.split("=", 1)[1].strip(" ;")
        data = json.loads(json_text)
    except Exception as e:
        return {"status": "error", "error": f"JSON parse failed: {e}", "events": []}

    events = []
    for key, value in data.items():
        if isinstance(value, dict) and "eventId" in value:
            teams = value.get("name", "")
            link = value.get("link", "")
            events.append({"teams": teams, "link": link})

    return {"status": "success", "events_found": len(events), "events": events}
