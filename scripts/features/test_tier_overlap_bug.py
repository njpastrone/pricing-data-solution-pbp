"""
Test script to demonstrate tier overlap edge case.

Issue: When tier ranges overlap (e.g., T2: 448-1107, T3: 1008+),
the tier selection returns the wrong tier for quantities in the overlap zone.

Expected: Quantity 1008 should be T3 (1008+)
Actual: Quantity 1008 returns T2 (448-1107)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.helpers import parse_tier_info
from src.pricing_engine import determine_tier_number


def test_overlapping_tiers():
    """Test the problematic tier string with overlaps."""

    tier_string = 'T1: 112-447, T2: 448-1107, T3: 1008+'

    print("=" * 70)
    print("TIER OVERLAP BUG DEMONSTRATION")
    print("=" * 70)
    print(f"\nTier String: {tier_string}")

    # Parse the tiers
    tier_dict = parse_tier_info(tier_string)
    print(f"\nParsed Tiers:")
    for tier_num, (min_qty, max_qty) in tier_dict.items():
        if max_qty == float('inf'):
            print(f"  T{tier_num}: {min_qty}+")
        else:
            print(f"  T{tier_num}: {min_qty}-{max_qty}")

    # Identify overlaps
    print(f"\nOVERLAP DETECTED:")
    print(f"  T2 ends at 1107, but T3 starts at 1008")
    print(f"  Quantities 1008-1107 are covered by BOTH tiers!")

    # Test critical quantities
    test_quantities = [
        (447, 1, "Last unit of T1"),
        (448, 2, "First unit of T2"),
        (1007, 2, "Last unit before overlap"),
        (1008, 3, "First unit of T3 (SHOULD BE T3)"),
        (1050, 3, "Mid-overlap (SHOULD BE T3)"),
        (1107, 3, "Last unit of T2 overlap (SHOULD BE T3)"),
        (1108, 3, "First unit after T2 ends (SHOULD BE T3)"),
        (2000, 3, "Well into T3"),
    ]

    print("\n" + "=" * 70)
    print("TIER SELECTION RESULTS")
    print("=" * 70)
    print(f"{'Qty':<10} {'Expected':<10} {'Actual':<10} {'Status':<10} {'Notes'}")
    print("-" * 70)

    failures = []
    for qty, expected_tier, notes in test_quantities:
        actual_tier = determine_tier_number(qty, tier_string, 'Y')
        status = "✓ PASS" if actual_tier == expected_tier else "✗ FAIL"

        if actual_tier != expected_tier:
            failures.append((qty, expected_tier, actual_tier, notes))

        print(f"{qty:<10} T{expected_tier:<9} T{actual_tier if actual_tier else 'None':<9} {status:<10} {notes}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if failures:
        print(f"\n{len(failures)} FAILURES DETECTED:")
        for qty, expected, actual, notes in failures:
            print(f"  - Qty {qty}: Expected T{expected}, got T{actual} ({notes})")

        print(f"\nROOT CAUSE:")
        print(f"  The tier selection algorithm checks tiers in order (T1, T2, T3)")
        print(f"  and returns the FIRST match. For qty 1008:")
        print(f"    - T1 (112-447): 112 <= 1008 <= 447? NO")
        print(f"    - T2 (448-1107): 448 <= 1008 <= 1107? YES ← Returns T2 and stops")
        print(f"    - T3 (1008+): Never checked!")

        print(f"\nDATA QUALITY ISSUE:")
        print(f"  T3 should start at 1108 (right after T2 ends), not 1008")
        print(f"  Correct tier string: 'T1: 112-447, T2: 448-1107, T3: 1108+'")

        print(f"\nCODE ISSUE:")
        print(f"  The parsing and selection logic does not:")
        print(f"    1. Validate for overlapping ranges")
        print(f"    2. Warn users about data quality issues")
        print(f"    3. Handle ambiguous tier assignments")
    else:
        print("\nAll tests passed! (Unexpected - the bug should be present)")

    print("\n" + "=" * 70)


def test_correct_tiers():
    """Test what the tier string SHOULD be (no overlaps)."""

    tier_string = 'T1: 112-447, T2: 448-1107, T3: 1108+'

    print("\n" + "=" * 70)
    print("CORRECTED TIER STRING (NO OVERLAPS)")
    print("=" * 70)
    print(f"\nTier String: {tier_string}")

    tier_dict = parse_tier_info(tier_string)
    print(f"\nParsed Tiers:")
    for tier_num, (min_qty, max_qty) in tier_dict.items():
        if max_qty == float('inf'):
            print(f"  T{tier_num}: {min_qty}+")
        else:
            print(f"  T{tier_num}: {min_qty}-{max_qty}")

    print(f"\nNo overlaps - all tiers are mutually exclusive")

    # Test same quantities
    test_quantities = [
        (1007, 2),
        (1008, 2),
        (1107, 2),
        (1108, 3),
        (2000, 3),
    ]

    print("\nTier Selection (should all pass):")
    print(f"{'Qty':<10} {'Expected':<10} {'Actual':<10} {'Status'}")
    print("-" * 40)

    all_pass = True
    for qty, expected_tier in test_quantities:
        actual_tier = determine_tier_number(qty, tier_string, 'Y')
        status = "✓ PASS" if actual_tier == expected_tier else "✗ FAIL"
        all_pass = all_pass and (actual_tier == expected_tier)
        print(f"{qty:<10} T{expected_tier:<9} T{actual_tier if actual_tier else 'None':<9} {status}")

    if all_pass:
        print("\n✓ All tests pass with corrected tier ranges!")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_overlapping_tiers()
    test_correct_tiers()
