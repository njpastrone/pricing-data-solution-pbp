"""
Unit Tests for MOQ/MOV Calculation Logic
Tests the disaggregated MOQ/MOV schema implementation.

Run with: streamlit run scripts/features/test_moq_mov_calculation.py
"""

import sys
import os
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.helpers import (
    parse_moq_value,
    parse_mov_value,
    convert_mov_to_moq,
    calculate_moq
)

# ============================================================
# TEST SUITE
# ============================================================

def test_mov_to_quantity_conversion():
    """Test 1: MOV → quantity conversion"""
    st.subheader("Test 1: MOV → Quantity Conversion")

    # Test case 1: $2000 / $30 = 67 (ceiling)
    result = convert_mov_to_moq(2000.0, 30.0)
    expected = 67
    status = "✅ PASS" if result == expected else "❌ FAIL"
    st.write(f"{status} - MOV $2000 / $30 = {result} units (expected {expected})")

    # Test case 2: $1500 / $25 = 60 (exact)
    result = convert_mov_to_moq(1500.0, 25.0)
    expected = 60
    status = "✅ PASS" if result == expected else "❌ FAIL"
    st.write(f"{status} - MOV $1500 / $25 = {result} units (expected {expected})")

    # Test case 3: $1000 / $33 = 31 (ceiling of 30.3)
    result = convert_mov_to_moq(1000.0, 33.0)
    expected = 31
    status = "✅ PASS" if result == expected else "❌ FAIL"
    st.write(f"{status} - MOV $1000 / $33 = {result} units (expected {expected})")

    st.divider()


