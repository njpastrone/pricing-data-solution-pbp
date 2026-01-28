"""
Export Current Product Names for Google Form Update

This script extracts all current product names from the master pricing spreadsheet
so you can update the Google Form dropdown options to match.

Usage:
    streamlit run scripts/features/export_product_names_for_form.py
"""

import streamlit as st
import sys
sys.path.append('.')

from src.data_loader import load_pricing_data

st.title("Export Product Names for Google Form")
st.caption("Get current product names to update your Google Form dropdowns")

st.divider()

# Dataset selector
dataset = st.radio(
    "Select dataset:",
    options=['demo', 'real'],
    index=1,  # Default to real
    horizontal=True
)

if st.button("Get Product Names", type="primary"):
    st.markdown("### Loading data...")

    # Load data
    df_template, df_metadata, df_partner_info = load_pricing_data(dataset)

    st.success(f"Found {len(df_template)} products")

    # Extract product names
    product_names = sorted(df_template['Product/Service'].unique().tolist())

    st.markdown("### Current Product Names")
    st.caption(f"Total: {len(product_names)} unique products")

    # Display as numbered list (easier to copy)
    product_list = "\n".join(product_names)

    st.text_area(
        "Copy these names (already alphabetically sorted):",
        value=product_list,
        height=400,
        help="Copy all these names to update your Google Form dropdown options"
    )

    st.divider()

    st.markdown("### Next Steps:")
    st.markdown("""
    1. **Copy the list above** (click in text area, Ctrl+A or Cmd+A, then Ctrl+C or Cmd+C)

    2. **Open your Google Form** in edit mode:
       - Go to: https://docs.google.com/forms/d/1FAIpQLSeqkiNJbalPNWPa2DjizAEbOPGlTxbkgE76Bldqk08yFymCjA/edit

    3. **Update EACH product dropdown** (10 total):
       - Find "Product Line 1 - Product Name" question
       - Click on it to edit
       - Delete old options
       - Paste new options (one per line)
       - Repeat for Product Lines 2-10

    4. **Save the form**

    5. **Test it**:
       - Go to Tab 1 in the app
       - Create a proposal with some products
       - Go to Tab 2
       - Generate Google Form URL
       - Open the URL
       - ✅ Products should now appear pre-filled in dropdowns!
    """)

    st.info("""
    **Pro Tip:** You can copy-paste the entire list into all 10 dropdown questions at once.
    This ensures consistency across all product lines.
    """)

    st.divider()

    st.markdown("### Product Names by Partner")
    st.caption("For reference - see which partner offers which products")

    for partner in sorted(df_template['Partner'].unique()):
        with st.expander(f"{partner}"):
            partner_products = df_template[df_template['Partner'] == partner]['Product/Service'].tolist()
            for prod in sorted(partner_products):
                st.markdown(f"- {prod}")

st.divider()
st.caption("Script: export_product_names_for_form.py")
