#!/usr/bin/env python3
"""
Check raw Google Sheets structure for Partner-Specific Info
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_loader import connect_to_sheets

def check_raw_sheet():
    print("\n" + "="*60)
    print("RAW GOOGLE SHEETS INSPECTION: master_pricing")
    print("="*60)

    client = connect_to_sheets()
    # Use the URL for the real dataset
    spreadsheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1XjdC8l9_mjvNElkY2_Bu6_IXoarfIuVyIjMH5Hfm5Ms')

    # Get Partner-Specific Info sheet
    partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
    all_values = partner_sheet.get_all_values()

    print(f"\n📊 Total rows in sheet: {len(all_values)}")

    # Show first 10 rows to understand structure
    print("\n📋 First 10 rows of raw data:")
    for i, row in enumerate(all_values[:10]):
        # Show first 8 columns of each row
        display_row = row[:8] if len(row) > 8 else row
        print(f"Row {i}: {display_row}")

    # Check for POC columns anywhere
    print("\n🔍 Looking for POC-related headers in all rows...")
    for i, row in enumerate(all_values[:5]):
        for j, cell in enumerate(row):
            if 'POC' in str(cell) or 'Contact' in str(cell) or 'Email' in str(cell) or 'Phone' in str(cell):
                print(f"   Found at Row {i}, Col {j}: '{cell}'")

    # Show column count for each row
    print("\n📊 Column count per row:")
    for i, row in enumerate(all_values[:10]):
        print(f"   Row {i}: {len(row)} columns")

if __name__ == "__main__":
    check_raw_sheet()