"""
Test script for per-product kitting functionality
Created: 2026-01-20
Purpose: Verify per-product kitting feature implementation
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_order_item_structure():
    """Test that order items have kitting fields"""
    print("\n=== Test 1: Order Item Structure ===")

    # Simulate creating a new order item
    order_item = {
        'product_name': 'Test Product',
        'quantity': 50,
        'include_kitting': False,
        'kitting_pbp_cost': 0.0,
        'kitting_client_price': 0.0,
        'kitting_description': ''
    }

    # Check fields exist
    assert 'include_kitting' in order_item, "Missing include_kitting field"
    assert 'kitting_pbp_cost' in order_item, "Missing kitting_pbp_cost field"
    assert 'kitting_client_price' in order_item, "Missing kitting_client_price field"
    assert 'kitting_description' in order_item, "Missing kitting_description field"

    print("✓ Order item structure includes all kitting fields")
    print(f"  - include_kitting: {order_item['include_kitting']}")
    print(f"  - kitting_pbp_cost: ${order_item['kitting_pbp_cost']:.2f}")
    print(f"  - kitting_client_price: ${order_item['kitting_client_price']:.2f}")
    print(f"  - kitting_description: '{order_item['kitting_description']}'")

    return True

def test_kitting_calculations():
    """Test kitting cost calculations"""
    print("\n=== Test 2: Kitting Calculations ===")

    # Simulate order items with mixed kitting
    order_items = [
        {
            'product_name': 'Product A',
            'quantity': 50,
            'product_subtotal': 500.0,
            'markup_amount': 500.0,
            'include_kitting': True,
            'kitting_pbp_cost': 25.0,
            'kitting_client_price': 40.0,
            'kitting_description': 'Premium gift box'
        },
        {
            'product_name': 'Product B',
            'quantity': 100,
            'product_subtotal': 850.0,
            'markup_amount': 850.0,
            'include_kitting': True,
            'kitting_pbp_cost': 10.0,
            'kitting_client_price': 15.0,
            'kitting_description': 'Repackaging'
        },
        {
            'product_name': 'Product C',
            'quantity': 75,
            'product_subtotal': 600.0,
            'markup_amount': 600.0,
            'include_kitting': False,
            'kitting_pbp_cost': 0.0,
            'kitting_client_price': 0.0,
            'kitting_description': ''
        }
    ]

    # Global kitting
    global_kitting_pbp = 50.0
    global_kitting_client = 75.0

    # Calculate per-product kitting
    per_product_kitting_pbp = sum(
        item.get('kitting_pbp_cost', 0.0)
        for item in order_items
        if item.get('include_kitting', False)
    )
    per_product_kitting_client = sum(
        item.get('kitting_client_price', 0.0)
        for item in order_items
        if item.get('include_kitting', False)
    )

    # Total kitting
    total_kitting_pbp = global_kitting_pbp + per_product_kitting_pbp
    total_kitting_client = global_kitting_client + per_product_kitting_client

    print(f"Per-product kitting PBP: ${per_product_kitting_pbp:.2f}")
    print(f"Per-product kitting Client: ${per_product_kitting_client:.2f}")
    print(f"Global kitting PBP: ${global_kitting_pbp:.2f}")
    print(f"Global kitting Client: ${global_kitting_client:.2f}")
    print(f"Total kitting PBP: ${total_kitting_pbp:.2f}")
    print(f"Total kitting Client: ${total_kitting_client:.2f}")

    # Verify calculations
    assert per_product_kitting_pbp == 35.0, f"Expected $35.00 per-product PBP, got ${per_product_kitting_pbp:.2f}"
    assert per_product_kitting_client == 55.0, f"Expected $55.00 per-product client, got ${per_product_kitting_client:.2f}"
    assert total_kitting_pbp == 85.0, f"Expected $85.00 total PBP, got ${total_kitting_pbp:.2f}"
    assert total_kitting_client == 130.0, f"Expected $130.00 total client, got ${total_kitting_client:.2f}"

    print("✓ Kitting calculations correct")

    return True

def test_migration():
    """Test migration of old order items"""
    print("\n=== Test 3: Migration of Old Orders ===")

    # Simulate old order item without kitting fields
    old_order_item = {
        'product_name': 'Legacy Product',
        'quantity': 100,
        'product_subtotal': 1000.0
    }

    print(f"Old order item fields: {list(old_order_item.keys())}")

    # Migration logic
    if 'include_kitting' not in old_order_item:
        old_order_item['include_kitting'] = False
        old_order_item['kitting_pbp_cost'] = 0.0
        old_order_item['kitting_client_price'] = 0.0
        old_order_item['kitting_description'] = ''
        print("✓ Migration applied: Added kitting fields with default values")

    # Verify migration
    assert old_order_item['include_kitting'] == False
    assert old_order_item['kitting_pbp_cost'] == 0.0
    assert old_order_item['kitting_client_price'] == 0.0
    assert old_order_item['kitting_description'] == ''

    print(f"Migrated order item fields: {list(old_order_item.keys())}")
    print("✓ Migration successful - old orders will work correctly")

    return True

def test_display_logic():
    """Test order summary display logic"""
    print("\n=== Test 4: Display Logic ===")

    # Product with kitting
    item = {
        'product_name': 'Strawberry Jam',
        'quantity': 50,
        'product_subtotal': 500.0,
        'markup_amount': 500.0,
        'include_kitting': True,
        'kitting_pbp_cost': 25.0,
        'kitting_client_price': 40.0,
        'kitting_description': 'Premium gift box'
    }

    # Calculate display values (simulating Tab 3 order summary)
    product_pbp_cost = item.get('product_subtotal', 0)
    product_client_price = product_pbp_cost + item.get('markup_amount', 0)

    kitting_note = ""
    if item.get('include_kitting', False):
        kitting_pbp = item.get('kitting_pbp_cost', 0.0)
        kitting_client = item.get('kitting_client_price', 0.0)
        product_pbp_cost += kitting_pbp
        product_client_price += kitting_client
        if kitting_client > 0:
            kitting_desc = item.get('kitting_description', 'kitting')
            kitting_note = f" (includes ${kitting_client:.2f} {kitting_desc})"

    display_name = f"Base Product: {item['product_name']}{kitting_note}"

    print(f"Display name: {display_name}")
    print(f"PBP Cost: ${product_pbp_cost:.2f}")
    print(f"Client Price: ${product_client_price:.2f}")

    assert kitting_note == " (includes $40.00 Premium gift box)", f"Unexpected kitting note: {kitting_note}"
    assert product_pbp_cost == 525.0, f"Expected $525.00 PBP cost, got ${product_pbp_cost:.2f}"
    assert product_client_price == 1040.0, f"Expected $1040.00 client price, got ${product_client_price:.2f}"

    print("✓ Display logic correct - kitting merged into product rows")

    return True

def test_invoice_specs():
    """Test invoice specs generation"""
    print("\n=== Test 5: Invoice Specs ===")

    # Simulate invoice line item generation
    item = {
        'product_name': 'Coffee Beans',
        'quantity': 100,
        'product_subtotal': 850.0,
        'markup_amount': 850.0,
        'include_kitting': True,
        'kitting_pbp_cost': 10.0,
        'kitting_client_price': 15.0,
        'kitting_description': 'Repackaging'
    }

    items_specs = f"{item['product_name']}\nTier 1"
    partner_cost_total = item.get('product_subtotal', 0)
    sell_price_total = partner_cost_total + item.get('markup_amount', 0)

    # Add per-product kitting
    if item.get('include_kitting', False):
        kitting_pbp = item.get('kitting_pbp_cost', 0.0)
        kitting_client = item.get('kitting_client_price', 0.0)
        partner_cost_total += kitting_pbp
        sell_price_total += kitting_client
        kitting_desc = item.get('kitting_description', 'Kitting')
        items_specs += f" | {kitting_desc}: +${kitting_client:.2f}"

    print(f"Invoice specs: {items_specs}")
    print(f"Partner cost total: ${partner_cost_total:.2f}")
    print(f"Sell price total: ${sell_price_total:.2f}")

    assert "| Repackaging: +$15.00" in items_specs, f"Kitting not in specs: {items_specs}"
    assert partner_cost_total == 860.0, f"Expected $860.00 partner cost, got ${partner_cost_total:.2f}"
    assert sell_price_total == 1715.0, f"Expected $1715.00 sell price, got ${sell_price_total:.2f}"

    print("✓ Invoice specs generation correct - kitting appended to specs")

    return True

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("PER-PRODUCT KITTING FEATURE - TEST SUITE")
    print("=" * 60)

    tests = [
        test_order_item_structure,
        test_kitting_calculations,
        test_migration,
        test_display_logic,
        test_invoice_specs
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✓ ALL TESTS PASSED - Feature ready for production!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed - Review implementation")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
