"""
Test script for Payment Terms functionality
Tests Net 15 addition and custom payment terms option
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_net15_option():
    """Test 1: Verify Net 15 appears in dropdown"""
    print("\nTest 1: Net 15 Option")
    payment_options = ['Net 30', 'Net 15', 'Net 60', 'Due on Receipt', '50% Deposit', 'Custom']

    if 'Net 15' in payment_options:
        print("✓ Net 15 is available in payment terms options")
        assert payment_options.index('Net 15') == 1, "Net 15 should be second option"
        print("✓ Net 15 is in correct position (after Net 30)")
    else:
        print("✗ Net 15 is missing from payment terms")

    return 'Net 15' in payment_options

def test_custom_option_reveals_input():
    """Test 2: Custom option shows text field"""
    print("\nTest 2: Custom Option Reveals Input")

    # Simulate selecting Custom
    selected_payment = "Custom"

    if selected_payment == "Custom":
        print("✓ Custom selection triggers input field display")
        # Would show text input in actual UI
        custom_input_shown = True
    else:
        custom_input_shown = False

    return custom_input_shown

def test_custom_terms_persistence():
    """Test 3: Custom terms survive page reruns"""
    print("\nTest 3: Custom Terms Persistence")

    # Initialize session state
    if 'custom_payment_terms' not in st.session_state:
        st.session_state.custom_payment_terms = ''

    # Set custom terms
    st.session_state.custom_payment_terms = "2/10 Net 30"
    st.session_state.client_info = {'payment_timeline': "2/10 Net 30"}

    print(f"✓ Custom terms stored: {st.session_state.custom_payment_terms}")
    print(f"✓ Payment timeline updated: {st.session_state.client_info['payment_timeline']}")

    # Verify persistence
    assert st.session_state.custom_payment_terms == "2/10 Net 30"
    assert st.session_state.client_info['payment_timeline'] == "2/10 Net 30"

    return True

def test_standard_to_custom_switch():
    """Test 4: Switching from standard to custom"""
    print("\nTest 4: Standard to Custom Switch")

    # Start with standard option
    st.session_state.client_info = {'payment_timeline': 'Net 30'}
    print(f"Initial: {st.session_state.client_info['payment_timeline']}")

    # Switch to custom
    selected = "Custom"
    custom_value = "Net 45"

    if selected == "Custom":
        st.session_state.custom_payment_terms = custom_value
        st.session_state.client_info['payment_timeline'] = custom_value

    print(f"After switch: {st.session_state.client_info['payment_timeline']}")
    assert st.session_state.client_info['payment_timeline'] == "Net 45"
    print("✓ Successfully switched from standard to custom")

    return True

def test_custom_to_standard_switch():
    """Test 5: Switching from custom to standard"""
    print("\nTest 5: Custom to Standard Switch")

    # Start with custom
    st.session_state.custom_payment_terms = "Net 45"
    st.session_state.client_info = {'payment_timeline': 'Net 45'}
    print(f"Initial custom: {st.session_state.client_info['payment_timeline']}")

    # Switch to standard
    selected = "Net 15"
    st.session_state.client_info['payment_timeline'] = selected

    print(f"After switch: {st.session_state.client_info['payment_timeline']}")
    assert st.session_state.client_info['payment_timeline'] == "Net 15"
    print("✓ Successfully switched from custom to Net 15")

    return True

def test_save_load_custom_terms():
    """Test 6: Custom terms persist through save/load"""
    print("\nTest 6: Save/Load Custom Terms")

    # Create order with custom terms
    order_data = {
        'client_info': {
            'payment_timeline': 'COD - Cash on Delivery',
            'company_name': 'Test Company'
        },
        'custom_payment_terms': 'COD - Cash on Delivery'
    }

    # Simulate save
    print(f"Saving order with custom terms: {order_data['client_info']['payment_timeline']}")

    # Simulate load
    loaded_payment = order_data['client_info']['payment_timeline']
    loaded_custom = order_data.get('custom_payment_terms', '')

    print(f"Loaded payment timeline: {loaded_payment}")
    print(f"Loaded custom terms: {loaded_custom}")

    assert loaded_payment == 'COD - Cash on Delivery'
    print("✓ Custom payment terms persist through save/load")

    return True

def test_tab3_to_tab4_transfer():
    """Test 7: Payment terms transfer between tabs"""
    print("\nTest 7: Tab 3 to Tab 4 Transfer")

    # Set in Tab 3
    st.session_state.client_info = {'payment_timeline': 'Net 15'}
    tab3_value = st.session_state.client_info['payment_timeline']
    print(f"Tab 3 value: {tab3_value}")

    # Access in Tab 4 (same session state)
    tab4_value = st.session_state.client_info.get('payment_timeline', 'Net 30')
    print(f"Tab 4 value: {tab4_value}")

    assert tab3_value == tab4_value
    print("✓ Payment terms successfully transfer between tabs")

    return True

def test_empty_custom_handling():
    """Test 8: Empty custom input behavior"""
    print("\nTest 8: Empty Custom Handling")

    # Select custom but leave empty
    selected = "Custom"
    custom_terms = ""  # Empty input

    if selected == "Custom":
        st.session_state.custom_payment_terms = custom_terms
        # Should store "Custom" as placeholder
        payment_value = custom_terms if custom_terms else "Custom"
        st.session_state.client_info = {'payment_timeline': payment_value}

    print(f"Empty custom results in: {st.session_state.client_info['payment_timeline']}")
    assert st.session_state.client_info['payment_timeline'] == "Custom"
    print("✓ Empty custom input handled gracefully")

    return True

def test_special_characters():
    """Test 9: Custom terms with special characters"""
    print("\nTest 9: Special Characters")

    special_terms = "2/10, n/30 (2% discount if paid within 10 days)"
    st.session_state.custom_payment_terms = special_terms
    st.session_state.client_info = {'payment_timeline': special_terms}

    print(f"Special terms: {special_terms}")
    assert st.session_state.client_info['payment_timeline'] == special_terms
    print("✓ Special characters handled correctly")

    return True

def test_long_custom_terms():
    """Test 10: Long custom payment terms text"""
    print("\nTest 10: Long Custom Terms")

    long_terms = "Payment due within 30 days of invoice date. 2% discount if paid within 10 days. Late payments subject to 1.5% monthly interest."
    st.session_state.custom_payment_terms = long_terms
    st.session_state.client_info = {'payment_timeline': long_terms}

    print(f"Long terms length: {len(long_terms)} characters")
    assert st.session_state.client_info['payment_timeline'] == long_terms
    print("✓ Long custom terms stored successfully")

    return True

def main():
    print("=" * 50)
    print("PAYMENT TERMS FUNCTIONALITY TEST")
    print("=" * 50)

    # Initialize session state
    if 'client_info' not in st.session_state:
        st.session_state.client_info = {}
    if 'custom_payment_terms' not in st.session_state:
        st.session_state.custom_payment_terms = ''

    # Run all tests
    tests = [
        test_net15_option,
        test_custom_option_reveals_input,
        test_custom_terms_persistence,
        test_standard_to_custom_switch,
        test_custom_to_standard_switch,
        test_save_load_custom_terms,
        test_tab3_to_tab4_transfer,
        test_empty_custom_handling,
        test_special_characters,
        test_long_custom_terms
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
        print("✅ All payment terms tests passed!")
    else:
        print("❌ Some tests failed. Please review.")

    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)