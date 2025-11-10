"""
Debug script to check exact structure of both datasets
"""

import gspread
from google.oauth2.service_account import Credentials
import toml

# Load secrets
secrets = toml.load('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp/.streamlit/secrets.toml')

DATASETS = {
    'demo': 'https://docs.google.com/spreadsheets/d/1TSw50v7ydNSDdREkKRaM00LCg3-vj-ZcVNoYL9u8Lxs',
    'real': 'https://docs.google.com/spreadsheets/d/1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms'
}

creds_info = secrets['gcp_service_account']
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

for dataset_name, url in DATASETS.items():
    print(f"\n{'='*70}")
    print(f"DATASET: {dataset_name.upper()}")
    print(f"{'='*70}")

    try:
        spreadsheet = gc.open_by_url(url)

        for sheet_name in ['Data', 'Metadata', 'Partner-Specific Info']:
            print(f"\n--- {sheet_name} Sheet ---")
            try:
                sheet = spreadsheet.worksheet(sheet_name)
                values = sheet.get_all_values()

                print(f"Total rows: {len(values)}")
                print(f"Row count: {sheet.row_count}")
                print(f"Col count: {sheet.col_count}")

                # Show first 10 rows (or less if fewer rows exist)
                print(f"\nFirst {min(10, len(values))} rows:")
                for i, row in enumerate(values[:10], 1):
                    # Show first 5 columns of each row
                    preview = ' | '.join([str(cell)[:20] for cell in row[:5]])
                    print(f"  Row {i}: {preview}")

                # Check specific rows that code expects
                if sheet_name == 'Data':
                    print(f"\nRow 6 (index 5) - Expected headers:")
                    if len(values) > 5:
                        print(f"  {values[5][:10]}")
                    else:
                        print(f"  ❌ ERROR: Not enough rows! Only {len(values)} rows exist.")

                elif sheet_name in ['Metadata', 'Partner-Specific Info']:
                    print(f"\nRow 2 (index 1) - Expected headers:")
                    if len(values) > 1:
                        print(f"  {values[1][:10]}")
                    else:
                        print(f"  ❌ ERROR: Not enough rows! Only {len(values)} rows exist.")

            except Exception as e:
                print(f"❌ Error loading sheet: {str(e)}")

    except Exception as e:
        print(f"❌ Error opening spreadsheet: {str(e)}")

print(f"\n{'='*70}")
print("Debug complete!")
