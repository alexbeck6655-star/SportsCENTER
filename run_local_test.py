import sys
sys.path.append("src")  # allow imports from src/

from common.odds import american_to_prob

print("=== Local Test: Odds Conversion ===")
for o in [-150, +200, +110]:
    prob = american_to_prob(o)
    print(f"Odds {o}: implied prob = {prob:.2%}")

print("✅ Test finished.")
