"""
Debug Google Form Responses

This script helps diagnose issues with loading form responses.
It shows:
1. Connection status to response sheet
2. All columns present in the sheet
3. All responses (regardless of import status)
4. Tracking column status

Run with: streamlit run scripts/investigations/debug_google_form_responses.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from src.data_loader import connect_to_sheets
from src.forms_config import GOOGLE_FORM_CONFIG, RESPONSE_COLUMNS

st.title("🔍 Google Form Response Debugger")
st.caption("Diagnose issues with loading form responses")

if st.button("🔄 Load Response Sheet", type="primary"):
    with st.spinner("Connecting to Google Sheets..."):
        try:
            # Connect to sheets
            gc = connect_to_sheets()
            st.success("✅ Connected to Google Sheets")

            # Open response sheet
            sheet_id = GOOGLE_FORM_CONFIG['response_sheet_id']
            sheet_name = GOOGLE_FORM_CONFIG['response_sheet_name']

            st.info(f"**Sheet ID:** {sheet_id}")
            st.info(f"**Sheet Name:** {sheet_name}")

            spreadsheet = gc.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)

            st.success(f"✅ Opened worksheet: {sheet_name}")

            # Get all data
            all_values = worksheet.get_all_values()

            if not all_values:
                st.error("❌ Sheet is empty - no data found")
                st.stop()

            # First row is headers
            headers = all_values[0]
            data_rows = all_values[1:]

            st.success(f"✅ Found {len(headers)} columns and {len(data_rows)} data rows")

            # Show columns
            st.subheader("📋 Columns in Response Sheet")
            st.caption(f"Total columns: {len(headers)}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**First 20 columns:**")
                for i, col in enumerate(headers[:20], 1):
                    st.text(f"{i}. {col}")

            with col2:
                st.markdown("**Last 10 columns:**")
                start_idx = max(0, len(headers) - 10)
                for i, col in enumerate(headers[start_idx:], start_idx + 1):
                    st.text(f"{i}. {col}")

            # Check for tracking columns
            st.subheader("🔍 Tracking Columns Status")

            tracking_cols = {
                'Imported?': RESPONSE_COLUMNS['imported'],
                'Order ID': RESPONSE_COLUMNS['order_id'],
                'Imported By': RESPONSE_COLUMNS['imported_by'],
                'Import Date': RESPONSE_COLUMNS['import_date']
            }

            missing_cols = []
            found_cols = []

            for label, col_name in tracking_cols.items():
                if col_name in headers:
                    found_cols.append(label)
                    st.success(f"✅ Found: {label} ('{col_name}')")
                else:
                    missing_cols.append(label)
                    st.error(f"❌ Missing: {label} (looking for '{col_name}')")

            if missing_cols:
                st.warning(f"**Missing {len(missing_cols)} tracking column(s).** These need to be added manually to the response sheet.")
                st.info("**To fix:** Open the Google Sheet and add these columns at the end:\n- Imported?\n- Order ID\n- Imported By\n- Import Date")

            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)

            # Show all responses
            st.subheader("📝 All Responses")
            st.caption(f"Showing all {len(df)} response(s)")

            if df.empty:
                st.info("No responses submitted yet")
            else:
                # Show key columns
                display_cols = ['Timestamp']

                # Add company name if exists
                if RESPONSE_COLUMNS['company_name'] in df.columns:
                    display_cols.append(RESPONSE_COLUMNS['company_name'])

                # Add tracking columns if they exist
                for col_name in tracking_cols.values():
                    if col_name in df.columns:
                        display_cols.append(col_name)

                st.dataframe(df[display_cols], use_container_width=True)

                # Show full data in expander
                with st.expander("📊 Show Full Response Data"):
                    st.dataframe(df, use_container_width=True)

                # Count imported vs not imported
                if 'Imported?' in df.columns:
                    imported_count = df[df['Imported?'].isin(['TRUE', 'true', True])].shape[0]
                    not_imported_count = len(df) - imported_count

                    st.metric("Total Responses", len(df))
                    col1, col2 = st.columns(2)
                    col1.metric("Already Imported", imported_count)
                    col2.metric("Not Yet Imported", not_imported_count)
                else:
                    st.info("Cannot determine import status (no 'Imported?' column)")

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.exception(e)

st.divider()

st.subheader("💡 Common Issues")

st.markdown("""
**Issue 1: "No new responses found" but you just submitted**
- ✅ Check if tracking columns exist (see above)
- ✅ Check if response actually saved to Google Sheet (open sheet manually)
- ✅ Check if service account has access to response sheet

**Issue 2: Responses show as already imported when they're not**
- ✅ Check 'Imported?' column values (should be empty or FALSE for new responses)
- ✅ Check if column name exactly matches 'Imported?' (case-sensitive)

**Issue 3: Form submission doesn't appear in sheet**
- ✅ Verify form is linked to correct response sheet
- ✅ Check if form has been published/activated
- ✅ Try submitting a test response yourself

**Issue 4: Cannot see old responses**
- ✅ This is by design - current code only shows unimported responses
- ✅ Need to update app to show all responses with filter options
""")
