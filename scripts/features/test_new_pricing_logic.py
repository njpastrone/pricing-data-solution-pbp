"""
Test new pricing logic with 3 pricing methods.
Part of January 2026 schema transition testing.

Usage:
    streamlit run scripts/features/test_new_pricing_logic.py
"""

import streamlit as st
from src.data_loader import load_pricing_data
from src.pricing_engine import calculate_pbp_msrp, calculate_vendor_markup, calculate_pbp_markup
from src.helpers import normalize_cost_to_per_item, get_pricing_logic

st.title("Test New Pricing Logic (Jan 2026)")
st.caption("Testing 3 pricing methods: MSRP + % of cost, MSRP capped, Standard markup")

# Dataset selector
dataset = st.sidebar.radio("Select Dataset", ["demo", "real"], index=0)

# Load data
try:
    df_template, df_metadata, df_partner_info = load_pricing_data(dataset)
    st.success(f"✅ Loaded {len(df_template)} products from {dataset} dataset")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Test quantity selector
test_quantity = st.sidebar.number_input("Test Quantity", min_value=1, max_value=1000, value=100, step=10)

st.divider()

# Test each product
for idx, row in df_template.iterrows():
    product_name = row.get('Product/Service', 'Unknown')
    pricing_logic = get_pricing_logic(row)

    with st.expander(f"**{product_name}**", expanded=False):
        st.write(f"**Pricing Logic:** {pricing_logic}")

        # Calculate price at test quantity
        try:
            result = calculate_pbp_msrp(row, quantity=test_quantity)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Calculated PBP MSRP", f"${result['pbp_msrp']:.2f}")
                st.write(f"**Method Used:** {result['method_used']}")

            with col2:
                if result['spreadsheet_msrp']:
                    st.metric("Spreadsheet MSRP", f"${result['spreadsheet_msrp']:.2f}")

                    if result['validation_status'] == 'match':
                        st.success("✓ Validation: Match")
                    elif result['validation_status'] == 'mismatch':
                        diff = abs(result['pbp_msrp'] - result['spreadsheet_msrp'])
                        st.error(f"⚠️ Validation: Mismatch (${diff:.2f} difference)")
                else:
                    st.info("No spreadsheet MSRP for comparison")

            # Calculation details
            st.write("**Calculation Details:**")
            details = result['calculation_details']
            st.json(details)

            # Diagnostic markups
            if 'per_item_cost' in details:
                per_item_cost = details['per_item_cost']

                st.write("**Diagnostic Markups:**")

                # Vendor markup
                vendor_markup_result = calculate_vendor_markup(row, per_item_cost)
                if vendor_markup_result['vendor_markup_pct'] is not None:
                    vendor_pct = vendor_markup_result['vendor_markup_pct']
                    st.write(f"- Vendor Markup: {vendor_pct:.2f}%")
                    if vendor_markup_result['spreadsheet_value']:
                        spreadsheet_pct = vendor_markup_result['spreadsheet_value']
                        if vendor_markup_result['validation_status'] == 'match':
                            st.write(f"  - Spreadsheet: {spreadsheet_pct:.2f}% ✓")
                        else:
                            st.write(f"  - Spreadsheet: {spreadsheet_pct:.2f}% ⚠️ Mismatch")

                # PBP markup
                pbp_markup_result = calculate_pbp_markup(result['pbp_msrp'], per_item_cost, row)
                pbp_pct = pbp_markup_result['pbp_markup_pct']
                st.write(f"- PBP Markup: {pbp_pct:.2f}%")
                if pbp_markup_result['spreadsheet_value']:
                    spreadsheet_pct = pbp_markup_result['spreadsheet_value']
                    if pbp_markup_result['validation_status'] == 'match':
                        st.write(f"  - Spreadsheet: {spreadsheet_pct:.2f}% ✓")
                    else:
                        st.write(f"  - Spreadsheet: {spreadsheet_pct:.2f}% ⚠️ Mismatch")

        except Exception as e:
            st.error(f"Error calculating price: {e}")

st.divider()
st.caption("Phase 1: Core Pricing Engine - January 2026 Schema Transition")
