#!/usr/bin/env python3
"""
Check Partner POC data in the REAL dataset (master_pricing)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_loader import load_pricing_data, connect_to_sheets
from src.helpers import extract_partner_contacts

def check_real_dataset():
    print("\n" + "="*60)
    print("CHECKING REAL DATASET: master_pricing")
    print("="*60)

    # Load the REAL dataset
    print("\n📊 Loading REAL dataset...")
    df_template, df_metadata, df_partner_info = load_pricing_data('real')

    print(f"✅ Loaded Partner-Specific Info with shape: {df_partner_info.shape}")
    print(f"   Rows: {len(df_partner_info)}, Columns: {len(df_partner_info.columns)}")

    # Show columns
    print("\n📋 Columns in Partner-Specific Info:")
    for i, col in enumerate(df_partner_info.columns):
        print(f"   [{i}] {col}")

    # Check if POC columns exist
    poc_columns = ['POC Name', 'POC Email', 'POC Phone',
                   'POC name', 'POC email', 'POC phone',
                   'Contact Name', 'Contact Email', 'Contact Phone']

    found_poc_cols = []
    for col in df_partner_info.columns:
        if any(poc in col for poc in poc_columns):
            found_poc_cols.append(col)

    if found_poc_cols:
        print(f"\n✅ Found POC columns: {found_poc_cols}")
    else:
        print("\n❌ No POC columns found")

    # Show data
    if not df_partner_info.empty:
        print("\n📊 Partner data (first 5 rows):")
        # Show all columns to see the new data
        import pandas as pd
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        print(df_partner_info.head())

        # Extract partner contacts
        print("\n🔍 Extracting partner contacts...")
        partner_contacts = extract_partner_contacts(df_partner_info)

        if partner_contacts:
            print(f"✅ Extracted {len(partner_contacts)} partner contacts:")
            for partner, info in partner_contacts.items():
                print(f"\n   Partner: {partner}")
                print(f"   - POC Name: {info.get('poc_name', 'N/A')}")
                print(f"   - POC Email: {info.get('poc_email', 'N/A')}")
                print(f"   - POC Phone: {info.get('poc_phone', 'N/A')}")
        else:
            print("❌ No partner contacts extracted")
    else:
        print("\n⚠️ Partner-Specific Info sheet is empty")

if __name__ == "__main__":
    check_real_dataset()