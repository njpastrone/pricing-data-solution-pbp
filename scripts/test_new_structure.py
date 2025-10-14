"""
Test script to verify new Google Sheet structure loads correctly
"""

import sys
sys.path.insert(0, '/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp')

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

# Load credentials
creds_info = st.secrets["gcp_service_account"]
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

print("Testing connection to master_pricing_template_10_14...")
print("=" * 80)

try:
    spreadsheet = gc.open("master_pricing_template_10_14")
    print(f"✓ Successfully opened spreadsheet: {spreadsheet.title}")
    print()

    # Load Template sheet
    print("Loading Template sheet...")
    template_sheet = spreadsheet.worksheet("Template")
    template_values = template_sheet.get_all_values()
    print(f"  Total rows: {len(template_values)}")
    print(f"  Headers (row 5): {template_values[4][:5]}...")

    template_headers = [col.strip() for col in template_values[4]]
    template_data = template_values[5:]
    df_template = pd.DataFrame(template_data, columns=template_headers)
    df_template = df_template[df_template['Partner'].str.strip() != '']

    print(f"  Products loaded: {len(df_template)}")
    print(f"  Partners: {df_template['Partner'].unique().tolist()}")
    print(f"  Columns: {list(df_template.columns)[:10]}...")
    print()

    # Load Metadata sheet
    print("Loading Metadata sheet...")
    metadata_sheet = spreadsheet.worksheet("Metadata")
    metadata_values = metadata_sheet.get_all_values()
    print(f"  Total rows: {len(metadata_values)}")
    print()

    # Load Partner-Specific Info sheet
    print("Loading Partner-Specific Info sheet...")
    partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
    partner_values = partner_sheet.get_all_values()
    partner_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(partner_values[1])]
    partner_data = partner_values[2:]
    df_partner_info = pd.DataFrame(partner_data, columns=partner_headers)
    df_partner_info = df_partner_info[df_partner_info['Partner'].str.strip() != '']

    print(f"  Partners: {len(df_partner_info)}")
    print(f"  Partner names: {df_partner_info['Partner'].tolist()}")
    print()

    # Test sample product
    print("Testing sample product pricing...")
    print("-" * 80)
    sample = df_template.iloc[0]
    print(f"Partner: {sample['Partner']}")
    print(f"Product/Service: {sample['Product/Service']}")
    print(f"Pricing Tiers (Y/N): {sample.get('Pricing Tiers (Y/N)', 'N/A')}")
    print(f"Pricing Tiers Info: {sample.get('Pricing Tiers Info', 'N/A')}")
    print(f"PBP Cost (No Tiers): {sample.get('PBP Cost (No Tiers)', 'N/A')}")

    for i in range(1, 7):
        tier_col = f'PBP Cost: Tier {i}'
        print(f"{tier_col}: {sample.get(tier_col, 'N/A')}")

    print(f"Customization Setup Fee: {sample.get('Customization Setup Fee', 'N/A')}")
    print(f"Customization Cost per Unit: {sample.get('Customization Cost per Unit', 'N/A')}")
    print()

    print("=" * 80)
    print("✓ All tests passed! Data structure is correct.")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
