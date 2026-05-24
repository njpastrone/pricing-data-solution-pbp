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
                items = proposal_data.get('proposal_products', [])
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


def submit_form(proposal_id, session_id, form_data, file_data=None, file_name=None):
    """
    Submit the completed form to the Form Responses 1 sheet.

    Writes data in the same column format as the Google Form so that
    Tab 3's import (parse_form_response) works without changes.

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
        client_obj = connect_to_sheets()
        sheet_id = GOOGLE_FORM_CONFIG['response_sheet_id']
        spreadsheet = client_obj.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(GOOGLE_FORM_CONFIG['response_sheet_name'])

        # Get headers to build row in correct column order
        headers = worksheet.row_values(1)
        if not headers:
            return False, "Response sheet has no headers"

        # Build a row matching the header columns
        row = [''] * len(headers)

        # Timestamp
        timestamp_col = RESPONSE_COLUMNS.get('timestamp', 'Timestamp')
        if timestamp_col in headers:
            row[headers.index(timestamp_col)] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        # Client info
        client_info = form_data.get('client_info', {})
        field_map = {
            'client_type': client_info.get('client_type', ''),
            'company_name': client_info.get('company_name', ''),
            'contact_name': client_info.get('contact_name', ''),
            'contact_email': client_info.get('contact_email', ''),
            'contact_phone': client_info.get('contact_phone', ''),
        }

        for key, value in field_map.items():
            col_name = RESPONSE_COLUMNS.get(key)
            if col_name and col_name in headers:
                row[headers.index(col_name)] = value

        # Products
        products = form_data.get('products', [])
        for i, product in enumerate(products[:10], start=1):
            name_col = RESPONSE_COLUMNS.get(f'line_{i}_name')
            qty_col = RESPONSE_COLUMNS.get(f'line_{i}_qty')
            notes_col = RESPONSE_COLUMNS.get(f'line_{i}_notes')

            if name_col and name_col in headers:
                row[headers.index(name_col)] = product.get('name', '')
            if qty_col and qty_col in headers:
                row[headers.index(qty_col)] = str(product.get('quantity', ''))
            if notes_col and notes_col in headers:
                row[headers.index(notes_col)] = product.get('customization_notes', '')

        # Shipping info
        shipping = form_data.get('shipping_info', {})
        shipping_map = {
            'shipping_address': shipping.get('shipping_address', ''),
            'billing_address': shipping.get('billing_address', ''),
            'drop_shipping': shipping.get('drop_shipping', ''),
            'drop_shipping_instructions': shipping.get('drop_shipping_instructions', ''),
            'in_hands_date': shipping.get('in_hands_date', ''),
        }

        for key, value in shipping_map.items():
            col_name = RESPONSE_COLUMNS.get(key)
            if col_name and col_name in headers:
                row[headers.index(col_name)] = value

        # Payment info
        payment = form_data.get('payment_info', {})
        payment_map = {
            'impact_cards': payment.get('impact_cards', ''),
            'impact_card_selection': payment.get('impact_card_selection', ''),
            'payment_preference': payment.get('payment_preference', ''),
            'payment_method': payment.get('payment_method', ''),
        }

        for key, value in payment_map.items():
            col_name = RESPONSE_COLUMNS.get(key)
            if col_name and col_name in headers:
                row[headers.index(col_name)] = value

        # Special requests
        notes = form_data.get('notes', '')
        notes_col = RESPONSE_COLUMNS.get('special_requests')
        if notes_col and notes_col in headers:
            row[headers.index(notes_col)] = notes

        # Dropshipping file name (if uploaded)
        if file_name:
            file_col = RESPONSE_COLUMNS.get('dropshipping_file', 'Dropshipping File Name')
            if file_col in headers:
                row[headers.index(file_col)] = file_name
            else:
                # Add new column if it doesn't exist yet
                headers.append(file_col)
                row.append(file_name)
                worksheet.update_cell(1, len(headers), file_col)

        # Append response row
        worksheet.append_row(row)

        # Save file to drafts sheet (so exec can download it later)
        if file_data and file_name:
            save_draft(proposal_id, session_id, form_data, file_data, file_name)

        # Mark draft as submitted
        _mark_draft_submitted(proposal_id, session_id)

        return True, "Order submitted successfully!"

    except Exception as e:
        return False, f"Error submitting form: {str(e)}"


def _mark_draft_submitted(proposal_id, session_id):
    """Mark a draft's status as 'submitted'."""
    try:
        sheet = _get_drafts_sheet()
        if sheet is None:
            return

        all_values = sheet.get_all_values()
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 2 and row[0] == proposal_id and row[1] == session_id:
                sheet.update_cell(i, 8, 'submitted')
                break
    except Exception:
        pass  # Non-critical — form was already submitted successfully


def retrieve_uploaded_file(proposal_id, session_id):
    """
    Retrieve an uploaded file from the drafts sheet.

    Args:
        proposal_id (str): Proposal ID
        session_id (str): Session token

    Returns:
        tuple: (file_bytes, filename) or (None, None) if not found
    """
    draft = load_draft(proposal_id, session_id)
    if draft and draft.get('file_data') and draft.get('file_name'):
        return draft['file_data'], draft['file_name']
    return None, None


def retrieve_file_by_proposal(proposal_id):
    """
    Find the most recent uploaded file for a given proposal (any session).

    Args:
        proposal_id (str): Proposal ID

    Returns:
        tuple: (file_bytes, filename) or (None, None) if not found
    """
    try:
        sheet = _get_drafts_sheet()
        if sheet is None:
            return None, None

        all_values = sheet.get_all_values()
        # Find most recent draft with a file for this proposal
        best_row = None
        for row in all_values[1:]:
            if len(row) >= 5 and row[0] == proposal_id and row[3]:  # Has file data
                best_row = row

        if best_row:
            file_b64 = best_row[3]
            file_name = best_row[4]
            file_data = base64.b64decode(file_b64) if file_b64 else None
            return file_data, file_name

        return None, None

    except Exception as e:
        print(f"Error retrieving file: {e}")
        return None, None
