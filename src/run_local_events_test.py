# src/run_local_events_test.py
import json
from books import dk_events

def main():
    print("DK Events Test starting...")

    payload = dk_events.fetch_events()

    # Handle empty or None payload
    if not payload:
        print(json.dumps({"status": "success", "events_found": 0, "events": []}, indent=2))
        print("DK Events Test finished.")
        return

    # If payload is a dictionary (single response object)
    if isinstance(payload, dict):
        page_title = payload.get("page_title", "")
        events = payload.get("events", [])
    # If payload is a list (list of events)
    elif isinstance(payload, list):
        page_title = f"{len(payload)} events found"
        events = payload
    else:
        page_title = "Unknown payload type"
        events = []

    # Print summary
    result = {
        "status": "success",
        "page_title": page_title,
        "events_found": len(events),
        "events_preview": events[:3]  # show first 3 events for debugging
    }

    print(json.dumps(result, indent=2))
    print("DK Events Test finished.")

if __name__ == "__main__":
    main()
