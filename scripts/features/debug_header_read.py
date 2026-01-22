#!/usr/bin/env python3
"""
Debug script to see what we're actually reading from the spreadsheet
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import connect_to_sheets, DATASET_CONFIGS

print("=" * 80)
print("DEBUG: HEADER ROW INSPECTION")
print("=" * 80)
print()

# Connect to sheets
gc = connect_to_sheets()
print("✓ Connected to Google Sheets")
print()

# Load demo dataset
config = DATASET_CONFIGS['demo']
spreadsheet = gc.open_by_url(config['url'])
template_sheet = spreadsheet.worksheet("Data")
template_values = template_sheet.get_all_values()

print(f"Total rows in sheet: {len(template_values)}")
print()

# Check rows 1-10
for i in range(min(10, len(template_values))):
    row = template_values[i]
    non_empty = sum(1 for cell in row if cell.strip())
    print(f"Row {i+1} (index {i}): {non_empty} non-empty cells")
    # Show first 5 cells
    print(f"  First 5 cells: {row[:5]}")
    print()

print("-" * 80)
print("CHECKING ROW 7 (INDEX 6) - NEW HEADER ROW")
print("-" * 80)

if len(template_values) > 6:
    headers_row = template_values[6]
    print(f"Full row 7 (index 6): {len(headers_row)} cells")
    print()

    # Find first non-empty
    first_non_empty_idx = None
    for i, cell in enumerate(headers_row):
        if cell.strip():
            first_non_empty_idx = i
            break

    if first_non_empty_idx is not None:
        print(f"First non-empty cell at index: {first_non_empty_idx}")
        print(f"Headers starting from index {first_non_empty_idx}:")
        print()

        headers = headers_row[first_non_empty_idx:]
        for i, header in enumerate(headers[:10]):  # Show first 10
            print(f"  {i+1}. {repr(header)}")
    else:
        print("⚠️ No non-empty cells found in row 7!")
else:
    print("⚠️ Sheet has fewer than 7 rows!")

print()
print("=" * 80)
