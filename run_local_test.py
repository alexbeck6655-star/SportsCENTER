# run_local_test.py (temporary: call DK probe)
import sys
sys.path.append("src")

from books.dk_probe import quick_probe

print("🔎 Running DraftKings connectivity probe…")
res = quick_probe()
print("Done.")
