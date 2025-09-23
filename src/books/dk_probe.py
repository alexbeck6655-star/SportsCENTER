# src/books/dk_probe.py
"""
DraftKings connectivity probe (no odds logic yet).
- Tries a few known public JSON endpoints used by the DK site.
- Prints a short status line so we can verify we can reach DK.
- No Playwright/JS yet: pure HTTP GET with a desktop User-Agent.
"""

from __future__ import annotations
import json
from typing import Dict, Any, Optional
import sys
import time

try:
    import requests  # type: ignore
except Exception as e:
    print("❌ requests not installed. Add it to requirements.txt")
    raise

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://sportsbook.draftkings.com/",
    "Connection": "keep-alive",
}

# Known event-group endpoints DK uses (IDs can change; we’ll try several).
# These are harmless GETs; we’re just checking reachability + some JSON shape.
CANDIDATES = [
    # NFL event group (varies by season/region; we probe multiple).
    "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/88670846?format=json",
    "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/88808?format=json",
    "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/84240?format=json",
]

def _shorten(obj: Any, n: int = 600) -> str:
    try:
        s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        s = str(obj)
    return (s[: n] + "…") if len(s) > n else s

def quick_probe(timeout: float = 12.0) -> Dict[str, Any]:
    session = requests.Session()
    session.headers.update(HEADERS)

    last_err: Optional[str] = None
    for url in CANDIDATES:
        try:
            t0 = time.time()
            r = session.get(url, timeout=timeout)
            dt = time.time() - t0
            status = r.status_code
            ctype = r.headers.get("Content-Type", "")
            note = f"status={status} time={dt:.2f}s ctype={ctype}"

            if status != 200:
                last_err = f"{url} -> {note}"
                continue

            # Try JSON first
            data: Any = None
            try:
                data = r.json()
            except Exception:
                pass

            if isinstance(data, dict) and ("eventGroup" in data or "eventGroupId" in _shorten(data, 200)):
                # Count a few things if present
                eg = data.get("eventGroup", {})
                events = eg.get("events") or data.get("events") or []
                categories = eg.get("offerCategories") or []
                summary = {
                    "events_count": len(events) if isinstance(events, list) else 0,
                    "categories": [c.get("name") for c in categories[:5] if isinstance(c, dict)],
                }
                print(f"✅ DK JSON OK :: {note}")
                print(f"• URL: {url}")
                print(f"• Summary: {summary}")
                # show a tiny sample of the first event id/name if available
                if isinstance(events, list) and events:
                    ev0 = events[0]
                    sample = {k: ev0.get(k) for k in ("eventId", "name", "startDate")}
                    print(f"• Sample event: {sample}")
                else:
                    print("• No events array visible (may be off-season or different group).")
                return {"ok": True, "url": url, "note": note, "summary": summary}

            # If JSON didn’t look right, at least show a snippet of text
            txt = r.text
            print(f"⚠️ DK responded but JSON shape unexpected :: {note}")
            print(_shorten(txt, 500))
            return {"ok": True, "url": url, "note": note, "summary": "unexpected-shape"}

        except Exception as e:
            last_err = f"{url} -> {type(e).__name__}: {e}"

    print("❌ DK probe could not confirm a working endpoint.")
    if last_err:
        print(f"Last error: {last_err}")
    return {"ok": False, "error": last_err or "unknown"}

if __name__ == "__main__":
    res = quick_probe()
    # exit non-zero on failure so Actions shows red if we genuinely can’t reach DK
    sys.exit(0 if res.get("ok") else 1)
