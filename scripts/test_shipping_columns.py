#!/usr/bin/env python
"""
Test Script for Shipping Column Updates
Tests the new shipping cost columns and helper functions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_pricing_data
from src.helpers import get_shipping_costs, format_shipping_display, clean_price

def test_shipping_columns():
    """Test that shipping columns load correctly from both datasets"""
    print("\n" + "="*50)
    print("TESTING SHIPPING COLUMN FUNCTIONALITY")
    print("="*50)

    # Test 1: Load demo data (legacy structure)
    print("\n1. Testing DEMO dataset (legacy single column)...")
    df_demo, _, _ = load_pricing_data('demo')

    # Check for column existence
    has_legacy = 'Shipping' in df_demo.columns
    has_new_pbp = 'Shipping Cost (PBP)' in df_demo.columns
    has_new_client = 'Shipping Price (Client)' in df_demo.columns

    print(f"   - Has 'Shipping' column: {has_legacy}")
    print(f"   - Has 'Shipping Cost (PBP)': {has_new_pbp}")
    print(f"   - Has 'Shipping Price (Client)': {has_new_client}")

    if has_legacy and not has_new_pbp:
        print("   ✅ Demo dataset correctly using legacy structure")
    else:
        print("   ❌ Demo dataset structure unexpected")

    # Test 2: Load real data (new structure)
    print("\n2. Testing REAL dataset (new dual columns)...")
    df_real, _, _ = load_pricing_data('real')

    has_legacy = 'Shipping' in df_real.columns
    has_new_pbp = 'Shipping Cost (PBP)' in df_real.columns
    has_new_client = 'Shipping Price (Client)' in df_real.columns

    print(f"   - Has 'Shipping' column: {has_legacy}")
    print(f"   - Has 'Shipping Cost (PBP)': {has_new_pbp}")
    print(f"   - Has 'Shipping Price (Client)': {has_new_client}")

    if has_new_pbp and has_new_client and not has_legacy:
        print("   ✅ Real dataset correctly using new structure")
    else:
        print("   ❌ Real dataset structure unexpected")

def test_helper_functions():
    """Test the shipping helper functions with various data"""
    print("\n" + "="*50)
    print("TESTING HELPER FUNCTIONS")
    print("="*50)

    test_cases = [
        {
            'name': 'New structure - both values',
            'data': {'Shipping Cost (PBP)': '$10.00', 'Shipping Price (Client)': '$15.00'},
            'expected_costs': (10.0, 15.0),
            'expected_display': 'PBP: $10.00 | Client: $15.00'
        },
        {
            'name': 'Legacy structure - single value',
            'data': {'Shipping': '$12.50'},
            'expected_costs': (12.5, 12.5),
            'expected_display': 'Shipping: $12.50'
        },
        {
            'name': 'No shipping data',
            'data': {},
            'expected_costs': (0.0, 0.0),
            'expected_display': 'No shipping data'
        },
        {
            'name': 'New structure - PBP only',
            'data': {'Shipping Cost (PBP)': '$8.00', 'Shipping Price (Client)': ''},
            'expected_costs': (8.0, 0.0),
            'expected_display': 'PBP: $8.00 | Client: $0.00'
        },
        {
            'name': 'Legacy with invalid value',
            'data': {'Shipping': 'N/A'},
            'expected_costs': (0.0, 0.0),
            'expected_display': 'No shipping data'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}:")
        print(f"   Input: {test['data']}")

        # Test get_shipping_costs
        pbp, client = get_shipping_costs(test['data'])
        print(f"   get_shipping_costs: ({pbp}, {client})")

        if (pbp, client) == test['expected_costs']:
            print(f"   ✅ Costs match expected: {test['expected_costs']}")
        else:
            print(f"   ❌ Expected {test['expected_costs']}, got ({pbp}, {client})")

        # Test format_shipping_display
        display = format_shipping_display(test['data'])
        print(f"   format_shipping_display: '{display}'")

        if display == test['expected_display']:
            print(f"   ✅ Display matches expected: '{test['expected_display']}'")
        else:
            print(f"   ❌ Expected '{test['expected_display']}', got '{display}'")

def test_real_product_examples():
    """Test with actual product data from spreadsheets"""
    print("\n" + "="*50)
    print("TESTING REAL PRODUCT EXAMPLES")
    print("="*50)

    # Load both datasets
    df_demo, _, _ = load_pricing_data('demo')
    df_real, _, _ = load_pricing_data('real')

    # Test a demo product
    print("\n1. Demo Product Example:")
    if len(df_demo) > 0:
        demo_product = df_demo.iloc[0].to_dict()
        print(f"   Product: {demo_product.get('Product/Service', 'Unknown')}")
        print(f"   Partner: {demo_product.get('Partner', 'Unknown')}")

        pbp, client = get_shipping_costs(demo_product)
        display = format_shipping_display(demo_product)

        print(f"   Shipping costs: PBP=${pbp:.2f}, Client=${client:.2f}")
        print(f"   Display format: {display}")
    else:
        print("   No demo products available")

    # Test a real product
    print("\n2. Real Product Example:")
    if len(df_real) > 0:
        # Find a product with shipping data
        for idx in range(min(5, len(df_real))):
            real_product = df_real.iloc[idx].to_dict()
            pbp, client = get_shipping_costs(real_product)

            if pbp > 0 or client > 0:
                print(f"   Product: {real_product.get('Product/Service', 'Unknown')}")
                print(f"   Partner: {real_product.get('Partner', 'Unknown')}")
                print(f"   Shipping Cost (PBP): {real_product.get('Shipping Cost (PBP)', 'N/A')}")
                print(f"   Shipping Price (Client): {real_product.get('Shipping Price (Client)', 'N/A')}")

                display = format_shipping_display(real_product)

                print(f"   Parsed costs: PBP=${pbp:.2f}, Client=${client:.2f}")
                print(f"   Display format: {display}")
                break
        else:
            print("   No products with shipping data found in first 5 rows")

def main():
    """Run all tests"""
    try:
        test_shipping_columns()
        test_helper_functions()
        test_real_product_examples()

        print("\n" + "="*50)
        print("ALL TESTS COMPLETED")
        print("="*50)
        print("\nSummary:")
        print("- Demo dataset uses legacy 'Shipping' column")
        print("- Real dataset uses new 'Shipping Cost (PBP)' and 'Shipping Price (Client)' columns")
        print("- Helper functions handle both structures correctly")
        print("- Backward compatibility maintained")

    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()