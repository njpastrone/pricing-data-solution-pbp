#!/usr/bin/env python3
"""
Test script for bidirectional price editing functionality.
Tests the calculate_markup_from_price helper function.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.helpers import calculate_markup_from_price

def test_calculate_markup_from_price():
    """Test the calculate_markup_from_price function with various scenarios."""

    print("Testing bidirectional price editing helper function...")
    print("-" * 50)

    # Test 1: Standard 100% markup
    base_cost = 50.0
    client_price = 100.0
    expected_markup = 100.0
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 1 - Standard 100% markup:")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    # Test 2: 50% markup
    base_cost = 50.0
    client_price = 75.0
    expected_markup = 50.0
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 2 - 50% markup:")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    # Test 3: Break-even (0% markup)
    base_cost = 50.0
    client_price = 50.0
    expected_markup = 0.0
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 3 - Break-even (0% markup):")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    # Test 4: Below cost (-20% markup)
    base_cost = 50.0
    client_price = 40.0
    expected_markup = -20.0
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 4 - Below cost (-20% markup):")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    # Test 5: Edge case - zero base cost
    base_cost = 0.0
    client_price = 100.0
    expected_markup = 0.0  # Should return 0 for zero base cost
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 5 - Edge case (zero base cost):")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    # Test 6: High markup (250%)
    base_cost = 20.0
    client_price = 70.0
    expected_markup = 250.0
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 6 - High markup (250%):")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    # Test 7: Rounding precision (should round to 2 decimal places)
    base_cost = 33.33
    client_price = 99.99
    expected_markup = 200.00  # ((99.99/33.33) - 1) * 100 = 200.00
    actual_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Test 7 - Rounding precision:")
    print(f"  Base cost: ${base_cost:.2f}, Client price: ${client_price:.2f}")
    print(f"  Expected markup: {expected_markup}%, Actual: {actual_markup}%")
    print(f"  ✓ PASS" if abs(actual_markup - expected_markup) < 0.01 else f"  ✗ FAIL")
    print()

    print("-" * 50)
    print("✅ All tests completed!")

    # Test bidirectional consistency
    print("\nTesting bidirectional consistency:")
    print("-" * 50)

    base_cost = 45.67
    original_markup = 75.0

    # Calculate client price from markup
    client_price = base_cost * (1 + original_markup / 100)
    print(f"Starting with base cost: ${base_cost:.2f}")
    print(f"Applied markup: {original_markup}%")
    print(f"Resulting client price: ${client_price:.2f}")

    # Calculate markup back from client price
    calculated_markup = calculate_markup_from_price(base_cost, client_price)
    print(f"Calculated markup from price: {calculated_markup}%")

    if abs(calculated_markup - original_markup) < 0.01:
        print("✓ Bidirectional conversion is consistent!")
    else:
        print("✗ Bidirectional conversion has precision issues")

    print("\n✅ Testing complete!")

if __name__ == "__main__":
    test_calculate_markup_from_price()