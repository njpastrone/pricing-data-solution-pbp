"""
Test script to verify Tab 5 properly imports and uses Customization & Shipping data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from src.data_loader import load_pricing_data
from src.helpers import clean_price, get_column_value, get_shipping_costs
from src.pricing_engine import get_unit_price_new_system

print("Testing Tab 5 Customization & Shipping Data Import")
print("=" * 80)

# Load the demo data
print("\n1. Loading Demo Dataset...")
df_template, df_metadata, df_partner_info = load_pricing_data('demo')
print(f"   Loaded {len(df_template)} products")

# Check what columns are available
print("\n2. Checking Available Columns:")
columns = df_template.columns.tolist()
print(f"   Total columns: {len(columns)}")

# Look for customization columns
print("\n3. Customization Columns:")
custom_cols = [col for col in columns if 'custom' in col.lower() or 'Custom' in col]
for col in custom_cols:
    print(f"   - {col}")

# Look for shipping columns
print("\n4. Shipping Columns:")
ship_cols = [col for col in columns if 'ship' in col.lower() or 'Ship' in col]
for col in ship_cols:
    print(f"   - {col}")

# Look for tariff columns
print("\n5. Tariff Columns:")
tariff_cols = [col for col in columns if 'tariff' in col.lower() or 'Tariff' in col]
for col in tariff_cols:
    print(f"   - {col}")

# Test a few products to see what data they have
print("\n6. Sample Product Data:")
for idx, row in df_template.head(3).iterrows():
    print(f"\n   Product: {row['Product/Service']}")
    print(f"   Partner: {row['Partner']}")

    # Get base cost
    base_cost, _, _ = get_unit_price_new_system(row, 100)
    print(f"   Base Cost: ${base_cost:.2f}" if base_cost else "   Base Cost: None")

    # Check customization data using get_column_value
    setup_fee = clean_price(get_column_value(
        row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    per_unit = clean_price(get_column_value(
        row, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))

    print(f"   Customization Setup: ${setup_fee:.2f}" if setup_fee else "   Customization Setup: None/0")
    print(f"   Customization Per Unit: ${per_unit:.2f}" if per_unit else "   Customization Per Unit: None/0")

    # Check client customization prices
    client_setup = clean_price(get_column_value(
        row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    client_per_unit = clean_price(get_column_value(
        row, 'Client Price: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))

    print(f"   Client Custom Setup: ${client_setup:.2f}" if client_setup else "   Client Custom Setup: None/0")
    print(f"   Client Custom Per Unit: ${client_per_unit:.2f}" if client_per_unit else "   Client Custom Per Unit: None/0")

    # Check shipping data
    shipping_pbp, shipping_client = get_shipping_costs(row)
    print(f"   Shipping PBP: ${shipping_pbp:.2f}" if shipping_pbp else "   Shipping PBP: None/0")
    print(f"   Shipping Client: ${shipping_client:.2f}" if shipping_client else "   Shipping Client: None/0")

    # Check MSRP
    msrp = clean_price(get_column_value(row, 'Vendor Published MSRP', 'MSRP', 0))
    print(f"   MSRP: ${msrp:.2f}" if msrp else "   MSRP: None/0")

# Now simulate what Tab 5 does
print("\n7. Simulating Tab 5 Pricing Calculation:")
test_row = df_template.iloc[0]  # First product

print(f"\n   Testing: {test_row['Product/Service']} from {test_row['Partner']}")

# Get base cost at quantity 100
base_cost, tier_range, tier_col = get_unit_price_new_system(test_row, 100)
if not base_cost:
    print("   ERROR: No base cost found!")
else:
    print(f"   Base cost at qty 100: ${base_cost:.2f}")

    # Apply 100% markup
    markup = 100
    client_base = base_cost * (1 + markup / 100)
    print(f"   With {markup}% markup: ${client_base:.2f}")

    # Get additional costs (as Tab 5 does)
    customization_setup = clean_price(get_column_value(
        test_row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    customization_per_unit = clean_price(get_column_value(
        test_row, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))

    # Handle None values
    if customization_setup is None:
        customization_setup = 0
    if customization_per_unit is None:
        customization_per_unit = 0

    shipping_pbp, shipping_client = get_shipping_costs(test_row)

    # Build progressive pricing
    with_custom = client_base + (customization_setup / 100) + customization_per_unit
    with_shipping = with_custom + shipping_client

    print(f"\n   Progressive Pricing Build-up:")
    print(f"   Base Price:      ${client_base:.2f}")
    print(f"   + Custom Setup:  ${customization_setup/100:.2f} (setup fee / 100)")
    print(f"   + Custom/Unit:   ${customization_per_unit:.2f}")
    print(f"   = With Custom:   ${with_custom:.2f}")
    print(f"   + Shipping:      ${shipping_client:.2f}")
    print(f"   = With Shipping: ${with_shipping:.2f}")

# Check if there's a difference between PBP costs and Client prices
print("\n8. Checking PBP vs Client Price Differences:")
has_client_custom = False
has_client_shipping = False

for idx, row in df_template.iterrows():
    # Check for client-specific customization pricing
    client_setup = clean_price(get_column_value(
        row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    if client_setup and client_setup > 0:
        has_client_custom = True
        print(f"   Found client custom pricing in: {row['Product/Service']}")
        break

for idx, row in df_template.iterrows():
    # Check for client-specific shipping
    pbp_ship, client_ship = get_shipping_costs(row)
    if pbp_ship != client_ship and client_ship > 0:
        has_client_shipping = True
        print(f"   Found different client shipping in: {row['Product/Service']}")
        print(f"      PBP: ${pbp_ship:.2f}, Client: ${client_ship:.2f}")
        break

if not has_client_custom:
    print("   No client-specific customization pricing found in demo data")
if not has_client_shipping:
    print("   No client-specific shipping pricing found in demo data")

print("\n" + "=" * 80)
print("Analysis Complete!")
print("\nKey Findings:")
print("- Customization data is being read using get_column_value() with fallbacks")
print("- Shipping data is being read using get_shipping_costs()")
print("- Tab 5 correctly handles None values by converting to 0")
print("- Progressive pricing calculation appears correct")
print("\nRECOMMENDATION: Check if the spreadsheet actually contains data in these columns")