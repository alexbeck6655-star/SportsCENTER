import requests
from bs4 import BeautifulSoup

DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"

def fetch_events():
    """
    Scrapes DraftKings NFL page for available games and event links.
    Returns a list of dicts: [{"teams": "Jets vs Patriots", "link": "..."}]
    """
    try:
        r = requests.get(DK_URL, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return {"status": "error", "error": str(e), "events": []}

    soup = BeautifulSoup(r.text, "html.parser")
    events = []

    # Look for all game links containing "/event/"
    for a in soup.find_all("a", href=True):
        if "/event/" in a["href"]:
            teams = a.get_text(strip=True)
            link = f"https://sportsbook.draftkings.com{a['href']}"
            events.append({"teams": teams, "link": link})

    return {"status": "success", "events_found": len(events), "events": events}


if __name__ == "__main__":
    result = fetch_events()
    print(result)
