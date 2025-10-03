"""
Debug script to check pricing data structure
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.title("Debug: Pricing Data Structure")

@st.cache_resource
def connect_to_sheets():
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_pricing_data():
    gc = connect_to_sheets()
    sheet = gc.open("jaggery_sample_6_23").sheet1
    all_values = sheet.get_all_values()
    headers = all_values[4]
    data_rows = all_values[5:]
    df = pd.DataFrame(data_rows, columns=headers)
    df = df[df['Product Ref. No.'].str.strip() != '']
    return df

try:
    df = load_pricing_data()
    st.success(f"✅ Loaded {len(df)} products")

    # Show first product
    st.subheader("First Product Data")
    first_product = df.iloc[0]

    st.write("**Product Info:**")
    st.write(f"- Product Ref: {first_product['Product Ref. No.']}")
    st.write(f"- Gift Name: {first_product['Gift Name']}")

    st.write("**Pricing Columns:**")
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
        if col in first_product.index:
            value = first_product[col]
            st.write(f"- {col}: '{value}' (type: {type(value).__name__}, empty: {value == ''})")
        else:
            st.write(f"- {col}: **COLUMN NOT FOUND**")

    st.subheader("All Column Names")
    st.write(list(df.columns))

    st.subheader("Sample Row as Dict")
    st.json(first_product.to_dict())

except Exception as e:
    st.error(f"❌ Error: {e}")
    import traceback
    st.code(traceback.format_exc())
