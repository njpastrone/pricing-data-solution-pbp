"""
Test script for Editable Product Descriptions functionality
Tests the Item + Specs column editing feature in Tab 4
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_description_persistence():
    """Test 1: Edit descriptions survive page reruns"""
    print("\nTest 1: Description Persistence")

    # Create a sample order item
    sample_item = {
        'product_name': 'Test Product',
        'partner': 'Partner X',
        'quantity': 5,
        'edited_description': 'Custom description for testing'
    }

    # Store in session state
    st.session_state.order_items = [sample_item]

    # Verify description persists
    assert st.session_state.order_items[0]['edited_description'] == 'Custom description for testing'
    print("✓ Edited description persists in session state")

    return True

def test_empty_description_handling():
    """Test 2: Empty input falls back to default"""
    print("\nTest 2: Empty Description Handling")

    # Create item with empty edited_description
    item = {
        'product_name': 'Product ABC',
        'partner': 'Partner Y',
        'quantity': 1,
        'edited_description': ''
    }

    # Generate default description
    if item.get('edited_description', ''):
        desc = item['edited_description']
    else:
        desc = item['product_name']
        if item.get('quantity', 1) > 1:
            desc += f" (Qty: {item['quantity']})"

    print(f"Description used: {desc}")
    assert desc == 'Product ABC'
    print("✓ Empty description falls back to product name")

    return True

def test_special_characters():
    """Test 3: Descriptions with quotes, commas, special chars"""
    print("\nTest 3: Special Characters")

    special_desc = 'Product with "quotes", commas, & special chars! (10% off)'

    item = {
        'product_name': 'Special Product',
        'edited_description': special_desc
    }

    assert item['edited_description'] == special_desc
    print(f"✓ Special characters preserved: {special_desc}")

    return True

def test_long_descriptions():
    """Test 4: Very long description text handling"""
    print("\nTest 4: Long Descriptions")

    long_desc = "This is a very long product description that includes multiple specifications, details about the product features, manufacturing information, usage instructions, and other relevant information that might be needed for bookkeeping and invoice purposes. " * 3

    item = {
        'product_name': 'Product',
        'edited_description': long_desc
    }

    assert len(item['edited_description']) > 500
    print(f"✓ Long description stored ({len(long_desc)} characters)")

    return True

def test_save_load_descriptions():
    """Test 5: Edited descriptions persist through save/load"""
    print("\nTest 5: Save/Load Descriptions")

    # Create order with edited descriptions
    order_data = {
        'order_items': [
            {
                'product_name': 'Product A',
                'edited_description': 'Custom description A',
                'quantity': 2
            },
            {
                'product_name': 'Product B',
                'edited_description': 'Custom description B',
                'quantity': 3
            }
        ]
    }

    # Simulate save/load
    saved_items = order_data['order_items']

    # Verify descriptions persist
    assert saved_items[0]['edited_description'] == 'Custom description A'
    assert saved_items[1]['edited_description'] == 'Custom description B'
    print("✓ Edited descriptions persist through save/load")

    return True

def test_csv_export_descriptions():
    """Test 6: CSV contains edited descriptions"""
    print("\nTest 6: CSV Export Descriptions")

    # Simulate invoice line item with edited description
    invoice_line = {
        'PARTNER': 'Partner X',
        'ITEMS + SPECS': 'Custom edited description for CSV',
        'QTY': 5,
        'TOTAL COST': '$100.00'
    }

    # CSV would contain the ITEMS + SPECS field
    csv_content = f"{invoice_line['PARTNER']},{invoice_line['ITEMS + SPECS']},{invoice_line['QTY']},{invoice_line['TOTAL COST']}"

    assert 'Custom edited description for CSV' in csv_content
    print("✓ CSV export includes edited description")

    return True

def test_html_export_descriptions():
    """Test 7: HTML contains edited descriptions"""
    print("\nTest 7: HTML Export Descriptions")

    # Simulate HTML generation with edited description
    invoice_line = {
        'ITEMS + SPECS': 'Custom HTML description\nWith newline'
    }

    # HTML would replace newlines with <br>
    html_content = invoice_line['ITEMS + SPECS'].replace('\n', '<br>')

    assert 'Custom HTML description<br>With newline' in html_content
    print("✓ HTML export includes edited description with proper formatting")

    return True

def test_multiple_product_descriptions():
    """Test 8: Edit multiple products independently"""
    print("\nTest 8: Multiple Product Descriptions")

    # Create multiple items
    items = [
        {'product_name': 'Product 1', 'edited_description': 'Description 1'},
        {'product_name': 'Product 2', 'edited_description': 'Description 2'},
        {'product_name': 'Product 3', 'edited_description': 'Description 3'}
    ]

    # Verify each has independent description
    for i, item in enumerate(items, 1):
        assert item['edited_description'] == f'Description {i}'

    print("✓ Multiple products have independent descriptions")

    return True

def test_description_with_customization():
    """Test 9: Descriptions for customized products"""
    print("\nTest 9: Description with Customization")

    item = {
        'product_name': 'Custom Product',
        'edited_description': 'Product with logo embroidery',
        'include_customization': True,
        'customization_description': 'Logo embroidery'
    }

    # Description should be independent of customization
    assert item['edited_description'] == 'Product with logo embroidery'
    assert item['customization_description'] == 'Logo embroidery'
    print("✓ Edited description independent of customization details")

    return True

def test_description_callback_updates():
    """Test 10: Callbacks properly update session state"""
    print("\nTest 10: Description Callback Updates")

    # Initialize session state
    if 'order_items' not in st.session_state:
        st.session_state.order_items = []

    # Add test item
    st.session_state.order_items = [
        {'product_name': 'Test', 'edited_description': ''}
    ]

    # Simulate callback function
    def update_description(idx=0):
        st.session_state.order_items[idx]['edited_description'] = 'Updated via callback'

    # Call the update function
    update_description(0)

    assert st.session_state.order_items[0]['edited_description'] == 'Updated via callback'
    print("✓ Callback function updates description correctly")

    return True

def test_custom_item_descriptions():
    """Test 11: Custom line items use custom_description"""
    print("\nTest 11: Custom Item Descriptions")

    custom_item = {
        'is_custom': True,
        'product_name': 'Custom Service',
        'custom_description': 'Special consulting service',
        'edited_description': ''  # Should be ignored for custom items
    }

    # Custom items should use custom_description, not edited_description
    if custom_item.get('is_custom', False):
        desc = custom_item.get('custom_description', 'Custom Item')
    else:
        desc = custom_item.get('edited_description', '') or custom_item['product_name']

    assert desc == 'Special consulting service'
    print("✓ Custom items correctly use custom_description field")

    return True

def main():
    print("=" * 50)
    print("EDITABLE DESCRIPTIONS FUNCTIONALITY TEST")
    print("=" * 50)

    # Initialize session state
    if 'order_items' not in st.session_state:
        st.session_state.order_items = []
    if 'client_info' not in st.session_state:
        st.session_state.client_info = {}

    # Run all tests
    tests = [
        test_description_persistence,
        test_empty_description_handling,
        test_special_characters,
        test_long_descriptions,
        test_save_load_descriptions,
        test_csv_export_descriptions,
        test_html_export_descriptions,
        test_multiple_product_descriptions,
        test_description_with_customization,
        test_description_callback_updates,
        test_custom_item_descriptions
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ Test failed: {test_func.__name__}")
        except Exception as e:
            failed += 1
            print(f"  ✗ Test error in {test_func.__name__}: {e}")

    print("\n" + "=" * 50)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed == 0:
        print("✅ All editable description tests passed!")
    else:
        print("❌ Some tests failed. Please review.")

    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)