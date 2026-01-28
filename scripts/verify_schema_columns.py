"""
Verify Schema: Check if all v8.1.0 columns are loading from Google Sheets

This script verifies that:
1. All 45 expected columns from v8.1.0 schema are present
2. No columns are missing or misnamed
3. Data is loading correctly
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import load_pricing_data

st.title("🔍 Schema Column Verification")
st.markdown("Verify all v8.1.0 schema columns (45 total) are loading from Google Sheets")

# Expected columns from schema_reference.md v8.1.0
EXPECTED_COLUMNS = [
    "Partner",  # 1
    "Product/Service",  # 2
    "Has Variants (Y/N)",  # 3
    "Variant Type",  # 4
    "Purchase Description (to Partner)",  # 5
    "Billing Description (to Client)",  # 6
    "Marketing Description (Website)",  # 7
    "MOQ (Partner)",  # 8
    "MOV (Partner)",  # 9
    "MOQ (PBP)",  # 10
    "MOV (PBP)",  # 11
    "Pricing Tiers (Y/N)",  # 12
    "Pricing Tiers Info",  # 13
    "PBP Cost (No Tiers/Tier 1)",  # 14
    "PBP Cost: Tier 2",  # 15
    "PBP Cost: Tier 3",  # 16
    "PBP Cost: Tier 4",  # 17
    "PBP Cost: Tier 5",  # 18
    "PBP Cost: Tier 6",  # 19
    "Cost Basis (Per Item/Per Case)",  # 20
    "Units per Case",  # 21
    "PBP Cost (Per-Unit, No Tiers, Calculated)",  # 22
    "Pricing Logic",  # 23
    "Shipping Add-On % (of Cost)",  # 24
    "Other Add-On % (of Cost)",  # 25 - NEW in v8.1.0
    "Pricing Notes",  # 26
    "Vendor Published MSRP",  # 27
    "Vendor Markup (No Tiers, Calculated)",  # 28
    "PBP Markup (Vendor+Add-On, No Tiers)",  # 29
    "PBP MSRP (Per-Unit, No Tiers, Calculated)",  # 30
    "PBP MSRP (Website)",  # 31
    "PBP Cost: Customization Setup Fee",  # 32
    "Client Price: Customization Setup Fee",  # 33
    "PBP Cost: Customization Cost per Unit",  # 34
    "Client Price: Customization Cost per Unit",  # 35
    "Customization Info",  # 36
    "Country of Origin (Made In)",  # 37
    "Country of Origin (Ships From)",  # 38
    "PBP Cost: Shipping Cost per Unit",  # 39
    "Client Price: Shipping Price per Unit",  # 40
    "Shipping Details",  # 41
    "Tariff Estimate ($)",  # 42
    "Tariff Estimate (%)",  # 43
    "Tariff Info",  # 44
    "Data Collection Notes",  # 45
]

st.markdown("---")

# Section 1: Load Data
st.header("1. Load Data and Check Columns")

if 'selected_dataset' not in st.session_state:
    st.session_state.selected_dataset = 'real'

dataset = st.selectbox("Select Dataset", ['real', 'demo'], index=0)

if st.button("Load Data and Verify Schema", use_container_width=True, type="primary"):
    try:
        # Clear cache and load fresh
        load_pricing_data.clear()
        df_template, df_metadata, df_partner_info = load_pricing_data(dataset)

        st.success(f"✅ Loaded {len(df_template)} products from {dataset} dataset")

        # Get actual columns
        actual_columns = list(df_template.columns)

        st.markdown("---")
        st.subheader("📊 Column Analysis")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Expected Columns", len(EXPECTED_COLUMNS))
        with col2:
            st.metric("Actual Columns", len(actual_columns))

        # Check for missing columns
        missing = set(EXPECTED_COLUMNS) - set(actual_columns)
        extra = set(actual_columns) - set(EXPECTED_COLUMNS)
        matching = set(EXPECTED_COLUMNS) & set(actual_columns)

        st.markdown("---")

        # Results
        if len(missing) == 0 and len(extra) == 0:
            st.success("🎉 **PERFECT MATCH!** All expected columns are present and no unexpected columns.")
        else:
            st.warning("⚠️ Schema mismatch detected")

        # Matching columns
        with st.expander(f"✅ Matching Columns ({len(matching)})", expanded=True):
            if matching:
                for i, col in enumerate(sorted(matching), 1):
                    st.text(f"{i}. {col}")
            else:
                st.info("No matching columns")

        # Missing columns
        if missing:
            with st.expander(f"❌ Missing from Google Sheets ({len(missing)})", expanded=True):
                st.error("These columns are in the schema but NOT in Google Sheets:")
                for col in sorted(missing):
                    st.text(f"• {col}")
                st.markdown("**Action Required:** Add these columns to the Google Sheet")

        # Extra columns
        if extra:
            with st.expander(f"⚠️ Extra in Google Sheets ({len(extra)})", expanded=True):
                st.warning("These columns are in Google Sheets but NOT in schema:")
                for col in sorted(extra):
                    st.text(f"• {col}")
                st.markdown("**Possible Reasons:**")
                st.markdown("- Old column names (should be renamed)")
                st.markdown("- Typos in column names")
                st.markdown("- New columns not yet documented")

        st.markdown("---")

        # Show all actual columns
        with st.expander("📋 All Columns from Google Sheets (Raw List)"):
            for i, col in enumerate(actual_columns, 1):
                st.text(f"{i}. {col}")

        st.markdown("---")

        # Section 2: Check Critical New Columns (v8.1.0)
        st.subheader("🔍 Critical New Columns Check")
        st.markdown("Verify v8.1.0 additions are present:")

        critical_columns = {
            "Other Add-On % (of Cost)": "NEW in v8.1.0 - Non-shipping markup add-on",
            "Cost Basis (Per Item/Per Case)": "Renamed from 'Cost Basis (Per Item/Per Package)'",
            "Units per Case": "Renamed from 'Units per Package'",
            "PBP Cost (No Tiers/Tier 1)": "Renamed from 'PBP Cost (No Tiers)'",
        }

        for col, note in critical_columns.items():
            if col in actual_columns:
                st.success(f"✅ **{col}** - {note}")
            else:
                st.error(f"❌ **{col}** - {note}")

        st.markdown("---")

        # Section 3: Sample Data
        st.subheader("📄 Sample Data (First 3 Products)")

        # Show key columns
        display_cols = [
            "Partner",
            "Product/Service",
            "PBP Cost (No Tiers/Tier 1)",
            "Pricing Logic",
            "Other Add-On % (of Cost)",
            "Units per Case"
        ]

        # Filter to only columns that exist
        available_display_cols = [col for col in display_cols if col in df_template.columns]

        if available_display_cols:
            st.dataframe(df_template.head(3)[available_display_cols])
        else:
            st.error("None of the key columns are available to display")

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.exception(e)

st.markdown("---")

# Instructions
st.info("""
**What to do if columns are missing:**

1. **Open Google Sheets** and check the header row (row 7)
2. **Compare with expected columns** listed above
3. **Add any missing columns** in the exact spelling shown
4. **Rename any old columns** to new names (e.g., "Units per Package" → "Units per Case")
5. **Run this script again** to verify

**Common issues:**
- Typos in column names (case-sensitive!)
- Extra spaces before/after column names
- Old column names not yet updated
- Columns in wrong order (shouldn't matter, but verify)
""")
