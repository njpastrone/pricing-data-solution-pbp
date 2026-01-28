"""
Simple script to check for tier overlaps in spreadsheet data.
Run with: python scripts/investigations/check_tier_overlaps_simple.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_pricing_data
from src.helpers import parse_tier_info, get_column_value


def check_overlaps(dataset_name):
    print(f"\n{'='*70}")
    print(f"CHECKING {dataset_name.upper()} DATASET FOR TIER OVERLAPS")
    print('='*70)

    try:
        # Load data (suppress Streamlit warnings)
        import warnings
        warnings.filterwarnings('ignore')

        df_template, df_metadata, df_partner_info = load_pricing_data(dataset_name)

        print(f"\n✓ Loaded {len(df_template)} products from {dataset_name} dataset")

        # Find products with tier ranges
        tiered_products = []
        for idx, row in df_template.iterrows():
            # Updated: Column is named "Pricing Tiers Info" not "Tier Range"
            tier_range = get_column_value(row, 'Pricing Tiers Info', 'Tier Range', '')
            has_tiers = get_column_value(row, 'Pricing Tiers (Y/N)', 'Pricing Tiers', 'N')

            if has_tiers == 'Y' and tier_range and str(tier_range).strip():
                product_name = get_column_value(row, 'Product/Service', 'Product Name', 'Unknown')
                partner = get_column_value(row, 'Partner', None, 'Unknown')
                tiered_products.append({
                    'product': product_name,
                    'partner': partner,
                    'tier_range': str(tier_range)
                })

        print(f"\n✓ Found {len(tiered_products)} products with tiered pricing")

        # Check for overlaps
        overlaps_found = []

        for item in tiered_products:
            tier_string = item['tier_range']
            tier_dict = parse_tier_info(tier_string)

            if not tier_dict:
                continue

            # Check each pair of adjacent tiers
            tier_numbers = sorted(tier_dict.keys())

            for i in range(len(tier_numbers) - 1):
                t1_num = tier_numbers[i]
                t2_num = tier_numbers[i + 1]

                t1_min, t1_max = tier_dict[t1_num]
                t2_min, t2_max = tier_dict[t2_num]

                # Check for overlap: T1's max >= T2's min means overlap
                if t1_max != float('inf') and t1_max >= t2_min:
                    overlaps_found.append({
                        'product': item['product'],
                        'partner': item['partner'],
                        'tier_string': tier_string,
                        't1_num': t1_num,
                        't1_max': t1_max,
                        't2_num': t2_num,
                        't2_min': t2_min,
                        'overlap_units': int(t1_max - t2_min + 1)
                    })

        # Display results
        if overlaps_found:
            print(f"\n⚠️  {len(overlaps_found)} OVERLAPS DETECTED!\n")

            for overlap in overlaps_found:
                print(f"Product: {overlap['product']}")
                print(f"Partner: {overlap['partner']}")
                print(f"Tier String: {overlap['tier_string']}")
                print(f"Problem: T{overlap['t1_num']} ends at {overlap['t1_max']}, "
                      f"T{overlap['t2_num']} starts at {overlap['t2_min']}")
                print(f"Overlap: {overlap['overlap_units']} units ({overlap['t2_min']}-{overlap['t1_max']})")

                # Show parsed tiers
                tier_dict = parse_tier_info(overlap['tier_string'])
                print("Parsed Tiers:")
                for tier_num, (min_qty, max_qty) in sorted(tier_dict.items()):
                    if max_qty == float('inf'):
                        print(f"  T{tier_num}: {min_qty}+")
                    else:
                        print(f"  T{tier_num}: {min_qty}-{max_qty}")
                print()

            print(f"\nRECOMMENDATIONS:")
            print(f"- Update spreadsheet data to remove overlaps")
            print(f"- Each tier should start exactly where the previous tier ends + 1")
            print(f"- Example: If T1 is 1-25, T2 should be 26-50 (not 25-50)")

        else:
            print(f"\n✓ No tier overlaps detected! All tier ranges are mutually exclusive.")

    except Exception as e:
        print(f"\n✗ Error loading {dataset_name} dataset: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check both datasets
    check_overlaps('demo')
    check_overlaps('real')

    print(f"\n{'='*70}")
    print("INVESTIGATION COMPLETE")
    print('='*70)
