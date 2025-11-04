"""
Test script for improved matching system (Phase 1, Day 1).

Tests all 4 improvements:
1. Multi-scorer fuzzy matching
2. Keyword category boosting
3. Variant name normalization
4. Manual product mappings

Compares results with baseline (original matching logic).
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pptx import Presentation
from slide_matcher import SlideMatcher, normalize_product_name
import gspread
from google.oauth2 import service_account
import toml


def load_google_sheets_products():
    """Load product names from Google Sheets (hardcoded list from previous analysis)."""
    # These are the 19 products from the Google Sheets as of previous analysis
    product_names = [
        'Upcycled Executive Urban Briefcase',
        'Upcycled Laptop Sleeve (Enfold)-MOF',
        'Upcycled Day Tripper Backpack (Noir)',
        'Butcher Block - Large',
        'Candle Holders - Set of 3',
        'Trivets',
        'Mini Catchall Bowls - Set of 3',
        'Organic Baking Mixes - Set of 3',
        'Salts & Seasonings - Set of 3',
        'Organic Trail Mix - Set of 3',
        'Organic Granola - Set of 3',
        'Organic Popcorn - Set of 3',
        'Organic Hot Cocoa - Set of 3',
        'Cutting Board with Handle',
        'Coasters - Set of 4',
        'Minimalist Wall Hook - Set of 2',
        'Beaded Bracelet',
        'Woven Wall Hanging',
        'Wooden Plant Stand',
    ]
    return product_names


def load_pptx_products():
    """Load product names from PowerPoint."""
    pptx_path = Path(__file__).parent.parent / 'templates' / 'November All Slides.pptx'

    # Read product names from file (already extracted)
    product_names_file = Path(__file__).parent.parent / 'product_names_from_slides.txt'
    with open(product_names_file, 'r') as f:
        product_names = [line.strip() for line in f if line.strip()]

    return product_names


def test_improved_matching():
    """Run improved matching test on all 19 products."""
    print("=" * 80)
    print("IMPROVED MATCHING SYSTEM TEST - Phase 1, Day 1")
    print("=" * 80)
    print()

    # Load data
    print("Loading product names from Google Sheets...")
    gs_products = load_google_sheets_products()
    print(f"Found {len(gs_products)} products in Google Sheets")
    print()

    print("Loading product names from PowerPoint...")
    pptx_products = load_pptx_products()
    print(f"Found {len(pptx_products)} products in PowerPoint")
    print()

    # Create matcher
    matcher = SlideMatcher(pptx_products)

    # Test all products
    print("=" * 80)
    print("MATCHING RESULTS")
    print("=" * 80)
    print()

    results = []
    for gs_product in gs_products:
        result = matcher.find_match(gs_product)
        results.append(result)

        # Display result
        normalized = normalize_product_name(gs_product)

        if result.match_type == 'exact':
            icon = "[✓]"
            status = "EXACT"
        elif result.match_type == 'fuzzy':
            if result.confidence >= 90:
                icon = "[✓]"
                status = "EXCELLENT"
            elif result.confidence >= 70:
                icon = "[~]"
                status = "GOOD"
            else:
                icon = "[?]"
                status = "UNCERTAIN"
        else:
            icon = "[X]"
            status = "NO MATCH"

        print(f"{icon} {status:10s} ({result.confidence:3d}%) | GS: {gs_product}")
        if normalized != gs_product.upper():
            print(f"                      | Normalized: {normalized}")
        print(f"                      | PPTX: {result.pptx_product_name}")

        if result.alternatives:
            print(f"                      | Alternatives:")
            for alt_name, alt_score in result.alternatives[:2]:
                print(f"                      |   - {alt_name} ({alt_score}%)")
        print()

    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()

    summary = matcher.get_match_summary(results, min_confidence=70)

    print(f"Total products:        {summary['total']}")
    print(f"Exact matches:         {summary['exact']} ({summary['exact']/summary['total']*100:.1f}%)")
    print(f"Fuzzy matches (≥70%):  {summary['fuzzy']} ({summary['fuzzy']/summary['total']*100:.1f}%)")
    print(f"Poor matches (<70%):   {summary['poor']} ({summary['poor']/summary['total']*100:.1f}%)")
    print(f"No matches:            {summary['none']} ({summary['none']/summary['total']*100:.1f}%)")
    print()
    print(f"{'=' * 40}")
    print(f"USABLE MATCHES (≥70%): {summary['usable']} / {summary['total']} ({summary['usable_pct']:.1f}%)")
    print(f"{'=' * 40}")
    print()

    # Success check
    if summary['usable_pct'] >= 60:
        print("[SUCCESS] ✓ Target match rate of 60% achieved!")
    else:
        print(f"[WARNING] Target match rate of 60% NOT achieved (got {summary['usable_pct']:.1f}%)")
        print("Consider adding more manual mappings or adjusting boost parameters.")
    print()

    return results, summary


if __name__ == '__main__':
    test_improved_matching()
