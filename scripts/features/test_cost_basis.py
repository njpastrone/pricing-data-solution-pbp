"""
Test cost basis normalization (Per Item vs Per Package).
Part of January 2026 schema transition testing.

Usage:
    streamlit run scripts/features/test_cost_basis.py
"""

import streamlit as st
from src.data_loader import load_pricing_data
from src.helpers import normalize_cost_to_per_item, get_column_value

st.title("Test Cost Basis Normalization (Jan 2026)")
st.caption("Testing Per Item vs Per Package cost normalization")

# Dataset selector
dataset = st.sidebar.radio("Select Dataset", ["demo", "real"], index=0)

# Load data
try:
    df_template, df_metadata, df_partner_info = load_pricing_data(dataset)
    st.success(f"✅ Loaded {len(df_template)} products from {dataset} dataset")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

st.divider()

# Filter to only show Per Package products
st.subheader("Products with Per Package Pricing")

per_package_count = 0

for idx, row in df_template.iterrows():
    product_name = row.get('Product/Service', 'Unknown')
    cost_basis = get_column_value(row, 'Cost Basis (Per Item/Per Package)', None, 'Per Item')

    # Get base cost (try consolidated column first)
    base_cost_raw = get_column_value(row, 'PBP Cost (No Tiers/Tier 1)', 'PBP Cost (No Tiers)', None)

    if base_cost_raw:
        try:
            from src.helpers import clean_price
            base_cost = clean_price(base_cost_raw)

            if base_cost and cost_basis == 'Per Package':
                per_package_count += 1

                with st.expander(f"**{product_name}** (Per Package)", expanded=True):
                    units_per_package = row.get('Units per Package', 1)

                    # Convert to float
                    try:
                        units_per_package = float(units_per_package) if units_per_package else 1
                    except (ValueError, TypeError):
                        units_per_package = 1

                    per_item_cost = normalize_cost_to_per_item(row, base_cost)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Package Cost", f"${base_cost:.2f}")

                    with col2:
                        st.metric("Units per Package", f"{units_per_package:.0f}")

                    with col3:
                        st.metric("Per-Item Cost", f"${per_item_cost:.2f}")

                    # Formula display
                    st.info(f"**Formula:** ${base_cost:.2f} ÷ {units_per_package:.0f} = **${per_item_cost:.2f}**")

                    # Show partner
                    partner = row.get('Partner', 'Unknown')
                    st.caption(f"Partner: {partner}")

        except Exception as e:
            st.error(f"Error processing {product_name}: {e}")

if per_package_count == 0:
    st.warning("No products found with 'Per Package' cost basis in this dataset.")
    st.info("To test this feature, add products with:")
    st.code("""
Cost Basis (Per Item/Per Package): "Per Package"
Units per Package: 6 (or any number > 1)
PBP Cost (No Tiers/Tier 1): $48.00
    """)
    st.write("Expected result: Per-item cost = $48.00 / 6 = $8.00")
else:
    st.success(f"✅ Found {per_package_count} product(s) with Per Package pricing")

st.divider()

# Show all products and their cost basis
st.subheader("All Products - Cost Basis Summary")

cost_basis_summary = {}

for idx, row in df_template.iterrows():
    product_name = row.get('Product/Service', 'Unknown')
    cost_basis = get_column_value(row, 'Cost Basis (Per Item/Per Package)', None, 'Per Item')

    if cost_basis not in cost_basis_summary:
        cost_basis_summary[cost_basis] = []

    cost_basis_summary[cost_basis].append(product_name)

for basis, products in cost_basis_summary.items():
    with st.expander(f"**{basis}** ({len(products)} products)"):
        for product in products:
            st.write(f"- {product}")

st.divider()
st.caption("Phase 1: Core Pricing Engine - January 2026 Schema Transition")
