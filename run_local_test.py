# run_local_test.py
import sys
sys.path.append("src")      # allow imports from src/

from books.dk_probe import quick_probe, pretty_line

print("🧪 SportsCENTER smoke test running…")

res = quick_probe()
print(pretty_line(res))

print("🔚 Test finished.")
