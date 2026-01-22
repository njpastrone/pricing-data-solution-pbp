#!/usr/bin/env python3
"""
Check REAL dataset schema - should have 44 columns with new schema
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_pricing_data

print("=" * 80)
print("REAL DATASET SCHEMA CHECK (master_pricing)")
print("=" * 80)
print()

# Load REAL dataset
print("Loading REAL dataset (master_pricing)...")
try:
    df_template, df_metadata, df_partner_info = load_pricing_data('real')
    print(f"✅ Loaded successfully")
except Exception as e:
    print(f"❌ Failed to load: {e}")
    sys.exit(1)

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
    'PBP Markup (Vendor+Add-On, No Tiers)',
    'Data Collection Notes'
]

print("\nNEW SCHEMA COLUMNS CHECK:")
print("-" * 80)
found_count = 0
for col in new_schema_columns:
    if col in df_template.columns:
        non_null = df_template[col].notna().sum()
        print(f"✓ {col:50} ({non_null} values)")
        found_count += 1
    else:
        print(f"✗ {col:50} (MISSING)")

print()
if found_count == len(new_schema_columns):
    print(f"🎉 ALL {len(new_schema_columns)} NEW SCHEMA COLUMNS FOUND!")
elif found_count > 0:
    print(f"⚠️ PARTIAL: {found_count}/{len(new_schema_columns)} new columns found")
else:
    print(f"❌ NO NEW SCHEMA COLUMNS FOUND - Still using old schema")

print()
print("=" * 80)

# Check if we're at 44 columns
if len(df_template.columns) == 44:
    print("✅ PERFECT: 44 columns detected - new schema is active!")
elif len(df_template.columns) > 44:
    print(f"⚠️ MORE THAN EXPECTED: {len(df_template.columns)} columns (expected 44)")
else:
    print(f"⚠️ FEWER THAN EXPECTED: {len(df_template.columns)} columns (expected 44)")

print("=" * 80)
