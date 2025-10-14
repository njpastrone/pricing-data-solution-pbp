"""
Test complete data loading function with the fix
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

def load_pricing_data():
    """
    Load pricing data from master_pricing_template_10_14 Google Sheet.
    Loads three sheets: Template, Metadata, Partner-Specific Info
    Returns three DataFrames.
    """
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    gc = gspread.authorize(creds)

    spreadsheet = gc.open("master_pricing_template_10_14")

    # Load Template sheet (header at row 6, index 5)
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

    # Load Metadata sheet (header at row 2, index 1)
    metadata_sheet = spreadsheet.worksheet("Metadata")
    metadata_values = metadata_sheet.get_all_values()
    metadata_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(metadata_values[1])]
    metadata_data = metadata_values[2:]
    df_metadata = pd.DataFrame(metadata_data, columns=metadata_headers)

    # Load Partner-Specific Info sheet (header at row 2, index 1)
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

# Run the test
print("="*80)
print("Testing complete data loading function...")
print("="*80)

try:
    df_template, df_metadata, df_partner_info = load_pricing_data()

    print("\n✓ Template Sheet:")
    print(f"  Rows: {len(df_template)}")
    print(f"  Columns: {len(df_template.columns)}")
    print(f"  Partners: {df_template['Partner'].unique().tolist()}")
    print(f"  Products: {df_template['Product/Service'].unique().tolist()}")

    print("\n✓ Metadata Sheet:")
    print(f"  Rows: {len(df_metadata)}")
    print(f"  Columns: {len(df_metadata.columns)}")

    print("\n✓ Partner-Specific Info Sheet:")
    print(f"  Rows: {len(df_partner_info)}")
    print(f"  Columns: {list(df_partner_info.columns)}")
    if 'Partner' in df_partner_info.columns:
        print(f"  Partners: {df_partner_info['Partner'].tolist()}")
    else:
        print(f"  Note: 'Partner' column not found in this sheet")

    # Test sample product
    print("\n" + "="*80)
    print("Sample Product Data:")
    print("="*80)
    sample = df_template.iloc[0]
    print(f"Partner: {sample['Partner']}")
    print(f"Product/Service: {sample['Product/Service']}")
    print(f"Pricing Tiers (Y/N): {sample['Pricing Tiers (Y/N)']}")
    print(f"PBP Cost: Tier 1: {sample['PBP Cost: Tier 1']}")
    print(f"Customization Setup Fee: {sample['Customization Setup Fee']}")

    print("\n" + "="*80)
    print("✓✓✓ ALL TESTS PASSED! ✓✓✓")
    print("="*80)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
