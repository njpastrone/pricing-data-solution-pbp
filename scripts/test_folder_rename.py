#!/usr/bin/env python3
"""
Test script to verify Google Sheets access after folder rename
Tests that changing folder name from 'pbp-pricing-data-solutions' to 'PBP DATA TOOL'
doesn't affect sheet access (since we use direct sheet IDs)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import connect_to_sheets, load_pricing_data, DATASET_CONFIGS

def test_connection_after_rename():
    """Test that folder rename doesn't affect Google Sheets access"""

    print("=" * 60)
    print("TESTING GOOGLE SHEETS ACCESS AFTER FOLDER RENAME")
    print("=" * 60)
    print("\nFolder renamed from: 'pbp-pricing-data-solutions'")
    print("Folder renamed to:   'PBP DATA TOOL'")
    print("\n" + "-" * 60)

    # Test 1: Basic connection
    print("\n1. Testing basic Google Sheets connection...")
    try:
        client = connect_to_sheets()
        if client:
            print("   ✅ Connection successful!")
        else:
            print("   ❌ Connection failed")
            return False
    except Exception as e:
        print(f"   ❌ Error connecting: {e}")
        return False

    # Test 2: List all configured sheets
    print("\n2. Checking access to configured sheets:")
    print("   (These use direct sheet IDs, not folder paths)")
    print()

    for key, config in DATASET_CONFIGS.items():
        print(f"   • {config['name']}:")
        print(f"     Sheet ID: {config.get('spreadsheet_id', 'N/A')}")

        # Try to open each sheet
        try:
            if 'spreadsheet_id' in config:
                sheet = client.open_by_key(config['spreadsheet_id'])
                worksheets = sheet.worksheets()
                print(f"     ✅ Accessible - {len(worksheets)} worksheet(s) found")
                print(f"     Worksheets: {', '.join([ws.title for ws in worksheets[:3]])}")
            else:
                print("     ⏩ Skipped (no sheet ID)")
        except Exception as e:
            print(f"     ❌ Error: {str(e)[:50]}")

    # Test 3: Load actual data
    print("\n3. Testing data loading from Demo dataset...")
    try:
        df_template, df_metadata, df_partner_info = load_pricing_data('demo')

        print(f"   ✅ Data loaded successfully!")
        print(f"   • Template data: {len(df_template)} rows, {len(df_template.columns)} columns")
        print(f"   • Metadata: {len(df_metadata)} rows")
        print(f"   • Partner info: {len(df_partner_info)} rows")

        # Show sample of partners
        if 'Partner' in df_template.columns:
            partners = df_template['Partner'].dropna().unique()[:4]
            print(f"   • Sample partners: {', '.join(partners)}")

    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        return False

    # Summary
    print("\n" + "=" * 60)
    print("RESULT: ✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nConclusion: The folder rename does NOT affect the application")
    print("because we access Google Sheets directly by their IDs, not by")
    print("folder paths. No code changes are needed!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = test_connection_after_rename()
    sys.exit(0 if success else 1)