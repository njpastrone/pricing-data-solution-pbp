#!/usr/bin/env python3
"""
Quick Phase 5 test - Direct Python execution (no Streamlit)
Tests pricing methods and description fallbacks

Run: python scripts/features/test_phase5_quick.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data_loader import load_pricing_data
from src.pricing_engine import calculate_pbp_msrp
from src.helpers import get_column_value, get_pricing_logic

print("=" * 80)
print("PHASE 5 QUICK TEST - Pricing Methods & Description Fallbacks")
print("=" * 80)
print()

# Test with demo dataset
print("Loading demo dataset...")
try:
    df_template, df_metadata, df_partner_info = load_pricing_data('demo')
    print(f"✅ Loaded {len(df_template)} products from demo dataset")
except Exception as e:
    print(f"❌ Failed to load data: {e}")
    sys.exit(1)

print()
print("-" * 80)
print("TEST 1: PRICING METHOD CLASSIFICATION")
print("-" * 80)

method_counts = {
    "MSRP + % of cost": 0,
    "MSRP capped – ship absorbed": 0,
    "Standard markup": 0,
    "Empty/Default": 0
}

for idx, row in df_template.iterrows():
    pricing_logic = get_pricing_logic(row)

    if pricing_logic in ["MSRP + % of cost", "MSRP capped – ship absorbed", "Standard markup"]:
        method_counts[pricing_logic] += 1
    else:
        method_counts["Empty/Default"] += 1

print("\nPricing Method Distribution:")
for method, count in method_counts.items():
    pct = (count / len(df_template) * 100) if len(df_template) > 0 else 0
    print(f"  {method}: {count} products ({pct:.1f}%)")

print()
print("-" * 80)
print("TEST 2: SAMPLE PRICE CALCULATIONS")
print("-" * 80)

test_quantity = 100
test_count = min(5, len(df_template))  # Test first 5 products

print(f"\nTesting {test_count} products at quantity {test_quantity}...")
print()

errors = []
warnings = []

for idx in range(test_count):
    row = df_template.iloc[idx]
    product_name = get_column_value(row, 'product_service_name', f"Product {idx}")

    try:
        result = calculate_pbp_msrp(row, test_quantity)

        print(f"Product: {product_name}")
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

        print()

    except Exception as e:
        error_msg = f"{product_name}: {str(e)}"
        errors.append(error_msg)
        print(f"Product: {product_name}")
        print(f"  ❌ ERROR: {e}")
        print()

if errors:
    print(f"\n⚠️ {len(errors)} ERRORS FOUND:")
    for err in errors:
        print(f"  - {err}")
else:
    print(f"\n✓ All {test_count} products calculated successfully")

if warnings:
    print(f"\n⚠️ {len(warnings)} VALIDATION WARNINGS:")
    for warn in warnings:
        print(f"  - {warn}")

print()
print("-" * 80)
print("TEST 3: DESCRIPTION FIELD AVAILABILITY")
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

    # Check if values exist and are not empty/NaN
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
total = len(df_template)
for field, stats in desc_stats.items():
    count_pct = (stats['count'] / total * 100) if total > 0 else 0
    empty_pct = (stats['empty'] / total * 100) if total > 0 else 0
    print(f"  {field.capitalize()} Description:")
    print(f"    Populated: {stats['count']}/{total} ({count_pct:.1f}%)")
    print(f"    Empty: {stats['empty']}/{total} ({empty_pct:.1f}%)")

print()
print("-" * 80)
print("TEST 4: DESCRIPTION FALLBACK LOGIC")
print("-" * 80)

# Test invoice fallback (Billing → Marketing → Product Name)
invoice_fallback = {'billing': 0, 'marketing': 0, 'product_name': 0}

# Test PO fallback (Purchase → Billing → Product Name)
po_fallback = {'purchase': 0, 'billing': 0, 'product_name': 0}

# Test proposal fallback (Marketing → Billing → Product Name)
proposal_fallback = {'marketing': 0, 'billing': 0, 'product_name': 0}

for idx, row in df_template.iterrows():
    product_name = get_column_value(row, 'product_service_name', 'Unknown')
    purchase_desc = get_column_value(row, 'purchase_description', None)
    billing_desc = get_column_value(row, 'billing_description', None)
    marketing_desc = get_column_value(row, 'marketing_description', None)

    has_purchase = purchase_desc and str(purchase_desc).strip() and str(purchase_desc).strip().lower() != 'nan'
    has_billing = billing_desc and str(billing_desc).strip() and str(billing_desc).strip().lower() != 'nan'
    has_marketing = marketing_desc and str(marketing_desc).strip() and str(marketing_desc).strip().lower() != 'nan'

    # Invoice: Billing → Marketing → Name
    if has_billing:
        invoice_fallback['billing'] += 1
    elif has_marketing:
        invoice_fallback['marketing'] += 1
    else:
        invoice_fallback['product_name'] += 1

    # PO: Purchase → Billing → Name
    if has_purchase:
        po_fallback['purchase'] += 1
    elif has_billing:
        po_fallback['billing'] += 1
    else:
        po_fallback['product_name'] += 1

    # Proposal: Marketing → Billing → Name
    if has_marketing:
        proposal_fallback['marketing'] += 1
    elif has_billing:
        proposal_fallback['billing'] += 1
    else:
        proposal_fallback['product_name'] += 1

print("\nInvoice Description Sources (Billing → Marketing → Name):")
for source, count in invoice_fallback.items():
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {source}: {count} ({pct:.1f}%)")

print("\nPO Description Sources (Purchase → Billing → Name):")
for source, count in po_fallback.items():
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {source}: {count} ({pct:.1f}%)")

print("\nProposal Description Sources (Marketing → Billing → Name):")
for source, count in proposal_fallback.items():
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {source}: {count} ({pct:.1f}%)")

print()
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

total_errors = len(errors)
total_warnings = len(warnings)

if total_errors == 0 and total_warnings == 0:
    print("✅ ALL TESTS PASSED - No errors or warnings")
elif total_errors == 0:
    print(f"⚠️ TESTS PASSED WITH WARNINGS - {total_warnings} validation mismatches")
else:
    print(f"❌ TESTS FAILED - {total_errors} errors, {total_warnings} warnings")

print()
print("Phase 5: Testing & Validation - January 2026 Schema Transition")
print("=" * 80)
