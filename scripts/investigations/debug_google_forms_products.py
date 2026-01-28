"""
Debug Google Forms Product Selection Issue

Investigating why products from proposals don't show up in Google Form generation.
User reports: quantities show up, but not product names.

This script will:
1. Load data
2. Simulate creating a proposal item
3. Show the structure of proposal_products
4. Extract product name the same way Tab 2 does
5. Identify the issue
"""

import sys
sys.path.append('.')

from src.data_loader import load_pricing_data, connect_to_sheets

print("="*60)
print("Google Forms Product Debug Script")
print("="*60)

# Load demo data
print("\n1. Loading demo dataset...")
df_template, df_metadata, df_partner_info = load_pricing_data('demo')
print(f"   Loaded {len(df_template)} products")

# Get first product as example
print("\n2. Getting first product from catalog...")
product_row = df_template.iloc[0]
print(f"   Product: {product_row.get('Product/Service', 'NOT FOUND')}")

# Show what keys are actually in the product_row
print("\n3. Checking column names in product data:")
print(f"   Available columns ({len(product_row.index)} total):")
for col in list(product_row.index)[:10]:  # Show first 10
    print(f"      - {col}")
if len(product_row.index) > 10:
    print(f"      ... and {len(product_row.index) - 10} more")

# Check if 'Product/Service' column exists
if 'Product/Service' in product_row.index:
    print(f"\n   ✅ 'Product/Service' column EXISTS")
    print(f"   Value: '{product_row['Product/Service']}'")
else:
    print(f"\n   ❌ 'Product/Service' column NOT FOUND")
    # Check for similar column names
    similar = [col for col in product_row.index if 'product' in col.lower() or 'service' in col.lower()]
    if similar:
        print(f"   Similar columns found:")
        for col in similar:
            print(f"      - {col}: '{product_row[col]}'")

# Simulate how proposal_products stores data
print("\n4. Simulating proposal item structure (how Tab 1 stores products)...")
proposal_item = {
    'product_data': product_row.to_dict(),  # Convert Series to dict
    'markup_percent': 100.0,
    'pricing_snapshot': {
        'quantity': 100,
        'pbp_cost': 5.0,
        'client_price': 10.0,
    }
}

print(f"   Proposal item keys: {list(proposal_item.keys())}")
print(f"   product_data type: {type(proposal_item['product_data'])}")
print(f"   product_data keys (first 10): {list(proposal_item['product_data'].keys())[:10]}")

# Extract product name THE SAME WAY Tab 2 does (line 4072 in app.py)
print("\n5. Extracting product name (same as app.py line 4072)...")
product_name = proposal_item['product_data'].get('Product/Service', '')
quantity = proposal_item.get('pricing_snapshot', {}).get('quantity', 100)

print(f"   product_name: '{product_name}'")
print(f"   quantity: {quantity}")

if product_name:
    print(f"\n   ✅ SUCCESS: Product name extracted correctly")
else:
    print(f"\n   ❌ PROBLEM: Product name is empty!")
    print(f"   Let's check what's in product_data...")

    # Show all keys containing 'product' or 'service'
    relevant_keys = [k for k in proposal_item['product_data'].keys()
                    if 'product' in k.lower() or 'service' in k.lower()]
    print(f"   Keys with 'product' or 'service': {relevant_keys}")

    for key in relevant_keys:
        print(f"      {key}: '{proposal_item['product_data'][key]}'")

# Test what would be passed to generate_prefilled_form_url
print("\n6. Simulating selected_products list (what gets passed to generate_prefilled_form_url)...")
selected_products = []
# This is exactly what happens in app.py lines 4093-4098
selected_products.append({
    'name': product_name,
    'quantity': quantity,
    'customization_notes': ''
})

print(f"   selected_products: {selected_products}")

if selected_products[0]['name']:
    print(f"\n   ✅ Product name would be included in form URL")
else:
    print(f"\n   ❌ Product name is EMPTY - this is the problem!")

# Show what the URL parameter would look like
from src.forms_config import ALL_ENTRY_IDS
import urllib.parse

print("\n7. Testing URL generation (first product only)...")
product = selected_products[0]
if product.get('name'):
    name_key = 'line_1_name'
    url_param = f"{ALL_ENTRY_IDS[name_key]}={urllib.parse.quote(product['name'])}"
    print(f"   URL parameter: {url_param}")
    print(f"   ✅ Would appear in pre-filled URL")
else:
    print(f"   ❌ Product name is empty - NO URL parameter would be generated")
    print(f"   This explains why quantities show but products don't!")

print("\n" + "="*60)
print("Debug complete")
print("="*60)
