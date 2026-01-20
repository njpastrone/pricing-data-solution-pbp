"""
Test script for proposal pricing preservation feature.

This script verifies that pricing snapshots are created correctly when adding
products to proposals, and that they are properly used when importing to orders.

Usage:
    streamlit run scripts/features/test_proposal_pricing_preservation.py

Tests:
    1. New proposal with snapshot → Order has matching prices
    2. Snapshot creation with various settings (discount, rounding)
    3. convert_proposal_to_order uses snapshot when available
    4. convert_proposal_to_order falls back to recalculation when no snapshot
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.helpers import calculate_pricing_snapshot, convert_proposal_to_order, calculate_product_tariff
from src.pricing_engine import get_unit_price_new_system

st.title("Proposal Pricing Preservation - Test Suite")
st.markdown("Testing pricing snapshot creation and usage in proposal-to-order conversion")

# Create sample product data
sample_product = {
    'Product/Service': 'Test Product - Strawberry Jam',
    'Partner': 'Test Partner',
    'Pricing Tiers (Y/N)': 'Y',
    'PBP Cost (No Tiers)': 0,
    'PBP Cost: Tier 1': 10.0,
    'PBP Cost: Tier 2': 9.5,
    'PBP Cost: Tier 3': 9.0,
    'PBP Cost: Tier 4': 8.5,
    'PBP Cost: Tier 5': 8.0,
    'PBP Cost: Tier 6': 7.5,
    'T1 Start': 1,
    'T1 End': 50,
    'T2 Start': 51,
    'T2 End': 100,
    'T3 Start': 101,
    'T3 End': 200,
    'T4 Start': 201,
    'T4 End': 500,
    'T5 Start': 501,
    'T5 End': 1000,
    'T6 Start': 1001,
    'T6 End': 99999,
    'Country of Origin (Made In)': 'USA',
    'Country of Origin (Ships From)': 'USA',
    'Vendor Published MSRP': 25.0,
    'MOQ (PBP)': '',
    'MOV (PBP)': '',
    'MOQ (Partner)': '',
    'MOV (Partner)': '',
    'Customization Setup Fee': 0,
    'Customization Cost per Unit': 0,
    'Customization Info': '',
    'Marketing Description': 'Test product description',
    'Purchase Description': 'Test reference',
    'Tariff Info': '',
    'Tariff Estimate (%)': 0,
    'Units per Package': 1,
    'PBP Standard Markup': 100.0
}

st.write("---")
st.header("Test 1: Pricing Snapshot Creation")
st.markdown("Verify that `calculate_pricing_snapshot()` creates correct snapshot data")

# Test with different settings
test_cases = [
    {"markup": 100.0, "discount": 0.0, "marketing_rounding": True, "fifty_cent_rounding": True, "label": "100% markup, no discount, both roundings"},
    {"markup": 150.0, "discount": 5.0, "marketing_rounding": True, "fifty_cent_rounding": True, "label": "150% markup, 5% discount, both roundings"},
    {"markup": 75.0, "discount": 0.0, "marketing_rounding": False, "fifty_cent_rounding": False, "label": "75% markup, no discount, no roundings"},
]

for i, test_case in enumerate(test_cases):
    st.subheader(f"Test Case {i+1}: {test_case['label']}")

    try:
        snapshot = calculate_pricing_snapshot(
            product_data=sample_product,
            markup_percent=test_case['markup'],
            quantity=100,
            discount_percent=test_case['discount'],
            marketing_rounding=test_case['marketing_rounding'],
            fifty_cent_rounding=test_case['fifty_cent_rounding']
        )

        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("MOQ", snapshot['moq'])
            st.metric("Base Price/Unit", f"${snapshot['base_price_per_unit']:.2f}")
        with col2:
            st.metric("Tier Range", snapshot['tier_range'])
            st.metric("Tier Column", snapshot['tier_column'] if snapshot['tier_column'] else "N/A")
        with col3:
            st.metric("Client Price/Unit", f"${snapshot['client_price_per_unit']:.2f}")
            st.metric("Discount %", f"{snapshot['discount_percent']}%")

        st.success(f"✓ Snapshot created successfully")
        with st.expander("View Full Snapshot Data"):
            st.json(snapshot)

    except Exception as e:
        st.error(f"✗ Error creating snapshot: {e}")
        st.exception(e)

st.write("---")
st.header("Test 2: Proposal-to-Order Conversion with Snapshot")
st.markdown("Verify that `convert_proposal_to_order()` uses snapshot when available")

try:
    # Create proposal item WITH snapshot
    snapshot = calculate_pricing_snapshot(
        product_data=sample_product,
        markup_percent=100.0,
        quantity=100,
        discount_percent=5.0,
        marketing_rounding=True,
        fifty_cent_rounding=True
    )

    proposal_item_with_snapshot = {
        'product_data': sample_product,
        'markup_percent': 100.0,
        'selected_variant': None,
        'pricing_snapshot': snapshot
    }

    # Convert to order
    order_item = convert_proposal_to_order(
        proposal_item_with_snapshot,
        get_unit_price_new_system,
        calculate_product_tariff
    )

    st.subheader("Order Item Created from Proposal (with snapshot)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Quantity", order_item['quantity'])
        st.metric("Base Price/Unit", f"${order_item['base_price']:.2f}")
    with col2:
        st.metric("Tier Range", order_item['tier_range'])
        st.metric("Tier Column", order_item['tier_column'] if order_item['tier_column'] else "N/A")
    with col3:
        st.metric("From Snapshot?", "✓ Yes" if order_item['from_proposal_snapshot'] else "✗ No")
        st.metric("Markup %", f"{order_item['markup_percent']}%")

    # Verify snapshot was used
    if order_item['from_proposal_snapshot']:
        st.success("✓ Pricing snapshot was used correctly")

        # Verify prices match
        if abs(order_item['base_price'] - snapshot['base_price_per_unit']) < 0.01:
            st.success("✓ Base price matches snapshot")
        else:
            st.error(f"✗ Base price mismatch: {order_item['base_price']} vs {snapshot['base_price_per_unit']}")

        if order_item['quantity'] == snapshot['quantity']:
            st.success("✓ Quantity matches snapshot MOQ")
        else:
            st.error(f"✗ Quantity mismatch: {order_item['quantity']} vs {snapshot['quantity']}")

    else:
        st.error("✗ Pricing snapshot was NOT used (expected it to be used)")

    with st.expander("View Full Order Item Data"):
        st.json(order_item)

except Exception as e:
    st.error(f"✗ Error in conversion with snapshot: {e}")
    st.exception(e)

st.write("---")
st.header("Test 3: Proposal-to-Order Conversion WITHOUT Snapshot (Backward Compatibility)")
st.markdown("Verify that `convert_proposal_to_order()` falls back to recalculation when no snapshot")

try:
    # Create proposal item WITHOUT snapshot (old format)
    proposal_item_without_snapshot = {
        'product_data': sample_product,
        'markup_percent': 100.0,
        'quantity': 50,  # Explicitly set quantity
        'selected_variant': None
        # NO pricing_snapshot field
    }

    # Convert to order
    order_item_old = convert_proposal_to_order(
        proposal_item_without_snapshot,
        get_unit_price_new_system,
        calculate_product_tariff
    )

    st.subheader("Order Item Created from Proposal (without snapshot - backward compatibility)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Quantity", order_item_old['quantity'])
        st.metric("Base Price/Unit", f"${order_item_old['base_price']:.2f}")
    with col2:
        st.metric("Tier Range", order_item_old['tier_range'])
        st.metric("Tier Column", order_item_old['tier_column'] if order_item_old['tier_column'] else "N/A")
    with col3:
        st.metric("From Snapshot?", "✓ Yes" if order_item_old['from_proposal_snapshot'] else "✗ No")
        st.metric("Markup %", f"{order_item_old['markup_percent']}%")

    # Verify fallback was used
    if not order_item_old['from_proposal_snapshot']:
        st.success("✓ Fallback to recalculation worked correctly (backward compatibility)")
    else:
        st.error("✗ Expected fallback to recalculation, but snapshot flag is True")

    with st.expander("View Full Order Item Data"):
        st.json(order_item_old)

except Exception as e:
    st.error(f"✗ Error in conversion without snapshot: {e}")
    st.exception(e)

st.write("---")
st.header("Test Summary")

st.markdown("""
**Tests Completed:**
1. ✓ Pricing snapshot creation with various settings
2. ✓ Proposal-to-order conversion using snapshot
3. ✓ Proposal-to-order conversion fallback (backward compatibility)

**Expected Behavior:**
- New proposals should create pricing snapshots
- Snapshots should capture: MOQ, base price, tier, client price, discount
- Order items from proposals with snapshots should use snapshot data
- Order items from old proposals (no snapshot) should recalculate from spreadsheet
- UI indicator should show price source (snapshot vs. recalculated)

**Next Steps:**
- Test in full app (Tab 1 → Tab 3 workflow)
- Verify saved proposals work correctly
- Test with both demo and real datasets
""")
