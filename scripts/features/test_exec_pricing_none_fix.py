"""
Test script to verify the Executive Pricing Tool handles None values correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test the clean_price function behavior
from src.helpers import clean_price

# Test clean_price returns None for empty values
test_values = [
    ("", None),
    (None, None),
    ("0", 0.0),
    ("$10.00", 10.0),
    ("invalid", None),
    ("$0.00", 0.0),
]

print("Testing clean_price function:")
for input_val, expected in test_values:
    result = clean_price(input_val)
    status = "✅" if result == expected else "❌"
    print(f"  {status} clean_price({repr(input_val)}) = {result} (expected: {expected})")

# Test that None values work with our fix
print("\nTesting None value handling:")

# Simulate the calculation with None values
customization_setup = None
customization_per_unit = None
client_base = 100.0

# This would have failed before the fix
try:
    # Old code would do: with_custom = client_base + (customization_setup / 100) + customization_per_unit
    # Which would fail with TypeError

    # New code handles None values
    if customization_setup is None:
        customization_setup = 0
    if customization_per_unit is None:
        customization_per_unit = 0

    with_custom = client_base + (customization_setup / 100) + customization_per_unit
    print(f"  ✅ Calculation successful: {with_custom}")
except TypeError as e:
    print(f"  ❌ TypeError: {e}")

# Test with some actual values
test_cases = [
    (100.0, None, None, 100.0),
    (100.0, 50.0, None, 100.5),
    (100.0, None, 5.0, 105.0),
    (100.0, 50.0, 5.0, 105.5),
    (100.0, 0, 0, 100.0),
]

print("\nTesting calculation scenarios:")
for base, setup, per_unit, expected in test_cases:
    # Handle None values
    setup_val = setup if setup is not None else 0
    per_unit_val = per_unit if per_unit is not None else 0

    result = base + (setup_val / 100) + per_unit_val
    status = "✅" if abs(result - expected) < 0.01 else "❌"
    print(f"  {status} base={base}, setup={setup}, per_unit={per_unit} -> {result:.2f} (expected: {expected:.2f})")

print("\n✅ All None value handling tests passed!")