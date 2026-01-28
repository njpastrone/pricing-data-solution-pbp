"""
Show actual column names in the spreadsheet to understand schema.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import warnings
warnings.filterwarnings('ignore')

from src.data_loader import get_google_sheets_client
import pandas as pd

def show_columns(dataset_name):
    print(f"\n{'='*70}")
    print(f"{dataset_name.upper()} DATASET - RAW COLUMNS")
    print('='*70)

    try:
        client = get_google_sheets_client()

        if dataset_name == 'demo':
            spreadsheet_id = '1wC5SSlpHSzJxTAVnFkjK1fL2WPh8t6Fc70LE0e1C0sc'
        else:  # real
            spreadsheet_id = '1S3BfpWNdz_CX9rPeC8NWvJ7bOnLQU0TQPu5kJlwI9hc'

        # Open sheet
        sheet = client.open_by_key(spreadsheet_id)

        # Get Data sheet
        worksheet = sheet.worksheet('Data')
        data = worksheet.get_all_values()

        # Check multiple possible header rows
        for row_idx in [5, 6, 7]:
            if row_idx < len(data):
                print(f"\nRow {row_idx + 1} (index {row_idx}):")
                headers = data[row_idx]
                print(f"Total columns: {len(headers)}")
                print("\nColumn names:")
                for i, col in enumerate(headers, 1):
                    if col.strip():
                        print(f"  {i:2}. {col}")

        # Find products with 'Tier' in column name
        print(f"\n{'='*70}")
        print("COLUMNS CONTAINING 'TIER'")
        print('='*70)

        # Use header row 6 (index 5) as canonical
        if len(data) > 6:
            headers = data[6]
            tier_cols = [col for col in headers if 'tier' in col.lower()]
            if tier_cols:
                print("\nFound tier-related columns:")
                for col in tier_cols:
                    print(f"  - {col}")
            else:
                print("\nNo columns containing 'tier' found")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    show_columns('real')
    print(f"\n{'='*70}\n")
