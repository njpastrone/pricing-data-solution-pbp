"""
Investigate the new jaggery_demo sheet structure
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.title("🔍 Investigating jaggery_demo Sheet")

@st.cache_resource
def connect_to_sheets():
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

try:
    gc = connect_to_sheets()
    st.success("✅ Connected to Google Sheets")

    sheet = gc.open("jaggery_demo").sheet1
    st.success(f"✅ Opened jaggery_demo sheet")

    # Get all values
    all_values = sheet.get_all_values()

    st.subheader("Sheet Structure")
    st.write(f"- Total rows: {len(all_values)}")
    st.write(f"- Total columns: {len(all_values[0]) if all_values else 0}")

    st.subheader("First 5 Rows (Raw)")
    for i, row in enumerate(all_values[:5], 1):
        st.write(f"**Row {i}:** {row[:10]}...")  # First 10 columns

    st.subheader("Headers (Row 2)")
    if len(all_values) >= 2:
        headers = [col.strip() for col in all_values[1]]
        st.write(headers)

    st.subheader("First Product (Row 3)")
    if len(all_values) >= 3:
        headers = [col.strip() for col in all_values[1]]
        first_product = all_values[2]

        product_dict = dict(zip(headers, first_product))

        st.write("**Product Info:**")
        st.write(f"- Product Ref: {product_dict.get('Product Ref. No.', 'N/A')}")
        st.write(f"- Gift Name: {product_dict.get('Gift Name', 'N/A')}")
        st.write(f"- Partner: {product_dict.get('Artisan Partner', 'N/A')}")

        st.write("\n**Pricing Tiers:**")
        pricing_cols = [
            'PBP Cost w/o shipping (1-25)',
            'PBP Cost w/o shipping (26-50)',
            'PBP Cost w/o shipping (51-100)',
            'PBP Cost w/o shipping (101-250)',
            'PBP Cost w/o shipping (251-500)',
            'PBP Cost w/o shipping (501-1000)',
            'PBP Cost w/o shipping (1000+)'
        ]

        for col in pricing_cols:
            value = product_dict.get(col, 'N/A')
            st.write(f"- {col}: '{value}'")

        st.write("\n**Additional Costs:**")
        st.write(f"- Art Setup Fee: {product_dict.get('Art Setup Fee', 'N/A')}")
        st.write(f"- Labels: {product_dict.get('Labels up to 1\" x 2.5\\'', 'N/A')}")
        st.write(f"- Minimum for labels: {product_dict.get('Minimum for labels', 'N/A')}")

        st.subheader("Full First Product Data")
        st.json(product_dict)

    st.subheader("Sample of 5 Products")
    if len(all_values) >= 7:
        headers = [col.strip() for col in all_values[1]]
        data_rows = all_values[2:7]
        df = pd.DataFrame(data_rows, columns=headers)
        st.dataframe(df[['Product Ref. No.', 'Gift Name', 'PBP Cost w/o shipping (1-25)', 'PBP Cost w/o shipping (51-100)', 'Art Setup Fee']])

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
