"""
Test script to verify Units Per Package normalization works correctly.
Tests Homeless Garden Project products (6-pack cost normalization).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.data_loader import load_pricing_data
from src.pricing_engine import get_unit_price_new_system
from src.helpers import clean_price

st.set_page_config(page_title="Test Units Per Package", layout="wide")
st.title("Units Per Package Normalization Test")

# Load demo dataset
df, df_meta, df_partner = load_pricing_data('demo')

# Filter for Homeless Garden Project products
hgp_products = df[df['Partner'] == 'Homeless Garden Project']

st.header(f"Found {len(hgp_products)} Homeless Garden Project products")

if not hgp_products.empty:
    for idx, product in hgp_products.iterrows():
        st.subheader(product['Product/Service'])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("6-Pack Cost (from sheet)",
                     clean_price(product.get('PBP Cost (No Tiers)', '')) or "N/A")

        with col2:
            st.metric("Units Per Package",
                     product.get('Units Per Package', 1))

        with col3:
            st.metric("MSRP (per unit)",
                     clean_price(product.get('MSRP', '')) or "N/A")

        # Calculate normalized per-unit cost
        unit_price, tier_range, price_col = get_unit_price_new_system(product, 100)

        with col4:
            st.metric("Normalized Per-Unit Cost",
                     f"${unit_price:.2f}" if unit_price else "N/A")

        # Test MSRP markup calculation
        if unit_price:
            msrp = clean_price(product.get('MSRP', ''))
            if msrp and msrp > 0 and unit_price > 0:
                required_markup = ((msrp / unit_price) - 1) * 100

                st.write(f"**MSRP Markup Calculation:**")
                st.write(f"- Formula: ((MSRP / Cost) - 1) × 100")
                st.write(f"- Calculation: (({msrp} / {unit_price:.2f}) - 1) × 100 = **{required_markup:.1f}%**")

                if required_markup >= 0 and required_markup <= 200:
                    st.success(f"✅ Realistic markup: {required_markup:.1f}%")
                else:
                    st.error(f"❌ Unrealistic markup: {required_markup:.1f}%")
            else:
                st.warning("No MSRP available for markup calculation")

        st.divider()

else:
    st.warning("No Homeless Garden Project products found in dataset")

# Test a non-HGP product for comparison
st.header("Test Non-HGP Product (Should Have Units Per Package = 1)")
non_hgp = df[df['Partner'] != 'Homeless Garden Project'].iloc[0]

st.subheader(non_hgp['Product/Service'])
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Original Cost", clean_price(non_hgp.get('PBP Cost (No Tiers)', '')) or "N/A")

with col2:
    st.metric("Units Per Package", non_hgp.get('Units Per Package', 1))

with col3:
    unit_price, _, _ = get_unit_price_new_system(non_hgp, 100)
    st.metric("Per-Unit Cost (should match Original)", f"${unit_price:.2f}" if unit_price else "N/A")

st.success("If Units Per Package = 1, Original Cost should equal Per-Unit Cost (no change)")
