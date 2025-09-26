# run_local_events_test.py
import sys
sys.path.append("src")

from books.dk_events import fetch_events
from common.odds import american_to_prob  # keep this import; nice sanity tool

def main():
    print("DK Events Test starting...")
    events = fetch_events(debug=True)

    if not events:
        print("{")
        print('  "status": "success",')
        print(f'  "events_found": 0,')
        print('  "events": []')
        print("}")
        return

    # Show first 3 safely
    preview = events[:3]
    print("{")
    print('  "status": "success",')
    print(f'  "events_found": {len(events)},')
    print('  "events_preview": [')
    for i, e in enumerate(preview):
        teams = e.get("teams", "")
        link = e.get("link")
        comma = "," if i < len(preview) - 1 else ""
        print(f'    {{"teams": "{teams}", "link": "{link or ""}"}}{comma}')
    print("  ]")
    print("}")

if __name__ == "__main__":
    main()
