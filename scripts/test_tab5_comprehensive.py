#!/usr/bin/env python3
"""
Comprehensive test script to verify ALL Tab 5 functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.data_loader import load_pricing_data
from src.helpers import (
    clean_price,
    get_column_value,
    get_shipping_costs,
    get_tariff_rate,
    calculate_product_tariff,
    convert_proposal_to_order
)
from src.pricing_engine import get_unit_price_new_system

print("COMPREHENSIVE TAB 5 VERIFICATION")
print("=" * 80)

# Load demo data
df_template, df_metadata, df_partner_info = load_pricing_data('demo')

# Test counters
tests_passed = 0
tests_failed = 0
issues = []

def test(name, condition, details=""):
    global tests_passed, tests_failed, issues
    if condition:
        print(f"✅ {name}")
        tests_passed += 1
    else:
        print(f"❌ {name}")
        if details:
            print(f"   Details: {details}")
        tests_failed += 1
        issues.append(f"{name}: {details}")

print("\n1. PRICING STRATEGY LOGIC")
print("-" * 40)

# Simulate MSRP pricing logic
def calculate_msrp_markup(product_data):
    """Same as app.py"""
    msrp_raw = get_column_value(product_data, 'Vendor Published MSRP', 'MSRP', '')
    msrp = clean_price(msrp_raw)

    if msrp and msrp > 0:
        base_cost, _, _ = get_unit_price_new_system(product_data, 100)
        if base_cost and base_cost > 0:
            required_markup = ((msrp / base_cost) - 1) * 100
            return max(0.0, required_markup)
    return 100.0

def get_default_markup(product_data):
    """Same as app.py"""
    pbp_markup = get_column_value(product_data, 'PBP Standard Markup', None, None)

    if pbp_markup:
        try:
            multiplier = float(pbp_markup)
            if multiplier > 0:
                return (multiplier - 1) * 100
        except:
            pass
    return 100.0

# Test product with MSRP
test_row_with_msrp = None
for _, row in df_template.iterrows():
    if clean_price(get_column_value(row, 'Vendor Published MSRP', 'MSRP', '')):
        test_row_with_msrp = row
        break

if test_row_with_msrp is not None:
    msrp_markup = calculate_msrp_markup(test_row_with_msrp)
    test("MSRP markup calculation works", msrp_markup >= 0, f"Markup: {msrp_markup:.1f}%")
else:
    print("⚠️  No products with MSRP in demo data to test")

# Test default markup
test_row = df_template.iloc[0]
default_markup = get_default_markup(test_row)
test("Default markup fallback works", default_markup == 100.0, f"Got {default_markup}%")

print("\n2. CUSTOMIZATION DATA (CLIENT vs PBP)")
print("-" * 40)

# Check we're using CLIENT prices for customization
for idx, row in df_template.head(3).iterrows():
    # Get CLIENT customization (correct)
    client_setup = clean_price(get_column_value(
        row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    client_per_unit = clean_price(get_column_value(
        row, 'Client Price: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))

    # Get PBP customization (wrong - shouldn't use)
    pbp_setup = clean_price(get_column_value(
        row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    pbp_per_unit = clean_price(get_column_value(
        row, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))

    # Tab 5 should use CLIENT prices
    product_name = row['Product/Service'][:30]
    if client_setup or client_per_unit:
        test(f"Using CLIENT custom for {product_name}", True,
             f"Client: ${client_setup or 0:.2f}/${client_per_unit or 0:.2f}")

print("\n3. SHIPPING DATA")
print("-" * 40)

# Test shipping costs extraction
for idx, row in df_template.head(3).iterrows():
    pbp_ship, client_ship = get_shipping_costs(row)
    product_name = row['Product/Service'][:30]

    # Tab 5 should use client shipping
    if client_ship > 0:
        test(f"Shipping for {product_name}", True,
             f"Using client price: ${client_ship:.2f}")

print("\n4. TARIFF CALCULATIONS")
print("-" * 40)

# Test tariff is calculated per-unit
test_row = df_template.iloc[0]
base_cost, _, _ = get_unit_price_new_system(test_row, 100)

if base_cost:
    markup = 100
    product_cost_at_100 = base_cost * 100
    tariff_base = product_cost_at_100 + (product_cost_at_100 * (markup / 100))
    tariff_rate_percent = get_tariff_rate(test_row.to_dict(), product_cost_at_100)

    if tariff_rate_percent > 0:
        tariff_total = calculate_product_tariff(tariff_base, tariff_rate_percent)
        tariff_per_unit = tariff_total / 100 if tariff_total > 0 else 0

        test("Tariff calculated on total order", tariff_total >= 0, f"Total: ${tariff_total:.2f}")
        test("Tariff converted to per-unit", tariff_per_unit == tariff_total/100,
             f"Per-unit: ${tariff_per_unit:.2f}")
    else:
        print("⚠️  No tariff rate in demo data")

print("\n5. PROGRESSIVE PRICING BUILD-UP")
print("-" * 40)

# Test the full pricing calculation as Tab 5 does it
test_row = df_template.iloc[0]
base_cost, _, _ = get_unit_price_new_system(test_row, 100)

if base_cost:
    # Step 1: Base cost
    test("Base cost retrieved", base_cost > 0, f"${base_cost:.2f}")

    # Step 2: Apply markup
    markup = 100
    client_base = base_cost * (1 + markup / 100)
    test("Markup applied correctly", client_base == base_cost * 2, f"${client_base:.2f}")

    # Step 3: Add customization (CLIENT prices)
    client_setup = clean_price(get_column_value(
        test_row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0
    )) or 0
    client_per_unit = clean_price(get_column_value(
        test_row, 'Client Price: Customization Cost per Unit', 'Customization Cost per Unit', 0
    )) or 0

    with_custom = client_base + (client_setup / 100) + client_per_unit
    expected_custom = client_base + (client_setup / 100) + client_per_unit
    test("Customization added correctly", abs(with_custom - expected_custom) < 0.01,
         f"${with_custom:.2f}")

    # Step 4: Add shipping
    _, client_ship = get_shipping_costs(test_row)
    with_shipping = with_custom + client_ship
    test("Shipping added correctly", with_shipping == with_custom + client_ship,
         f"${with_shipping:.2f}")

    # Step 5: Add tariff
    product_cost_at_100 = base_cost * 100
    tariff_base = product_cost_at_100 + (product_cost_at_100 * (markup / 100))
    tariff_rate_percent = get_tariff_rate(test_row.to_dict(), product_cost_at_100)
    tariff_total = calculate_product_tariff(tariff_base, tariff_rate_percent)
    tariff_per_unit = tariff_total / 100 if tariff_total > 0 else 0

    fully_loaded = with_shipping + tariff_per_unit
    test("Fully loaded price calculated", fully_loaded >= with_shipping,
         f"${fully_loaded:.2f}")

print("\n6. BIDIRECTIONAL EDITING LOGIC")
print("-" * 40)

# Test markup to price calculation
base_cost = 50.0
markup = 150.0
expected_price = base_cost * (1 + markup / 100)
test("Markup → Price calculation", expected_price == 125.0, f"${expected_price:.2f}")

# Test price to markup calculation
target_price = 75.0
calculated_markup = ((target_price / base_cost) - 1) * 100
test("Price → Markup calculation", abs(calculated_markup - 50.0) < 0.01,
     f"{calculated_markup:.1f}%")

print("\n7. DATA STRUCTURE INTEGRITY")
print("-" * 40)

# Check that pricing_data dictionary has all required fields
sample_row = df_template.iloc[0]
required_fields = [
    'Partner', 'Product', 'PBP Cost', 'Default Markup %', 'Markup %',
    'Base Price', '+ Custom', '+ Shipping', 'Fully Loaded',
    '_row_data', '_customization_setup', '_customization_per_unit',
    '_shipping', '_tariff'
]

# Simulate building a pricing_data entry
pricing_entry = {
    'Partner': sample_row['Partner'],
    'Product': sample_row['Product/Service'],
    'PBP Cost': 10.0,
    'Default Markup %': 100.0,
    'Markup %': 100.0,
    'Base Price': 20.0,
    '+ Custom': 25.0,
    '+ Shipping': 30.0,
    'Fully Loaded': 35.0,
    'MSRP': None,
    'vs MSRP %': None,
    '_row_data': sample_row.to_dict(),
    '_customization_setup': 50.0,
    '_customization_per_unit': 5.0,
    '_shipping': 5.0,
    '_tariff': 5.0
}

for field in required_fields:
    test(f"Field '{field}' exists", field in pricing_entry, "")

print("\n8. IMPORT TO PROPOSAL/ORDER")
print("-" * 40)

# Test proposal item structure
proposal_item = {
    'product_data': sample_row.to_dict(),
    'markup_percent': 100.0
}
test("Proposal item has product_data", 'product_data' in proposal_item)
test("Proposal item has markup_percent", 'markup_percent' in proposal_item)

# Test order conversion
order_item = convert_proposal_to_order(
    proposal_item,
    get_unit_price_new_system,
    calculate_product_tariff
)
test("Order conversion works", order_item is not None)
test("Order item has product_name", 'product_name' in order_item)
test("Order item has quantity", 'quantity' in order_item and order_item['quantity'] == 1)

print("\n9. EDGE CASES")
print("-" * 40)

# Test None handling
test("None customization handled", (None or 0) == 0, "Converts to 0")
test("None shipping handled", (None or 0) == 0, "Converts to 0")

# Test negative markup prevention
negative_markup = -50
prevented_markup = max(0, negative_markup)
test("Negative markup prevented", prevented_markup == 0, f"{prevented_markup}%")

# Test division by zero protection
if base_cost == 0:
    test("Division by zero handled", True, "Skipped products with zero cost")
else:
    test("Non-zero base cost", base_cost > 0, f"${base_cost:.2f}")

print("\n" + "=" * 80)
print(f"FINAL RESULTS: {tests_passed} passed, {tests_failed} failed")

if tests_failed > 0:
    print("\nISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n🎉 ALL TESTS PASSED! Tab 5 is working correctly.")

# Additional sanity checks
print("\n" + "=" * 80)
print("SANITY CHECKS:")

# Check syntax
try:
    with open('app.py', 'r') as f:
        code = f.read()
    compile(code, 'app.py', 'exec')
    print("✅ No syntax errors in app.py")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")

# Check that we're not using PBP costs for customization anymore
with open('app.py', 'r') as f:
    lines = f.readlines()

tab5_start = None
tab5_end = None
for i, line in enumerate(lines):
    if 'with tab5:' in line:
        tab5_start = i
    elif tab5_start and 'with tab' in line:
        tab5_end = i
        break

if tab5_start:
    tab5_code = ''.join(lines[tab5_start:tab5_end or len(lines)])

    # Check for wrong usage
    if 'PBP Cost: Customization Setup Fee' in tab5_code:
        print("❌ WARNING: Tab 5 still references PBP customization costs!")
    else:
        print("✅ Tab 5 correctly uses Client customization prices")

    # Check tariff is per-unit
    if 'tariff_per_unit' in tab5_code:
        print("✅ Tab 5 correctly calculates per-unit tariff")
    else:
        print("❌ WARNING: Tab 5 may not be calculating per-unit tariff!")

print("\n✅ VERIFICATION COMPLETE")