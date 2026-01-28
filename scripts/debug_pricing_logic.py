"""
Debug script to check Pricing Logic column for Anchal products.
Run with: streamlit run scripts/debug_pricing_logic.py
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_pricing_data
from src.helpers import get_column_value, get_pricing_logic, get_other_addon_percent, get_shipping_addon_percent

st.title("Debug: Pricing Logic Column Check")

# Load data
st.write("Loading data from Google Sheets...")
df, df_metadata, df_partner_info = load_pricing_data(dataset='real')

st.write(f"Loaded {len(df)} products")

# Show all columns
st.subheader("All Column Names in Spreadsheet")
st.write(list(df.columns))

# Check if Pricing Logic column exists
st.subheader("Pricing Logic Column Check")
if 'Pricing Logic' in df.columns:
    st.success("'Pricing Logic' column EXISTS in spreadsheet")
else:
    st.error("'Pricing Logic' column NOT FOUND in spreadsheet")
    similar = [col for col in df.columns if 'pricing' in col.lower() or 'logic' in col.lower()]
    if similar:
        st.warning(f"Similar columns found: {similar}")

# Check if Other Add-On column exists
st.subheader("Other Add-On % Column Check")
if 'Other Add-On % (of Cost)' in df.columns:
    st.success("'Other Add-On % (of Cost)' column EXISTS in spreadsheet")
else:
    st.error("'Other Add-On % (of Cost)' column NOT FOUND in spreadsheet")
    similar = [col for col in df.columns if 'add-on' in col.lower() or 'addon' in col.lower()]
    if similar:
        st.warning(f"Similar columns found: {similar}")

# Filter for Anchal partner
st.subheader("Anchal Products")
anchal_products = df[df['Partner'].str.contains('Anchal', case=False, na=False)]
st.write(f"Found {len(anchal_products)} Anchal products")

if len(anchal_products) > 0:
    for idx, row in anchal_products.iterrows():
        product_name = row.get('Product/Service', 'Unknown')
        st.write(f"---")
        st.write(f"**Product:** {product_name}")

        # Check Pricing Logic using raw access
        raw_pricing_logic = row.get('Pricing Logic', 'COLUMN NOT FOUND')
        st.write(f"Raw 'Pricing Logic' value: `{raw_pricing_logic}` (type: {type(raw_pricing_logic).__name__})")

        # Check using helper function
        helper_pricing_logic = get_pricing_logic(row)
        st.write(f"get_pricing_logic() returns: `{helper_pricing_logic}`")

        # Check Other Add-On %
        raw_other_addon = row.get('Other Add-On % (of Cost)', 'COLUMN NOT FOUND')
        st.write(f"Raw 'Other Add-On % (of Cost)' value: `{raw_other_addon}` (type: {type(raw_other_addon).__name__})")

        helper_other_addon = get_other_addon_percent(row)
        st.write(f"get_other_addon_percent() returns: `{helper_other_addon}`")

        # Check Shipping Add-On %
        raw_shipping_addon = row.get('Shipping Add-On % (of Cost)', 'COLUMN NOT FOUND')
        st.write(f"Raw 'Shipping Add-On % (of Cost)' value: `{raw_shipping_addon}`")

        helper_shipping_addon = get_shipping_addon_percent(row)
        st.write(f"get_shipping_addon_percent() returns: `{helper_shipping_addon}`")

# Show the specific product: Cross stitch toiletry bag
st.subheader("Specific Product: Cross stitch toiletry bag")
toiletry_bag = df[df['Product/Service'].str.contains('Cross stitch toiletry bag', case=False, na=False)]
if len(toiletry_bag) > 0:
    for idx, row in toiletry_bag.iterrows():
        st.json({
            'Partner': row.get('Partner', ''),
            'Product/Service': row.get('Product/Service', ''),
            'Pricing Logic': str(row.get('Pricing Logic', 'NOT FOUND')),
            'Other Add-On % (of Cost)': str(row.get('Other Add-On % (of Cost)', 'NOT FOUND')),
            'Shipping Add-On % (of Cost)': str(row.get('Shipping Add-On % (of Cost)', 'NOT FOUND')),
            'Vendor Published MSRP': str(row.get('Vendor Published MSRP', 'NOT FOUND')),
            'PBP Cost (No Tiers/Tier 1)': str(row.get('PBP Cost (No Tiers/Tier 1)', 'NOT FOUND')),
        })
else:
    st.warning("Product 'Cross stitch toiletry bag' not found")

st.write("---")
st.write("If columns show 'NOT FOUND' or have empty/nan values, that's why it defaults to 'Standard markup'")
