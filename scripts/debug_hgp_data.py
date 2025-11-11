"""
Debug script to see what's actually in the Homeless Garden Project product data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.data_loader import load_pricing_data
from src.pricing_engine import get_unit_price_new_system
from src.helpers import clean_price

st.set_page_config(page_title="Debug HGP Data", layout="wide")
st.title("Homeless Garden Project Data Debugging")

# Load demo dataset
df, df_meta, df_partner = load_pricing_data('demo')

# Check if "Units Per Package" column exists
st.header("Column Check")
if 'Units Per Package' in df.columns:
    st.success("✅ 'Units Per Package' column EXISTS in DataFrame")
else:
    st.error("❌ 'Units Per Package' column DOES NOT EXIST in DataFrame")
    st.write("Available columns:", df.columns.tolist())

# Find HGP products
hgp = df[df['Partner'] == 'Homeless Garden Project']

if not hgp.empty:
    product = hgp.iloc[0]

    st.header(f"First HGP Product: {product['Product/Service']}")

    # Show raw data
    st.subheader("Raw Data from DataFrame")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cost_raw = product.get('PBP Cost (No Tiers)', 'NOT FOUND')
        st.metric("PBP Cost (No Tiers) [raw]", cost_raw)
        st.caption(f"Type: {type(cost_raw)}")

    with col2:
        units_raw = product.get('Units Per Package', 'NOT FOUND')
        st.metric("Units Per Package [raw]", units_raw)
        st.caption(f"Type: {type(units_raw)}")

    with col3:
        msrp_raw = product.get('MSRP', 'NOT FOUND')
        st.metric("MSRP [raw]", msrp_raw)
        st.caption(f"Type: {type(msrp_raw)}")

    with col4:
        tiers_raw = product.get('Pricing Tiers (Y/N)', 'NOT FOUND')
        st.metric("Pricing Tiers (Y/N)", tiers_raw)
        st.caption(f"Type: {type(tiers_raw)}")

    # Show cleaned data
    st.subheader("After clean_price()")
    col1, col2, col3 = st.columns(3)

    with col1:
        cost_clean = clean_price(product.get('PBP Cost (No Tiers)', ''))
        st.metric("PBP Cost (cleaned)", cost_clean)

    with col2:
        msrp_clean = clean_price(product.get('MSRP', ''))
        st.metric("MSRP (cleaned)", msrp_clean)

    with col3:
        units_value = product.get('Units Per Package', 1)
        st.metric("Units Per Package (get with default)", units_value)
        st.caption(f"Type: {type(units_value)}")

    # Test get_unit_price_new_system
    st.subheader("get_unit_price_new_system() Test")

    st.code(f"""
# Calling: get_unit_price_new_system(product, 100)
product_dict = product.to_dict()

# What get_unit_price_new_system sees:
has_tiers = '{product.get('Pricing Tiers (Y/N)', '')}'
cost_raw = '{product.get('PBP Cost (No Tiers)', '')}'
units_per_package = {product.get('Units Per Package', 1)}

# Expected calculation (if has_tiers != 'Y'):
cost_clean = clean_price('{product.get('PBP Cost (No Tiers)', '')}') = {clean_price(product.get('PBP Cost (No Tiers)', ''))}
units = {product.get('Units Per Package', 1)}
normalized_cost = {clean_price(product.get('PBP Cost (No Tiers)', ''))} / {product.get('Units Per Package', 1)} = {clean_price(product.get('PBP Cost (No Tiers)', '')) / product.get('Units Per Package', 1) if clean_price(product.get('PBP Cost (No Tiers)', '')) and product.get('Units Per Package', 1) else 'ERROR'}
    """)

    unit_price, tier_range, price_col = get_unit_price_new_system(product, 100)

    st.metric("ACTUAL Result from get_unit_price_new_system()", unit_price)

    if unit_price:
        expected = clean_price(product.get('PBP Cost (No Tiers)', '')) / product.get('Units Per Package', 1)
        if abs(unit_price - expected) < 0.01:
            st.success(f"✅ Correct! {unit_price} matches expected {expected:.2f}")
        else:
            st.error(f"❌ Wrong! Got {unit_price}, expected {expected:.2f}")

    # Test MSRP markup
    st.subheader("MSRP Markup Calculation")
    if msrp_clean and unit_price:
        markup = ((msrp_clean / unit_price) - 1) * 100
        st.metric("Calculated Markup %", f"{markup:.1f}%")

        if markup >= 0 and markup <= 200:
            st.success("✅ Realistic markup percentage")
        else:
            st.error("❌ Unrealistic markup percentage")

    # Show full product dict
    with st.expander("Full Product Dictionary"):
        st.json(product.to_dict())
else:
    st.error("No Homeless Garden Project products found")
