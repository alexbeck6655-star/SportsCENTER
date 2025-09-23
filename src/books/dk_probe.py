# src/books/dk_probe.py
from __future__ import annotations
import time
import typing as t
import requests
from requests import Response

# A very gentle "are you there?" probe for the NFL landing page.
# This DOES NOT crawl or parse odds yet—just proves we can fetch a public page.

NFL_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"

HEADERS = {
    # Look like a real browser so we aren't insta-blocked
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "close",
}

class ProbeResult(t.TypedDict, total=False):
    ok: bool
    status: int
    elapsed_ms: int
    url: str
    html_len: int
    marker_hit: bool
    note: str

def _marker_check(html: str) -> bool:
    """
    Very light fingerprint that tends to appear on DK pages without parsing JS.
    We keep it loose so minor site tweaks don’t break this.
    """
    needles = [
        "DraftKings",              # brand name
        "sportsbook.draftkings",   # asset urls
        "data-reactroot",          # React app root
        "data-tracking-context",   # analytics attrs seen on league pages
    ]
    h = html[:50000]  # cap to first chunk for speed
    return any(n.lower() in h.lower() for n in needles)

def quick_probe(timeout_sec: float = 12.0) -> ProbeResult:
    t0 = time.time()
    try:
        resp: Response = requests.get(NFL_URL, headers=HEADERS, timeout=timeout_sec)
        elapsed_ms = int((time.time() - t0) * 1000)
        html = resp.text or ""
        ok_basic = (200 <= resp.status_code < 300)
        ok_marker = _marker_check(html)
        return ProbeResult(
            ok=ok_basic and ok_marker,
            status=resp.status_code,
            elapsed_ms=elapsed_ms,
            url=str(resp.url),
            html_len=len(html),
            marker_hit=ok_marker,
            note=("OK" if ok_basic else "Non-2xx") + (" + marker" if ok_marker else " (no marker)"),
        )
    except requests.exceptions.RequestException as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return ProbeResult(
            ok=False,
            status=-1,
            elapsed_ms=elapsed_ms,
            url=NFL_URL,
            html_len=0,
            marker_hit=False,
            note=f"requests error: {type(e).__name__}: {e}",
        )

def pretty_line(res: ProbeResult) -> str:
    emoji = "✅" if res.get("ok") else "❌"
    return (
        f"{emoji} DK probe — status={res.get('status')} "
        f"elapsed={res.get('elapsed_ms')}ms "
        f"html={res.get('html_len')} "
        f"marker={res.get('marker_hit')} "
        f"url={res.get('url')} "
        f"note={res.get('note')}"
    )
