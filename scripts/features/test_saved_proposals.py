"""
Test script for saved proposals functionality.
Tests save, load, and delete operations.
"""

import sys
sys.path.append('/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp')

from src.proposal_manager import (
    save_proposal,
    load_all_proposals,
    load_proposal_data,
    delete_proposal,
    initialize_proposals_sheet
)

def test_saved_proposals():
    """Test the complete save/load/delete workflow"""

    print("=" * 60)
    print("Testing Saved Proposals Functionality")
    print("=" * 60)

    # Test 1: Initialize sheet
    print("\n1. Initializing proposals sheet...")
    sheet = initialize_proposals_sheet()
    if sheet:
        print("✅ Sheet initialized successfully")
    else:
        print("❌ Failed to initialize sheet")
        return

    # Test 2: Save a proposal
    print("\n2. Saving test proposal...")
    test_proposal_data = {
        'proposal_products': [
            {
                'product_data': {'Product/Service': 'Test Product 1', 'Partner': 'Test Partner'},
                'markup_percent': 100.0
            }
        ],
        'proposal_marketing_rounding': False,
        'proposal_use_msrp': True,
        'proposal_discount_type': 'NGO',
        'proposal_discount_percent': 5.0,
        'proposal_client_budget': 1000.0
    }

    success, message, proposal_id = save_proposal(
        name="Test Proposal 1",
        created_by="Test User",
        proposal_data=test_proposal_data,
        dataset="demo"
    )

    if success:
        print(f"✅ {message}")
        print(f"   Proposal ID: {proposal_id}")
    else:
        print(f"❌ {message}")
        return

    # Test 3: Load all proposals
    print("\n3. Loading all proposals...")
    proposals = load_all_proposals()

    if proposals:
        print(f"✅ Found {len(proposals)} proposal(s)")
        for p in proposals:
            print(f"   - {p['name']} (ID: {p['proposal_id']}, Created: {p['created_date']})")
    else:
        print("❌ No proposals found")

    # Test 4: Load specific proposal data
    print("\n4. Loading proposal data...")
    success, data, dataset = load_proposal_data(proposal_id)

    if success:
        print(f"✅ Loaded proposal data")
        print(f"   Dataset: {dataset}")
        print(f"   Products: {len(data['proposal_products'])}")
        print(f"   Use MSRP: {data['proposal_use_msrp']}")
        print(f"   Discount: {data['proposal_discount_percent']}%")
    else:
        print("❌ Failed to load proposal data")

    # Test 5: Save duplicate name (should suggest versioned name)
    print("\n5. Testing duplicate name handling...")
    success, message, result = save_proposal(
        name="Test Proposal 1",
        created_by="Test User 2",
        proposal_data=test_proposal_data,
        dataset="demo"
    )

    if not success and result:
        print(f"✅ Duplicate detected, suggested name: {result}")
    else:
        print(f"❌ Expected duplicate detection, got: {message}")

    # Test 6: Delete proposal
    print("\n6. Deleting test proposal...")
    success, message = delete_proposal(proposal_id)

    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

    # Test 7: Verify deletion
    print("\n7. Verifying deletion...")
    proposals = load_all_proposals()

    if proposal_id not in [p['proposal_id'] for p in proposals]:
        print("✅ Proposal successfully deleted")
    else:
        print("❌ Proposal still exists after deletion")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_saved_proposals()
