"""
Debug script to understand why tiered products aren't being detected.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import warnings
warnings.filterwarnings('ignore')

from src.data_loader import load_pricing_data
from src.helpers import parse_tier_info, get_column_value
import pandas as pd

def debug_tiered_detection(dataset_name='real'):
    print(f"\n{'='*70}")
    print(f"DEBUG: TIERED PRODUCT DETECTION - {dataset_name.upper()} DATASET")
    print('='*70)

    try:
        df_template, df_metadata, df_partner_info = load_pricing_data(dataset_name)

        print(f"\n✓ Loaded {len(df_template)} products")

        # Show all column names
        print(f"\n{'='*70}")
        print("ALL COLUMN NAMES")
        print('='*70)
        for i, col in enumerate(df_template.columns, 1):
            print(f"{i:3}. {col}")

        # Look for tier-related columns
        print(f"\n{'='*70}")
        print("TIER-RELATED COLUMNS")
        print('='*70)

        tier_related_cols = [col for col in df_template.columns if 'tier' in col.lower()]
        if tier_related_cols:
            print(f"Found {len(tier_related_cols)} tier-related columns:")
            for col in tier_related_cols:
                print(f"  - {col}")
                # Show sample values
                non_null = df_template[col].dropna()
                if len(non_null) > 0:
                    print(f"    Sample values: {list(non_null.head(3).values)}")
        else:
            print("❌ No columns with 'tier' in the name found!")

        # Check for specific column names we expect
        print(f"\n{'='*70}")
        print("CHECKING EXPECTED COLUMN NAMES")
        print('='*70)

        expected_cols = [
            'Pricing Tiers (Y/N)',
            'Pricing Tiers',
            'Tier Range',
            'Tiers',
            'Has Tiers'
        ]

        for expected in expected_cols:
            if expected in df_template.columns:
                print(f"✓ Found: '{expected}'")
                non_null = df_template[expected].dropna()
                print(f"  Non-null values: {len(non_null)}")
                if len(non_null) > 0:
                    unique_vals = non_null.unique()
                    print(f"  Unique values: {list(unique_vals[:10])}")
            else:
                print(f"✗ Missing: '{expected}'")

        # Try different ways to find tiered products
        print(f"\n{'='*70}")
        print("ATTEMPTING TO FIND TIERED PRODUCTS")
        print('='*70)

        # Method 1: Using get_column_value
        print("\nMethod 1: Using get_column_value()")
        tiered_count_1 = 0
        for idx, row in df_template.iterrows():
            has_tiers = get_column_value(row, 'Pricing Tiers (Y/N)', 'Pricing Tiers', 'N')
            if has_tiers == 'Y':
                tiered_count_1 += 1
                if tiered_count_1 <= 3:  # Show first 3
                    product = get_column_value(row, 'Product/Service', 'Product Name', 'Unknown')
                    tier_range = get_column_value(row, 'Tier Range', None, '')
                    print(f"  Found: {product}")
                    print(f"    Has Tiers: {has_tiers}")
                    print(f"    Tier Range: {tier_range}")
        print(f"Total found: {tiered_count_1}")

        # Method 2: Direct column access
        print("\nMethod 2: Direct column access")
        for col in df_template.columns:
            if 'tier' in col.lower() and 'y/n' in col.lower():
                print(f"  Checking column: '{col}'")
                tiered_2 = df_template[df_template[col] == 'Y']
                print(f"  Products with 'Y': {len(tiered_2)}")
                if len(tiered_2) > 0:
                    print(f"  Sample products:")
                    for idx, row in tiered_2.head(3).iterrows():
                        product = row.get('Product/Service', row.get('Product Name', 'Unknown'))
                        print(f"    - {product}")

        # Method 3: Check for tier range values
        print("\nMethod 3: Looking for tier range data")
        for col in df_template.columns:
            if 'tier' in col.lower() and 'range' in col.lower():
                print(f"  Checking column: '{col}'")
                non_empty = df_template[df_template[col].notna() & (df_template[col] != '')]
                print(f"  Non-empty values: {len(non_empty)}")
                if len(non_empty) > 0:
                    print(f"  Sample values:")
                    for idx, row in non_empty.head(3).iterrows():
                        product = row.get('Product/Service', row.get('Product Name', 'Unknown'))
                        tier_range = row[col]
                        print(f"    - {product}: {tier_range}")

        # Method 4: Show raw data for first product with any tier info
        print(f"\n{'='*70}")
        print("RAW DATA FOR PRODUCTS WITH TIER INFO")
        print('='*70)

        found_any = False
        for idx, row in df_template.iterrows():
            # Check if any column has tier-related data
            has_tier_data = False
            for col in df_template.columns:
                if 'tier' in col.lower():
                    val = row.get(col, '')
                    if pd.notna(val) and str(val).strip() not in ['', 'N', 'NA']:
                        has_tier_data = True
                        break

            if has_tier_data:
                found_any = True
                product = row.get('Product/Service', row.get('Product Name', 'Unknown'))
                print(f"\nProduct: {product}")
                print(f"Tier-related columns:")
                for col in df_template.columns:
                    if 'tier' in col.lower():
                        val = row.get(col, '')
                        print(f"  {col}: {repr(val)}")

                # Only show first one
                break

        if not found_any:
            print("\n❌ No products found with ANY tier-related data!")
            print("\nThis suggests:")
            print("  1. The column names may have changed")
            print("  2. The data may be in a different format")
            print("  3. The header row detection may be incorrect")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_tiered_detection('real')
    print(f"\n{'='*70}\n")
