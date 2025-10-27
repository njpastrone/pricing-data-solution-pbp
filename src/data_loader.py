"""
Data Loader Module for PBP Pricing App

This module handles all Google Sheets integration:
- Connection to Google Sheets API
- Loading pricing data from master_pricing_template_10_14
- Data caching with TTL
- Data frame processing and cleanup

The module loads data from 3 sheets:
1. Template: Partner-product pricing data (header at row 6)
2. Metadata: Deliverable field definitions (header at row 2)
3. Partner-Specific Info: Partner configuration (header at row 2)
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd


@st.cache_resource
def connect_to_sheets():
    """
    Connect to Google Sheets using service account credentials.
    Cached so we don't reconnect on every rerun.

    Returns:
        gspread.Client: Authorized gspread client

    Raises:
        Exception: If connection fails or credentials are invalid

    Note:
        Requires st.secrets["gcp_service_account"] to be configured
        with valid Google Cloud service account credentials.
    """
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)


@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_pricing_data():
    """
    Load pricing data from master_pricing_template_10_14 Google Sheet.
    Loads three sheets: Template, Metadata, Partner-Specific Info
    Returns three DataFrames.

    Returns:
        tuple: (df_template, df_metadata, df_partner_info)
            - df_template: Product pricing data with tiers
            - df_metadata: Field definitions and metadata
            - df_partner_info: Partner contact information

    Raises:
        Exception: If spreadsheet not found or sheets cannot be loaded

    Data Structure:
        Template Sheet:
            - Header at row 6 (index 5)
            - Data starts at row 7 (index 6)
            - First column may be empty (skipped)
            - Filters out rows with empty Partner column

        Metadata Sheet:
            - Header at row 2 (index 1)
            - Data starts at row 3 (index 2)

        Partner-Specific Info Sheet:
            - Header at row 2 (index 1)
            - Data starts at row 3 (index 2)
            - First column may be empty (skipped)
            - Filters out rows with empty Partner column

    Example:
        >>> df_template, df_metadata, df_partner_info = load_pricing_data()
        >>> print(len(df_template))
        42  # 42 products loaded
        >>> print(df_template['Partner'].unique())
        ['Partner X', 'Partner Y']
    """
    gc = connect_to_sheets()
    spreadsheet = gc.open("master_pricing_template_10_14")

    # ========== LOAD TEMPLATE SHEET ==========
    # Header at row 6 (index 5), data starts at row 7 (index 6)
    template_sheet = spreadsheet.worksheet("Template")
    template_values = template_sheet.get_all_values()

    # Row 6 has headers, but first column is empty - skip it
    raw_headers = template_values[5]
    raw_data = template_values[6:]

    # Find first non-empty column index
    first_col_idx = 0
    for i, header in enumerate(raw_headers):
        if header.strip():
            first_col_idx = i
            break

    # Extract headers and data starting from first non-empty column
    template_headers = [col.strip() for col in raw_headers[first_col_idx:]]
    template_data = [row[first_col_idx:] for row in raw_data]

    df_template = pd.DataFrame(template_data, columns=template_headers)

    # Remove empty rows (where Partner column is empty)
    df_template = df_template[df_template['Partner'].str.strip() != '']

    # ========== LOAD METADATA SHEET ==========
    # Header at row 2 (index 1), data starts at row 3 (index 2)
    metadata_sheet = spreadsheet.worksheet("Metadata")
    metadata_values = metadata_sheet.get_all_values()
    metadata_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(metadata_values[1])]  # Row 2 (index 1)
    metadata_data = metadata_values[2:]
    df_metadata = pd.DataFrame(metadata_data, columns=metadata_headers)

    # ========== LOAD PARTNER-SPECIFIC INFO SHEET ==========
    # Header at row 2 (index 1), data starts at row 3 (index 2)
    partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
    partner_values = partner_sheet.get_all_values()

    # Row 2 has headers, may have empty first column - skip it
    raw_partner_headers = partner_values[1]
    raw_partner_data = partner_values[2:]

    # Find first non-empty column index for partner sheet
    first_partner_col_idx = 0
    for i, header in enumerate(raw_partner_headers):
        if header.strip():
            first_partner_col_idx = i
            break

    # Extract headers and data starting from first non-empty column
    partner_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(raw_partner_headers[first_partner_col_idx:])]
    partner_data = [row[first_partner_col_idx:] for row in raw_partner_data]

    df_partner_info = pd.DataFrame(partner_data, columns=partner_headers)

    # Remove empty rows from partner info (only if Partner column exists)
    if 'Partner' in df_partner_info.columns:
        df_partner_info = df_partner_info[df_partner_info['Partner'].str.strip() != '']

    return df_template, df_metadata, df_partner_info
