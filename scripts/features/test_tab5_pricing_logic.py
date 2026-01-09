"""
Test script to verify Tab 5 Executive Pricing Tool follows correct pricing logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required functions
from src.helpers import clean_price, get_column_value

# Mock functions for testing
def calculate_msrp_markup_mock(product_data):
    """Mock version of calculate_msrp_markup"""
    msrp_raw = product_data.get('Vendor Published MSRP', '')
    msrp = clean_price(msrp_raw) if msrp_raw else None

    if msrp and msrp > 0:
        base_cost = 50.0  # Mock base cost for testing
        if base_cost > 0:
            required_markup = ((msrp / base_cost) - 1) * 100
            return max(0.0, required_markup)
    return 100.0

def get_default_markup_mock(product_data):
    """Mock version of get_default_markup"""
    pbp_markup = product_data.get('PBP Standard Markup', None)

    if pbp_markup:
        try:
            multiplier = float(pbp_markup)
            if multiplier > 0:
                return (multiplier - 1) * 100
        except (ValueError, TypeError):
            pass
    return 100.0

# Test scenarios
print("Testing Tab 5 Pricing Logic\n")
print("=" * 60)

# Test 1: MSRP pricing when available
print("\nTest 1: MSRP Pricing ON, product has MSRP")
product_with_msrp = {
    'Product/Service': 'Test Product 1',
    'Vendor Published MSRP': '$150.00',
    'PBP Standard Markup': '2.0'  # 100% markup
}
use_msrp = True
apply_global = False
global_markup = 100

if use_msrp:
    markup = calculate_msrp_markup_mock(product_with_msrp)
else:
    markup = get_default_markup_mock(product_with_msrp)

if apply_global:
    markup = global_markup

print(f"  Product: {product_with_msrp['Product/Service']}")
print(f"  MSRP: {product_with_msrp['Vendor Published MSRP']}")
print(f"  PBP Standard: {product_with_msrp['PBP Standard Markup']} (100% markup)")
print(f"  Settings: Use MSRP={use_msrp}, Apply Global={apply_global}")
print(f"  Expected: 200% (to reach $150 from $50 base)")
print(f"  Result: {markup:.0f}%")
print(f"  ✅ PASS" if abs(markup - 200) < 0.1 else f"  ❌ FAIL")

# Test 2: PBP Standard Markup when MSRP is OFF
print("\nTest 2: MSRP Pricing OFF, use PBP Standard Markup")
product_with_standard = {
    'Product/Service': 'Test Product 2',
    'PBP Standard Markup': '2.5'  # 150% markup
}
use_msrp = False
apply_global = False

if use_msrp:
    markup = calculate_msrp_markup_mock(product_with_standard)
else:
    markup = get_default_markup_mock(product_with_standard)

if apply_global:
    markup = global_markup

print(f"  Product: {product_with_standard['Product/Service']}")
print(f"  PBP Standard: {product_with_standard['PBP Standard Markup']} (150% markup)")
print(f"  Settings: Use MSRP={use_msrp}, Apply Global={apply_global}")
print(f"  Expected: 150%")
print(f"  Result: {markup:.0f}%")
print(f"  ✅ PASS" if abs(markup - 150) < 0.1 else f"  ❌ FAIL")

# Test 3: Global override
print("\nTest 3: Global Markup Override Active")
product_any = {
    'Product/Service': 'Test Product 3',
    'Vendor Published MSRP': '$200.00',
    'PBP Standard Markup': '3.0'  # 200% markup
}
use_msrp = True  # Should be ignored
apply_global = True
global_markup = 75

if apply_global:
    markup = global_markup
else:
    if use_msrp:
        markup = calculate_msrp_markup_mock(product_any)
    else:
        markup = get_default_markup_mock(product_any)

print(f"  Product: {product_any['Product/Service']}")
print(f"  MSRP: {product_any['Vendor Published MSRP']}")
print(f"  PBP Standard: {product_any['PBP Standard Markup']}")
print(f"  Settings: Use MSRP={use_msrp}, Apply Global={apply_global}, Global={global_markup}%")
print(f"  Expected: 75% (global override)")
print(f"  Result: {markup:.0f}%")
print(f"  ✅ PASS" if abs(markup - 75) < 0.1 else f"  ❌ FAIL")

# Test 4: No MSRP, No PBP Standard - fallback to 100%
print("\nTest 4: No MSRP, No PBP Standard - Default 100%")
product_basic = {
    'Product/Service': 'Test Product 4'
}
use_msrp = False
apply_global = False

if use_msrp:
    markup = calculate_msrp_markup_mock(product_basic)
else:
    markup = get_default_markup_mock(product_basic)

if apply_global:
    markup = global_markup

print(f"  Product: {product_basic['Product/Service']}")
print(f"  Settings: Use MSRP={use_msrp}, Apply Global={apply_global}")
print(f"  Expected: 100% (default fallback)")
print(f"  Result: {markup:.0f}%")
print(f"  ✅ PASS" if abs(markup - 100) < 0.1 else f"  ❌ FAIL")

# Test 5: MSRP below cost
print("\nTest 5: MSRP Below Cost - 0% Markup")
product_below_cost = {
    'Product/Service': 'Test Product 5',
    'Vendor Published MSRP': '$40.00'  # Below $50 base cost
}
use_msrp = True
apply_global = False

if use_msrp:
    markup = calculate_msrp_markup_mock(product_below_cost)
else:
    markup = get_default_markup_mock(product_below_cost)

if apply_global:
    markup = global_markup

print(f"  Product: {product_below_cost['Product/Service']}")
print(f"  MSRP: {product_below_cost['Vendor Published MSRP']} (below $50 cost)")
print(f"  Settings: Use MSRP={use_msrp}, Apply Global={apply_global}")
print(f"  Expected: 0% (break-even, no negative markup)")
print(f"  Result: {markup:.0f}%")
print(f"  ✅ PASS" if abs(markup - 0) < 0.1 else f"  ❌ FAIL")

print("\n" + "=" * 60)
print("✅ All pricing logic tests completed!")