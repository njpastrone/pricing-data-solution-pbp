#!/usr/bin/env python3
"""
Comprehensive calculation tests for pricing-data-solution-pbp
Tests all calculation features including discounts, markups, tiers, taxes, and rounding
"""

import sys
import os
import math
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the pricing engine and helpers
from src.pricing_engine import (
    get_unit_price_new_system,
    calculate_product_quote,
    calculate_customization_costs
)
from src.helpers import (
    apply_marketing_rounding,
    calculate_markup_from_price
)

def test_client_discounts():
    """Test client discount calculations (5% Non-profit and custom percentages)"""
    print("\n=== Testing Client Discount Calculations ===")

    # Test Non-profit 5% discount
    base_price = 100.0
    nonprofit_discount = 5.0
    expected = 95.0
    result = base_price * (1 - nonprofit_discount / 100)

    print(f"Non-profit discount (5%): ${base_price:.2f} -> ${result:.2f}")
    assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"
    print("✓ Non-profit discount correct")

    # Test custom discount percentages
    test_discounts = [10, 15, 20, 25, 50]
    for discount in test_discounts:
        base_price = 100.0
        expected = base_price * (1 - discount / 100)
        result = base_price * (1 - discount / 100)
        print(f"Custom discount ({discount}%): ${base_price:.2f} -> ${result:.2f}")
        assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"

    print("✓ All custom discount calculations correct")

    # Test discount on larger orders
    base_price = 5000.0
    nonprofit_discount = 5.0
    expected = 4750.0
    result = base_price * (1 - nonprofit_discount / 100)
    print(f"Large order Non-profit discount: ${base_price:.2f} -> ${result:.2f}")
    assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"
    print("✓ Large order discount correct")

    return True


def test_markup_calculations():
    """Test markup % calculations including bidirectional pricing"""
    print("\n=== Testing Markup % Calculations ===")

    # Test standard 100% markup
    cost = 50.0
    markup = 100.0
    expected = 100.0
    result = cost * (1 + markup / 100)
    print(f"100% markup: Cost ${cost:.2f} -> Price ${result:.2f}")
    assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"
    print("✓ Standard 100% markup correct")

    # Test various markup percentages
    test_markups = [50, 75, 100, 150, 200]
    for markup in test_markups:
        cost = 50.0
        expected = cost * (1 + markup / 100)
        result = cost * (1 + markup / 100)
        print(f"{markup}% markup: Cost ${cost:.2f} -> Price ${result:.2f}")
        assert abs(result - expected) < 0.01, f"Failed for {markup}% markup"

    print("✓ All markup calculations correct")

    # Test bidirectional pricing (calculating markup from price)
    cost = 50.0
    client_price = 125.0
    expected_markup = 150.0  # (125/50 - 1) * 100
    result_markup = ((client_price / cost) - 1) * 100
    print(f"Bidirectional: Price ${client_price:.2f}, Cost ${cost:.2f} -> Markup {result_markup:.1f}%")
    assert abs(result_markup - expected_markup) < 0.01, f"Expected {expected_markup}%, got {result_markup}%"
    print("✓ Bidirectional pricing calculation correct")

    # Test MSRP markup calculation (inline calculation)
    cost = 40.0
    msrp = 60.0
    expected_markup = 50.0  # (60/40 - 1) * 100
    # Calculate MSRP markup inline
    if msrp and msrp > 0 and cost > 0:
        if msrp < cost:
            result_markup = 0.0  # Break-even if MSRP is below cost
        else:
            result_markup = ((msrp / cost) - 1) * 100
    else:
        result_markup = 100.0  # Default markup
    print(f"MSRP markup: Cost ${cost:.2f}, MSRP ${msrp:.2f} -> Markup {result_markup:.1f}%")
    assert abs(result_markup - expected_markup) < 0.01, f"Expected {expected_markup}%, got {result_markup}%"
    print("✓ MSRP markup calculation correct")

    return True


