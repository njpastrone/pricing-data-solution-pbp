"""
Investigation script to find tier overlaps in spreadsheet data.
Run with: streamlit run scripts/investigations/investigate_tier_overlaps.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_pricing_data
from src.helpers import parse_tier_info, get_column_value

st.title("Tier Overlap Investigation")
st.markdown("This script checks for overlapping tier ranges in the pricing data.")

# Dataset selector
dataset = st.sidebar.selectbox("Select Dataset", ["demo", "real"], index=1)

st.header(f"Checking {dataset.upper()} Dataset")

try:
    # Load data
    df_template, df_metadata, df_partner_info = load_pricing_data(dataset)

    st.success(f"Loaded {len(df_template)} products from {dataset} dataset")

    # Find products with tier ranges
    st.subheader("1. Products with Tiered Pricing")

    tiered_products = []
    for idx, row in df_template.iterrows():
        # Get tier range using helper (column is "Pricing Tiers Info" not "Tier Range")
        tier_range = get_column_value(row, 'Pricing Tiers Info', 'Tier Range', '')
        has_tiers = get_column_value(row, 'Pricing Tiers (Y/N)', 'Pricing Tiers', 'N')

        if has_tiers == 'Y' and tier_range and str(tier_range).strip():
            product_name = get_column_value(row, 'Product/Service', 'Product Name', 'Unknown')
            partner = get_column_value(row, 'Partner', None, 'Unknown')
            tiered_products.append({
                'Product': product_name,
                'Partner': partner,
                'Tier Range': str(tier_range)
            })

    if tiered_products:
        st.write(f"Found **{len(tiered_products)}** products with tiered pricing:")
        st.dataframe(tiered_products)
    else:
        st.warning("No tiered products found in this dataset")
        st.stop()

    # Check for overlaps
    st.subheader("2. Checking for Tier Overlaps")

    overlaps_found = []

    for item in tiered_products:
        tier_string = item['Tier Range']
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
                    'Product': item['Product'],
                    'Partner': item['Partner'],
                    'Tier String': tier_string,
                    'Overlap': f"T{t1_num} ends at {t1_max}, T{t2_num} starts at {t2_min}",
                    'Overlap Range': f"{t2_min}-{t1_max}",
                    'Affected Units': int(t1_max - t2_min + 1)
                })

    if overlaps_found:
        st.error(f"**{len(overlaps_found)} OVERLAPS DETECTED!**")

        for overlap in overlaps_found:
            with st.expander(f"⚠️ {overlap['Product']} ({overlap['Partner']})"):
                st.write(f"**Tier String:** `{overlap['Tier String']}`")
                st.write(f"**Problem:** {overlap['Overlap']}")
                st.write(f"**Overlap Range:** {overlap['Overlap Range']} ({overlap['Affected Units']} units)")

                # Parse and display all tiers
                tier_dict = parse_tier_info(overlap['Tier String'])
                st.write("**Parsed Tiers:**")
                for tier_num, (min_qty, max_qty) in sorted(tier_dict.items()):
                    if max_qty == float('inf'):
                        st.write(f"  - T{tier_num}: {min_qty}+")
                    else:
                        st.write(f"  - T{tier_num}: {min_qty}-{max_qty}")

        # Summary table
        st.subheader("3. Summary Table")
        st.dataframe(overlaps_found)

        # Recommendations
        st.subheader("4. Recommendations")
        st.markdown("""
        **To fix these overlaps:**

        1. **Update the spreadsheet data** - The tier ranges should be mutually exclusive:
           - T1 should end exactly where T2 begins minus 1
           - Example: If T1 is 112-447, T2 should start at 448 (not 447 or earlier)
           - If T2 is 448-1107, T3 should start at 1108 (not 1108 or earlier)

        2. **Current behavior with overlaps:**
           - The app checks tiers in order (T1, T2, T3, etc.)
           - It returns the FIRST matching tier
           - Quantities in the overlap zone will be assigned to the EARLIER tier
           - Example: Qty 1008 with "T2: 448-1107, T3: 1008+" will be assigned to T2

        3. **Code improvements needed:**
           - Add validation to detect overlaps when loading data
           - Warn users about data quality issues
           - Optionally: Auto-correct by using highest matching tier instead of first
        """)

    else:
        st.success("✓ No tier overlaps detected! All tier ranges are mutually exclusive.")

    # Show tier distribution
    st.subheader("5. Tier Range Examples")
    st.write("Sample tier ranges from your data:")

    for item in tiered_products[:5]:  # Show first 5
        with st.expander(f"{item['Product']} - {item['Partner']}"):
            tier_string = item['Tier Range']
            tier_dict = parse_tier_info(tier_string)

            st.write(f"**Raw:** `{tier_string}`")
            st.write("**Parsed:**")

            for tier_num, (min_qty, max_qty) in sorted(tier_dict.items()):
                if max_qty == float('inf'):
                    st.write(f"  - Tier {tier_num}: {min_qty}+ units")
                else:
                    st.write(f"  - Tier {tier_num}: {min_qty}-{max_qty} units")

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.exception(e)
