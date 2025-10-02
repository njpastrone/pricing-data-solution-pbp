"""
Quick lightweight check of jaggery_sample_6_23 sheet
Loads only essential information to avoid timeout
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Quick Data Check", page_icon="⚡")

st.title("⚡ Quick Data Structure Check")

# Connect
creds_info = st.secrets["gcp_service_account"]
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

st.write("Connecting to sheet...")
sheet = gc.open("jaggery_sample_6_23").sheet1

# Get basic info
st.success("✅ Connected!")

st.write(f"**Sheet title:** {sheet.title}")
st.write(f"**Row count:** {sheet.row_count}")
st.write(f"**Column count:** {sheet.col_count}")

# Get just first 5 rows
st.write("---")
st.write("**First 5 rows:**")
first_rows = sheet.get_values("A1:Z5")  # Get first 5 rows, up to column Z
for i, row in enumerate(first_rows, 1):
    st.write(f"Row {i}: {row}")

# Get header row
st.write("---")
st.write("**Header row (Row 1):**")
header = sheet.row_values(1)
st.write(header)

st.write("---")
st.info("💡 Based on what you see above, we can create the DATA_STRUCTURE.md file")
