"""
Test script for saved orders functionality.
Tests save, load, and delete operations.
"""

import sys
sys.path.append('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp')

from src.order_manager import (
    save_order,
    load_all_orders,
    load_order_data,
    delete_order,
    initialize_orders_sheet
)

def test_saved_orders():
    """Test the complete save/load/delete workflow"""

    print("=" * 60)
    print("Testing Saved Orders Functionality")
    print("=" * 60)

    # Test 1: Initialize sheet
    print("\n1. Initializing orders sheet...")
    sheet = initialize_orders_sheet()
    if sheet:
        print("✅ Sheet initialized successfully")
    else:
        print("❌ Failed to initialize sheet")
        return

    # Test 2: Save an order
    print("\n2. Saving test order...")
    test_order_data = {
        'order_items': [
            {
                'product_data': {'Product/Service': 'Test Product 1', 'Partner': 'Test Partner'},
                'quantity': 100,
                'markup_percent': 100.0,
                'include_customization': False
            }
        ],
        'order_shipping': 50.0,
        'partner_shipping': 25.0,
        'order_discount_type': 'preset',
        'order_discount_preset': 'NGO Discount (5%)',
        'order_discount_custom_desc': '',
        'order_discount_custom_value': 0.0,
        'order_use_marketing_rounding': False,
        'apply_cc_fee': False,
        'cc_fee_percent': 3.0,
        'client_info': {
            'is_new_client': True,
            'company_name': 'Test Company',
            'contact_name': 'Test Contact',
            'contact_email': 'test@example.com',
            'client_po': 'PO-TEST-001',
            'billing_address': '123 Test St',
            'shipping_type': 'Ground',
            'shipping_address': '456 Ship St',
            'payment_timeline': 'Net 30',
            'payment_preference': 'Check'
        },
        # Old 2-category structure (for backward compatibility testing)
        # Will be replaced with fresh 4-category structure on load
        'order_notes': {
            'notes_to_partner': 'Test partner notes',
            'accounting_notes': 'Test accounting notes'
        },
        'order_confirmed': False
    }

    success, message, order_id = save_order(
        name="Test Order 1",
        created_by="Test User",
        order_data=test_order_data,
        dataset="demo"
    )

    if success:
        print(f"✅ {message}")
        print(f"   Order ID: {order_id}")
    else:
        print(f"❌ {message}")
        return

    # Test 3: Load all orders
    print("\n3. Loading all orders...")
    orders = load_all_orders()

    if orders:
        print(f"✅ Found {len(orders)} order(s)")
        for o in orders:
            print(f"   - {o['name']} (ID: {o['order_id']}, Created: {o['created_date']})")
    else:
        print("❌ No orders found")

    # Test 4: Load specific order data
    print("\n4. Loading order data...")
    success, data, dataset = load_order_data(order_id)

    if success:
        print(f"✅ Loaded order data")
        print(f"   Dataset: {dataset}")
        print(f"   Products: {len(data['order_items'])}")
        print(f"   Shipping: ${data['order_shipping']:.2f}")
        print(f"   Company: {data['client_info']['company_name']}")
        print(f"   Confirmed: {data['order_confirmed']}")
    else:
        print("❌ Failed to load order data")

    # Test 5: Save duplicate name (should suggest versioned name)
    print("\n5. Testing duplicate name handling...")
    success, message, result = save_order(
        name="Test Order 1",
        created_by="Test User 2",
        order_data=test_order_data,
        dataset="demo"
    )

    if not success and result:
        print(f"✅ Duplicate detected, suggested name: {result}")
    else:
        print(f"❌ Expected duplicate detection, got: {message}")

    # Test 6: Delete order
    print("\n6. Deleting test order...")
    success, message = delete_order(order_id)

    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

    # Test 7: Verify deletion
    print("\n7. Verifying deletion...")
    orders = load_all_orders()

    if order_id not in [o['order_id'] for o in orders]:
        print("✅ Order successfully deleted")
    else:
        print("❌ Order still exists after deletion")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_saved_orders()
