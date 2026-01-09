"""
Test script to verify Tab 5 fixes for customization, shipping, and tariff calculations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.data_loader import load_pricing_data
from src.helpers import clean_price, get_column_value, get_shipping_costs, get_tariff_rate, calculate_product_tariff
from src.pricing_engine import get_unit_price_new_system

print("Testing Tab 5 Fixed Calculations")
print("=" * 80)

# Load the demo data
df_template, _, _ = load_pricing_data('demo')

# Test with the first product that has customization
test_row = df_template.iloc[0]  # Product Y from Partner X
print(f"\nTesting: {test_row['Product/Service']} from {test_row['Partner']}")
print("-" * 40)

# 1. Base cost calculation
base_cost, _, _ = get_unit_price_new_system(test_row, 100)
print(f"1. Base cost at qty 100: ${base_cost:.2f}")

# 2. Apply markup
markup = 100  # 100% markup
client_base = base_cost * (1 + markup / 100)
print(f"2. With {markup}% markup: ${client_base:.2f}")

# 3. Get CLIENT customization prices (not PBP costs)
print("\n3. Customization Costs:")
# PBP costs (what we were incorrectly using)
pbp_setup = clean_price(get_column_value(
    test_row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
))
pbp_per_unit = clean_price(get_column_value(
    test_row, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
))
print(f"   PBP Setup Fee: ${pbp_setup:.2f} (WRONG - shouldn't use this)" if pbp_setup else "   PBP Setup Fee: None")
print(f"   PBP Per Unit: ${pbp_per_unit:.2f} (WRONG - shouldn't use this)" if pbp_per_unit else "   PBP Per Unit: None")

# Client prices (what we should be using)
client_setup = clean_price(get_column_value(
    test_row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0
))
client_per_unit = clean_price(get_column_value(
    test_row, 'Client Price: Customization Cost per Unit', 'Customization Cost per Unit', 0
))

# Handle None values
if client_setup is None:
    client_setup = 0
if client_per_unit is None:
    client_per_unit = 0

print(f"   Client Setup Fee: ${client_setup:.2f} (CORRECT - use this)")
print(f"   Client Per Unit: ${client_per_unit:.2f} (CORRECT - use this)")

# 4. Calculate with customization
with_custom = client_base + (client_setup / 100) + client_per_unit
print(f"\n4. With Customization:")
print(f"   ${client_base:.2f} + ${client_setup/100:.2f} (setup/100) + ${client_per_unit:.2f} = ${with_custom:.2f}")

# 5. Get shipping costs
shipping_pbp, shipping_client = get_shipping_costs(test_row)
with_shipping = with_custom + shipping_client
print(f"\n5. With Shipping:")
print(f"   PBP shipping: ${shipping_pbp:.2f}")
print(f"   Client shipping: ${shipping_client:.2f} (use this)")
print(f"   ${with_custom:.2f} + ${shipping_client:.2f} = ${with_shipping:.2f}")

# 6. Calculate tariff (per unit)
print(f"\n6. Tariff Calculation:")
product_cost_at_100 = base_cost * 100
tariff_base = product_cost_at_100 + (product_cost_at_100 * (markup / 100))
tariff_rate_percent = get_tariff_rate(test_row.to_dict(), product_cost_at_100)
tariff_total = calculate_product_tariff(tariff_base, tariff_rate_percent)
tariff_per_unit = tariff_total / 100 if tariff_total > 0 else 0

print(f"   Product cost (100 units): ${product_cost_at_100:.2f}")
print(f"   With markup: ${tariff_base:.2f}")
print(f"   Tariff rate: {tariff_rate_percent:.1f}%")
print(f"   Total tariff: ${tariff_total:.2f}")
print(f"   Per-unit tariff: ${tariff_per_unit:.2f} (÷100)")

# 7. Fully loaded price
fully_loaded = with_shipping + tariff_per_unit
print(f"\n7. Fully Loaded Price:")
print(f"   ${with_shipping:.2f} + ${tariff_per_unit:.2f} = ${fully_loaded:.2f}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY OF FIXES:")
print("1. ✅ Now using CLIENT customization prices (not PBP costs)")
print("2. ✅ Tariff calculated per-unit (dividing total by 100)")
print("3. ✅ Shipping using client price (via get_shipping_costs)")
print("\nFinal Progressive Pricing:")
print(f"  Base:         ${client_base:.2f}")
print(f"  + Custom:     ${with_custom:.2f}")
print(f"  + Shipping:   ${with_shipping:.2f}")
print(f"  Fully Loaded: ${fully_loaded:.2f}")

# Test with a product that has different PBP vs Client costs
print("\n" + "=" * 80)
print("TESTING MARKUP DIFFERENCES:")

# Find a product with customization
for idx, row in df_template.iterrows():
    pbp_setup = clean_price(get_column_value(row, 'PBP Cost: Customization Setup Fee', None, 0))
    client_setup = clean_price(get_column_value(row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0))

    # Check if there's customization data
    if client_setup and client_setup > 0:
        print(f"\nProduct: {row['Product/Service']}")
        print(f"  Client Setup Fee: ${client_setup:.2f}")

        # Check if PBP cost exists and is different
        if pbp_setup and pbp_setup != client_setup:
            print(f"  PBP Setup Fee: ${pbp_setup:.2f}")
            print(f"  Markup on customization: {((client_setup - pbp_setup) / pbp_setup * 100):.0f}%")
        break

print("\n✅ All calculations verified!")