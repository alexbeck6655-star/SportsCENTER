import requests

def quick_probe():
    """
    Quick probe to check if DraftKings NFL page is reachable.
    Returns a tuple: (status_code, elapsed_ms, marker_found, url)
    """
    url = "https://sportsbook.draftkings.com/leagues/football/nfl"
    try:
        r = requests.get(url, timeout=5)
        html = r.text
        marker = "DraftKings" in html or "NFL" in html
        return (r.status_code, int(r.elapsed.total_seconds() * 1000), marker, url)
    except Exception as e:
        return (None, None, False, url)

if __name__ == "__main__":
    status, elapsed, marker, url = quick_probe()
    print(f"DK probe -> status={status} elapsed={elapsed}ms marker={marker} url={url}")
