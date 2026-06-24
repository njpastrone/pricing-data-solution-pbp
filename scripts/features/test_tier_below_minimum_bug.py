"""
Test: quantity below the lowest tier minimum should use the LOWEST tier.

Bug (reported June 2026): Craft Boat "Custom Recycled Cotton Notebook - 5 x7"
has tiers 'T1: 100-249' ($6.00) and 'T2: 250-300' ($5.50). The order tab adds
products at quantity 1. Because 1 is below tier 1's minimum (100),
determine_tier_number() fell through to "use highest tier" and returned T2,
giving the cheaper bulk cost ($5.50) instead of the entry price ($6.00).

Expected: quantity below all ranges -> Tier 1 (entry-level price).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pricing_engine import determine_tier_number


def run():
    tier_string = 'T1: 100-249, T2: 250-300'

    cases = [
        (1,   1, "Below all tiers (order default qty) -> lowest tier"),
        (50,  1, "Still below tier 1 minimum -> lowest tier"),
        (100, 1, "First unit of tier 1"),
        (249, 1, "Last unit of tier 1"),
        (250, 2, "First unit of tier 2"),
        (300, 2, "Last unit of tier 2"),
        (500, 2, "Above all tiers -> highest tier (bulk)"),
    ]

    print(f"Tier string: {tier_string}\n")
    print(f"{'Qty':<6}{'Expected':<10}{'Actual':<10}{'Status':<8}Notes")
    print("-" * 70)

    failures = []
    for qty, expected, notes in cases:
        actual = determine_tier_number(qty, tier_string, 'Y')
        ok = actual == expected
        if not ok:
            failures.append((qty, expected, actual, notes))
        print(f"{qty:<6}T{expected:<9}T{str(actual):<9}{'PASS' if ok else 'FAIL':<8}{notes}")

    print("-" * 70)
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for qty, exp, act, notes in failures:
            print(f"  qty={qty}: expected T{exp}, got T{act} ({notes})")
        return False
    print("\nAll tier-selection cases pass.")
    return True


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
