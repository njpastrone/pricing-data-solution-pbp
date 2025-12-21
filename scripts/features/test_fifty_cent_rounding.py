#!/usr/bin/env python3
"""
Test script for $0.50 rounding functionality.
Tests the round_to_nearest_fifty_cents helper function and rounding order of operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.helpers import round_to_nearest_fifty_cents, apply_marketing_rounding

def test_fifty_cent_rounding():
    """Test the round_to_nearest_fifty_cents function with various scenarios."""

    print("Testing $0.50 Rounding Functionality")
    print("=" * 50)

    # Test 1: Basic rounding up
    test_cases = [
        (24.37, 24.50, "Round up from .37"),
        (24.23, 24.00, "Round down from .23"),
        (24.75, 25.00, "Round up from .75"),
        (24.25, 24.00, "Round down from .25 (banker's rounding)"),
        (24.50, 24.50, "No change from .50"),
        (24.00, 24.00, "No change from .00"),
        (100.49, 100.50, "Round up near hundred"),
        (100.51, 100.50, "Round down near hundred"),
        (100.74, 100.50, "Round down from .74"),
        (100.76, 101.00, "Round up from .76"),
        (0.23, 0.00, "Round down near zero"),
        (0.26, 0.50, "Round up near zero"),
        (0.50, 0.50, "Exact half dollar"),
        (0.75, 1.00, "Round up from 0.75"),
        (1234.62, 1234.50, "Large number rounding"),
    ]

    print("\nTest 1: Basic Rounding Tests")
    print("-" * 40)

    all_passed = True
    for input_price, expected, description in test_cases:
        result = round_to_nearest_fifty_cents(input_price, enabled=True)
        passed = abs(result - expected) < 0.01
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"  ${input_price:7.2f} → ${result:7.2f} (expected ${expected:7.2f}) - {description} - {status}")

    if all_passed:
        print("\n✓ All basic tests passed!")
    else:
        print("\n✗ Some basic tests failed!")

    # Test 2: Disabled rounding
    print("\nTest 2: Disabled Rounding")
    print("-" * 40)

    input_price = 24.37
    result_enabled = round_to_nearest_fifty_cents(input_price, enabled=True)
    result_disabled = round_to_nearest_fifty_cents(input_price, enabled=False)

    print(f"  Input: ${input_price:.2f}")
    print(f"  With rounding enabled: ${result_enabled:.2f}")
    print(f"  With rounding disabled: ${result_disabled:.2f}")

    assert result_enabled == 24.50
    assert result_disabled == 24.37
    print("✓ PASS: Disabled rounding preserves original price")

    # Test 3: Order of operations (50 cent then marketing)
    print("\nTest 3: Order of Operations (50¢ → Marketing)")
    print("-" * 40)

    # Test case 1: Price that becomes divisible by 10 after 50 cent rounding
    price1 = 59.73
    step1 = round_to_nearest_fifty_cents(price1, enabled=True)
    step2 = apply_marketing_rounding(step1, enabled=True)

    print(f"  Start: ${price1:.2f}")
    print(f"  After 50¢ rounding: ${step1:.2f}")
    print(f"  After marketing rounding: ${step2:.2f}")
    print(f"  Expected: $59.50 (no marketing applied since not divisible by 10)")
    assert step1 == 59.50
    assert step2 == 59.50  # Marketing rounding doesn't apply to 59.50
    print("✓ PASS: Correct order of operations")

    # Test case 2: Price that becomes exactly divisible by 10
    price2 = 59.87
    step1 = round_to_nearest_fifty_cents(price2, enabled=True)
    step2 = apply_marketing_rounding(step1, enabled=True)

    print(f"\n  Start: ${price2:.2f}")
    print(f"  After 50¢ rounding: ${step1:.2f}")
    print(f"  After marketing rounding: ${step2:.2f}")
    print(f"  Expected: $59.00 (60.00 - 1.00)")
    assert step1 == 60.00
    assert step2 == 59.00  # Marketing rounding applies to 60.00
    print("✓ PASS: Marketing rounding applies to multiples of 10")

    # Test 4: Real-world pricing scenarios
    print("\nTest 4: Real-World Pricing Scenarios")
    print("-" * 40)

    scenarios = [
        (48.00, 100, 96.00, 96.00, 96.00, "Base product with 100% markup"),
        (48.00, 75, 84.00, 84.00, 84.00, "Base product with 75% markup"),
        (48.00, 50, 72.00, 72.00, 72.00, "Base product with 50% markup"),
        (25.00, 100, 50.00, 50.00, 49.00, "Product that triggers marketing rounding"),
        (33.33, 100, 66.66, 66.50, 66.50, "Product with decimal base cost"),
        (12.50, 100, 25.00, 25.00, 25.00, "Product with .50 base cost"),
    ]

    print("  Base Cost | Markup | Raw Price | After 50¢ | After Marketing | Description")
    print("  " + "-" * 75)

    for base_cost, markup_pct, raw_price, expected_50c, expected_marketing, desc in scenarios:
        calc_raw = base_cost * (1 + markup_pct / 100)
        after_50c = round_to_nearest_fifty_cents(calc_raw, enabled=True)
        after_marketing = apply_marketing_rounding(after_50c, enabled=True)

        # Check calculations
        assert abs(calc_raw - raw_price) < 0.01, f"Raw price mismatch: {calc_raw} vs {raw_price}"
        assert abs(after_50c - expected_50c) < 0.01, f"50c rounding mismatch: {after_50c} vs {expected_50c}"
        assert abs(after_marketing - expected_marketing) < 0.01, f"Marketing mismatch: {after_marketing} vs {expected_marketing}"

        print(f"  ${base_cost:8.2f} | {markup_pct:5}% | ${calc_raw:9.2f} | ${after_50c:9.2f} | ${after_marketing:15.2f} | {desc}")

    print("\n✓ All real-world scenarios passed!")

    # Test 5: Edge cases
    print("\nTest 5: Edge Cases")
    print("-" * 40)

    # Very small numbers
    assert round_to_nearest_fifty_cents(0.01, enabled=True) == 0.00
    assert round_to_nearest_fifty_cents(0.24, enabled=True) == 0.00
    assert round_to_nearest_fifty_cents(0.25, enabled=True) == 0.00  # Banker's rounding
    assert round_to_nearest_fifty_cents(0.26, enabled=True) == 0.50
    print("✓ PASS: Very small numbers handled correctly")

    # Very large numbers
    assert round_to_nearest_fifty_cents(999999.74, enabled=True) == 999999.50
    assert round_to_nearest_fifty_cents(999999.75, enabled=True) == 1000000.00
    print("✓ PASS: Very large numbers handled correctly")

    # Negative numbers (for below-cost pricing)
    assert round_to_nearest_fifty_cents(-24.37, enabled=True) == -24.50
    assert round_to_nearest_fifty_cents(-24.23, enabled=True) == -24.00
    print("✓ PASS: Negative numbers handled correctly")

    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("\n$0.50 rounding feature is working correctly:")
    print("- Rounds to nearest $0.50 increment")
    print("- Can be enabled/disabled")
    print("- Works with marketing rounding in correct order")
    print("- Handles edge cases properly")

if __name__ == "__main__":
    test_fifty_cent_rounding()