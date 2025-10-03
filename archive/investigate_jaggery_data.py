"""
Full investigation of jaggery_sample_6_23 sheet structure
This script will explore the data format, columns, data types, and sample values
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="Jaggery Data Investigation", page_icon="🔍", layout="wide")

st.title("🔍 Jaggery Sample Data Investigation")

# Load credentials and connect
creds_info = st.secrets["gcp_service_account"]
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

# Open the sheet
sheet = gc.open("jaggery_sample_6_23").sheet1

# Get all data as raw values (no headers assumed)
all_values = sheet.get_all_values()

st.header("📊 Raw Data Overview")
st.write(f"**Total rows (including headers):** {len(all_values)}")
st.write(f"**Total columns:** {len(all_values[0]) if all_values else 0}")

# Display first 20 rows as raw data
st.subheader("First 20 Rows (Raw)")
st.write("This shows exactly what's in the sheet, including any headers or formatting:")
raw_df = pd.DataFrame(all_values[:20])
st.dataframe(raw_df)

# Try to identify header row
st.header("🔎 Header Detection")
st.write("**First row values:**")
st.write(all_values[0] if all_values else "No data")

# Try loading as records (assumes first row is headers)
try:
    records_data = sheet.get_all_records()
    df = pd.DataFrame(records_data)

    st.header("📋 Data Loaded as DataFrame")
    st.write(f"**Rows:** {len(df)}")
    st.write(f"**Columns:** {list(df.columns)}")

    st.subheader("Column Information")
    col_info = []
    for col in df.columns:
        col_info.append({
            "Column Name": col,
            "Data Type": str(df[col].dtype),
            "Non-Null Count": df[col].count(),
            "Null Count": df[col].isna().sum(),
            "Unique Values": df[col].nunique(),
            "Sample Value": str(df[col].iloc[0]) if len(df) > 0 else "N/A"
        })

    col_info_df = pd.DataFrame(col_info)
    st.dataframe(col_info_df, use_container_width=True)

    st.subheader("First 10 Rows")
    st.dataframe(df.head(10), use_container_width=True)

    st.subheader("Sample Values for Each Column")
    for col in df.columns:
        with st.expander(f"📌 {col}"):
            unique_vals = df[col].unique()[:20]  # Show first 20 unique values
            st.write(f"**Sample values:** {list(unique_vals)}")
            st.write(f"**Total unique:** {df[col].nunique()}")

    # Check for empty rows or columns
    st.header("🧹 Data Quality Check")
    empty_cols = [col for col in df.columns if df[col].isna().all()]
    if empty_cols:
        st.warning(f"⚠️ Completely empty columns: {empty_cols}")
    else:
        st.success("✅ No completely empty columns")

    # Check if there are any unnamed columns
    unnamed_cols = [col for col in df.columns if 'Unnamed' in str(col) or col == '']
    if unnamed_cols:
        st.warning(f"⚠️ Unnamed or blank columns: {unnamed_cols}")

    # Show full data in expandable section
    with st.expander("View Full Dataset"):
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error loading as DataFrame: {e}")
    st.write("The data might not have a proper header row or has formatting issues")

# Check if there are multiple sheets
st.header("📑 Sheet Information")
try:
    worksheets = gc.open("jaggery_sample_6_23").worksheets()
    st.write(f"**Number of worksheets/tabs:** {len(worksheets)}")
    for i, ws in enumerate(worksheets):
        st.write(f"{i+1}. **{ws.title}** - {ws.row_count} rows x {ws.col_count} columns")
except Exception as e:
    st.error(f"Error getting worksheet info: {e}")
