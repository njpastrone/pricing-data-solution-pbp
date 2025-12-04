#!/usr/bin/env python
"""
Quick script to check column names in the spreadsheets
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_pricing_data

# Load demo data
print("Loading DEMO data...")
df_template_demo, _, _ = load_pricing_data('demo')
print("\nDEMO Columns in Data sheet:")
for i, col in enumerate(df_template_demo.columns, 1):
    if 'shipping' in col.lower():
        print(f"  {i}. {col} <-- SHIPPING COLUMN")
    else:
        print(f"  {i}. {col}")

# Load real data
print("\n" + "="*50)
print("Loading REAL data...")
df_template_real, _, _ = load_pricing_data('real')
print("\nREAL Columns in Data sheet:")
for i, col in enumerate(df_template_real.columns, 1):
    if 'shipping' in col.lower():
        print(f"  {i}. {col} <-- SHIPPING COLUMN")
    else:
        print(f"  {i}. {col}")