"""
Test script to access jaggery_sample_6_23.xlsx Google Sheet
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Page configuration
st.set_page_config(page_title="Jaggery Sheet Test", page_icon="🧪")

st.title("🧪 Jaggery Sample Sheet Connection Test")

# Load credentials from Streamlit secrets
try:
    creds_info = st.secrets["gcp_service_account"]
    st.success("✅ Credentials loaded from secrets")
except Exception as e:
    st.error(f"❌ Failed to load credentials: {e}")
    st.stop()

# Create credentials object and authorize
try:
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

# Test connection to jaggery_sample_6_23 sheet
st.header("📊 Testing: jaggery_sample_6_23")

# Note: .xlsx files in Google Drive are typically accessed without the extension
sheet_name = "jaggery_sample_6_23"

try:
    # Try opening the sheet
    sheet = gc.open(sheet_name).sheet1
    data = pd.DataFrame(sheet.get_all_records())

    st.success(f"✅ Connected to '{sheet_name}' successfully!")
    st.write(f"**Rows:** {len(data)}")
    st.write(f"**Columns:** {list(data.columns)}")
    st.write("**Preview:**")
    st.dataframe(data.head(10))

    # Show full data with expandable section
    with st.expander("View Full Data"):
        st.dataframe(data)

except Exception as e:
    st.error(f"❌ Failed to connect to '{sheet_name}': {e}")
    st.info("""
    **Troubleshooting tips:**
    1. Make sure the file is shared with: pbp-app-service@pricing-data-solutions-pbp.iam.gserviceaccount.com
    2. If the file is named 'jaggery_sample_6_23.xlsx', try removing the extension in Google Drive
    3. Check that the file exists in your Google Drive
    """)
