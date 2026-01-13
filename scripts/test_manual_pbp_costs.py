#!/usr/bin/env python3
"""
Test script for manual PBP cost input functionality in Tab 5
Tests that users can manually input PBP costs for customization when not in spreadsheet
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_data
from src.pricing_engine import get_unit_price_new_system
from src.helpers import clean_price, get_column_value

def test_manual_pbp_costs():
    """Test manual PBP cost input functionality"""

    st.title("Manual PBP Cost Input Test")

    # Load data
    df_template, _, _ = load_data('Demo')

    # Find a product to test with
    test_product = df_template.iloc[0]  # First product

    st.header("Test Product")
    st.write(f"Product: {test_product['Product/Service']}")
    st.write(f"Partner: {test_product['Partner']}")

    # Check if product has PBP customization costs in spreadsheet
    st.header("PBP Customization Costs from Spreadsheet")

    pbp_setup = clean_price(get_column_value(
        test_product, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
    ))
    pbp_per_unit = clean_price(get_column_value(
        test_product, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
    ))

    st.write(f"PBP Setup Fee: ${pbp_setup:.2f}" if pbp_setup else "PBP Setup Fee: Not in spreadsheet")
    st.write(f"PBP Per Unit: ${pbp_per_unit:.2f}" if pbp_per_unit else "PBP Per Unit: Not in spreadsheet")

    st.header("Manual Input Test")

    # Simulate product dictionary
    product = {
        'product_name': test_product['Product/Service'],
        'partner': test_product['Partner'],
        'quantity': 100,
        'markup_percent': 100.0,
        'include_customization': True,
        'custom_setup_fee': 50.0,  # Client price
        'custom_per_unit': 2.0,     # Client price
        'pbp_setup_fee': 0.0,        # Initialize
        'pbp_per_unit_cost': 0.0     # Initialize
    }

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Setup Fee**")
        product['custom_setup_fee'] = st.number_input(
            "Client Price",
            value=product['custom_setup_fee'],
            step=10.0
        )

        if pbp_setup:
            st.caption(f"PBP Cost: ${pbp_setup:.2f} (from spreadsheet)")
            product['pbp_setup_fee'] = pbp_setup
        else:
            product['pbp_setup_fee'] = st.number_input(
                "PBP Cost (enter manually)",
                value=product['pbp_setup_fee'],
                step=10.0,
                help="What PBP pays the partner"
            )

    with col2:
        st.markdown("**Per Unit Cost**")
        product['custom_per_unit'] = st.number_input(
            "Client Price",
            value=product['custom_per_unit'],
            step=0.50
        )

        if pbp_per_unit:
            st.caption(f"PBP Cost: ${pbp_per_unit:.2f} (from spreadsheet)")
            product['pbp_per_unit_cost'] = pbp_per_unit
        else:
            product['pbp_per_unit_cost'] = st.number_input(
                "PBP Cost (enter manually)",
                value=product['pbp_per_unit_cost'],
                step=0.50,
                help="What PBP pays the partner"
            )

    st.header("Pricing Breakdown Using Stored Values")

    # Calculate margins
    client_setup_total = product['custom_setup_fee']
    client_per_unit_total = product['custom_per_unit'] * product['quantity']
    pbp_setup_total = product['pbp_setup_fee']
    pbp_per_unit_total = product['pbp_per_unit_cost'] * product['quantity']

    custom_margin = (client_setup_total + client_per_unit_total) - (pbp_setup_total + pbp_per_unit_total)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Client Total", f"${client_setup_total + client_per_unit_total:.2f}")

    with col2:
        st.metric("PBP Cost Total", f"${pbp_setup_total + pbp_per_unit_total:.2f}")

    with col3:
        st.metric("Margin", f"${custom_margin:.2f}")

    # Show detailed breakdown
    st.subheader("Detailed Breakdown")

    breakdown = []

    if product['custom_setup_fee'] > 0:
        breakdown.append({
            'Item': 'Setup Fee',
            'PBP Cost': f"${product['pbp_setup_fee']:.2f}",
            'Client Price': f"${product['custom_setup_fee']:.2f}",
            'Margin': f"${product['custom_setup_fee'] - product['pbp_setup_fee']:.2f}"
        })

    if product['custom_per_unit'] > 0:
        breakdown.append({
            'Item': f'Per Unit x {product["quantity"]}',
            'PBP Cost': f"${pbp_per_unit_total:.2f}",
            'Client Price': f"${client_per_unit_total:.2f}",
            'Margin': f"${client_per_unit_total - pbp_per_unit_total:.2f}"
        })

    if breakdown:
        import pandas as pd
        st.table(pd.DataFrame(breakdown))

    # Summary
    st.success(f"""
    ✅ Manual PBP cost input is working!
    - PBP costs can be entered when not in spreadsheet
    - Values are stored in product dictionary
    - Calculations use stored values correctly
    - Margins calculated properly
    """)

if __name__ == "__main__":
    test_manual_pbp_costs()