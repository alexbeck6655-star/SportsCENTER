# src/common/odds.py
"""
Simple odds math utilities to test our setup.
"""

def american_to_prob(odds: int) -> float:
    """
    Convert American odds to implied probability.
    e.g. -150 -> 0.60, +200 -> 0.3333
    """
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    return 100 / (odds + 100)
