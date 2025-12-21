"""
Script to investigate the Partner-Specific Info sheet structure and contents.
"""

import sys
import os

# Add parent directory to path so we can import from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from src.data_loader import connect_to_sheets, DATASET_CONFIGS

def check_partner_info_sheet(dataset_name):
    """Check the Partner-Specific Info sheet contents."""
    print(f"\n{'='*80}")
    print(f"Partner-Specific Info Sheet - {dataset_name.upper()} Dataset")
    print(f"{'='*80}")

    config = DATASET_CONFIGS[dataset_name]

    try:
        gc = connect_to_sheets()
        spreadsheet = gc.open_by_url(config['url'])

        # Get Partner-Specific Info sheet
        partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
        partner_values = partner_sheet.get_all_values()

        print(f"\nTotal rows: {len(partner_values)}")

        # Show first 10 rows to understand structure
        print(f"\nFirst 10 rows:")
        print("-" * 80)
        for i, row in enumerate(partner_values[:10], 1):
            # Show only first 10 columns to keep it readable
            row_preview = row[:10] if len(row) > 10 else row
            # Filter out empty strings for readability
            non_empty = [cell for cell in row_preview if cell.strip()]
            if non_empty:
                print(f"Row {i}: {non_empty}")
            else:
                print(f"Row {i}: [empty]")

        # Try to find header row
        print(f"\n\nLooking for header row...")
        print("-" * 80)
        for i in range(min(10, len(partner_values))):
            row = partner_values[i]
            # Check if row contains header-like content
            non_empty = [cell.strip() for cell in row if cell.strip()]
            if non_empty and any(word in ' '.join(non_empty).lower() for word in ['partner', 'contact', 'email', 'phone', 'name']):
                print(f"\nPotential header at row {i+1}:")
                print(non_empty)

        # Show what the data_loader.py would extract
        print(f"\n\nWhat data_loader.py extracts (header at row 2, index 1):")
        print("-" * 80)
        if len(partner_values) >= 2:
            raw_headers = partner_values[1]  # Row 2 (index 1)
            print(f"Raw headers (row 2): {raw_headers}")

            # Find first non-empty column
            first_col_idx = 0
            for idx, header in enumerate(raw_headers):
                if header.strip():
                    first_col_idx = idx
                    break

            print(f"\nFirst non-empty column index: {first_col_idx}")

            # Extract headers
            headers = [col.strip() for col in raw_headers[first_col_idx:]]
            print(f"\nExtracted headers: {headers[:10]}")  # Show first 10

            # Show first few data rows
            if len(partner_values) > 2:
                print(f"\nFirst 3 data rows:")
                for i in range(2, min(5, len(partner_values))):
                    row_data = partner_values[i][first_col_idx:]
                    # Only show non-empty rows
                    if any(cell.strip() for cell in row_data):
                        print(f"  Row {i+1}: {row_data[:10]}")  # Show first 10 columns

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to check partner info in both datasets."""
    print("\n" + "="*80)
    print("PARTNER-SPECIFIC INFO SHEET INVESTIGATION")
    print("="*80)

    # Check demo dataset
    check_partner_info_sheet('demo')

    # Check real dataset
    check_partner_info_sheet('real')

    print("\n" + "="*80)
    print("Investigation Complete")
    print("="*80)


if __name__ == "__main__":
    main()
