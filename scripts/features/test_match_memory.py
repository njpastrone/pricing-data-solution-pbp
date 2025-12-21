"""
Test script for Match Memory system

Tests the confirmed match storage and retrieval functionality:
1. Save confirmed matches to Google Sheets
2. Load matches by dataset
3. Retrieve individual matches
4. Delete matches
5. Clear all matches

Run with: streamlit run scripts/test_match_memory.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from src.match_memory import (
    save_confirmed_match,
    load_all_confirmed_matches,
    get_confirmed_match,
    delete_confirmed_match,
    clear_all_confirmed_matches
)

def test_save_and_load():
    """Test saving and loading confirmed matches"""
    results = []
    results.append("### TEST 1: Save and Load Matches")

    # Test data
    test_matches = [
        {
            'product_name': 'Upcycled Laptop Sleeve (Enfold)',
            'slide_index': 42,
            'slide_title': 'UPCYCLED LAPTOP SLEEVE',
            'dataset': 'demo',
            'match_type': 'fuzzy_confirmed',
            'confidence': 85
        },
        {
            'product_name': 'Butcher Block - Large',
            'slide_index': 120,
            'slide_title': 'BUTCHER BLOCK',
            'dataset': 'demo',
            'match_type': 'alternative_selected',
            'confidence': 75
        },
        {
            'product_name': 'Test Product',
            'slide_index': 99,
            'slide_title': 'TEST SLIDE',
            'dataset': 'real',
            'match_type': 'fuzzy_confirmed',
            'confidence': 90
        }
    ]

    # Save test matches
    for match in test_matches:
        success, message = save_confirmed_match(
            product_name=match['product_name'],
            slide_index=match['slide_index'],
            slide_title=match['slide_title'],
            dataset=match['dataset'],
            match_type=match['match_type'],
            confidence=match['confidence']
        )
        if success:
            results.append(f"✓ Saved: {match['product_name']}")
        else:
            results.append(f"✗ Failed: {message}")

    # Load matches by dataset
    results.append("\n**Loading demo dataset matches:**")
    demo_matches = load_all_confirmed_matches(dataset='demo')
    results.append(f"Found {len(demo_matches)} demo matches:")
    for match in demo_matches:
        results.append(f"  - {match['original_product_name']} → {match['slide_title']}")

    results.append("\n**Loading real dataset matches:**")
    real_matches = load_all_confirmed_matches(dataset='real')
    results.append(f"Found {len(real_matches)} real matches:")
    for match in real_matches:
        results.append(f"  - {match['original_product_name']} → {match['slide_title']}")

    results.append("\n**Loading all matches (no filter):**")
    all_matches = load_all_confirmed_matches()
    results.append(f"Found {len(all_matches)} total matches")

    return results


def test_get_individual_match():
    """Test retrieving individual matches"""
    results = []
    results.append("### TEST 2: Get Individual Match")

    # Test exact match
    match = get_confirmed_match('Upcycled Laptop Sleeve (Enfold)', 'demo')
    if match:
        results.append(f"✓ Found match for 'Upcycled Laptop Sleeve (Enfold)'")
        results.append(f"  - Slide: {match['slide_title']}")
        results.append(f"  - Type: {match['match_type']}")
        results.append(f"  - Confidence: {match['confidence']}%")
    else:
        results.append("✗ No match found")

    # Test variant match (should match due to normalization)
    match = get_confirmed_match('Upcycled Laptop Sleeve', 'demo')
    if match:
        results.append(f"✓ Variant matched: 'Upcycled Laptop Sleeve' (normalized)")
    else:
        results.append("✗ Variant did not match")

    # Test wrong dataset
    match = get_confirmed_match('Upcycled Laptop Sleeve (Enfold)', 'real')
    if match:
        results.append("✗ Should not have matched wrong dataset")
    else:
        results.append("✓ Correctly rejected wrong dataset")

    return results


def test_delete_match():
    """Test deleting individual matches"""
    results = []
    results.append("### TEST 3: Delete Individual Match")

    success, message = delete_confirmed_match('Butcher Block - Large', 'demo')
    if success:
        results.append(f"✓ {message}")

        # Verify deletion
        match = get_confirmed_match('Butcher Block - Large', 'demo')
        if match:
            results.append("✗ Match still exists after deletion")
        else:
            results.append("✓ Match successfully removed")
    else:
        results.append(f"✗ {message}")

    return results


def test_clear_all():
    """Test clearing all matches"""
    results = []
    results.append("### TEST 4: Clear All Matches")

    # Clear demo dataset
    success, message, count = clear_all_confirmed_matches(dataset='demo')
    if success:
        results.append(f"✓ {message}")
        results.append(f"  Cleared {count} demo matches")
    else:
        results.append(f"✗ {message}")

    # Verify demo cleared
    demo_matches = load_all_confirmed_matches(dataset='demo')
    if len(demo_matches) == 0:
        results.append("✓ Demo dataset cleared successfully")
    else:
        results.append(f"✗ Demo dataset still has {len(demo_matches)} matches")

    # Verify real dataset NOT cleared
    real_matches = load_all_confirmed_matches(dataset='real')
    if len(real_matches) > 0:
        results.append(f"✓ Real dataset intact ({len(real_matches)} matches)")
    else:
        results.append("⚠️  Real dataset unexpectedly empty")

    # Clear real dataset
    success, message, count = clear_all_confirmed_matches(dataset='real')
    if success:
        results.append(f"✓ {message}")

    return results


def test_update_existing():
    """Test updating an existing match"""
    results = []
    results.append("### TEST 5: Update Existing Match")

    # Save initial match
    success, message = save_confirmed_match(
        product_name='Update Test Product',
        slide_index=50,
        slide_title='ORIGINAL SLIDE',
        dataset='demo',
        match_type='fuzzy_confirmed',
        confidence=70
    )
    results.append(f"Initial save: {message}")

    # Update the same product with different slide
    success, message = save_confirmed_match(
        product_name='Update Test Product',
        slide_index=60,
        slide_title='UPDATED SLIDE',
        dataset='demo',
        match_type='alternative_selected',
        confidence=85
    )
    results.append(f"Update save: {message}")

    # Verify update
    match = get_confirmed_match('Update Test Product', 'demo')
    if match and match['slide_title'] == 'UPDATED SLIDE':
        results.append(f"✓ Match successfully updated to: {match['slide_title']}")
        results.append(f"  New confidence: {match['confidence']}%")
    else:
        results.append("✗ Match not updated correctly")

    # Clean up
    delete_confirmed_match('Update Test Product', 'demo')

    return results


def main():
    """Run all tests in Streamlit UI"""
    st.title("Match Memory System Tests")
    st.markdown("Testing confirmed match storage and retrieval functionality")

    if st.button("Run All Tests", type="primary"):
        st.markdown("---")

        try:
            with st.spinner("Running tests..."):
                # Test 1
                results = test_save_and_load()
                for line in results:
                    st.markdown(line)
                st.markdown("---")

                # Test 2
                results = test_get_individual_match()
                for line in results:
                    st.markdown(line)
                st.markdown("---")

                # Test 3
                results = test_delete_match()
                for line in results:
                    st.markdown(line)
                st.markdown("---")

                # Test 4
                results = test_clear_all()
                for line in results:
                    st.markdown(line)
                st.markdown("---")

                # Test 5
                results = test_update_existing()
                for line in results:
                    st.markdown(line)
                st.markdown("---")

                st.success("✓ ALL TESTS COMPLETED")

        except Exception as e:
            st.error(f"✗ TEST FAILED: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

    else:
        st.info("Click 'Run All Tests' to start testing the match memory system")

        with st.expander("Test Details"):
            st.markdown("""
            **Test 1: Save and Load Matches**
            - Saves 3 test matches (2 demo, 1 real)
            - Loads matches by dataset
            - Verifies filtering works

            **Test 2: Get Individual Match**
            - Tests exact match lookup
            - Tests variant matching (normalization)
            - Tests dataset isolation

            **Test 3: Delete Individual Match**
            - Deletes a match
            - Verifies deletion succeeded

            **Test 4: Clear All Matches**
            - Clears all matches for demo dataset
            - Verifies real dataset unaffected
            - Clears real dataset

            **Test 5: Update Existing Match**
            - Saves a match
            - Updates same product with new slide
            - Verifies update succeeded
            """)


if __name__ == "__main__":
    main()