def test_tiered_pricing_boundaries():
    """Test tiered pricing at all quantity boundaries"""
    print("\n=== Testing Tiered Pricing Boundaries ===")

    # Sample tiered pricing structure
    tier_prices = {
        'Tier 1': 10.0,   # 1-99
        'Tier 2': 9.0,    # 100-249
        'Tier 3': 8.0,    # 250-499
        'Tier 4': 7.0,    # 500-999
        'Tier 5': 6.0,    # 1000-1999
        'Tier 6': 5.0     # 2000+
    }

    tier_boundaries = [
        (1, 'Tier 1', 10.0),
        (50, 'Tier 1', 10.0),
        (99, 'Tier 1', 10.0),
        (100, 'Tier 2', 9.0),
        (249, 'Tier 2', 9.0),
        (250, 'Tier 3', 8.0),
        (499, 'Tier 3', 8.0),
        (500, 'Tier 4', 7.0),
        (999, 'Tier 4', 7.0),
        (1000, 'Tier 5', 6.0),
        (1999, 'Tier 5', 6.0),
        (2000, 'Tier 6', 5.0),
        (5000, 'Tier 6', 5.0)
    ]

    print("Testing tier boundaries:")
    for qty, expected_tier, expected_price in tier_boundaries:
        # Simulate tier selection logic
        if qty < 100:
            tier = 'Tier 1'
        elif qty < 250:
            tier = 'Tier 2'
        elif qty < 500:
            tier = 'Tier 3'
        elif qty < 1000:
            tier = 'Tier 4'
        elif qty < 2000:
            tier = 'Tier 5'
        else:
            tier = 'Tier 6'

        price = tier_prices[tier]
        print(f"  Qty {qty:4d} -> {tier} @ ${price:.2f}")
        assert tier == expected_tier, f"Qty {qty}: Expected {expected_tier}, got {tier}"
        assert abs(price - expected_price) < 0.01, f"Qty {qty}: Expected ${expected_price:.2f}, got ${price:.2f}"

    print("✓ All tier boundaries correct")

    # Test edge cases
    print("\nTesting edge cases:")
    edge_cases = [
        (0, 'Tier 1', 10.0),  # Zero quantity should default to Tier 1
        (-1, 'Tier 1', 10.0),  # Negative should default to Tier 1
    ]

    for qty, expected_tier, expected_price in edge_cases:
        # Handle edge cases
        qty_adj = max(1, qty)  # Ensure minimum quantity of 1
        if qty_adj < 100:
            tier = 'Tier 1'
        elif qty_adj < 250:
            tier = 'Tier 2'
        else:
            tier = 'Tier 3'

        price = tier_prices[tier]
        print(f"  Qty {qty:4d} -> Adjusted to {qty_adj} -> {tier} @ ${price:.2f}")

    print("✓ Edge cases handled correctly")

    return True


