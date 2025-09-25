from books.dk_events import fetch_events
import json

print("DK Events Test starting...")
events = fetch_events()
print(json.dumps({
    "status": "success",
    "events_found": len(events),
    "events": events[:3]  # just preview first 3
}, indent=2))
print("DK Events Test finished.")
