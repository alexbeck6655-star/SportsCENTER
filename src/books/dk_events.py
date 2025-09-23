import requests
from bs4 import BeautifulSoup

DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"

def fetch_events():
    """
    Scrapes the DraftKings NFL page for available games and event links.
    Returns a list of dicts: [{"teams": "Jets vs Patriots", "link": "..."}]
    """
    try:
        r = requests.get(DK_URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Could not fetch DK page: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    events = []

    # Look for all game links
    for a in soup.find_all("a", href=True):
        if "/event/" in a["href"]:  # Event links contain /event/
            teams = a.get_text(strip=True)
            events.append({"teams": teams, "link": a["href"]})

    print(f"[INFO] Found {len(events)} events")
    return events

if __name__ == "__main__":
    events = fetch_events()
    for e in events:
        print(f"{e['teams']} -> {e['link']}")
