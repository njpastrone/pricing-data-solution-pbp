"""
Test both demo and real datasets with new 'Data' sheet name
"""

import gspread
from google.oauth2.service_account import Credentials
import toml
import pandas as pd

# Load secrets
secrets = toml.load('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp/.streamlit/secrets.toml')

DATASETS = {
    'demo': 'https://docs.google.com/spreadsheets/d/1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs',
    'real': 'https://docs.google.com/spreadsheets/d/1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms'
}

print("Testing both datasets with new 'Data' sheet structure...\n")

creds_info = secrets['gcp_service_account']
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

for dataset_name, url in DATASETS.items():
    print(f"=" * 60)
    print(f"Testing {dataset_name.upper()} dataset")
    print(f"=" * 60)

    try:
        spreadsheet = gc.open_by_url(url)

        # Check all worksheets
        worksheets = spreadsheet.worksheets()
        print(f"Spreadsheet: {spreadsheet.title}")
        print(f"Total sheets: {len(worksheets)}")
        print("\nAvailable sheets:")
        for sheet in worksheets:
            print(f"  - {sheet.title}")

        # Try to load Data sheet
        print("\nLoading 'Data' sheet...")
        data_sheet = spreadsheet.worksheet("Data")
        data_values = data_sheet.get_all_values()

        # Get headers from row 6 (index 5)
        headers = data_values[5]
        data_rows = data_values[6:]

        # Find first non-empty column
        first_col_idx = 0
        for i, header in enumerate(headers):
            if header.strip():
                first_col_idx = i
                break

        # Extract data
        clean_headers = [col.strip() for col in headers[first_col_idx:]]
        clean_data = [row[first_col_idx:] for row in data_rows]

        df = pd.DataFrame(clean_data, columns=clean_headers)
        df = df[df['Partner'].str.strip() != '']

        print(f"  ✓ Data sheet loaded successfully")
        print(f"  ✓ Products: {len(df)}")
        print(f"  ✓ Partners: {len(df['Partner'].unique())}")
        print(f"  ✓ Partner list: {', '.join(df['Partner'].unique())}")

        # Try to load Metadata sheet
        print("\nLoading 'Metadata' sheet...")
        metadata_sheet = spreadsheet.worksheet("Metadata")
        metadata_values = metadata_sheet.get_all_values()
        print(f"  ✓ Metadata sheet loaded ({len(metadata_values)} rows)")

        # Try to load Partner-Specific Info sheet
        print("\nLoading 'Partner-Specific Info' sheet...")
        partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
        partner_values = partner_sheet.get_all_values()
        print(f"  ✓ Partner-Specific Info sheet loaded ({len(partner_values)} rows)")

        print(f"\n✅ {dataset_name.upper()} DATASET: ALL TESTS PASSED\n")

    except Exception as e:
        print(f"\n❌ {dataset_name.upper()} DATASET: FAILED")
        print(f"Error: {str(e)}\n")

print("=" * 60)
print("Test complete!")
