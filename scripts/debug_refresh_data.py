"""
Debug Script: Refresh Data Investigation

This script helps diagnose why the "Refresh Data" button isn't showing updated data.

It will:
1. Show current cached data
2. Show what's in session state
3. Show what's in Google Sheets
4. Test if cache clearing works
5. Show timestamps and data samples
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_loader import load_pricing_data, connect_to_sheets

st.title("🔍 Debug: Refresh Data Investigation")

st.markdown("""
This script will help us understand why refreshed data isn't showing up.
We'll check each step of the data flow.
""")

st.markdown("---")

# Initialize session state
if 'selected_dataset' not in st.session_state:
    st.session_state.selected_dataset = 'real'

if 'debug_refresh_counter' not in st.session_state:
    st.session_state.debug_refresh_counter = 0

# Section 1: Check Cached Function
st.header("1. Check Cached Function")
st.markdown("Let's see what `load_pricing_data()` returns (this might be cached)")

if st.button("Call load_pricing_data() [May Return Cached]", use_container_width=True):
    try:
        df_template, df_metadata, df_partner_info = load_pricing_data(st.session_state.selected_dataset)

        st.success("✅ Function called successfully")
        st.write(f"**Products loaded:** {len(df_template)}")
        st.write(f"**First product:** {df_template.iloc[0]['Product/Service'] if len(df_template) > 0 else 'N/A'}")
        st.write(f"**Last product:** {df_template.iloc[-1]['Product/Service'] if len(df_template) > 0 else 'N/A'}")

        # Show first 3 products
        st.markdown("**First 3 products:**")
        st.dataframe(df_template.head(3)[['Partner', 'Product/Service', 'PBP Cost (No Tiers/Tier 1)']])

    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("---")

# Section 2: Clear Cache and Reload
st.header("2. Clear Cache and Reload")
st.markdown("Now let's clear the cache and reload to see if we get fresh data")

if st.button("Clear Cache + Reload [Should Get Fresh Data]", use_container_width=True, type="primary"):
    try:
        # Clear cache
        st.info("Clearing cache...")
        load_pricing_data.clear()

        # Reload
        st.info("Loading fresh data from Google Sheets...")
        df_template, df_metadata, df_partner_info = load_pricing_data(st.session_state.selected_dataset)

        # Store in session state
        st.session_state.df_template = df_template
        st.session_state.df_metadata = df_metadata
        st.session_state.df_partner_info = df_partner_info
        st.session_state.data_loaded_at = datetime.now()
        st.session_state.debug_refresh_counter += 1

        st.success("✅ Cache cleared and fresh data loaded!")
        st.write(f"**Refresh counter:** {st.session_state.debug_refresh_counter}")
        st.write(f"**Products loaded:** {len(df_template)}")
        st.write(f"**Loaded at:** {datetime.now().strftime('%H:%M:%S')}")

        # Show first 3 products
        st.markdown("**First 3 products (fresh from Google Sheets):**")
        st.dataframe(df_template.head(3)[['Partner', 'Product/Service', 'PBP Cost (No Tiers/Tier 1)']])

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

st.markdown("---")

# Section 3: Check Session State
st.header("3. Check Session State")
st.markdown("What data is stored in session state?")

if 'df_template' in st.session_state:
    df = st.session_state.df_template
    st.success("✅ Data found in session state")
    st.write(f"**Products in session state:** {len(df)}")
    st.write(f"**First product:** {df.iloc[0]['Product/Service'] if len(df) > 0 else 'N/A'}")
    st.write(f"**Last product:** {df.iloc[-1]['Product/Service'] if len(df) > 0 else 'N/A'}")

    if 'data_loaded_at' in st.session_state:
        st.write(f"**Loaded at:** {st.session_state.data_loaded_at.strftime('%H:%M:%S')}")

    st.markdown("**First 3 products from session state:**")
    st.dataframe(df.head(3)[['Partner', 'Product/Service', 'PBP Cost (No Tiers/Tier 1)']])

    # Show full data in expander
    with st.expander("📋 Show All Products in Session State"):
        st.dataframe(df[['Partner', 'Product/Service', 'PBP Cost (No Tiers/Tier 1)']])
else:
    st.warning("⚠️ No data in session state yet. Click 'Clear Cache + Reload' above.")

st.markdown("---")

# Section 4: Direct Google Sheets Check
st.header("4. Direct Google Sheets Check")
st.markdown("Let's bypass all caching and read directly from Google Sheets")

if st.button("Read Direct from Google Sheets [No Cache]", use_container_width=True):
    try:
        st.info("Connecting to Google Sheets (bypassing all caches)...")

        # Get fresh connection
        gc = connect_to_sheets()

        # Get spreadsheet URL
        from src.data_loader import DATASET_CONFIGS
        config = DATASET_CONFIGS[st.session_state.selected_dataset]
        spreadsheet_url = config['url']

        st.write(f"**Dataset:** {config['name']}")
        st.write(f"**URL:** {spreadsheet_url}")

        # Open spreadsheet
        spreadsheet = gc.open_by_url(spreadsheet_url)

        # Get Data sheet
        template_sheet = spreadsheet.worksheet("Data")
        template_values = template_sheet.get_all_values()

        # Get header row (row 7, index 6)
        raw_headers = template_values[6]

        # Find first non-empty column
        first_col_idx = 0
        for i, header in enumerate(raw_headers):
            if header.strip():
                first_col_idx = i
                break

        # Get headers
        headers = [col.strip() for col in raw_headers[first_col_idx:]]

        # Get data rows (skip header row)
        data_rows = [row[first_col_idx:] for row in template_values[7:]]

        # Filter out empty rows
        data_rows = [row for row in data_rows if row[0].strip()]  # Partner column not empty

        st.success(f"✅ Read {len(data_rows)} rows directly from Google Sheets!")
        st.write(f"**Sheet has {len(template_values)} total rows**")
        st.write(f"**First data row (index 7):** {data_rows[0][0:3] if len(data_rows) > 0 else 'N/A'}")
        st.write(f"**Last data row:** {data_rows[-1][0:3] if len(data_rows) > 0 else 'N/A'}")

        # Show first few rows
        st.markdown("**First 5 data rows from Google Sheets:**")
        import pandas as pd
        df_direct = pd.DataFrame(data_rows, columns=headers)
        st.dataframe(df_direct.head(5)[['Partner', 'Product/Service', 'PBP Cost (No Tiers/Tier 1)']])

        # Compare with session state
        if 'df_template' in st.session_state:
            st.markdown("---")
            st.subheader("🔍 Comparison: Google Sheets vs Session State")

            df_session = st.session_state.df_template

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Google Sheets (Direct)**")
                st.write(f"Rows: {len(df_direct)}")
                st.write(f"First product: {df_direct.iloc[0]['Product/Service']}")

            with col2:
                st.markdown("**Session State (Cached)**")
                st.write(f"Rows: {len(df_session)}")
                st.write(f"First product: {df_session.iloc[0]['Product/Service']}")

            if len(df_direct) == len(df_session):
                st.success("✅ Row counts match!")
            else:
                st.error(f"❌ Row count mismatch! Google Sheets has {len(df_direct)}, Session State has {len(df_session)}")

            # Check if first product matches
            if df_direct.iloc[0]['Product/Service'] == df_session.iloc[0]['Product/Service']:
                st.success("✅ First product matches!")
            else:
                st.error("❌ First product DOES NOT match!")
                st.write("Google Sheets:", df_direct.iloc[0]['Product/Service'])
                st.write("Session State:", df_session.iloc[0]['Product/Service'])

    except Exception as e:
        st.error(f"❌ Error reading from Google Sheets: {e}")
        st.exception(e)

st.markdown("---")

# Section 5: Cache Info
st.header("5. Cache Information")
st.markdown("Details about Streamlit's caching")

st.code("""
@st.cache_data(ttl=300)  # 5 minute cache
def load_pricing_data(dataset='demo'):
    # This function is cached for 5 minutes
    # Calling .clear() should force a fresh load
    ...
