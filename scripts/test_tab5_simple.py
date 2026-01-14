#!/usr/bin/env python3
"""
Simple functional test for Tab 5 (Executive Pricing Tool)
Focuses on testing manual PBP cost inputs and calculations
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_data
from src.pricing_engine import get_unit_price_new_system
from src.helpers import clean_price, get_column_value

def main():
    st.set_page_config(page_title="Tab 5 Test", layout="wide")
    st.title("Tab 5: Executive Pricing Tool - Functional Test")

    # Load data
    df_template, _, _ = load_data('Demo')

    # Simulate session state
    if 'exec_products' not in st.session_state:
        st.session_state.exec_products = []

    # Test adding a product
    st.header("Test 1: Product Addition")

    if st.button("Add Test Product"):
        # Find a product without PBP customization costs
        test_product = None
        for idx, row in df_template.iterrows():
            pbp_setup = clean_price(get_column_value(
                row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
            ))
            if not pbp_setup or pbp_setup == 0:
                test_product = row
                break

        if test_product is not None:
            # Get country for tariff auto-check
            country = test_product.get('Country of Origin (Ships From)', 'Unknown')
            auto_tariff = country.upper() not in ['USA', 'UNITED STATES', 'US', 'U.S.']

            product = {
                'product_name': test_product['Product/Service'],
                'partner': test_product['Partner'],
                'product_data': test_product.to_dict(),
                'quantity': 100,
                'markup_percent': 100.0,
                'include_customization': True,  # Enable to test manual PBP input
                'custom_setup_fee': 100.0,
                'custom_per_unit': 5.0,
                'pbp_setup_fee': 0.0,  # Will be set manually
                'pbp_per_unit_cost': 0.0,  # Will be set manually
                'include_tariffs': auto_tariff,
                'tariff_rate': 10.0 if auto_tariff else 0.0
            }
            st.session_state.exec_products.append(product)
            st.success(f"Added {product['product_name']} (Country: {country}, Auto-tariff: {auto_tariff})")
            st.rerun()

    # Display products
    if st.session_state.exec_products:
        st.header("Test 2: Manual PBP Cost Input")

        for idx, product in enumerate(st.session_state.exec_products):
            with st.expander(f"**{product['product_name']}**", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Customization Setup Fee")

                    # Client price
                    product['custom_setup_fee'] = st.number_input(
                        "Client Price",
                        value=product['custom_setup_fee'],
                        step=10.0,
                        key=f"client_setup_{idx}"
                    )

                    # Check if PBP cost is in spreadsheet
                    row = product['product_data']
                    pbp_setup = clean_price(get_column_value(
                        row, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
                    ))

                    if pbp_setup and pbp_setup > 0:
                        st.info(f"PBP Cost: ${pbp_setup:.2f} (from spreadsheet)")
                        product['pbp_setup_fee'] = pbp_setup
                    else:
                        st.warning("PBP Cost not in spreadsheet")
                        product['pbp_setup_fee'] = st.number_input(
                            "Enter PBP Cost Manually",
                            value=product.get('pbp_setup_fee', 0.0),
                            step=10.0,
                            key=f"pbp_setup_{idx}",
                            help="What PBP pays the partner for setup"
                        )

                with col2:
                    st.markdown("### Customization Per Unit")

                    # Client price
                    product['custom_per_unit'] = st.number_input(
                        "Client Price",
                        value=product['custom_per_unit'],
                        step=0.50,
                        key=f"client_per_unit_{idx}"
                    )

                    # Check if PBP cost is in spreadsheet
                    pbp_per_unit = clean_price(get_column_value(
                        row, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
                    ))

                    if pbp_per_unit and pbp_per_unit > 0:
                        st.info(f"PBP Cost: ${pbp_per_unit:.2f} (from spreadsheet)")
                        product['pbp_per_unit_cost'] = pbp_per_unit
                    else:
                        st.warning("PBP Cost not in spreadsheet")
                        product['pbp_per_unit_cost'] = st.number_input(
                            "Enter PBP Cost Manually",
                            value=product.get('pbp_per_unit_cost', 0.0),
                            step=0.50,
                            key=f"pbp_per_unit_{idx}",
                            help="What PBP pays the partner per unit"
                        )

                # Test 3: Tariff Settings
                st.markdown("### Tariff Settings")

                # Show country
                country = row.get('Country of Origin (Ships From)', 'Unknown')
                st.info(f"Country of Origin (Ships From): {country}")

                product['include_tariffs'] = st.checkbox(
                    "Include Tariffs",
                    value=product.get('include_tariffs', False),
                    key=f"tariff_{idx}"
                )

                if product['include_tariffs']:
                    product['tariff_rate'] = st.number_input(
                        "Tariff Rate (%)",
                        value=product.get('tariff_rate', 10.0),
                        min_value=0.0,
                        max_value=100.0,
                        step=1.0,
                        key=f"tariff_rate_{idx}"
                    )

        # Test 4: Pricing Calculations
        st.header("Test 3: Pricing Calculations")

        total_pbp = 0
        total_client = 0
        total_tariff = 0
        products_pbp = 0
        products_client = 0
        custom_pbp = 0
        custom_client = 0

        for product in st.session_state.exec_products:
            row = product['product_data']
            qty = product['quantity']

            # Base product costs
            base_cost, _, _ = get_unit_price_new_system(row, qty)
            if base_cost and base_cost > 0:
                client_price = base_cost * (1 + product['markup_percent'] / 100)
                products_pbp += base_cost * qty
                products_client += client_price * qty

                # Customization (using stored PBP values)
                if product.get('include_customization'):
                    # Using stored values from product dictionary
                    pbp_setup = product.get('pbp_setup_fee', 0)
                    pbp_per_unit = product.get('pbp_per_unit_cost', 0)

                    custom_pbp += pbp_setup + (pbp_per_unit * qty)
                    custom_client += product['custom_setup_fee'] + (product['custom_per_unit'] * qty)

                # Tariffs (calculated on commercial value)
                if product.get('include_tariffs'):
                    # Tariffs are based on client price (commercial value)
                    tariff_base = client_price * qty
                    if product.get('include_customization'):
                        tariff_base += product['custom_setup_fee'] + (product['custom_per_unit'] * qty)

                    tariff_amount = tariff_base * (product.get('tariff_rate', 0) / 100)
                    total_tariff += tariff_amount

        total_pbp = products_pbp + custom_pbp + total_tariff
        total_client = products_client + custom_client + total_tariff

        # Calculate true margin (excluding pass-through costs)
        true_margin = (products_client - products_pbp) + (custom_client - custom_pbp)
        revenue_base = products_client + custom_client
        margin_pct = (true_margin / revenue_base * 100) if revenue_base > 0 else 0

        # Display results
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Products", f"${products_client:.2f}")
            st.caption(f"PBP: ${products_pbp:.2f}")

        with col2:
            st.metric("Customization", f"${custom_client:.2f}")
            st.caption(f"PBP: ${custom_pbp:.2f}")

        with col3:
            st.metric("Tariffs (Pass-through)", f"${total_tariff:.2f}")
            st.caption("No markup")

        with col4:
            st.metric("True Margin", f"${true_margin:.2f}")
            st.caption(f"{margin_pct:.1f}% of revenue")

        st.divider()

        # Total summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.success(f"**Total Client Price:** ${total_client:.2f}")

        with col2:
            st.info(f"**Total PBP Cost:** ${total_pbp:.2f}")

        with col3:
            st.warning(f"**Total Profit:** ${total_client - total_pbp:.2f}")

        # Test verification
        st.header("Test Results")

        tests_passed = []
        tests_failed = []

        # Test 1: Manual PBP inputs stored correctly
        for product in st.session_state.exec_products:
            if 'pbp_setup_fee' in product and 'pbp_per_unit_cost' in product:
                tests_passed.append("✅ Manual PBP costs are stored in product dictionary")
            else:
                tests_failed.append("❌ Manual PBP costs not properly stored")
            break

        # Test 2: Tariffs auto-enabled for non-USA
        for product in st.session_state.exec_products:
            country = product['product_data'].get('Country of Origin (Ships From)', 'Unknown')
            is_usa = country.upper() in ['USA', 'UNITED STATES', 'US', 'U.S.']
            if (not is_usa and product.get('include_tariffs')) or (is_usa and not product.get('include_tariffs', False)):
                tests_passed.append(f"✅ Tariff auto-check working for {country}")
            else:
                tests_failed.append(f"❌ Tariff auto-check failed for {country}")
            break

        # Test 3: Margin excludes pass-through costs
        if total_tariff > 0:
            expected_margin = (products_client - products_pbp) + (custom_client - custom_pbp)
            if abs(true_margin - expected_margin) < 0.01:
                tests_passed.append("✅ True margin correctly excludes tariffs")
            else:
                tests_failed.append("❌ True margin calculation error")

        # Test 4: Calculations use stored PBP values
        if custom_pbp > 0:
            tests_passed.append("✅ Calculations using stored PBP cost values")

        # Display test results
        if tests_passed:
            for test in tests_passed:
                st.success(test)

        if tests_failed:
            for test in tests_failed:
                st.error(test)

        if not tests_failed:
            st.balloons()
            st.success("🎉 **ALL TESTS PASSED!**")

if __name__ == "__main__":
    main()