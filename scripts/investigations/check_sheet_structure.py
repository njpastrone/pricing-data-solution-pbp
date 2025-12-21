"""
Script to investigate the actual Google Sheets structure.
Lists all available sheets in both demo and real datasets.
"""

import sys
import os

# Add parent directory to path so we can import from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from src.data_loader import connect_to_sheets, DATASET_CONFIGS

def check_sheets(dataset_name):
    """Check what sheets exist in the specified dataset."""
    print(f"\n{'='*60}")
    print(f"Checking {dataset_name.upper()} Dataset")
    print(f"{'='*60}")

    config = DATASET_CONFIGS[dataset_name]
    print(f"Dataset: {config['name']}")
    print(f"URL: {config['url']}")
    print(f"Description: {config['description']}")

    try:
        gc = connect_to_sheets()
        spreadsheet = gc.open_by_url(config['url'])

        print(f"\nSpreadsheet Title: {spreadsheet.title}")
        print(f"\nAvailable Sheets ({len(spreadsheet.worksheets())} total):")
        print("-" * 60)

        for i, worksheet in enumerate(spreadsheet.worksheets(), 1):
            print(f"{i}. {worksheet.title}")
            print(f"   - Rows: {worksheet.row_count}")
            print(f"   - Columns: {worksheet.col_count}")

            # Try to get first few rows to show structure
            try:
                values = worksheet.get_all_values()
                if values:
                    print(f"   - First row: {values[0][:5] if len(values[0]) > 5 else values[0]}")  # Show first 5 columns
                    if len(values) > 1:
                        print(f"   - Second row: {values[1][:5] if len(values[1]) > 5 else values[1]}")
            except Exception as e:
                print(f"   - Error reading values: {e}")

            print()

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def main():
    """Main function to check both datasets."""
    print("\n" + "="*60)
    print("GOOGLE SHEETS STRUCTURE INVESTIGATION")
    print("="*60)

    # Check demo dataset
    check_sheets('demo')

    # Check real dataset
    check_sheets('real')

    print("\n" + "="*60)
    print("Investigation Complete")
    print("="*60)


if __name__ == "__main__":
    main()
