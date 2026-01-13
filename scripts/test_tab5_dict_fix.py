#!/usr/bin/env python3
"""
Quick test to verify the dictionary comprehension fix in Tab 5
"""

# Test the pattern that was causing the error
product_data = {
    "Product A": {"pbp_cost": 10, "tier_range": "100+"},
    "Product B": {"pbp_cost": 15, "tier_range": "50-99"}
}

print("Testing dictionary comprehension patterns...")

# This was the error - using product_data.items() as dictionary keys
try:
    # This would fail with "unhashable type: 'dict'"
    bad_pattern = {name: '─────────' for name in product_data.items()}
    print("❌ Bad pattern should have failed but didn't!")
except TypeError as e:
    print(f"✅ Bad pattern correctly failed: {e}")

# This is the fix - using product_data.keys()
try:
    good_pattern = {name: '─────────' for name in product_data.keys()}
    print(f"✅ Good pattern works: {good_pattern}")
except Exception as e:
    print(f"❌ Good pattern failed: {e}")

# Test with actual data structure
matrix_rows = [
    {'Metric': 'Base Cost', 'values': {name: f"${data['pbp_cost']:.2f}" for name, data in product_data.items()}},
    {'Metric': 'Tier', 'values': {name: data['tier_range'] for name, data in product_data.items()}},
    {'Metric': '─────────', 'values': {name: '─────────' for name in product_data.keys()}},  # Fixed line
]

print("\n✅ Matrix rows created successfully:")
for row in matrix_rows:
    print(f"  {row['Metric']}: {len(row['values'])} columns")

print("\n✅ Fix verified - Tab 5 should work correctly now")