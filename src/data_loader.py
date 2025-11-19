"""
Data Loader Module for PBP Pricing App

This module handles all Google Sheets integration:
- Connection to Google Sheets API
- Loading pricing data from multiple datasets (demo or real)
- Data caching with TTL
- Data frame processing and cleanup

The module loads data from 3 sheets:
1. Data: Partner-product pricing data (header at row 6)
2. Metadata: Deliverable field definitions (header at row 2)
3. Partner-Specific Info: Partner configuration (header at row 2)
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os


# Dataset configurations for demo and real pricing data
DATASET_CONFIGS = {
    'demo': {
        'name': 'Demo Data (master_pricing_template_10_14)',
        'url': 'https://docs.google.com/spreadsheets/d/1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs',
        'description': 'Testing template with sample data',
        'spreadsheet_id': '1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs'
    },
    'real': {
        'name': 'Real Pricing Data (master_pricing)',
        'url': 'https://docs.google.com/spreadsheets/d/1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms',
        'description': 'Production pricing data - actively being updated with real partner information',
        'spreadsheet_id': '1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms'
    },
    'saved_proposals': {
        'name': 'Saved Proposals',
        'url': 'https://docs.google.com/spreadsheets/d/1njImhHbLM6WwmdwobgJ0UQLj-4GdOgPYnjP7nDCFTb4',
        'description': 'Storage for user-saved proposals',
        'spreadsheet_id': '1njImhHbLM6WwmdwobgJ0UQLj-4GdOgPYnjP7nDCFTb4'
    },
    'saved_orders': {
        'name': 'Saved Orders',
        'url': 'https://docs.google.com/spreadsheets/d/1pXqBAQOeSvQi1ob8GLc70UhQsM0gwmczYfVWFRPjbao',
        'description': 'Storage for user-saved orders',
        'spreadsheet_id': '1pXqBAQOeSvQi1ob8GLc70UhQsM0gwmczYfVWFRPjbao'
    },
    'saved_matches': {
        'name': 'Saved Matches',
        'url': 'https://docs.google.com/spreadsheets/d/1cU5CW0ydE1BXDjy3TNkbm4TohZ9CA8jR6h4zQPY_9Io',
        'description': 'Storage for confirmed product-to-slide matches',
        'spreadsheet_id': '1cU5CW0ydE1BXDjy3TNkbm4TohZ9CA8jR6h4zQPY_9Io'
    }
}


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
        Supports two authentication methods:
        1. Streamlit secrets (local): st.secrets["gcp_service_account"]
        2. Environment variables (Render): GCP_* environment variables
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Try environment variables first (Render deployment)
    if os.getenv("GCP_PROJECT_ID"):
        creds_info = {
            "type": os.getenv("GCP_TYPE"),
            "project_id": os.getenv("GCP_PROJECT_ID"),
            "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GCP_PRIVATE_KEY"),
            "client_email": os.getenv("GCP_CLIENT_EMAIL"),
            "client_id": os.getenv("GCP_CLIENT_ID"),
            "auth_uri": os.getenv("GCP_AUTH_URI"),
            "token_uri": os.getenv("GCP_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN")
        }
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    # Fall back to Streamlit secrets (local development)
    else:
        try:
            creds_info = st.secrets["gcp_service_account"]
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        except Exception as e:
            raise Exception(f"No Google Cloud credentials found. Please configure either GCP_* environment variables or st.secrets['gcp_service_account']. Error: {e}")

    return gspread.authorize(creds)


@st.cache_data(ttl=300, show_spinner="Loading pricing data from Google Sheets...")  # Cache data for 5 minutes
def load_pricing_data(dataset='demo'):
    """
    Load pricing data from selected Google Sheet dataset (demo or real).
    Loads three sheets: Template, Metadata, Partner-Specific Info
    Returns three DataFrames.

    Args:
        dataset (str): Dataset to load ('demo' or 'real'). Defaults to 'demo'.
            - 'demo': master_pricing_template_10_14 (testing data)
            - 'real': master_pricing (production data)

    Returns:
        tuple: (df_template, df_metadata, df_partner_info)
            - df_template: Product pricing data with tiers
            - df_metadata: Field definitions and metadata
            - df_partner_info: Partner contact information

    Raises:
        Exception: If spreadsheet not found or sheets cannot be loaded
        KeyError: If invalid dataset name provided

    Data Structure:
        Data Sheet:
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
        >>> # Load demo data
        >>> df_template, df_metadata, df_partner_info = load_pricing_data('demo')
        >>> print(len(df_template))
        42  # 42 products loaded

        >>> # Load real production data
        >>> df_template, df_metadata, df_partner_info = load_pricing_data('real')
        >>> print(df_template['Partner'].unique())
        ['Partner X', 'Partner Y']
    """
    gc = connect_to_sheets()

    # Get configuration for selected dataset
    if dataset not in DATASET_CONFIGS:
        raise KeyError(f"Invalid dataset '{dataset}'. Must be 'demo' or 'real'.")

    config = DATASET_CONFIGS[dataset]
    spreadsheet_url = config['url']

    # Open by URL (more reliable than by name)
    spreadsheet = gc.open_by_url(spreadsheet_url)

    # ========== LOAD DATA SHEET ==========
    # Header at row 6 (index 5), data starts at row 7 (index 6)
    template_sheet = spreadsheet.worksheet("Data")
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

    # Check if sheet has enough rows
    if len(metadata_values) < 2:
        # Create empty DataFrame with minimal structure if sheet is empty
        df_metadata = pd.DataFrame()
    else:
        metadata_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(metadata_values[1])]  # Row 2 (index 1)
        metadata_data = metadata_values[2:] if len(metadata_values) > 2 else []
        df_metadata = pd.DataFrame(metadata_data, columns=metadata_headers)

    # ========== LOAD PARTNER-SPECIFIC INFO SHEET ==========
    # Header at row 2 (index 1), data starts at row 3 (index 2)
    partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
    partner_values = partner_sheet.get_all_values()

    # Check if sheet has enough rows
    if len(partner_values) < 2:
        # Create empty DataFrame with minimal structure if sheet is empty
        df_partner_info = pd.DataFrame()
    else:
        # Row 2 has headers, may have empty first column - skip it
        raw_partner_headers = partner_values[1]
        raw_partner_data = partner_values[2:] if len(partner_values) > 2 else []

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