def test_all_four_fields_present():
    """Test 2: All 4 fields present - verify max wins"""
    st.subheader("Test 2: All 4 Fields Present")

    product_data = {
        'MOQ (Partner)': 50,
        'MOV (Partner)': '$1,500',
        'MOQ (PBP)': 75,
        'MOV (PBP)': '$2,000'
    }

    result = calculate_moq(25.0, product_data)

    st.write("**Spreadsheet Data:**")
    st.json(product_data)
    st.write("**Unit Price:** $25")
    st.write("**Result:**")
    st.json({
        'moq': result['moq'],
        'source': result['breakdown']['source'],
        'display_text': result['display_text']
    })

    expected_moq = 80  # MOV (PBP) $2000 / $25 = 80
    expected_source = 'MOV (PBP)'

    moq_pass = result['moq'] == expected_moq
    source_pass = result['breakdown']['source'] == expected_source

    st.write(f"{'✅' if moq_pass else '❌'} MOQ = {result['moq']} (expected {expected_moq})")
    st.write(f"{'✅' if source_pass else '❌'} Source = {result['breakdown']['source']} (expected {expected_source})")

    if moq_pass and source_pass:
        st.success("✅ TEST PASSED")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_only_moq_fields():
    """Test 3: Only MOQ fields (no MOV)"""
    st.subheader("Test 3: Only MOQ Fields")

    product_data = {
        'MOQ (Partner)': 50,
        'MOQ (PBP)': 75
    }

    result = calculate_moq(25.0, product_data)

    st.write("**Spreadsheet Data:**")
    st.json(product_data)
    st.write("**Result:**")
    st.json({
        'moq': result['moq'],
        'source': result['breakdown']['source'],
        'display_text': result['display_text']
    })

    expected_moq = 75  # Max of 50 and 75
    expected_source = 'MOQ (PBP)'

    moq_pass = result['moq'] == expected_moq
    source_pass = result['breakdown']['source'] == expected_source

    st.write(f"{'✅' if moq_pass else '❌'} MOQ = {result['moq']} (expected {expected_moq})")
    st.write(f"{'✅' if source_pass else '❌'} Source = {result['breakdown']['source']} (expected {expected_source})")

    if moq_pass and source_pass:
        st.success("✅ TEST PASSED")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_only_mov_fields():
    """Test 4: Only MOV fields (no MOQ)"""
    st.subheader("Test 4: Only MOV Fields")

    product_data = {
        'MOV (Partner)': '$1,500',
        'MOV (PBP)': '$2,000'
    }

    result = calculate_moq(30.0, product_data)

    st.write("**Spreadsheet Data:**")
    st.json(product_data)
    st.write("**Unit Price:** $30")
    st.write("**Result:**")
    st.json({
        'moq': result['moq'],
        'source': result['breakdown']['source'],
        'display_text': result['display_text']
    })

    expected_moq = 67  # MOV (PBP) $2000 / $30 = 66.67 → 67
    expected_source = 'MOV (PBP)'

    moq_pass = result['moq'] == expected_moq
    source_pass = result['breakdown']['source'] == expected_source

    st.write(f"{'✅' if moq_pass else '❌'} MOQ = {result['moq']} (expected {expected_moq})")
    st.write(f"{'✅' if source_pass else '❌'} Source = {result['breakdown']['source']} (expected {expected_source})")

    if moq_pass and source_pass:
        st.success("✅ TEST PASSED")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_fallback_calculation():
    """Test 5: No spreadsheet data - fallback to calculation"""
    st.subheader("Test 5: Fallback Calculation")

    product_data = {}  # No MOQ/MOV fields

    result = calculate_moq(50.0, product_data)

    st.write("**Spreadsheet Data:** Empty")
    st.write("**Unit Price:** $50")
    st.write("**Result:**")
    st.json({
        'moq': result['moq'],
        'source': result['breakdown']['source'],
        'fallback_used': result['breakdown']['fallback_used'],
        'display_text': result['display_text']
    })

    expected_moq = 20  # ceil(1000 / 50) = 20
    expected_source = 'Calculated (Fallback)'

    moq_pass = result['moq'] == expected_moq
    source_pass = result['breakdown']['source'] == expected_source
    fallback_pass = result['breakdown']['fallback_used'] == True

    st.write(f"{'✅' if moq_pass else '❌'} MOQ = {result['moq']} (expected {expected_moq})")
    st.write(f"{'✅' if source_pass else '❌'} Source = {result['breakdown']['source']} (expected {expected_source})")
    st.write(f"{'✅' if fallback_pass else '❌'} Fallback Used = True")

    if moq_pass and source_pass and fallback_pass:
        st.success("✅ TEST PASSED")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_zero_and_negative_values():
    """Test 6: Zero and negative values should be ignored"""
    st.subheader("Test 6: Zero and Negative Values")

    product_data = {
        'MOQ (Partner)': 0,
        'MOV (Partner)': '-100',
        'MOQ (PBP)': 75,
        'MOV (PBP)': '$0'
    }

    result = calculate_moq(25.0, product_data)

    st.write("**Spreadsheet Data:**")
    st.json(product_data)
    st.write("**Result:**")
    st.json({
        'moq': result['moq'],
        'source': result['breakdown']['source'],
        'display_text': result['display_text']
    })

    expected_moq = 75  # Only valid value is MOQ (PBP) = 75
    expected_source = 'MOQ (PBP)'

    moq_pass = result['moq'] == expected_moq
    source_pass = result['breakdown']['source'] == expected_source

    st.write(f"{'✅' if moq_pass else '❌'} MOQ = {result['moq']} (expected {expected_moq})")
    st.write(f"{'✅' if source_pass else '❌'} Source = {result['breakdown']['source']} (expected {expected_source})")

    if moq_pass and source_pass:
        st.success("✅ TEST PASSED - Zero/negative values ignored")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_string_parsing():
    """Test 7: String formats like '$2,000.00' should parse correctly"""
    st.subheader("Test 7: String Parsing")

    # Test parse_mov_value
    test_cases = [
        ('$2,000.00', 2000.0),
        ('2000', 2000.0),
        ('$1,500', 1500.0),
        ('', None),
        (None, None)
    ]

    all_pass = True
    for input_val, expected in test_cases:
        result = parse_mov_value(input_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        st.write(f"{status} - parse_mov_value({repr(input_val)}) = {result} (expected {expected})")
        if result != expected:
            all_pass = False

    # Test parse_moq_value
    st.write("")
    st.write("**MOQ Parsing:**")
    moq_cases = [
        ('100', 100),
        (50.0, 50),
        (75, 75),
        ('', None),
        (None, None),
        ('invalid', None)
    ]

    for input_val, expected in moq_cases:
        result = parse_moq_value(input_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        st.write(f"{status} - parse_moq_value({repr(input_val)}) = {result} (expected {expected})")
        if result != expected:
            all_pass = False

    if all_pass:
        st.success("✅ ALL STRING PARSING TESTS PASSED")
    else:
        st.error("❌ SOME STRING PARSING TESTS FAILED")

    st.divider()


def test_backward_compatibility():
    """Test 8: Old 'MOQ' column should still work via fallback"""
    st.subheader("Test 8: Backward Compatibility")

    product_data = {
        'MOQ': 100  # Old column name (no new columns)
    }

    result = calculate_moq(25.0, product_data)

    st.write("**Spreadsheet Data:**")
    st.json(product_data)
    st.write("**Result:**")
    st.json({
        'moq': result['moq'],
        'source': result['breakdown']['source'],
        'display_text': result['display_text']
    })

    expected_moq = 100  # Should use old MOQ column via fallback

    moq_pass = result['moq'] == expected_moq

    st.write(f"{'✅' if moq_pass else '❌'} MOQ = {result['moq']} (expected {expected_moq})")

    if moq_pass:
        st.success("✅ TEST PASSED - Backward compatible with old 'MOQ' column")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_invalid_unit_price():
    """Test 9: Invalid unit price handling"""
    st.subheader("Test 9: Invalid Unit Price")

    product_data = {
        'MOV (PBP)': '$2,000'
    }

    # Test with zero unit price
    result_zero = calculate_moq(0, product_data)

    st.write("**Test with zero unit price:**")
    st.write(f"Unit Price: $0")
    st.write(f"Result: {result_zero}")

    # MOV should be ignored when unit price is 0
    # Should fall back to None or 0
    zero_pass = result_zero['moq'] is None
    st.write(f"{'✅' if zero_pass else '❌'} Zero unit price handled correctly (MOQ = None)")

    # Test with negative unit price
    result_neg = calculate_moq(-10, product_data)
    st.write("")
    st.write("**Test with negative unit price:**")
    st.write(f"Unit Price: $-10")
    st.write(f"Result: {result_neg}")

    neg_pass = result_neg['moq'] is None
    st.write(f"{'✅' if neg_pass else '❌'} Negative unit price handled correctly (MOQ = None)")

    if zero_pass and neg_pass:
        st.success("✅ TEST PASSED")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


def test_display_text_generation():
    """Test 10: Display text accuracy and format"""
    st.subheader("Test 10: Display Text Generation")

    product_data = {
        'MOQ (Partner)': 50,
        'MOV (Partner)': '$1,500',
        'MOQ (PBP)': 75,
        'MOV (PBP)': '$2,000'
    }

    result = calculate_moq(25.0, product_data)

    st.write("**Generated Display Text:**")
    st.code(result['display_text'])

    # Check key elements in display text
    contains_moq = "MOQ: 80 units" in result['display_text']
    contains_winner = "PBP MOV: $2000" in result['display_text'] or "PBP MOV: $2,000" in result['display_text']
    contains_also = "Also:" in result['display_text']

    st.write(f"{'✅' if contains_moq else '❌'} Contains final MOQ (80 units)")
    st.write(f"{'✅' if contains_winner else '❌'} Shows winning source (PBP MOV: $2000)")
    st.write(f"{'✅' if contains_also else '❌'} Shows other contributing factors (Also:)")

    if contains_moq and contains_winner and contains_also:
        st.success("✅ TEST PASSED - Display text formatted correctly")
    else:
        st.error("❌ TEST FAILED")

    st.divider()


# ============================================================
# MAIN TEST RUNNER
# ============================================================

def main():
    st.title("MOQ/MOV Calculation Unit Tests")
    st.write("Testing the disaggregated MOQ/MOV schema implementation")
    st.divider()

    # Run all tests
    test_mov_to_quantity_conversion()
    test_all_four_fields_present()
    test_only_moq_fields()
    test_only_mov_fields()
    test_fallback_calculation()
    test_zero_and_negative_values()
    test_string_parsing()
    test_backward_compatibility()
    test_invalid_unit_price()
    test_display_text_generation()

    st.success("🎉 All tests completed!")
    st.write("Review results above to verify all tests passed.")


if __name__ == "__main__":
    main()
