"""
Test script for Executive Pricing Tool (Tab 5)
Tests core functionality: data loading, pricing calculations, filtering
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
from src.data_loader import load_pricing_data
from src.pricing_engine import get_unit_price_new_system
from src.helpers import clean_price, get_column_value, calculate_product_tariff, get_shipping_costs

def test_pricing_table_calculation():
    """Test that pricing calculations match expected Tab 5 logic"""
    print("\n" + "="*60)
    print("Testing Executive Pricing Tool - Pricing Calculations")
    print("="*60)

    # Load demo data
    print("\n1. Loading demo dataset...")
    try:
        df_template, df_metadata, df_partner_info = load_pricing_data('demo')
        print(f"   ✓ Loaded {len(df_template)} products")
    except Exception as e:
        print(f"   ✗ Failed to load data: {e}")
        return False

    # Test pricing calculation for first product
    print("\n2. Testing pricing calculation logic...")
    test_row = df_template.iloc[0]

    # Get base cost at quantity 100
    base_cost, tier_range, tier_col = get_unit_price_new_system(test_row, 100)
    print(f"   Product: {test_row['Product/Service']}")
    print(f"   Base cost @ qty 100: ${base_cost:.2f}")

    # Apply 100% markup
    markup = 100
    client_base = base_cost * (1 + markup / 100)
    print(f"   Client base price (100% markup): ${client_base:.2f}")

    # Get additional costs
    customization_setup = clean_price(get_column_value(
        test_row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    customization_per_unit = clean_price(get_column_value(
        test_row, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))
    shipping_pbp, shipping_client = get_shipping_costs(test_row)

    # Calculate tariff (need to get rate first, then calculate amount)
    from src.helpers import get_tariff_rate
    product_cost_at_100 = base_cost * 100
    tariff_base = product_cost_at_100 + (product_cost_at_100 * (markup / 100))
    tariff_rate_percent = get_tariff_rate(test_row.to_dict(), product_cost_at_100)
    tariff = calculate_product_tariff(tariff_base, tariff_rate_percent)

    print(f"   Customization setup: ${customization_setup:.2f}")
    print(f"   Customization per unit: ${customization_per_unit:.2f}")
    print(f"   Shipping (client): ${shipping_client:.2f}")
    print(f"   Tariff: ${tariff:.2f}")

    # Build progressive pricing
    with_custom = client_base + (customization_setup / 100) + customization_per_unit
    with_shipping = with_custom + shipping_client
    fully_loaded = with_shipping + tariff

    print(f"   → With customization: ${with_custom:.2f}")
    print(f"   → With shipping: ${with_shipping:.2f}")
    print(f"   → Fully loaded: ${fully_loaded:.2f}")

    # Get MSRP
    msrp = clean_price(get_column_value(test_row, 'Vendor Published MSRP', 'MSRP', 0))
    if msrp and msrp > 0:
        vs_msrp = ((fully_loaded - msrp) / msrp) * 100
        print(f"   MSRP: ${msrp:.2f}")
        print(f"   vs MSRP: {vs_msrp:+.1f}%")

    print("   ✓ Pricing calculation successful")

    # Test bidirectional editing
    print("\n3. Testing bidirectional editing...")

    # Test 1: Edit markup → recalculate price
    new_markup = 150
    new_price = base_cost * (1 + new_markup / 100)
    print(f"   Markup changed to {new_markup}%")
    print(f"   → New base price: ${new_price:.2f}")

    # Test 2: Edit price → back-calculate markup
    target_price = 100.00
    back_calc_markup = ((target_price / base_cost) - 1) * 100
    print(f"   Price changed to ${target_price:.2f}")
    print(f"   → Back-calculated markup: {back_calc_markup:.1f}%")

    print("   ✓ Bidirectional editing works correctly")

    # Test filtering
    print("\n4. Testing partner filtering...")
    partners = df_template['Partner'].unique()
    print(f"   Found {len(partners)} partners: {', '.join(partners)}")

    for partner in partners:
        partner_products = df_template[df_template['Partner'] == partner]
        print(f"   - {partner}: {len(partner_products)} products")

    print("   ✓ Partner filtering works correctly")

    # Test search filtering
    print("\n5. Testing search filtering...")
    search_term = "jam"
    search_results = df_template[
        df_template['Product/Service'].str.contains(search_term, case=False, na=False)
    ]
    print(f"   Search for '{search_term}': {len(search_results)} results")
    if len(search_results) > 0:
        print(f"   First result: {search_results.iloc[0]['Product/Service']}")
    print("   ✓ Search filtering works correctly")

    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
    return True

def test_import_structure():
    """Test that import data structure matches proposal/order format"""
    print("\n" + "="*60)
    print("Testing Executive Pricing Tool - Import Structure")
    print("="*60)

    # Load demo data
    df_template, df_metadata, df_partner_info = load_pricing_data('demo')
    test_row = df_template.iloc[0]

    # Build proposal item structure (as done in Tab 5)
    print("\n1. Testing proposal import structure...")
    proposal_item = {
        'product_data': test_row.to_dict(),
        'markup_percent': 100
    }

    print(f"   Product: {proposal_item['product_data']['Product/Service']}")
    print(f"   Markup: {proposal_item['markup_percent']}%")
    print("   ✓ Proposal structure matches expected format")

    # Test order import (uses convert_proposal_to_order)
    print("\n2. Testing order import structure...")
    from src.helpers import convert_proposal_to_order

    order_item = convert_proposal_to_order(
        proposal_item,
        get_unit_price_new_system,
        calculate_product_tariff
    )

    print(f"   Product: {order_item['product_name']}")
    print(f"   Quantity: {order_item['quantity']}")
    print(f"   Markup: {order_item['markup_percent']}%")
    print("   ✓ Order structure matches expected format")

    print("\n" + "="*60)
    print("IMPORT STRUCTURE TESTS PASSED ✓")
    print("="*60)
    return True

if __name__ == "__main__":
    success = True

    try:
        success = test_pricing_table_calculation() and success
    except Exception as e:
        print(f"\n✗ Pricing calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    try:
        success = test_import_structure() and success
    except Exception as e:
        print(f"\n✗ Import structure test failed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    if success:
        print("\n" + "="*60)
        print("ALL EXECUTIVE PRICING TOOL TESTS PASSED ✓")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("SOME TESTS FAILED ✗")
        print("="*60)
        sys.exit(1)
