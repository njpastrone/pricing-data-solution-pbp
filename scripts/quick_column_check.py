"""
Quick Column Check - Fast diagnosis of what's in Google Sheets
Run this first to see exactly what columns exist
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import load_pricing_data

st.title("🚀 Quick Column Check")
st.markdown("Fast check: What columns are actually in Google Sheets?")

# Expected NEW columns from v8.1.0
NEW_COLUMNS_V8 = {
    "PBP Cost (No Tiers/Tier 1)": "Renamed from 'PBP Cost (No Tiers)'",
    "Units per Case": "Renamed from 'Units per Package'",
    "Cost Basis (Per Item/Per Case)": "Renamed from 'Cost Basis (Per Item/Per Package)'",
    "Other Add-On % (of Cost)": "NEW in v8.1.0",
    "Pricing Logic": "NEW in v8.0.0",
    "Shipping Add-On % (of Cost)": "NEW in v8.0.0",
}

# OLD columns that should NOT exist
OLD_COLUMNS_V7 = [
    "PBP Cost (No Tiers)",
    "Units per Package",
    "Cost Basis (Per Item/Per Package)",
]

if st.button("Check Now", type="primary", use_container_width=True):
    try:
        load_pricing_data.clear()
        df, _, _ = load_pricing_data('real')

        cols = list(df.columns)

        st.success(f"✅ Loaded data with {len(cols)} columns")

        st.markdown("---")
        st.subheader("🆕 New Schema Columns (v8.x)")

        for col, note in NEW_COLUMNS_V8.items():
            if col in cols:
                st.success(f"✅ **{col}**")
                st.caption(f"   {note}")
            else:
                st.error(f"❌ **{col}** - MISSING!")
                st.caption(f"   {note}")

        st.markdown("---")
        st.subheader("🗑️ Old Schema Columns (should NOT exist)")

        found_old = False
        for col in OLD_COLUMNS_V7:
            if col in cols:
                st.warning(f"⚠️ **{col}** - OLD COLUMN STILL EXISTS!")
                st.caption("   Should be renamed to new name")
                found_old = True

        if not found_old:
            st.success("✅ No old column names found - good!")

        st.markdown("---")
        st.subheader("📋 All Columns (Full List)")

        st.text(f"Total: {len(cols)} columns\n")
        for i, col in enumerate(cols, 1):
            st.text(f"{i:2d}. {col}")

        st.markdown("---")
        st.subheader("💡 Diagnosis")

        missing = [col for col in NEW_COLUMNS_V8.keys() if col not in cols]

        if not missing:
            st.success("🎉 **All v8.x columns are present!** Schema is up to date.")
        else:
            st.error(f"❌ **{len(missing)} columns missing** from v8.x schema")
            st.markdown("**Missing columns:**")
            for col in missing:
                st.text(f"  • {col}")

            st.markdown("---")
            st.markdown("**Action Required:**")
            st.markdown("1. Open the Google Sheet")
            st.markdown("2. Check row 7 (header row)")
            st.markdown("3. Add/rename the missing columns")
            st.markdown("4. Save and refresh this page")

            # Show which old columns to rename
            if any(old in cols for old in OLD_COLUMNS_V7):
                st.markdown("---")
                st.markdown("**Quick Fix - Rename these:**")
                if "PBP Cost (No Tiers)" in cols:
                    st.code("PBP Cost (No Tiers) → PBP Cost (No Tiers/Tier 1)")
                if "Units per Package" in cols:
                    st.code("Units per Package → Units per Case")
                if "Cost Basis (Per Item/Per Package)" in cols:
                    st.code("Cost Basis (Per Item/Per Package) → Cost Basis (Per Item/Per Case)")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

st.markdown("---")
st.info("**Tip:** If columns are missing, the Google Sheet needs to be updated to v8.1.0 schema")
