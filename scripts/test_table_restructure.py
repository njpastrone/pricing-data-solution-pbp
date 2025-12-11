#!/usr/bin/env python3
"""
Test script for verifying Tab 3 table restructuring functionality.

This script tests:
1. Helper functions for split total calculations
2. Pricing breakdown table structure
3. Order summary table structure with PBP Cost and Client Price columns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.helpers import calculate_split_totals, format_pricing_breakdown_row


def test_calculate_split_totals():
    """Test split totals calculation for different order scenarios."""

    print("Testing calculate_split_totals function...")
    print("=" * 50)

    # Test case 1: Single product with no customization
    order_items_1 = [{
        'is_custom': False,
        'product_subtotal': 100.0,  # PBP cost
        'markup_amount': 100.0,      # 100% markup
        'customization_setup_cost': 0,
        'customization_setup_total': 0,
        'customization_unit_cost': 0,
        'customization_unit_total': 0
    }]

    result_1 = calculate_split_totals(order_items_1)
    assert result_1['products_pbp_cost'] == 100.0, f"Expected 100.0, got {result_1['products_pbp_cost']}"
    assert result_1['products_client_price'] == 200.0, f"Expected 200.0, got {result_1['products_client_price']}"
    assert result_1['customization_pbp_cost'] == 0.0
    assert result_1['customization_client_price'] == 0.0
    print("✓ Test 1 passed: Single product, no customization")

    # Test case 2: Product with customization
    order_items_2 = [{
        'is_custom': False,
        'product_subtotal': 100.0,
        'markup_amount': 100.0,
        'customization_setup_cost': 25.0,   # PBP pays partner
        'customization_setup_total': 50.0,  # Client pays
        'customization_unit_cost': 10.0,    # PBP pays partner per unit
        'customization_unit_total': 20.0    # Client pays per unit
    }]

    result_2 = calculate_split_totals(order_items_2)
    assert result_2['products_pbp_cost'] == 100.0
    assert result_2['products_client_price'] == 200.0
    assert result_2['customization_pbp_cost'] == 35.0  # 25 + 10
    assert result_2['customization_client_price'] == 70.0  # 50 + 20
    assert result_2['total_pbp_cost'] == 135.0
    assert result_2['total_client_price'] == 270.0
    print("✓ Test 2 passed: Product with customization")

    # Test case 3: Multiple products
    order_items_3 = [
        {
            'is_custom': False,
            'product_subtotal': 100.0,
            'markup_amount': 100.0,
            'customization_setup_cost': 0,
            'customization_setup_total': 0,
            'customization_unit_cost': 0,
            'customization_unit_total': 0
        },
        {
            'is_custom': False,
            'product_subtotal': 50.0,
            'markup_amount': 25.0,  # 50% markup
            'customization_setup_cost': 10.0,
            'customization_setup_total': 20.0,
            'customization_unit_cost': 5.0,
            'customization_unit_total': 10.0
        }
    ]

    result_3 = calculate_split_totals(order_items_3)
    assert result_3['products_pbp_cost'] == 150.0  # 100 + 50
    assert result_3['products_client_price'] == 275.0  # 200 + 75
    assert result_3['customization_pbp_cost'] == 15.0  # 10 + 5
    assert result_3['customization_client_price'] == 30.0  # 20 + 10
    print("✓ Test 3 passed: Multiple products")

    # Test case 4: Custom line item
    order_items_4 = [{
        'is_custom': True,
        'product_total': 150.0
    }]

    result_4 = calculate_split_totals(order_items_4)
    assert result_4['products_pbp_cost'] == 150.0
    assert result_4['products_client_price'] == 150.0  # Custom items have same cost and price
    print("✓ Test 4 passed: Custom line item")

    print("\n✅ All calculate_split_totals tests passed!")
    return True


def test_format_pricing_breakdown_row():
    """Test formatting of pricing breakdown rows."""

    print("\nTesting format_pricing_breakdown_row function...")
    print("=" * 50)

    # Test case 1: Regular product row with new column structure
    row_1 = format_pricing_breakdown_row(
        "Base Product: Test Product",
        10,
        25.0,  # PBP per unit
        250.0,  # PBP total
        50.0,   # Client per unit
        500.0   # Client total
    )
    # New order: Description, Units, PBP Cost (Per Unit), PBP Cost, Client Price (Per Unit), Client Price
    assert row_1 == ["Base Product: Test Product", "10", "$25.00", "$250.00", "$50.00", "$500.00"]
    print("✓ Test 1 passed: Regular product row with logical column order")

    # Test case 2: One-time setup fee
    row_2 = format_pricing_breakdown_row(
        "Customization Setup",
        "one-time",
        100.0,  # PBP per unit (same as total for one-time)
        100.0,  # PBP total
        200.0,  # Client per unit (same as total for one-time)
        200.0   # Client total
    )
    assert row_2 == ["Customization Setup", "1", "$100.00", "$100.00", "$200.00", "$200.00"]
    print("✓ Test 2 passed: One-time setup fee")

    # Test case 3: Zero values
    row_3 = format_pricing_breakdown_row(
        "No cost item",
        5,
        0,  # PBP per unit
        0,  # PBP total
        0,  # Client per unit
        0   # Client total
    )
    assert row_3 == ["No cost item", "5", "", "$0.00", "", "$0.00"]
    print("✓ Test 3 passed: Zero values with proper empty strings")

    print("\n✅ All format_pricing_breakdown_row tests passed!")
    return True


def main():
    """Run all tests."""
    print("Tab 3 Table Restructuring Test Suite")
    print("=" * 50)

    all_passed = True

    try:
        all_passed &= test_calculate_split_totals()
        all_passed &= test_format_pricing_breakdown_row()

        if all_passed:
            print("\n" + "=" * 50)
            print("🎉 ALL TESTS PASSED! 🎉")
            print("=" * 50)
            print("\nThe table restructuring implementation is working correctly:")
            print("✓ Split totals calculation (PBP Cost vs Client Price)")
            print("✓ Pricing breakdown row formatting")
            print("✓ Handles products, customization, and custom line items")
            print("\nYou can now test the UI to verify:")
            print("1. Section 2 (Current Order) shows logical column order: Description, Units, PBP Cost (Per Unit), PBP Cost, Client Price (Per Unit), Client Price")
            print("2. Section 4 (Order Summary) uses the same column structure")
            print("3. Product descriptions show 'Base Product: [Product Name]' format")
            print("4. Per-unit prices come before totals (showing rate before calculation)")
            print("5. Both sections clearly differentiate PBP costs vs client prices")
        else:
            print("\n❌ Some tests failed. Please review the output above.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)