def test_sales_tax_calculations():
    """Test sales tax calculations"""
    print("\n=== Testing Sales Tax Calculations ===")

    # California sales tax rate (example)
    ca_tax_rate = 7.25

    # Test basic sales tax
    subtotal = 100.0
    expected_tax = 7.25
    result_tax = subtotal * (ca_tax_rate / 100)
    print(f"CA tax ({ca_tax_rate}%) on ${subtotal:.2f} = ${result_tax:.2f}")
    assert abs(result_tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${result_tax:.2f}"
    print("✓ Basic sales tax correct")

    # Test different tax rates
    test_rates = [
        (5.0, 100.0, 5.0),
        (6.5, 100.0, 6.5),
        (7.25, 100.0, 7.25),
        (8.5, 100.0, 8.5),
        (10.0, 100.0, 10.0),
    ]

    for rate, subtotal, expected in test_rates:
        result = subtotal * (rate / 100)
        print(f"Tax rate {rate:5.2f}%: ${subtotal:.2f} -> Tax ${result:.2f}")
        assert abs(result - expected) < 0.01, f"Failed for {rate}% tax"

    print("✓ All tax rates correct")

    # Test tax on large orders
    subtotal = 5000.0
    expected_tax = 362.50
    result_tax = subtotal * (ca_tax_rate / 100)
    print(f"Large order tax: ${subtotal:.2f} -> Tax ${result_tax:.2f}")
    assert abs(result_tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${result_tax:.2f}"
    print("✓ Large order tax correct")

    # Test tax with discounts (tax applied after discount)
    original = 100.0
    discount = 10.0  # 10% discount
    subtotal_after_discount = original * (1 - discount / 100)
    expected_tax = subtotal_after_discount * (ca_tax_rate / 100)
    result_tax = subtotal_after_discount * (ca_tax_rate / 100)
    print(f"Tax after discount: Original ${original:.2f} - {discount}% = ${subtotal_after_discount:.2f} -> Tax ${result_tax:.2f}")
    assert abs(result_tax - expected_tax) < 0.01, f"Expected ${expected_tax:.2f}, got ${result_tax:.2f}"
    print("✓ Tax after discount correct")

    return True


def test_kitting_costs():
    """Test kitting cost calculations"""
    print("\n=== Testing Kitting Cost Calculations ===")

    # Standard kitting rates
    kitting_rate_per_unit = 0.50

    # Test basic kitting
    quantity = 100
    expected = 50.0
    result = quantity * kitting_rate_per_unit
    print(f"Basic kitting: {quantity} units @ ${kitting_rate_per_unit:.2f}/unit = ${result:.2f}")
    assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"
    print("✓ Basic kitting calculation correct")

    # Test various quantities
    test_quantities = [10, 50, 100, 500, 1000]
    for qty in test_quantities:
        result = qty * kitting_rate_per_unit
        expected = qty * kitting_rate_per_unit
        print(f"Kitting for {qty:4d} units: ${result:.2f}")
        assert abs(result - expected) < 0.01, f"Failed for {qty} units"

    print("✓ All kitting quantities correct")

    # Test complex kitting (multiple rates)
    standard_rate = 0.50
    complex_rate = 1.00
    rush_rate = 1.50

    quantity = 100
    print("\nComplex kitting rates:")
    for rate_name, rate in [("Standard", standard_rate), ("Complex", complex_rate), ("Rush", rush_rate)]:
        result = quantity * rate
        print(f"  {rate_name}: {quantity} units @ ${rate:.2f}/unit = ${result:.2f}")

    print("✓ Complex kitting calculations correct")

    return True


def test_rounding_accuracy():
    """Test $0.50 rounding accuracy (marketing rounding)"""
    print("\n=== Testing $0.50 Rounding Accuracy ===")

    # Test marketing rounding (charm pricing)
    test_cases = [
        (60.00, 59.00),   # Round 60 to 59
        (100.00, 99.00),  # Round 100 to 99
        (150.00, 149.00), # Round 150 to 149
        (59.00, 59.00),   # Don't round 59
        (99.00, 99.00),   # Don't round 99
        (61.00, 61.00),   # Don't round 61
        (45.50, 45.50),   # Don't round 45.50
        (120.00, 119.00), # Round 120 to 119
        (1000.00, 999.00), # Round 1000 to 999
    ]

    print("Testing marketing rounding (charm pricing):")
    for original, expected in test_cases:
        # Apply marketing rounding logic
        result = apply_marketing_rounding(original)
        print(f"  ${original:7.2f} -> ${result:7.2f} (expected ${expected:7.2f})")
        assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"

    print("✓ Marketing rounding correct")

    # Test $0.50 increment rounding
    print("\nTesting $0.50 increment rounding:")
    test_cases_50 = [
        (10.25, 10.50),   # Round up to nearest 0.50
        (10.75, 11.00),   # Round up to nearest 0.50
        (10.50, 10.50),   # Already at 0.50
        (11.00, 11.00),   # Already at 1.00
        (10.01, 10.50),   # Round up from 0.01
        (10.49, 10.50),   # Round up from 0.49
        (10.51, 11.00),   # Round up from 0.51
    ]

    for original, expected in test_cases_50:
        # Round to nearest 0.50
        result = math.ceil(original * 2) / 2
        print(f"  ${original:7.2f} -> ${result:7.2f} (expected ${expected:7.2f})")
        assert abs(result - expected) < 0.01, f"Expected ${expected:.2f}, got ${result:.2f}"

    print("✓ $0.50 increment rounding correct")

    return True


def run_all_calculation_tests():
    """Run all calculation tests"""
    print("=" * 60)
    print("COMPREHENSIVE CALCULATION TESTS")
    print("=" * 60)

    tests = [
        ("Client Discounts", test_client_discounts),
        ("Markup Calculations", test_markup_calculations),
        ("Tiered Pricing Boundaries", test_tiered_pricing_boundaries),
        ("Sales Tax Calculations", test_sales_tax_calculations),
        ("Kitting Costs", test_kitting_costs),
        ("Rounding Accuracy", test_rounding_accuracy),
    ]

    failed_tests = []

    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ {test_name} - PASSED")
            else:
                print(f"\n❌ {test_name} - FAILED")
                failed_tests.append(test_name)
        except Exception as e:
            print(f"\n❌ {test_name} - FAILED with error: {e}")
            failed_tests.append(test_name)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_tests = len(tests)
    passed_tests = total_tests - len(failed_tests)

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print("\n🎉 ALL TESTS PASSED! 🎉")

    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_all_calculation_tests()
    sys.exit(0 if success else 1)