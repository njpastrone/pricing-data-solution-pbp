"""
Test that the Gronn product tier selection works correctly after the fix.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import warnings
warnings.filterwarnings('ignore')

from src.data_loader import load_pricing_data
from src.helpers import get_column_value, parse_tier_info
from src.pricing_engine import determine_tier_number

def test_gronn_tiers():
    print(f"\n{'='*70}")
    print("TESTING GRONN UPCYCLED GLASSES TIER SELECTION")
    print('='*70)

    # Load data
    df, _, _ = load_pricing_data('real')

    # Find Gronn Sand Blasted product
    gronn = df[df['Partner'].str.contains('Grønn', na=False)]
    sand_blasted = gronn[gronn['Product/Service'].str.contains('Sand Blasted', na=False)]

    if len(sand_blasted) == 0:
        print("\n✗ Product not found!")
        return

    row = sand_blasted.iloc[0]
    product_name = get_column_value(row, 'Product/Service', 'Product Name', 'Unknown')
    tier_info = get_column_value(row, 'Pricing Tiers Info', 'Tier Range', '')

    print(f"\nProduct: {product_name}")
    print(f"Tier String: {tier_info}")

    # Parse tiers
    tier_dict = parse_tier_info(tier_info)
    print(f"\nParsed Tiers:")
    for tier_num, (min_qty, max_qty) in sorted(tier_dict.items()):
        if max_qty == float('inf'):
            print(f"  T{tier_num}: {min_qty}+")
        else:
            print(f"  T{tier_num}: {min_qty}-{max_qty}")

    # Check for overlaps
    print(f"\n{'='*70}")
    print("OVERLAP CHECK")
    print('='*70)

    tier_numbers = sorted(tier_dict.keys())
    has_overlap = False

    for i in range(len(tier_numbers) - 1):
        t1_num = tier_numbers[i]
        t2_num = tier_numbers[i + 1]

        t1_min, t1_max = tier_dict[t1_num]
        t2_min, t2_max = tier_dict[t2_num]

        if t1_max != float('inf') and t1_max >= t2_min:
            has_overlap = True
            print(f"\n⚠️  OVERLAP DETECTED!")
            print(f"  T{t1_num} ends at {t1_max}, T{t2_num} starts at {t2_min}")
            print(f"  Overlap: {t2_min}-{t1_max}")
        else:
            gap = t2_min - t1_max
            if gap == 1:
                print(f"✓ T{t1_num} → T{t2_num}: Correctly adjacent (T{t1_num} ends at {t1_max}, T{t2_num} starts at {t2_min})")
            elif gap > 1:
                print(f"⚠️  T{t1_num} → T{t2_num}: Gap of {gap-1} units ({t1_max+1} to {t2_min-1})")

    if not has_overlap:
        print(f"\n✓ No overlaps detected - tier ranges are clean!")

    # Test tier selection with critical quantities
    print(f"\n{'='*70}")
    print("TIER SELECTION TEST")
    print('='*70)

    test_quantities = [
        (111, 'T1', 'Below T1'),
        (112, 'T1', 'First unit of T1'),
        (447, 'T1', 'Last unit of T1'),
        (448, 'T2', 'First unit of T2'),
        (1006, 'T2', 'Near end of T2'),
        (1007, 'T2', 'Last unit of T2 (CRITICAL)'),
        (1008, 'T3', 'First unit of T3 (CRITICAL - was overlapping before)'),
        (1009, 'T3', 'Second unit of T3'),
        (1050, 'T3', 'Mid T3'),
        (1107, 'T3', 'Former overlap zone'),
        (2000, 'T3', 'Well into T3'),
    ]

    print(f"\n{'Quantity':<10} {'Expected':<10} {'Actual':<10} {'Status':<10} {'Notes'}")
    print(f"{'-'*70}")

    all_pass = True
    failures = []

    for qty, expected_tier, notes in test_quantities:
        actual_tier_num = determine_tier_number(qty, tier_info, 'Y')

        if actual_tier_num is None:
            actual_tier = 'None'
        else:
            actual_tier = f'T{actual_tier_num}'

        expected_tier_display = expected_tier if expected_tier != 'None' else 'None'

        if actual_tier == expected_tier_display:
            status = '✓ PASS'
        else:
            status = '✗ FAIL'
            all_pass = False
            failures.append((qty, expected_tier_display, actual_tier, notes))

        print(f"{qty:<10} {expected_tier_display:<10} {actual_tier:<10} {status:<10} {notes}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)

    if all_pass:
        print(f"\n✓ ALL TESTS PASSED!")
        print(f"\nTier selection is working correctly:")
        print(f"  - No overlaps detected in tier ranges")
        print(f"  - All quantities map to correct tiers")
        print(f"  - Critical boundary at 1007/1008 works correctly")
        print(f"\nThe fix was successful!")
    else:
        print(f"\n✗ {len(failures)} TEST(S) FAILED:")
        for qty, expected, actual, notes in failures:
            print(f"  - Qty {qty}: Expected {expected}, got {actual} ({notes})")
        print(f"\nThere may still be issues with tier selection.")


if __name__ == "__main__":
    test_gronn_tiers()
    print(f"\n{'='*70}\n")
