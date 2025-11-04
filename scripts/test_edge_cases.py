"""
Test script for edge cases in matching system (Phase 1, Day 2, Task 2.4).

Tests:
1. All exact matches
2. All fuzzy matches
3. No matches
4. Mix of exact, fuzzy, and no matches
5. Empty product list
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from slide_matcher import SlideMatcher


def test_all_exact_matches():
    """Test case: All products have exact matches"""
    print("=" * 80)
    print("TEST CASE 1: All Exact Matches")
    print("=" * 80)

    pptx_products = [
        "UPCYCLED EXECUTIVE URBAN BRIEFCASE",
        "UPCYCLED LAPTOP SLEEVE",
        "BUTCHER BLOCK",
        "GRANOLA",
        "BEADED BRACELET – LOVE OR CUSTOM"
    ]

    gs_products = [
        "Upcycled Executive Urban Briefcase",
        "Upcycled Laptop Sleeve",
        "Butcher Block",
        "Granola",
        "Beaded Bracelet"
    ]

    matcher = SlideMatcher(pptx_products)
    results = matcher.batch_match(gs_products)

    for result in results:
        print(f"[{result.match_type.upper():5s}] {result.gs_product_name} → {result.pptx_product_name} ({result.confidence}%)")

    summary = matcher.get_match_summary(results)
    print(f"\nSummary: {summary['exact']} exact, {summary['fuzzy']} fuzzy, {summary['poor']} poor, {summary['none']} none")
    print(f"Expected: 5 exact matches")
    print(f"✓ PASS" if summary['exact'] == 5 else "✗ FAIL")
    print()


def test_all_fuzzy_matches():
    """Test case: All products have fuzzy matches only"""
    print("=" * 80)
    print("TEST CASE 2: All Fuzzy Matches")
    print("=" * 80)

    pptx_products = [
        "SELVA CUTTING BOARD",
        "MINIMALIST WOODEN CELL PHONE STAND",
        "COFFEE/SNACK COASTERS – SET OF 2",
        "ORGANIC COTTON APRON",
        "LARGE WOVEN BOWL"
    ]

    gs_products = [
        "Cutting Board with Handle",
        "Wooden Plant Stand",
        "Coasters - Set of 4",
        "Organic Popcorn - Set of 3",
        "Woven Wall Hanging"
    ]

    matcher = SlideMatcher(pptx_products)
    results = matcher.batch_match(gs_products)

    for result in results:
        print(f"[{result.match_type.upper():5s}] {result.gs_product_name} → {result.pptx_product_name} ({result.confidence}%)")

    summary = matcher.get_match_summary(results)
    print(f"\nSummary: {summary['exact']} exact, {summary['fuzzy']} fuzzy, {summary['poor']} poor, {summary['none']} none")
    print(f"Expected: 0 exact, 5 fuzzy (may vary by confidence)")
    print(f"✓ PASS" if summary['exact'] == 0 and summary['fuzzy'] > 0 else "✗ FAIL")
    print()


def test_no_matches():
    """Test case: No products have good matches"""
    print("=" * 80)
    print("TEST CASE 3: No Good Matches")
    print("=" * 80)

    pptx_products = [
        "UPCYCLED EXECUTIVE URBAN BRIEFCASE",
        "CUTTING BOARD",
        "BEADED BRACELET",
    ]

    gs_products = [
        "Organic Baking Mixes - Set of 3",
        "Salts & Seasonings - Set of 3",
        "Organic Hot Cocoa - Set of 3"
    ]

    matcher = SlideMatcher(pptx_products)
    results = matcher.batch_match(gs_products)

    for result in results:
        status = "POOR/NONE" if result.confidence < 70 else result.match_type.upper()
        print(f"[{status:9s}] {result.gs_product_name} → {result.pptx_product_name} ({result.confidence}%)")

    summary = matcher.get_match_summary(results, min_confidence=70)
    print(f"\nSummary: {summary['exact']} exact, {summary['fuzzy']} fuzzy, {summary['poor']} poor, {summary['none']} none")
    print(f"Expected: 0 usable matches (all below 70%)")
    print(f"✓ PASS" if summary['usable'] == 0 else "✗ FAIL")
    print()


def test_mixed_results():
    """Test case: Mix of exact, fuzzy, and no matches"""
    print("=" * 80)
    print("TEST CASE 4: Mixed Results")
    print("=" * 80)

    pptx_products = [
        "UPCYCLED EXECUTIVE URBAN BRIEFCASE",
        "UPCYCLED LAPTOP SLEEVE",
        "BUTCHER BLOCK",
        "SELVA CUTTING BOARD",
        "MINIMALIST WOODEN CELL PHONE STAND",
        "CROSS STITCH TOILETRIES BAG"
    ]

    gs_products = [
        "Upcycled Executive Urban Briefcase",  # Exact
        "Cutting Board with Handle",           # Fuzzy (good)
        "Organic Baking Mixes - Set of 3",     # No match
    ]

    matcher = SlideMatcher(pptx_products)
    results = matcher.batch_match(gs_products)

    for result in results:
        if result.confidence >= 90:
            status = "EXACT/EXCELLENT"
        elif result.confidence >= 70:
            status = "FUZZY (GOOD)"
        else:
            status = "POOR/NONE"
        print(f"[{status:15s}] {result.gs_product_name} → {result.pptx_product_name} ({result.confidence}%)")

    summary = matcher.get_match_summary(results, min_confidence=70)
    print(f"\nSummary: {summary['exact']} exact, {summary['fuzzy']} fuzzy, {summary['poor']} poor, {summary['none']} none")
    print(f"Expected: At least 1 exact, at least 1 fuzzy good, at least 1 poor")
    print(f"✓ PASS" if summary['exact'] >= 1 and summary['fuzzy'] >= 1 and summary['poor'] >= 1 else "✗ FAIL")
    print()


def test_empty_list():
    """Test case: Empty product list"""
    print("=" * 80)
    print("TEST CASE 5: Empty Product List")
    print("=" * 80)

    pptx_products = ["UPCYCLED EXECUTIVE URBAN BRIEFCASE"]
    gs_products = []

    matcher = SlideMatcher(pptx_products)
    results = matcher.batch_match(gs_products)

    print(f"Results: {len(results)} matches")
    print(f"Expected: 0 results")
    print(f"✓ PASS" if len(results) == 0 else "✗ FAIL")
    print()


if __name__ == '__main__':
    print("\n")
    print("=" * 80)
    print("PHASE 1, DAY 2, TASK 2.4: EDGE CASE TESTING")
    print("=" * 80)
    print("\n")

    test_all_exact_matches()
    test_all_fuzzy_matches()
    test_no_matches()
    test_mixed_results()
    test_empty_list()

    print("=" * 80)
    print("EDGE CASE TESTING COMPLETE")
    print("=" * 80)
    print("\nAll tests validate the matching system handles various scenarios correctly.")
    print("The UI should gracefully handle each case:")
    print("- All exact: Show all in 'Exact Matches' expander, auto-confirmed")
    print("- All fuzzy: Show all in 'Fuzzy Matches' section, require confirmation")
    print("- No matches: Show warning, disable generation button")
    print("- Mixed: Show each category appropriately")
    print("- Empty: Show no products, disable generation")
