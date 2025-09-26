# src/books/dk_events.py
from __future__ import annotations
import asyncio
import re
import time
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

DK_URL = "https://sportsbook.draftkings.com/leagues/football/nfl"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.8",
    "Cache-Control": "no-cache",
}


def _scan_links(html: str) -> List[Dict[str, str]]:
    """Scan static HTML anchors for event links."""
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    events = {}
    for a in anchors:
        href = a["href"]
        if "/event/" in href:
            m = re.search(r"/event/(\d+)", href)
            if not m:
                continue
            ev_id = m.group(1)
            link = href if href.startswith("http") else urljoin(DK_URL, href)
            label = a.get_text(" ", strip=True)
            if not label:
                label = a.get("aria-label") or a.get("title") or ""
            if ev_id not in events:
                events[ev_id] = {"id": ev_id, "teams": label.strip(), "link": link}
    return list(events.values())


async def _playwright_fetch() -> List[Dict[str, str]]:
    """Use Playwright to render JS and then scrape event links."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"]
        )
        page = await context.new_page()
        try:
            await page.goto(DK_URL, wait_until="domcontentloaded", timeout=20000)
        except PlaywrightTimeoutError:
            # fallback short wait
            pass

        # Wait for event link anchors to appear (any anchor with /event/)
        try:
            await page.wait_for_selector("a[href*='/event/']", timeout=7000)
        except PlaywrightTimeoutError:
            # no event links loaded in timeout — return empty
            await context.close()
            await browser.close()
            return []

        anchors = await page.query_selector_all("a[href*='/event/']")
        seen = {}
        for a in anchors:
            href = await a.get_attribute("href") or ""
            if "/event/" not in href:
                continue
            # extract id
            m = re.search(r"/event/(\d+)", href)
            if not m:
                continue
            ev_id = m.group(1)
            label = (await a.inner_text()).strip()
            link = href if href.startswith("http") else urljoin(DK_URL, href)
            if ev_id not in seen:
                seen[ev_id] = {"id": ev_id, "teams": label, "link": link}

        await context.close()
        await browser.close()
        return list(seen.values())


def fetch_events(debug: bool = False) -> List[Dict[str, str]]:
    """
    Try static fetch first; if no events, fall back to Playwright.
    """
    start = time.time()
    # 1) static HTML
    try:
        resp = requests.get(DK_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        html = resp.text
        events = _scan_links(html)
        if debug:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string if soup.title else ""
            print(f"[INFO] Static: title={title!r}, html_len={len(html)}, found={len(events)} via link scan")
        if events:
            return events
    except Exception as e:
        if debug:
            print(f"[WARN] Static fetch failed: {e}")

    # 2) Playwright fallback
    if debug:
        print("[INFO] Falling back to Playwright rendering…")
    try:
        evs = asyncio.run(_playwright_fetch())
        if debug:
            print(f"[INFO] Playwright found {len(evs)} events")
        return evs
    except Exception as e:
        if debug:
            print(f"[ERROR] Playwright path failed: {e}")
        return []
