"""
Test: Refresh Data Button Fix

This test verifies that the "Refresh Data" button actually clears the cache
and fetches fresh data from Google Sheets instead of returning cached data.

Bug Fixed:
- Button was calling load_pricing_data() without clearing cache first
- Users got cached data instead of fresh data
- Now clears cache with load_pricing_data.clear() before fetching

Test Instructions:
1. Run this script: streamlit run scripts/features/test_refresh_data_fix.py
2. Click "Simulate Initial Load" to load data (will cache for 5 minutes)
3. Click "Simulate Manual Edit in Google Sheets" to change test timestamp
4. WITHOUT FIX: Click "Refresh Data (OLD)" - returns cached timestamp (no change)
5. WITH FIX: Click "Refresh Data (NEW)" - returns fresh timestamp (changed!)

Expected Results:
- OLD button: Timestamp doesn't change (cached data returned)
- NEW button: Timestamp changes (fresh data fetched)
- Cooldown: NEW button disabled for 30 seconds after use
"""

import streamlit as st
from datetime import datetime
import time

st.title("🧪 Test: Refresh Data Button Fix")

st.markdown("""
### Bug Description
The "Refresh Data" button was returning cached data instead of fetching fresh data from Google Sheets.

**Root Cause:** Button didn't clear the cache before calling `load_pricing_data()`

**Impact:** Users clicking "Refresh Data" got the same cached data (no actual refresh)
""")

st.markdown("---")

# Initialize session state
if 'test_data' not in st.session_state:
    st.session_state.test_data = None
if 'test_loaded_at' not in st.session_state:
    st.session_state.test_loaded_at = None
if 'last_manual_refresh' not in st.session_state:
    st.session_state.last_manual_refresh = None
if 'simulated_sheet_timestamp' not in st.session_state:
    st.session_state.simulated_sheet_timestamp = datetime.now()

# Mock cached data loader (simulates load_pricing_data with 5-minute TTL)
@st.cache_data(ttl=300, show_spinner="Loading test data...")
def mock_load_data():
    """
    Simulates load_pricing_data() with 5-minute cache.
    Returns the simulated timestamp from "Google Sheets".
    """
    # In real app, this fetches from Google Sheets
    # Here we simulate it by returning session state value
    return {
        'timestamp': st.session_state.simulated_sheet_timestamp,
        'loaded_at': datetime.now()
    }

# Section 1: Simulate Initial Load
st.markdown("### Step 1: Simulate Initial Load")
st.markdown("Click below to load data (will be cached for 5 minutes)")

if st.button("Simulate Initial Load", use_container_width=True):
    data = mock_load_data()
    st.session_state.test_data = data
    st.session_state.test_loaded_at = data['loaded_at']
    st.success("Data loaded and cached!")

# Show current cached data
if st.session_state.test_data:
    st.info(f"**Current cached timestamp:** {st.session_state.test_data['timestamp'].strftime('%H:%M:%S')}")
    st.caption(f"Loaded at: {st.session_state.test_loaded_at.strftime('%H:%M:%S')}")
else:
    st.warning("No data loaded yet. Click 'Simulate Initial Load' first.")

st.markdown("---")

# Section 2: Simulate Manual Edit
st.markdown("### Step 2: Simulate Manual Edit in Google Sheets")
st.markdown("This simulates someone editing the Google Sheet (changing the timestamp)")

if st.button("Simulate Manual Edit in Google Sheets", use_container_width=True):
    # Update the "sheet" value
    st.session_state.simulated_sheet_timestamp = datetime.now()
    st.success(f"Sheet updated! New timestamp: {st.session_state.simulated_sheet_timestamp.strftime('%H:%M:%S')}")
    st.info("Now try the refresh buttons below to see which one gets the new timestamp")

st.markdown("---")

# Section 3: Test OLD Implementation (without cache clear)
st.markdown("### Step 3a: Test OLD Implementation (Bug)")
st.markdown("❌ This is how the button worked BEFORE the fix")

