"""
Read raw data directly from Google Sheets (no caching) to check actual values.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import warnings
warnings.filterwarnings('ignore')

import streamlit as st

# Get connection without using cached data loader
@st.cache_resource
def connect_to_sheets():
    """Direct connection to Google Sheets."""
    import gspread
    import os
    import json

    # Try environment variable first (Render deployment)
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')

    if credentials_json:
        credentials_dict = json.loads(credentials_json)
        gc = gspread.service_account_from_dict(credentials_dict)
    else:
        # Local development - use secrets file
        gc = gspread.service_account(filename='.streamlit/secrets.toml')

    return gc


def read_raw_gronn_product():
    print(f"\n{'='*70}")
    print("RAW DATA CHECK - GRONN UPCYCLED GLASSES")
    print('='*70)

    try:
        gc = connect_to_sheets()

        # Real dataset spreadsheet ID
        spreadsheet_id = '1S3BfpWNdz_CX9rPeC8NWvJ7bOnLQU0TQPu5kJlwI9hc'

        # Open the spreadsheet
        sheet = gc.open_by_key(spreadsheet_id)

        # Get Data worksheet
        worksheet = sheet.worksheet('Data')

        # Get all data (no caching!)
        all_data = worksheet.get_all_values()

        print(f"\n✓ Connected to Google Sheets")
        print(f"✓ Total rows in Data sheet: {len(all_data)}")

        # Headers should be at row 7 (index 6)
        headers = all_data[6]
        print(f"\n✓ Headers at row 7: {len(headers)} columns")

        # Find the columns we care about
        product_col = None
        partner_col = None
        tier_info_col = None
        tier_yn_col = None

        for i, header in enumerate(headers):
            if 'Product' in header and 'Service' in header:
                product_col = i
            elif header == 'Partner':
                partner_col = i
            elif 'Pricing Tiers Info' in header:
                tier_info_col = i
            elif 'Pricing Tiers (Y/N)' in header:
                tier_yn_col = i

        print(f"\nColumn indices:")
        print(f"  Product/Service: {product_col}")
        print(f"  Partner: {partner_col}")
        print(f"  Pricing Tiers (Y/N): {tier_yn_col}")
        print(f"  Pricing Tiers Info: {tier_info_col}")

        # Search for Gronn products
        print(f"\n{'='*70}")
        print("SEARCHING FOR GRØNN PRODUCTS")
        print('='*70)

        gronn_products = []
        for i, row in enumerate(all_data[7:], start=8):  # Start from row 8 (after headers)
            if len(row) > partner_col and 'Grønn' in str(row[partner_col]):
                product_name = row[product_col] if len(row) > product_col else ''
                tier_yn = row[tier_yn_col] if len(row) > tier_yn_col else ''
                tier_info = row[tier_info_col] if len(row) > tier_info_col else ''

                gronn_products.append({
                    'row': i,
                    'product': product_name,
                    'tier_yn': tier_yn,
                    'tier_info': tier_info
                })

        print(f"\nFound {len(gronn_products)} Grønn products:")

        for item in gronn_products:
            print(f"\n{'='*70}")
            print(f"Row {item['row']}: {item['product']}")
            print(f"  Has Tiers (Y/N): {repr(item['tier_yn'])}")
            print(f"  Tier Info: {repr(item['tier_info'])}")

            if item['tier_info']:
                # Parse the tier string character by character to see exact values
                print(f"\n  Analyzing tier string character-by-character:")
                tier_str = str(item['tier_info'])

                # Look for the T2 range specifically
                if 'T2:' in tier_str:
                    t2_start = tier_str.find('T2:')
                    t2_section = tier_str[t2_start:t2_start+30]  # Get next 30 chars
                    print(f"    T2 section: {repr(t2_section)}")

                    # Extract the numbers
                    import re
                    t2_match = re.search(r'T2:\s*(\d+)-(\d+)', tier_str)
                    if t2_match:
                        t2_start_num = t2_match.group(1)
                        t2_end_num = t2_match.group(2)
                        print(f"    T2 range: {t2_start_num} to {t2_end_num}")
                        print(f"    T2 end number is: {len(t2_end_num)} digits")

                        if len(t2_end_num) == 4:
                            print(f"    ⚠️  T2 ends at {t2_end_num} (4 digits - likely 1007 or 1107)")
                            if t2_end_num == '1007':
                                print(f"    ✓ Value is 1007 (NO overlap with T3: 1008+)")
                            elif t2_end_num == '1107':
                                print(f"    ⚠️  Value is 1107 (OVERLAPS with T3: 1008+)")
                            else:
                                print(f"    Value is {t2_end_num}")

                # Look for T3
                if 'T3:' in tier_str:
                    t3_start = tier_str.find('T3:')
                    t3_section = tier_str[t3_start:t3_start+15]
                    print(f"    T3 section: {repr(t3_section)}")

                    t3_match = re.search(r'T3:\s*(\d+)\+', tier_str)
                    if t3_match:
                        t3_start_num = t3_match.group(1)
                        print(f"    T3 starts at: {t3_start_num}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    read_raw_gronn_product()
    print(f"\n{'='*70}\n")
