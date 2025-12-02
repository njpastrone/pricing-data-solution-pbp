"""
Proposal Manager Module for PBP Pricing App

This module handles saving, loading, and managing proposals in Google Sheets.
Proposals are stored in the saved_proposals spreadsheet with the following columns:
- Proposal_ID: Unique identifier (PROP_YYYYMMDD_HHMMSS)
- Proposal_Name: User-provided name
- Created_By: Optional creator name/email
- Created_Date: Timestamp (YYYY-MM-DD HH:MM:SS)
- Dataset: Which dataset was used (demo/real)
- Proposal_Data_JSON: Serialized JSON of proposal state
"""

import json
from datetime import datetime
import streamlit as st
import gspread
from src.data_loader import connect_to_sheets, DATASET_CONFIGS


def initialize_proposals_sheet():
    """
    Initialize the saved_proposals sheet with headers if empty.

    Returns:
        gspread.Worksheet: The proposals worksheet
    """
    try:
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_proposals']['spreadsheet_id'])

        # Try to get Sheet1, or create it if it doesn't exist
        try:
            sheet = spreadsheet.worksheet('Sheet1')
        except gspread.exceptions.WorksheetNotFound:
            # Only try to create if it genuinely doesn't exist
            try:
                sheet = spreadsheet.add_worksheet(title='Sheet1', rows=100, cols=6)
            except Exception as create_error:
                # If creation fails, it might already exist - try getting it again
                sheet = spreadsheet.worksheet('Sheet1')

        # Check if headers exist
        first_row = sheet.row_values(1)
        if not first_row or first_row[0] != 'Proposal_ID':
            # Initialize with headers
            headers = ['Proposal_ID', 'Proposal_Name', 'Created_By', 'Created_Date', 'Dataset', 'Proposal_Data_JSON']
            sheet.update('A1:F1', [headers])

        return sheet

    except Exception as e:
        error_msg = str(e)
        # Only show rate limit message for actual rate limit errors (429 status code)
        if "429" in error_msg or "Quota exceeded" in error_msg:
            st.warning("""
            **Google Sheets is temporarily busy**

            The app is making too many requests to Google Sheets. This usually happens when:
            - Multiple users are using the app simultaneously
            - You're refreshing the page frequently

            **What to do:**
            1. Wait 60 seconds before trying again
            2. Avoid rapid page refreshes
            3. Your data is safe - this is just a temporary limit

            The limit will reset automatically in about 1 minute.
            """)
        else:
            # For other errors, log to console but don't show in UI (too noisy)
            print(f"Error initializing proposals sheet: {error_msg}")
        return None


def generate_proposal_id():
    """
    Generate a unique proposal ID based on current timestamp.
    Format: PROP_YYYYMMDD_HHMMSS

    Returns:
        str: Unique proposal ID
    """
    return datetime.now().strftime("PROP_%Y%m%d_%H%M%S")


def save_proposal(name, created_by, proposal_data, dataset):
    """
    Save a proposal to Google Sheets.

    Args:
        name (str): Proposal name (required)
        created_by (str): Creator name/email (optional)
        proposal_data (dict): Proposal state data to save
        dataset (str): Dataset used ('demo' or 'real')

    Returns:
        tuple: (success: bool, message: str, proposal_id: str or None)
    """
    if not name or not name.strip():
        return False, "Proposal name is required", None

    try:
        sheet = initialize_proposals_sheet()
        if sheet is None:
            return False, "Failed to connect to proposals sheet", None

        # Check if proposal name already exists
        all_values = sheet.get_all_values()
        existing_names = [row[1] for row in all_values[1:] if len(row) > 1]  # Skip header row

        if name in existing_names:
            # Suggest versioned name
            version = 2
            new_name = f"{name} (v{version})"
            while new_name in existing_names:
                version += 1
                new_name = f"{name} (v{version})"
            return False, f"Proposal '{name}' already exists. Save as '{new_name}' instead?", new_name

        # Generate unique ID and timestamp
        proposal_id = generate_proposal_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Serialize proposal data to JSON
        proposal_json = json.dumps(proposal_data)

        # Append row to sheet
        row_data = [
            proposal_id,
            name,
            created_by or "",
            timestamp,
            dataset,
            proposal_json
        ]

        sheet.append_row(row_data)

        return True, f"Proposal '{name}' saved successfully!", proposal_id

    except Exception as e:
        return False, f"Error saving proposal: {str(e)}", None


def load_all_proposals():
    """
    Load all saved proposals (metadata only, not full data).

    Returns:
        list: List of dicts with keys: proposal_id, name, created_by, created_date, dataset
              Returns empty list if error occurs
    """
    try:
        sheet = initialize_proposals_sheet()
        if sheet is None:
            return []

        all_values = sheet.get_all_values()

        if len(all_values) <= 1:  # Only headers or empty
            return []

        proposals = []
        for row in all_values[1:]:  # Skip header row
            if len(row) >= 5:  # Must have at least ID, name, creator, date, dataset
                proposals.append({
                    'proposal_id': row[0],
                    'name': row[1],
                    'created_by': row[2],
                    'created_date': row[3],
                    'dataset': row[4]
                })

        # Sort by date (newest first)
        proposals.sort(key=lambda x: x['created_date'], reverse=True)

        return proposals

    except Exception as e:
        # Silently fail - error already shown by initialize_proposals_sheet if needed
        print(f"Error loading proposals: {str(e)}")
        return []


def load_proposal_data(proposal_id):
    """
    Load full proposal data for a specific proposal ID.

    Args:
        proposal_id (str): Unique proposal ID

    Returns:
        tuple: (success: bool, data: dict or None, dataset: str or None)
    """
    try:
        sheet = initialize_proposals_sheet()
        if sheet is None:
            return False, None, None

        all_values = sheet.get_all_values()

        # Find row with matching proposal_id
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 6 and row[0] == proposal_id:
                # Deserialize JSON data
                proposal_data = json.loads(row[5])
                dataset = row[4]
                return True, proposal_data, dataset

        return False, None, None

    except Exception as e:
        st.error(f"Error loading proposal data: {str(e)}")
        return False, None, None


def delete_proposal(proposal_id):
    """
    Delete a proposal from Google Sheets.

    Args:
        proposal_id (str): Unique proposal ID to delete

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sheet = initialize_proposals_sheet()
        if sheet is None:
            return False, "Failed to connect to proposals sheet"

        all_values = sheet.get_all_values()

        # Find row with matching proposal_id
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 1 and row[0] == proposal_id:
                sheet.delete_rows(i)
                return True, "Proposal deleted successfully"

        return False, "Proposal not found"

    except Exception as e:
        return False, f"Error deleting proposal: {str(e)}"