""")

st.info("""
**How caching works:**
1. First call to `load_pricing_data('real')` fetches from Google Sheets (slow)
2. Result is cached for 5 minutes
3. Subsequent calls within 5 minutes return cached result (fast)
4. After 5 minutes, cache expires and fresh fetch happens
5. Calling `.clear()` immediately invalidates cache

**Expected behavior after clicking 'Refresh Data':**
1. `load_pricing_data.clear()` is called
2. Next `load_pricing_data('real')` fetches fresh data
3. Fresh data stored in session state
4. All tabs use session state data
5. User sees updated data ✅
""")

st.markdown("---")

# Section 6: Recommendations
st.header("6. Debugging Recommendations")

st.markdown("""
**If you're still not seeing updated data after refresh:**

1. **Check Google Sheets directly:**
   - Click "Read Direct from Google Sheets" above
   - Compare with Session State data
   - If they match → Cache clearing is working, problem is elsewhere
   - If they don't match → Cache isn't being cleared properly

2. **Check browser cache:**
   - Hard refresh the page: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Clear browser cache
   - Close and reopen browser

3. **Check what changed:**
   - What column/field did you change in Google Sheets?
   - Is that column being loaded? (Check in data display above)
   - Is it the correct sheet? ("Data" sheet, not "Metadata" or "Partner-Specific Info")

4. **Check for errors:**
   - Look at terminal/console output for error messages
   - Check if Google Sheets API quota is exceeded

5. **Verify the change exists:**
   - Open Google Sheets in browser
   - Verify your change is saved (not just in edit mode)
   - Check you're editing the correct spreadsheet (real vs demo)
""")

st.markdown("---")

st.info("💡 **Tip:** Run this script side-by-side with the main app to compare data")