if st.button("Refresh Data (OLD - No Cache Clear)", use_container_width=True, type="secondary"):
    # OLD implementation: just call load function (cache returns old data)
    data = mock_load_data()  # Returns cached data!
    st.session_state.test_data = data
    st.session_state.test_loaded_at = data['loaded_at']

    st.warning("⚠️ OLD: Returned cached data (no actual refresh)")
    st.caption(f"Timestamp: {data['timestamp'].strftime('%H:%M:%S')} (unchanged)")

st.markdown("---")

# Section 4: Test NEW Implementation (with cache clear)
st.markdown("### Step 3b: Test NEW Implementation (Fixed)")
st.markdown("✅ This is how the button works AFTER the fix")

# Check cooldown (30-second minimum between refreshes)
last_refresh = st.session_state.last_manual_refresh
can_refresh = True
cooldown_remaining = 0

if last_refresh:
    time_since_refresh = (datetime.now() - last_refresh).seconds
    if time_since_refresh < 30:
        can_refresh = False
        cooldown_remaining = 30 - time_since_refresh

if st.button("Refresh Data (NEW - With Cache Clear)", use_container_width=True, disabled=not can_refresh, type="primary"):
    if can_refresh:
        # NEW implementation: clear cache first, then load
        mock_load_data.clear()  # ✅ Clear cache
        data = mock_load_data()  # Returns fresh data!
        st.session_state.test_data = data
        st.session_state.test_loaded_at = data['loaded_at']
        st.session_state.last_manual_refresh = datetime.now()

        st.success("✅ NEW: Cache cleared, fresh data fetched!")
        st.caption(f"Timestamp: {data['timestamp'].strftime('%H:%M:%S')} (updated!)")

if not can_refresh:
    st.info(f"⏳ Cooldown: Please wait {cooldown_remaining}s before refreshing again (API rate limit protection)")
else:
    st.caption("Data auto-refreshes every 5 minutes")

st.markdown("---")

# Summary
st.markdown("### Summary")
st.markdown("""
**Expected Behavior:**
1. Load initial data (cached for 5 minutes)
2. Simulate manual edit (changes timestamp in "Google Sheets")
3. Click OLD button → Returns cached timestamp (unchanged) ❌
4. Click NEW button → Returns fresh timestamp (updated) ✅
5. NEW button has 30-second cooldown to prevent API rate limiting

**Result:** NEW implementation correctly fetches fresh data by clearing cache first!
""")

st.markdown("---")

# Technical Details
with st.expander("📋 Technical Details"):
    st.markdown("""
    ### Implementation Comparison

    **OLD (Broken):**
    ```python
    if st.button("Refresh Data"):
        # No cache clear - returns cached data!
        df_template, df_metadata, df_partner_info = load_pricing_data(dataset)
        st.session_state.df_template = df_template
        st.rerun()
    ```

    **NEW (Fixed):**
    ```python
    if st.button("Refresh Data", disabled=not can_refresh):
        if can_refresh:
            # Clear cache first - forces fresh fetch!
            load_pricing_data.clear()
            df_template, df_metadata, df_partner_info = load_pricing_data(dataset)
            st.session_state.df_template = df_template
            st.session_state.last_manual_refresh = datetime.now()
            st.rerun()

    if not can_refresh:
        st.caption(f"Please wait {cooldown_remaining}s...")
    ```

    ### API Rate Limiting Protection
    - **Google Sheets API Limit:** 100 requests per 100 seconds per user
    - **Each refresh:** 3 API calls (Data, Metadata, Partner-Specific Info)
    - **Cooldown:** 30 seconds minimum between manual refreshes
    - **Max spam:** 3 refreshes per 100 seconds = 9 API calls (safe)
    - **Auto-refresh:** Every 5 minutes (TTL cache expiration)
    """)
