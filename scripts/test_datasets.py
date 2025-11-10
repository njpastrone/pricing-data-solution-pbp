"""
Quick test script to verify both datasets are accessible via Google Sheets API
"""

import streamlit as st
from src.data_loader import load_pricing_data, DATASET_CONFIGS

st.set_page_config(page_title="Dataset Connection Test", layout="wide")

st.title("Dataset Connection Test")
st.markdown("Testing access to both demo and real pricing datasets")

# Test Demo Dataset
st.header("1. Demo Dataset (master_pricing_template_10_14)")
try:
    df_template_demo, df_metadata_demo, df_partner_demo = load_pricing_data('demo')

    st.success(f"✓ Demo dataset loaded successfully")
    st.info(f"**Products:** {len(df_template_demo)} | **Partners:** {len(df_template_demo['Partner'].unique())}")

    with st.expander("Show demo data preview"):
        st.dataframe(df_template_demo.head(10))
        st.caption("Showing first 10 rows")

except Exception as e:
    st.error(f"✗ Failed to load demo dataset: {str(e)}")

st.markdown("---")

# Test Real Dataset
st.header("2. Real Dataset (master_pricing)")
try:
    df_template_real, df_metadata_real, df_partner_real = load_pricing_data('real')

    st.success(f"✓ Real dataset loaded successfully")
    st.info(f"**Products:** {len(df_template_real)} | **Partners:** {len(df_template_real['Partner'].unique())}")

    with st.expander("Show real data preview"):
        st.dataframe(df_template_real.head(10))
        st.caption("Showing first 10 rows")

except Exception as e:
    st.error(f"✗ Failed to load real dataset: {str(e)}")

st.markdown("---")

# Show configuration
st.header("3. Dataset Configurations")
for key, config in DATASET_CONFIGS.items():
    with st.expander(f"{key.upper()}: {config['name']}"):
        st.markdown(f"**Description:** {config['description']}")
        st.markdown(f"**URL:** {config['url']}")
        st.markdown(f"**Spreadsheet ID:** {config['spreadsheet_id']}")
