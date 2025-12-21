"""
Data Investigation Tool
Streamlit app to explore master_pricing_template_10_14 structure and content.
"""
import streamlit as st
from src.data_loader import load_pricing_data

st.title("Data Inspector - master_pricing_template_10_14")

st.markdown("""
**Purpose:** Investigate the current data structure from the master pricing template.

This tool helps you:
- View sheet structure and column names
- Inspect product data
- Verify tier parsing logic
- Check partner configuration
""")

# Load data
try:
    df_template, df_metadata, df_partner_info = load_pricing_data()
    st.success(f"✅ Successfully loaded 3 sheets from master_pricing_template_10_14")
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Sheet selection
sheet_choice = st.selectbox(
    "Select sheet to inspect:",
    ["Template", "Metadata", "Partner-Specific Info"]
)

st.divider()

# ==================================================
# TEMPLATE SHEET
# ==================================================
if sheet_choice == "Template":
    st.subheader("Template Sheet")
    st.write(f"**Total products:** {len(df_template)}")
    st.write(f"**Columns:** {len(df_template.columns)}")

    # Show column names
    with st.expander("View All Column Names", expanded=False):
        for i, col in enumerate(df_template.columns, 1):
            st.write(f"{i}. `{col}`")

    st.markdown("---")

    # Partner filter
    partners = sorted(df_template['Partner'].unique())
    selected_partner = st.selectbox("Filter by Partner:", ["All"] + partners)

    if selected_partner != "All":
        filtered_df = df_template[df_template['Partner'] == selected_partner]
    else:
        filtered_df = df_template

    st.write(f"**Showing {len(filtered_df)} products**")

    # Show first 10 rows
    st.subheader("Product Data (First 10 Rows)")
    display_cols = ['Partner', 'Product/Service', 'Purchase Description',
                   'Pricing Tiers (Y/N)', 'Pricing Tiers Info']

    # Add tier columns if they exist
    tier_cols = [col for col in filtered_df.columns if 'PBP Cost: Tier' in col or 'PBP Cost (No Tiers)' in col]
    display_cols.extend(tier_cols[:3])  # Show first 3 tier columns

    available_cols = [col for col in display_cols if col in filtered_df.columns]
    st.dataframe(filtered_df[available_cols].head(10))

    # Detailed view of specific product
    st.markdown("---")
    st.subheader("Inspect Specific Product")

    product_names = filtered_df['Product/Service'].tolist()
    if product_names:
        selected_product = st.selectbox("Select Product:", product_names)

        product_row = filtered_df[filtered_df['Product/Service'] == selected_product].iloc[0]

        # Basic Info
        st.markdown("**Basic Information:**")
        st.write(f"- Partner: `{product_row.get('Partner', 'N/A')}`")
        st.write(f"- Product/Service: `{product_row.get('Product/Service', 'N/A')}`")
        st.write(f"- Purchase Description: `{product_row.get('Purchase Description', 'N/A')}`")

        # Pricing Structure
        st.markdown("**Pricing Structure:**")
        has_tiers = product_row.get('Pricing Tiers (Y/N)', 'N')
        st.write(f"- Has Tiers: `{has_tiers}`")

        if has_tiers == 'Y':
            tier_info = product_row.get('Pricing Tiers Info', '')
            st.write(f"- Tier Info: `{tier_info}`")

            st.markdown("**Tier Prices:**")
            for i in range(1, 7):
                tier_col = f'PBP Cost: Tier {i}'
                if tier_col in product_row.index:
                    value = product_row[tier_col]
                    st.write(f"  - Tier {i}: `{value}`")
        else:
            flat_price = product_row.get('PBP Cost (No Tiers)', '')
            st.write(f"- Flat Price: `{flat_price}`")

        # Customization
        st.markdown("**Customization:**")
        st.write(f"- Setup Fee: `{product_row.get('Customization Setup Fee', 'N/A')}`")
        st.write(f"- Per Unit Cost: `{product_row.get('Customization Cost per Unit', 'N/A')}`")
        st.write(f"- Minimum: `{product_row.get('Customization Minimum', 'N/A')}`")

        # Tariff & Shipping
        st.markdown("**Additional Costs:**")
        st.write(f"- Tariff Estimate: `{product_row.get('Tariff Estimate', 'N/A')}`")
        st.write(f"- Shipping: `{product_row.get('Shipping', 'N/A')}`")
        st.write(f"- MSRP: `{product_row.get('MSRP', 'N/A')}`")

        # Full data
        with st.expander("View Full Product Data (JSON)", expanded=False):
            product_dict = product_row.to_dict()
            st.json(product_dict)

# ==================================================
# METADATA SHEET
# ==================================================
elif sheet_choice == "Metadata":
    st.subheader("Metadata Sheet")
    st.write(f"**Total rows:** {len(df_metadata)}")
    st.write(f"**Columns:** {len(df_metadata.columns)}")

    st.markdown("This sheet contains field definitions for deliverable information.")

    # Show column names
    with st.expander("View All Column Names", expanded=False):
        for i, col in enumerate(df_metadata.columns, 1):
            st.write(f"{i}. `{col}`")

    st.markdown("---")

    # Show all metadata
    st.subheader("Metadata Content")
    st.dataframe(df_metadata)

    # Column explorer
    st.markdown("---")
    st.subheader("Inspect Specific Column")
    if len(df_metadata.columns) > 0:
        selected_col = st.selectbox("Select Column:", df_metadata.columns)
        st.write(f"**Values in `{selected_col}`:**")
        st.dataframe(df_metadata[selected_col])

# ==================================================
# PARTNER-SPECIFIC INFO SHEET
# ==================================================
elif sheet_choice == "Partner-Specific Info":
    st.subheader("Partner-Specific Info Sheet")
    st.write(f"**Total partners:** {len(df_partner_info)}")
    st.write(f"**Columns:** {len(df_partner_info.columns)}")

    # Show column names
    with st.expander("View All Column Names", expanded=False):
        for i, col in enumerate(df_partner_info.columns, 1):
            st.write(f"{i}. `{col}`")

    st.markdown("---")

    # Show all partner info
    st.subheader("Partner Configuration")

    # Show key columns if they exist
    key_cols = ['Partner', 'POC Name', 'POC Email', 'POC Phone',
                'Contact Name', 'Email', 'Phone']
    available_key_cols = [col for col in key_cols if col in df_partner_info.columns]

    if available_key_cols:
        st.dataframe(df_partner_info[available_key_cols])
    else:
        st.dataframe(df_partner_info)

    # Detailed partner view
    st.markdown("---")
    st.subheader("Inspect Specific Partner")

    if 'Partner' in df_partner_info.columns:
        partners = df_partner_info['Partner'].tolist()
        if partners:
            selected_partner = st.selectbox("Select Partner:", partners)

            partner_row = df_partner_info[df_partner_info['Partner'] == selected_partner].iloc[0]

            st.markdown("**Partner Details:**")
            for col in df_partner_info.columns:
                value = partner_row.get(col, 'N/A')
                st.write(f"- {col}: `{value}`")

            # Full data
            with st.expander("View Full Partner Data (JSON)", expanded=False):
                partner_dict = partner_row.to_dict()
                st.json(partner_dict)

st.markdown("---")
st.caption("💡 Tip: Use this tool to verify column names, pricing structures, and data formats before making changes to the app.")
