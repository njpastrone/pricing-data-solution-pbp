"""
Show ALL tiered products and their tier info to debug overlap detection.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import warnings
warnings.filterwarnings('ignore')

from src.data_loader import load_pricing_data
from src.helpers import parse_tier_info, get_column_value

def show_all_tiered():
    print(f"\n{'='*70}")
    print("ALL TIERED PRODUCTS IN REAL DATASET")
    print('='*70)

    try:
        df_template, df_metadata, df_partner_info = load_pricing_data('real')

        print(f"\n✓ Loaded {len(df_template)} products")

        # Find all tiered products
        tiered_products = []
        for idx, row in df_template.iterrows():
            has_tiers = get_column_value(row, 'Pricing Tiers (Y/N)', 'Pricing Tiers', 'N')

            if has_tiers == 'Y':
                product_name = get_column_value(row, 'Product/Service', 'Product Name', 'Unknown')
                partner = get_column_value(row, 'Partner', None, 'Unknown')
                tier_info = get_column_value(row, 'Pricing Tiers Info', 'Tier Range', '')

                tiered_products.append({
                    'product': product_name,
                    'partner': partner,
                    'tier_info': str(tier_info)
                })

        print(f"\nFound {len(tiered_products)} tiered products:\n")

        for i, item in enumerate(tiered_products, 1):
            print(f"{i}. {item['product']}")
            print(f"   Partner: {item['partner']}")
            print(f"   Tier Info: {item['tier_info']}")

            # Parse and show parsed tiers
            if item['tier_info']:
                tier_dict = parse_tier_info(item['tier_info'])
                print(f"   Parsed Tiers:")
                for tier_num, (min_qty, max_qty) in sorted(tier_dict.items()):
                    if max_qty == float('inf'):
                        print(f"     T{tier_num}: {min_qty}+")
                    else:
                        print(f"     T{tier_num}: {min_qty}-{max_qty}")

            # Check for overlaps in THIS product
            if item['tier_info']:
                tier_dict = parse_tier_info(item['tier_info'])
                tier_numbers = sorted(tier_dict.keys())

                has_overlap = False
                for j in range(len(tier_numbers) - 1):
                    t1_num = tier_numbers[j]
                    t2_num = tier_numbers[j + 1]

                    t1_min, t1_max = tier_dict[t1_num]
                    t2_min, t2_max = tier_dict[t2_num]

                    # Check for overlap
                    if t1_max != float('inf') and t1_max >= t2_min:
                        has_overlap = True
                        print(f"   ⚠️  OVERLAP DETECTED!")
                        print(f"      T{t1_num} ends at {t1_max}, T{t2_num} starts at {t2_min}")
                        print(f"      Overlap range: {t2_min}-{t1_max} ({int(t1_max - t2_min + 1)} units)")

                if not has_overlap:
                    print(f"   ✓ No overlaps")

            print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    show_all_tiered()
    print(f"{'='*70}\n")
