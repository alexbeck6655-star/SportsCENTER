# run_local_events_test.py
import sys
sys.path.append("src")  # allow "from books..." imports

from books.dk_events import fetch_events

print("▶ DK Events test starting…")
events = fetch_events()

if not events:
    print("⚠ No events found (could be DK layout/time window).")
else:
    print(f"✅ Found {len(events)} DK events. Showing first 10:")
    for e in events[:10]:
        teams = e.get("teams") or "(no label)"
        link = e.get("link")
        print(f" • {teams}  ->  {link}")

print("✓ Test finished.")
