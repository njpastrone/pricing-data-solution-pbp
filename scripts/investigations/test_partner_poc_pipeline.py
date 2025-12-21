#!/usr/bin/env python3
"""
Comprehensive test script for Partner POC data pipeline investigation.
This script traces the complete data flow from Google Sheets to Tab 4 display.
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from src.data_loader import load_pricing_data, connect_to_sheets
from src.helpers import extract_partner_contacts

def test_google_sheets_connection():
    """Test 1: Verify Google Sheets connection and Partner-Specific Info sheet exists"""
    print("\n" + "="*50)
    print("TEST 1: Google Sheets Connection")
    print("="*50)

    try:
        client = connect_to_sheets()
        print("✅ Successfully connected to Google Sheets")

        # Try to open the spreadsheet
        spreadsheet = client.open("data/master/master_pricing_template_10_14")
        print(f"✅ Opened spreadsheet: {spreadsheet.title}")

        # List all sheets
        sheets = spreadsheet.worksheets()
        sheet_names = [sheet.title for sheet in sheets]
        print(f"📋 Available sheets: {sheet_names}")

        # Check if Partner-Specific Info exists
        if "Partner-Specific Info" in sheet_names:
            print("✅ 'Partner-Specific Info' sheet exists")
            return True, spreadsheet
        else:
            print("❌ 'Partner-Specific Info' sheet NOT FOUND")
            print("   This is likely the root cause - the sheet doesn't exist!")
            return False, None

    except Exception as e:
        print(f"❌ Failed to connect: {str(e)}")
        return False, None

def test_load_partner_info():
    """Test 2: Load Partner-Specific Info data and examine structure"""
    print("\n" + "="*50)
    print("TEST 2: Load Partner-Specific Info Data")
    print("="*50)

    try:
        # Use the same function the app uses
        df_template, df_metadata, df_partner_info = load_pricing_data('demo')

        if df_partner_info is None:
            print("❌ No data loaded - df_partner_info is None")
            return None

        print(f"✅ Loaded dataframe with shape: {df_partner_info.shape}")
        print(f"   Rows: {len(df_partner_info)}, Columns: {len(df_partner_info.columns)}")

        # Show column names
        print("\n📋 Column names:")
        for i, col in enumerate(df_partner_info.columns):
            print(f"   [{i}] '{col}'")

        # Show first few rows
        print("\n📊 First 3 rows of data:")
        print(df_partner_info.head(3).to_string())

        # Check for expected POC columns
        expected_cols = ['Partner', 'POC Name', 'POC Email', 'POC Phone']
        found_cols = []
        missing_cols = []

        for col in expected_cols:
            if col in df_partner_info.columns:
                found_cols.append(col)
            else:
                # Check variations
                variations = [col.lower(), col.upper(), col.replace(' ', '_'),
                             col.replace('POC', 'Contact'), col.replace(' ', '')]
                found_variation = False
                for var in variations:
                    if any(var in str(c) for c in df_partner_info.columns):
                        found_cols.append(f"{col} (found as variation)")
                        found_variation = True
                        break
                if not found_variation:
                    missing_cols.append(col)

        print("\n📋 Expected columns check:")
        for col in found_cols:
            print(f"   ✅ {col}")
        for col in missing_cols:
            print(f"   ❌ {col} - MISSING")

        return df_partner_info

    except Exception as e:
        print(f"❌ Failed to load data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_extract_partner_contacts(df_partner_info):
    """Test 3: Extract partner contacts using the helper function"""
    print("\n" + "="*50)
    print("TEST 3: Extract Partner Contacts")
    print("="*50)

    if df_partner_info is None:
        print("⚠️ Skipping - no data to extract from")
        return None

    try:
        partner_contacts = extract_partner_contacts(df_partner_info)

        if not partner_contacts:
            print("❌ No partner contacts extracted (empty dictionary)")
            print("   This means either:")
            print("   1. No 'Partner' column with data")
            print("   2. No POC columns with data")
            return None

        print(f"✅ Extracted contacts for {len(partner_contacts)} partners")

        # Show extracted data
        print("\n📋 Extracted Partner Contacts:")
        for partner_name, contact_info in partner_contacts.items():
            print(f"\n   Partner: '{partner_name}'")
            print(f"   - POC Name: '{contact_info.get('poc_name', '')}'")
            print(f"   - POC Email: '{contact_info.get('poc_email', '')}'")
            print(f"   - POC Phone: '{contact_info.get('poc_phone', '')}'")

            # Check if any POC data exists
            has_data = any([
                contact_info.get('poc_name'),
                contact_info.get('poc_email'),
                contact_info.get('poc_phone')
            ])
            if not has_data:
                print(f"   ⚠️ No POC data for this partner")

        return partner_contacts

    except Exception as e:
        print(f"❌ Failed to extract contacts: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_session_state_storage(partner_contacts):
    """Test 4: Verify how partner contacts are stored in session state"""
    print("\n" + "="*50)
    print("TEST 4: Session State Storage")
    print("="*50)

    # Initialize session state if not in Streamlit
    if not hasattr(st, 'session_state'):
        print("⚠️ Not running in Streamlit context - simulating session state")
        class MockSessionState:
            def __init__(self):
                self.partner_contacts = None
        st.session_state = MockSessionState()

    # Store partner contacts
    st.session_state.partner_contacts = partner_contacts

    if hasattr(st.session_state, 'partner_contacts'):
        print("✅ partner_contacts stored in session state")
        if st.session_state.partner_contacts:
            print(f"   Contains {len(st.session_state.partner_contacts)} partners")
        else:
            print("   ⚠️ But it's empty or None")
    else:
        print("❌ partner_contacts NOT in session state")

    return st.session_state.partner_contacts is not None

def test_invoice_generation_logic():
    """Test 5: Check invoice generation logic for Partner POCs"""
    print("\n" + "="*50)
    print("TEST 5: Invoice Generation Logic")
    print("="*50)

    print("📋 Invoice generation expects:")
    print("   1. st.session_state.partner_contacts to exist")
    print("   2. Dictionary structure: {partner_name: {poc_name, poc_email, poc_phone}}")
    print("   3. Partners in order (from st.session_state.order_items)")

    # Simulate order with partners
    test_partners = ['Partner X', 'She Is Hope', 'Homeless Garden Project']
    print(f"\n🧪 Testing with partners: {test_partners}")

    # Check if partner_contacts would work
    if hasattr(st.session_state, 'partner_contacts') and st.session_state.partner_contacts:
        for partner in test_partners:
            if partner in st.session_state.partner_contacts:
                contact = st.session_state.partner_contacts[partner]
                print(f"   ✅ {partner}: Found POC data")
            else:
                print(f"   ❌ {partner}: No POC data")
    else:
        print("   ❌ No partner_contacts in session state - POCs won't display")

def check_raw_sheet_data():
    """Directly check the raw Google Sheets data"""
    print("\n" + "="*50)
    print("DIRECT SHEET INSPECTION")
    print("="*50)

    try:
        client = connect_to_sheets()
        spreadsheet = client.open("data/master/master_pricing_template_10_14")

        # Try to get Partner-Specific Info sheet
        try:
            sheet = spreadsheet.worksheet("Partner-Specific Info")
            print("✅ Found 'Partner-Specific Info' sheet")

            # Get all values
            all_values = sheet.get_all_values()

            if not all_values:
                print("❌ Sheet exists but is empty")
                return

            print(f"📊 Sheet has {len(all_values)} rows")

            # Show first 5 rows (including header)
            print("\n📋 First 5 rows of raw data:")
            for i, row in enumerate(all_values[:5]):
                print(f"   Row {i}: {row[:5]}...")  # Show first 5 columns

            # Try to identify header row
            print("\n🔍 Looking for header row...")
            for i, row in enumerate(all_values[:10]):
                if any('partner' in str(cell).lower() for cell in row):
                    print(f"   Found potential header at row {i}: {row[:5]}...")
                    break

        except Exception as e:
            print(f"❌ Could not access 'Partner-Specific Info' sheet: {str(e)}")
            print("   The sheet might not exist or might be named differently")

            # List available sheets
            sheets = spreadsheet.worksheets()
            print("\n📋 Available sheets in spreadsheet:")
            for sheet in sheets:
                print(f"   - {sheet.title}")

    except Exception as e:
        print(f"❌ Failed to inspect sheet: {str(e)}")

def main():
    """Run all tests in sequence"""
    print("\n" + "#"*60)
    print("# PARTNER POC PIPELINE INVESTIGATION")
    print("#"*60)
    print("\nThis script will trace the complete Partner POC data pipeline")
    print("from Google Sheets to Tab 4 invoice display.\n")

    # Test 1: Connection
    success, spreadsheet = test_google_sheets_connection()

    # Test 2: Load data
    df_partner_info = test_load_partner_info()

    # Test 3: Extract contacts
    partner_contacts = test_extract_partner_contacts(df_partner_info)

    # Test 4: Session state
    stored = test_session_state_storage(partner_contacts)

    # Test 5: Invoice logic
    test_invoice_generation_logic()

    # Direct inspection
    check_raw_sheet_data()

    # Summary
    print("\n" + "="*60)
    print("INVESTIGATION SUMMARY")
    print("="*60)

    if not success:
        print("❌ Root Cause: 'Partner-Specific Info' sheet doesn't exist")
        print("   Solution: Create the sheet with columns: Partner, POC Name, POC Email, POC Phone")
    elif df_partner_info is None:
        print("❌ Root Cause: Sheet exists but can't be loaded")
        print("   Solution: Check sheet permissions and structure")
    elif not partner_contacts:
        print("❌ Root Cause: Sheet loads but no POC data extracted")
        print("   Solution: Add POC data to the sheet with correct column names")
    elif not stored:
        print("❌ Root Cause: POC data extracted but not stored in session")
        print("   Solution: Check app.py initialization code")
    else:
        print("✅ Pipeline is working - check if partners in order match sheet data")

    print("\n📋 Next Steps:")
    print("1. Check if 'Partner-Specific Info' sheet exists in Google Sheets")
    print("2. If not, create it with columns: Partner, POC Name, POC Email, POC Phone")
    print("3. Add POC data for each partner")
    print("4. Ensure Partner names match exactly between sheets")
    print("5. Restart the Streamlit app to reload data")

if __name__ == "__main__":
    main()