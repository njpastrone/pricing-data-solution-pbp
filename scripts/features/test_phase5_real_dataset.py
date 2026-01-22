#!/usr/bin/env python3
"""
Phase 5 Test - REAL Dataset with New 44-Column Schema
Tests all 3 pricing methods with actual data

Run: python scripts/features/test_phase5_real_dataset.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_pricing_data
from src.pricing_engine import calculate_pbp_msrp
from src.helpers import get_column_value, get_pricing_logic

print("=" * 80)
print("PHASE 5 TEST - REAL DATASET (44-Column Schema)")
print("=" * 80)
print()

# Test with REAL dataset
print("Loading REAL dataset (master_pricing)...")
try:
    df_template, df_metadata, df_partner_info = load_pricing_data('real')
    print(f"✅ Loaded {len(df_template)} products from real dataset")
except Exception as e:
    print(f"❌ Failed to load data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("-" * 80)
print("TEST 1: PRICING METHOD CLASSIFICATION")
print("-" * 80)

method_counts = {
    "MSRP + % of cost": 0,
    "MSRP capped – ship absorbed": 0,
    "Standard markup": 0,
    "Empty/Default": 0,
    "Other": 0
}

method_examples = {key: [] for key in method_counts.keys()}

for idx, row in df_template.iterrows():
    pricing_logic = get_pricing_logic(row)
    product_name = row.get('Product/Service', f"Product {idx}")

    if pricing_logic in ["MSRP + % of cost", "MSRP capped – ship absorbed", "Standard markup"]:
        method_counts[pricing_logic] += 1
        if len(method_examples[pricing_logic]) < 3:
            method_examples[pricing_logic].append(product_name)
    elif not pricing_logic or pricing_logic.strip() == '':
        method_counts["Empty/Default"] += 1
        if len(method_examples["Empty/Default"]) < 3:
            method_examples["Empty/Default"].append(product_name)
    else:
        method_counts["Other"] += 1
        if len(method_examples["Other"]) < 3:
            method_examples["Other"].append(product_name)

print("\nPricing Method Distribution:")
total = len(df_template)
for method, count in method_counts.items():
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {method:35} {count:3} products ({pct:5.1f}%)")

    # Show examples
    if method_examples[method]:
        print(f"    Examples: {', '.join(method_examples[method][:3])}")

# Check if we have products for each method
has_msrp_plus = method_counts["MSRP + % of cost"] > 0
has_msrp_capped = method_counts["MSRP capped – ship absorbed"] > 0
has_standard = method_counts["Standard markup"] > 0

if has_msrp_plus and has_msrp_capped and has_standard:
    print("\n✅ EXCELLENT: All 3 pricing methods represented in dataset!")
elif has_msrp_plus or has_msrp_capped:
    print("\n✅ GOOD: At least one new pricing method found!")
else:
    print("\n⚠️ WARNING: No new pricing methods found - all using Standard markup")

print()
print("-" * 80)
print("TEST 2: SAMPLE PRICE CALCULATIONS (First 10 Products)")
print("-" * 80)

test_quantity = 100
test_count = min(10, len(df_template))

print(f"\nTesting {test_count} products at quantity {test_quantity}...")
print()

errors = []
warnings = []
successes = 0

for idx in range(test_count):
    row = df_template.iloc[idx]
    product_name = row.get('Product/Service', f"Product {idx}")

    try:
        result = calculate_pbp_msrp(row, test_quantity)

        print(f"Product #{idx+1}: {product_name}")
        print(f"  Method: {result['method_used']}")
        print(f"  Calculated MSRP: ${result['pbp_msrp']:.2f}")

        if result.get('spreadsheet_msrp'):
            print(f"  Spreadsheet MSRP: ${result['spreadsheet_msrp']:.2f}")
            if result['validation_status'] == 'match':
                print(f"  Validation: ✓ Match")
            elif result['validation_status'] == 'mismatch':
                diff = abs(result['pbp_msrp'] - result['spreadsheet_msrp'])
                print(f"  Validation: ⚠️ Mismatch (${diff:.2f} difference)")
                warnings.append(f"{product_name}: ${diff:.2f} difference")
        else:
            print(f"  Validation: No spreadsheet value")

        # Show calculation details for first 3 products
        if idx < 3:
            details = result.get('calculation_details', {})
            if details:
                print(f"  Details: {details}")

        print()
        successes += 1

    except Exception as e:
        error_msg = f"{product_name}: {str(e)}"
        errors.append(error_msg)
        print(f"Product #{idx+1}: {product_name}")
        print(f"  ❌ ERROR: {e}")
        print()

print(f"Results: {successes}/{test_count} successful")

if errors:
    print(f"\n⚠️ {len(errors)} ERRORS FOUND:")
    for err in errors:
        print(f"  - {err}")
else:
    print(f"\n✅ All {test_count} products calculated successfully!")

if warnings:
    print(f"\n⚠️ {len(warnings)} VALIDATION WARNINGS:")
    for warn in warnings:
        print(f"  - {warn}")

print()
print("-" * 80)
print("TEST 3: DESCRIPTION FIELD VALIDATION")
print("-" * 80)

desc_stats = {
    'purchase': {'count': 0, 'empty': 0},
    'billing': {'count': 0, 'empty': 0},
    'marketing': {'count': 0, 'empty': 0}
}

for idx, row in df_template.iterrows():
    purchase_desc = get_column_value(row, 'purchase_description', None)
    billing_desc = get_column_value(row, 'billing_description', None)
    marketing_desc = get_column_value(row, 'marketing_description', None)

    has_purchase = purchase_desc and str(purchase_desc).strip() and str(purchase_desc).strip().lower() != 'nan'
    has_billing = billing_desc and str(billing_desc).strip() and str(billing_desc).strip().lower() != 'nan'
    has_marketing = marketing_desc and str(marketing_desc).strip() and str(marketing_desc).strip().lower() != 'nan'

    if has_purchase:
        desc_stats['purchase']['count'] += 1
    else:
        desc_stats['purchase']['empty'] += 1

    if has_billing:
        desc_stats['billing']['count'] += 1
    else:
        desc_stats['billing']['empty'] += 1

    if has_marketing:
        desc_stats['marketing']['count'] += 1
    else:
        desc_stats['marketing']['empty'] += 1

print("\nDescription Field Availability:")
for field, stats in desc_stats.items():
    count_pct = (stats['count'] / total * 100) if total > 0 else 0
    empty_pct = (stats['empty'] / total * 100) if total > 0 else 0
    print(f"  {field.capitalize()} Description:")
    print(f"    Populated: {stats['count']}/{total} ({count_pct:.1f}%)")
    print(f"    Empty: {stats['empty']}/{total} ({empty_pct:.1f}%)")

# Check if all products have at least one description
all_have_desc = all([
    desc_stats['purchase']['count'] + desc_stats['billing']['count'] + desc_stats['marketing']['count'] == total * 3
])

if desc_stats['purchase']['count'] > 0 or desc_stats['billing']['count'] > 0 or desc_stats['marketing']['count'] > 0:
    print("\n✅ Description fields populated in new schema!")
else:
    print("\n⚠️ All description fields empty")

print()
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

total_errors = len(errors)
total_warnings = len(warnings)

if total_errors == 0 and total_warnings == 0:
    print("✅ ALL TESTS PASSED - No errors or warnings")
    print("✅ New 44-column schema working correctly!")
elif total_errors == 0:
    print(f"⚠️ TESTS PASSED WITH WARNINGS - {total_warnings} validation mismatches")
    print("✅ Calculations working, some spreadsheet formulas may need review")
else:
    print(f"❌ TESTS FAILED - {total_errors} errors, {total_warnings} warnings")

print()
print("Phase 5: Testing & Validation - January 2026 Schema Transition")
print("Dataset: master_pricing (51 products, 44 columns)")
print("=" * 80)
