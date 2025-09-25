import json
from books.dk_events import fetch_events

print("DK Events Test starting...")

result = fetch_events()

print(json.dumps(result, indent=2))

print("DK Events Test finished.")
