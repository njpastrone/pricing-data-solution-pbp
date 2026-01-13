"""
Test script to debug bidirectional editing issues in Tab 5
"""
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.helpers import calculate_markup_from_price

st.set_page_config(page_title="Test Bidirectional Editing", layout="wide")

st.title("Debug Bidirectional Editing - Tab 5 Pattern")

# Initialize session state
if 'test_products' not in st.session_state:
    st.session_state.test_products = [
        {
            'name': 'Test Product',
            'base_cost': 10.0,
            'markup_percent': 100.0
        }
    ]

# Display debug info
st.sidebar.header("Debug Info")
st.sidebar.write("Session State Flags:")
for key in st.session_state:
    if 'updating_from' in key:
        st.sidebar.write(f"{key}: {st.session_state[key]}")

st.header("Product Configuration Test")

for idx, product in enumerate(st.session_state.test_products):
    st.subheader(f"Product {idx + 1}: {product['name']}")

    col1, col2, col3 = st.columns(3)

    base_cost = product['base_cost']

    with col1:
        st.write(f"Base Cost: ${base_cost:.2f}")

    with col2:
        # Markup % input
        if st.session_state.get(f'updating_from_price_{idx}', False):
            # Display only
            st.markdown("**Markup % (calculated)**")
            st.markdown(f"{product['markup_percent']:.1f}%")
            st.info("Updated from price change")
            # Clear flag
            st.session_state[f'updating_from_price_{idx}'] = False
        else:
            # Editable
            new_markup = st.number_input(
                "Markup %",
                min_value=-50,
                max_value=500,
                value=int(product['markup_percent']),
                step=5,
                key=f"markup_{idx}"
            )

            if new_markup != product['markup_percent']:
                st.warning(f"Markup changed: {product['markup_percent']} → {new_markup}")
                product['markup_percent'] = float(new_markup)
                st.session_state[f'updating_from_markup_{idx}'] = True
                st.rerun()

    with col3:
        # Calculate client price
        client_price = base_cost * (1 + product['markup_percent'] / 100)

        # Client Price input
        if st.session_state.get(f'updating_from_markup_{idx}', False):
            # Display only
            st.markdown("**Client Price (calculated)**")
            st.markdown(f"${client_price:.2f}")
            st.info("Updated from markup change")
            # Clear flag
            st.session_state[f'updating_from_markup_{idx}'] = False
        else:
            # Editable
            new_price = st.number_input(
                "Client Price/Unit",
                min_value=0.01,
                value=client_price,
                step=1.0,
                format="%.2f",
                key=f"price_{idx}"
            )

            if abs(new_price - client_price) > 0.01:
                st.warning(f"Price changed: ${client_price:.2f} → ${new_price:.2f}")
                new_markup_calc = calculate_markup_from_price(base_cost, new_price)
                st.info(f"Calculated new markup: {new_markup_calc:.1f}%")
                product['markup_percent'] = new_markup_calc
                st.session_state[f'updating_from_price_{idx}'] = True
                st.rerun()

st.divider()
st.subheader("Current Product State")
st.json(st.session_state.test_products)