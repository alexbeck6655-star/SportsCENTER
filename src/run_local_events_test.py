#!/usr/bin/env python3
"""
Local DK events smoke test.

- Imports books.dk_events.fetch_events()
- Runs it (works whether it's sync or async)
- Prints a compact JSON summary so you can see if events are being found
"""

from __future__ import annotations

import os
import sys
import json
import asyncio
import inspect
from typing import Any, Dict, List

# --- make "src/" imports work whether the runner cwd is repo root or src/ ---
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if HERE not in sys.path:
    sys.path.append(HERE)
if ROOT not in sys.path:
    sys.path.append(ROOT)

# ---- import the DK fetcher ----
try:
    from books.dk_events import fetch_events  # type: ignore
except Exception as e:
    print("DK Events Test starting...")
    print(json.dumps({
        "status": "import_error",
        "error": f"could not import books.dk_events.fetch_events: {e}"
    }, ensure_ascii=False))
    raise SystemExit(1)


def _run_maybe_async(fn):
    """Call fn() whether it's sync or async, and return the result."""
    if inspect.iscoroutinefunction(fn):
        return asyncio.run(fn())
    # If the module gave us a *callable* object that returns a coroutine, catch that too.
    result = fn()
    if inspect.iscoroutine(result):
        return asyncio.run(result)
    return result


def main() -> None:
    print("DK Events Test starting...")

    # how many events to preview in the log; override with env var if you want
    try:
        preview_n = int(os.getenv("PREVIEW_N", "3"))
    except ValueError:
        preview_n = 3

    try:
        # Expectation: fetch_events() returns a dict with at least:
        #   {"page_title": str, "events": List[Dict[str, Any]]}
        payload: Dict[str, Any] = _run_maybe_async(fetch_events)
    except Exception as e:
        print(json.dumps({
            "status": "fetch_error",
            "error": f"{type(e).__name__}: {e}"
        }, ensure_ascii=False))
        raise SystemExit(1)

    # Normalize structure defensively
    page_title = payload.get("page_title") or payload.get("title") or ""
    events: List[Dict[str, Any]] = payload.get("events") or []

    summary = {
        "status": "success",
        "page_title": page_title,
        "events_found": len(events),
        # only preview the first N in the console to keep logs short
        "events_preview": events[:preview_n],
    }

    print(json.dumps(summary, ensure_ascii=False))
    print("DK Events Test finished.")


if __name__ == "__main__":
    main()
