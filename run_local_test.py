import sys
sys.path.append("src")  # allow imports from src/

from books.dk_probe import quick_probe  # type: ignore

print("🏁 SportsCENTER smoke test (parse check)…")

info = quick_probe()
print(f"✅ DK probe — status={info['status']} elapsed={info['elapsed_ms']}ms "
      f"html={info['html_len']:,} marker={info['marker']} url={info['url']}")

parsed = info.get("parsed", {}) or {}
print(f"🔎 Title: {parsed.get('title','(none)')}")
print(f"🔗 Links found: {parsed.get('total_links',0)} | "
      f"event-ish: {parsed.get('eventish_links',0)}")

samples = parsed.get("sample_eventish", [])
if samples:
    print("🧪 Sample event-ish links:")
    for u in samples:
        print("   •", u)

print("✅ Test finished.")
