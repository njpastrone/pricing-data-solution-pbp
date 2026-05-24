"""
Client Order Form Module for PBP Pricing App

Handles in-app client-facing order forms:
- Loading proposal products for the form (no pricing info exposed)
- Draft save/load for form progress persistence
- Form submission to existing response sheet
- File upload storage (base64 chunked in Google Sheets)
- Session token generation for unique form links

Created: 2026-05-24
"""

import json
import uuid
import base64
from datetime import datetime
import gspread
from src.data_loader import connect_to_sheets, DATASET_CONFIGS
from src.forms_config import GOOGLE_FORM_CONFIG, RESPONSE_COLUMNS


# Sheet name for client form drafts
DRAFTS_SHEET_NAME = "client_form_drafts"

# Base64 chunk size (same as drive_helper.py)
CHUNK_SIZE = 40000


def generate_session_token():
    """
    Generate a unique, URL-safe session token for form links.

    Returns:
        str: 12-character lowercase alphanumeric token
    """
    return uuid.uuid4().hex[:12]


def load_proposal_for_client(proposal_id):
    """
    Load proposal products for the client form (no pricing info).

    Args:
        proposal_id (str): Proposal ID (e.g., "PROP_20260524_143022")

    Returns:
        dict or None: {
            'proposal_name': str,
            'products': [{'name': str, 'partner': str}, ...]
        }
        Returns None if proposal not found or error.
    """
    try:
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_proposals']['spreadsheet_id'])
        sheet = spreadsheet.worksheet('Sheet1')

        all_values = sheet.get_all_values()

        # Find row with matching proposal_id
        for row in all_values[1:]:  # Skip header
            if len(row) >= 6 and row[0] == proposal_id:
                proposal_name = row[1]
                proposal_data = json.loads(row[5])

                # Extract product list (name + partner only — no pricing)
                products = []
                items = proposal_data.get('proposal_items', proposal_data.get('items', []))
                for item in items:
                    product_data = item.get('product_data', {})
                    products.append({
                        'name': product_data.get('Product/Service', ''),
                        'partner': product_data.get('Partner', ''),
                    })

                return {
                    'proposal_name': proposal_name,
                    'products': products,
                }

        return None

    except Exception as e:
        print(f"Error loading proposal for client form: {e}")
        return None


def _serialize_form_data(form_data):
    """Serialize form data dict to JSON string for storage."""
    return json.dumps(form_data)


def _deserialize_form_data(json_string):
    """Deserialize JSON string back to form data dict."""
    if not json_string or not json_string.strip():
        return {}
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return {}


def _get_drafts_sheet():
    """
    Get or create the client_form_drafts sheet.

    Returns:
        gspread.Worksheet or None
    """
    try:
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_orders']['spreadsheet_id'])

        try:
            sheet = spreadsheet.worksheet(DRAFTS_SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=DRAFTS_SHEET_NAME, rows=100, cols=8)
            headers = [
                'Proposal_ID', 'Session_ID', 'Draft_Data_JSON',
                'File_Data_Base64', 'File_Name', 'Created_Date',
                'Updated_Date', 'Status'
            ]
            sheet.update('A1:H1', [headers])

        return sheet

    except Exception as e:
        print(f"Error accessing drafts sheet: {e}")
        return None


def save_draft(proposal_id, session_id, form_data, file_data=None, file_name=None):
    """
    Save or update a form draft in Google Sheets.

    Args:
        proposal_id (str): Proposal ID
        session_id (str): Session token
        form_data (dict): All form field values
        file_data (bytes or None): Uploaded file bytes
        file_name (str or None): Original filename

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sheet = _get_drafts_sheet()
        if sheet is None:
            return False, "Failed to connect to drafts sheet"

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        json_data = _serialize_form_data(form_data)

        # Encode file if provided
        file_b64 = ""
        if file_data:
            file_b64 = base64.b64encode(file_data).decode('utf-8')

        # Check if draft already exists for this proposal+session
        all_values = sheet.get_all_values()
        existing_row = None
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 2 and row[0] == proposal_id and row[1] == session_id:
                existing_row = i
                break

        if existing_row:
            # Update existing draft (preserve Created_Date in column F)
            sheet.update(f'C{existing_row}:E{existing_row}', [[json_data, file_b64, file_name or '']])
            sheet.update(f'G{existing_row}:H{existing_row}', [[now, 'draft']])
        else:
            # Create new draft
            sheet.append_row([
                proposal_id, session_id, json_data,
                file_b64, file_name or '', now, now, 'draft'
            ])

        return True, "Draft saved"

    except Exception as e:
        return False, f"Error saving draft: {str(e)}"


def load_draft(proposal_id, session_id):
    """
    Load a saved draft for a proposal+session.

    Args:
        proposal_id (str): Proposal ID
        session_id (str): Session token

    Returns:
        dict or None: {
            'form_data': dict,
            'file_name': str or None,
            'file_data': bytes or None,
            'updated_date': str,
            'status': str
        }
        Returns None if no draft found.
    """
    try:
        sheet = _get_drafts_sheet()
        if sheet is None:
            return None

        all_values = sheet.get_all_values()

        for row in all_values[1:]:
            if len(row) >= 8 and row[0] == proposal_id and row[1] == session_id:
                form_data = _deserialize_form_data(row[2])
                file_b64 = row[3]
                file_name = row[4] if row[4] else None
                file_data = base64.b64decode(file_b64) if file_b64 else None

                return {
                    'form_data': form_data,
                    'file_name': file_name,
                    'file_data': file_data,
                    'updated_date': row[6],
                    'status': row[7],
                }

        return None

    except Exception as e:
        print(f"Error loading draft: {e}")
        return None
