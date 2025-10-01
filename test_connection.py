"""
Simple test script to verify Google Sheets API connection.
Tests connection to both master_pricing and master_pricing_demo sheets.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Page configuration
st.set_page_config(page_title="Google Sheets Connection Test", page_icon="✅")

st.title("🔌 Google Sheets API Connection Test")

# Load credentials from Streamlit secrets
try:
    creds_info = st.secrets["gcp_service_account"]
    st.success("✅ Credentials loaded from secrets")
except Exception as e:
    st.error(f"❌ Failed to load credentials: {e}")
    st.stop()

# Create credentials object and authorize
try:
    # Define the scopes needed for Google Sheets
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    gc = gspread.authorize(creds)
    st.success("✅ Successfully authorized with Google API")
except Exception as e:
    st.error(f"❌ Authorization failed: {e}")
    st.stop()

# Test connection to master_pricing sheet
st.header("📊 Testing: master_pricing")
try:
    sheet_master = gc.open("master_pricing").sheet1
    data_master = pd.DataFrame(sheet_master.get_all_records())

    st.success(f"✅ Connected to 'master_pricing' successfully!")
    st.write(f"**Rows:** {len(data_master)}")
    st.write(f"**Columns:** {list(data_master.columns)}")
    st.write("**Preview:**")
    st.dataframe(data_master.head())

except Exception as e:
    st.error(f"❌ Failed to connect to 'master_pricing': {e}")

# Test connection to master_pricing_demo sheet
st.header("📊 Testing: master_pricing_demo")
try:
    sheet_demo = gc.open("master_pricing_demo").sheet1
    data_demo = pd.DataFrame(sheet_demo.get_all_records())

    st.success(f"✅ Connected to 'master_pricing_demo' successfully!")
    st.write(f"**Rows:** {len(data_demo)}")
    st.write(f"**Columns:** {list(data_demo.columns)}")
    st.write("**Preview:**")
    st.dataframe(data_demo.head())

except Exception as e:
    st.error(f"❌ Failed to connect to 'master_pricing_demo': {e}")

st.info("💡 If you see errors above, make sure the sheets exist and are shared with your service account email.")
