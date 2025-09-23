import requests
from bs4 import BeautifulSoup
import json

print("DK Events Test starting...")

url = "https://sportsbook.draftkings.com/leagues/football/nfl"
response = requests.get(url)
if response.status_code != 200:
    print(json.dumps({"status": "fail", "error": f"HTTP {response.status_code}"}))
else:
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    print(json.dumps({
        "status": "success",
        "page_title": title,
        "html_length": len(response.text)
    }))

print("DK Events Test finished.")
