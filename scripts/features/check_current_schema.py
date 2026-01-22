#!/usr/bin/env python3
"""
Check current schema - what columns do we actually have?
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_pricing_data

print("=" * 80)
print("CURRENT SCHEMA CHECK")
print("=" * 80)
print()

# Load demo dataset
print("Loading demo dataset...")
df_template, df_metadata, df_partner_info = load_pricing_data('demo')

print(f"\nTotal products: {len(df_template)}")
print(f"Total columns: {len(df_template.columns)}")
print()

print("Column List:")
print("-" * 80)
for i, col in enumerate(df_template.columns, 1):
    # Check if column has any non-null values
    non_null = df_template[col].notna().sum()
    pct = (non_null / len(df_template) * 100) if len(df_template) > 0 else 0
    print(f"{i:3}. {col:50} ({non_null}/{len(df_template)} = {pct:.0f}% filled)")

print()
print("=" * 80)

# Check for new schema columns
new_schema_columns = [
    'Pricing Logic',
    'Cost Basis (Per Item/Per Package)',
    'Shipping Add-On % (of Cost)',
    'PBP Cost (No Tiers/Tier 1)',
    'Billing Description (to Client)',
    'Purchase Description (to Partner)',
    'Marketing Description (Website)',
    'Pricing Notes',
    'PBP MSRP (Per-Unit, No Tiers, Calculated)',
    'Vendor Markup (No Tiers, Calculated)',
    'PBP Markup (Vendor+Add-On, No Tiers)'
]

print("\nNEW SCHEMA COLUMNS CHECK:")
print("-" * 80)
for col in new_schema_columns:
    if col in df_template.columns:
        non_null = df_template[col].notna().sum()
        print(f"✓ {col:50} ({non_null} values)")
    else:
        print(f"✗ {col:50} (MISSING)")

print()
print("=" * 80)
