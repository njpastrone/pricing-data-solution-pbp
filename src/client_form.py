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
import time
import uuid
import threading
import base64
from datetime import datetime
import gspread
import streamlit as st
from src.data_loader import connect_to_sheets, DATASET_CONFIGS
from src.forms_config import GOOGLE_FORM_CONFIG, RESPONSE_COLUMNS, MAX_PRODUCT_LINES, find_response_column


# Sheet name for client form drafts
DRAFTS_SHEET_NAME = "client_form_drafts"

# Base64 chunk size (same as drive_helper.py)
CHUNK_SIZE = 40000

# Google Sheets refuses any single cell longer than this
SHEET_CELL_LIMIT = 50000

# Google Sheets allows about 60 read requests per minute for our service account,
# shared by the live app and any local copy. When Google answers "quota exceeded"
# (HTTP 429) we wait and try again instead of failing.
QUOTA_RETRY_WAITS = [2, 4, 8, 16]  # seconds between attempts

# Saving the client's backup copy is retried for about 1-2 minutes before we give up.
BACKUP_RETRY_WAITS = [5, 10, 20, 30]  # seconds between attempts

# Copying a received order into Form Responses is retried in the background.
SYNC_RETRY_WAITS = [10, 30, 60, 120]  # seconds between attempts

# An order still waiting to be copied after this long is flagged to staff.
STUCK_AFTER_MINUTES = 10

# Draft statuses in the backup tab (column H)
STATUS_DRAFT = 'draft'
STATUS_PENDING = 'pending_sync'   # order received, not yet in Form Responses
STATUS_SUBMITTED = 'submitted'    # order is in Form Responses

# ponytail: one lock per app process; fine while the app runs as a single Render instance
_sync_lock = threading.Lock()


def _retry_on_quota(action):
    """
    Run action(); if Google says "quota exceeded" (HTTP 429), wait and retry.

    A 429 means Google rejected the request without applying it, so retrying
    a write (like append_row) cannot create a duplicate row.
    """
    for wait in QUOTA_RETRY_WAITS:
        try:
            return action()
        except gspread.exceptions.APIError as e:
            if getattr(e, 'code', None) != 429:
                raise
            print(f"Google Sheets quota hit, retrying in {wait}s")
            time.sleep(wait)
    return action()  # Last try: any error now goes to the caller


# ponytail: handles are cached until the app restarts; a renamed tab needs a restart
@st.cache_resource(show_spinner=False)
def _open_worksheet(spreadsheet_id, sheet_name):
    """Open a worksheet once and reuse it (each open costs 2 read requests)."""
    spreadsheet = _retry_on_quota(lambda: connect_to_sheets().open_by_key(spreadsheet_id))
    return _retry_on_quota(lambda: spreadsheet.worksheet(sheet_name))


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
        sheet = _open_worksheet(DATASET_CONFIGS['saved_proposals']['spreadsheet_id'], 'Sheet1')
        all_values = _retry_on_quota(sheet.get_all_values)

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


@st.cache_resource(show_spinner=False)
def _open_drafts_sheet():
    """Open (or create) the client_form_drafts sheet once and reuse it. Raises on error."""
    spreadsheet = _retry_on_quota(
        lambda: connect_to_sheets().open_by_key(DATASET_CONFIGS['saved_orders']['spreadsheet_id'])
    )
    try:
        return _retry_on_quota(lambda: spreadsheet.worksheet(DRAFTS_SHEET_NAME))
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=DRAFTS_SHEET_NAME, rows=100, cols=8)
        headers = [
            'Proposal_ID', 'Session_ID', 'Draft_Data_JSON',
            'File_Data_Base64', 'File_Name', 'Created_Date',
            'Updated_Date', 'Status'
        ]
        sheet.update('A1:H1', [headers])
        return sheet


def _get_drafts_sheet():
    """
    Get or create the client_form_drafts sheet.

    Returns:
        gspread.Worksheet or None
    """
    try:
        return _open_drafts_sheet()
    except Exception as e:
        print(f"Error accessing drafts sheet: {e}")
        return None


def _read_backup_rows(sheet):
    """
    Read every backup row, skipping the large file column (D) to save quota.

    Returns:
        list of dict: {'row_number', 'proposal_id', 'session_id', 'json', 'file_name', 'status'}
    """
    ids_and_json, rest = _retry_on_quota(lambda: sheet.batch_get(['A:C', 'E:H']))
    rows = []
    for i in range(1, len(ids_and_json)):
        a_to_c = list(ids_and_json[i]) + [''] * 3
        e_to_h = (list(rest[i]) if i < len(rest) else []) + [''] * 4
        rows.append({
            'row_number': i + 1,
            'proposal_id': a_to_c[0],
            'session_id': a_to_c[1],
            'json': a_to_c[2],
            'file_name': e_to_h[0],
            'status': e_to_h[3],
        })
    return rows


def _find_backup(rows, proposal_id, session_id):
    """Return the backup row (from _read_backup_rows) for this proposal+session, or None."""
    for row in rows:
        if row['proposal_id'] == proposal_id and row['session_id'] == session_id:
            return row
    return None


def save_draft(proposal_id, session_id, form_data, file_data=None, file_name=None, status=STATUS_DRAFT):
    """
    Save or update a form draft in Google Sheets.

    Args:
        proposal_id (str): Proposal ID
        session_id (str): Session token
        form_data (dict): All form field values
        file_data (bytes or None): Uploaded file bytes
        file_name (str or None): Original filename
        status (str): Status to store (draft, or pending_sync on submit)

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
        existing = _find_backup(_read_backup_rows(sheet), proposal_id, session_id)

        # Once an order is received it is never rewritten: a "Save Progress" or a
        # second Submit from an old browser tab must not turn it back into a draft
        # or give it a new submit time (which would add a second Form Responses row)
        if existing and existing['status'] in (STATUS_PENDING, STATUS_SUBMITTED):
            return True, "Order already received"

        if existing:
            existing_row = existing['row_number']
            # Update existing draft (preserve Created_Date in column F).
            # Without new file data, keep the stored file as it is.
            if file_data:
                _retry_on_quota(lambda: sheet.update(f'C{existing_row}:E{existing_row}', [[json_data, file_b64, file_name or '']]))
            else:
                _retry_on_quota(lambda: sheet.update(f'C{existing_row}', [[json_data]]))
            _retry_on_quota(lambda: sheet.update(f'G{existing_row}:H{existing_row}', [[now, status]]))
        else:
            # Create new draft
            _retry_on_quota(lambda: sheet.append_row([
                proposal_id, session_id, json_data,
                file_b64, file_name or '', now, now, status
            ]))

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

        all_values = _retry_on_quota(sheet.get_all_values)

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
    Receive the client's completed order.

    A client never sees a Google Sheets error (their order must never be lost):
    1. The full order is saved to the backup tab (client_form_drafts) with
       status "pending_sync", retrying for about 1-2 minutes. If the uploaded
       file is too big for a sheet cell, the copy is saved without the file.
    2. The client is told "Order received".
    3. The order is copied into Form Responses in the background
       (see sync_submission). If that keeps failing, the main app retries
       on its next run and warns staff about stuck orders.

    Args:
        proposal_id (str): Proposal ID
        session_id (str): Session token
        form_data (dict): All form field values
        file_data (bytes or None): Uploaded file bytes
        file_name (str or None): Original filename

    Returns:
        tuple: (success: bool, message: str)
    """
    if len(form_data.get('products', [])) > MAX_PRODUCT_LINES:
        return False, f"Too many products: the form holds at most {MAX_PRODUCT_LINES} items."

    # The submit time is the Form Responses timestamp; it is kept in the backup
    # so every later sync attempt writes (and recognises) the very same row.
    backup = dict(form_data, submitted_at=datetime.now().strftime("%m/%d/%Y %H:%M:%S"))

    # A file too big for one sheet cell can never be saved there, so it is left
    # out (the file name is still kept). Any other error is retried WITH the file.
    if file_data and len(base64.b64encode(file_data)) > SHEET_CELL_LIMIT:
        print(f"Client form file for {proposal_id} is too big for the backup tab; saving the order without it")
        file_data = None

    # Step 1: Save the order to the backup tab, retrying for about 1-2 minutes
    backup_ok = False
    for wait in BACKUP_RETRY_WAITS + [None]:
        backup_ok, backup_msg = save_draft(proposal_id, session_id, backup, file_data, file_name, STATUS_PENDING)
        if backup_ok or wait is None:
            break
        print(f"Client form backup failed for {proposal_id}, retrying in {wait}s: {backup_msg}")
        time.sleep(wait)

    if not backup_ok:
        print(f"Client form backup gave up for {proposal_id}: {backup_msg}")
        return False, "We could not save your order right now. Please wait a minute and press Submit again."

    # Step 2: Copy it into Form Responses without making the client wait
    _sync_in_background(proposal_id, session_id)
    return True, "Order received"


def _sync_in_background(proposal_id, session_id):
    """Run sync_submission on a background thread, retrying with growing waits."""
    def run():
        for wait in SYNC_RETRY_WAITS + [None]:
            ok, msg = sync_submission(proposal_id, session_id)
            if ok or wait is None:
                break
            print(f"Form Responses sync failed for {proposal_id}, retrying in {wait}s: {msg}")
            time.sleep(wait)
        if not ok:
            print(f"Form Responses sync still pending for {proposal_id}; the app will retry on its next run")

    threading.Thread(target=run, daemon=True).start()


def _build_response_row(headers, form_data, file_name):
    """
    Build the Form Responses row in the same column format as the Google Form,
    so Tab 3's import (parse_form_response) works without changes.

    Returns:
        tuple: (row, unmatched field labels, whether the file-name column must be added)
    """
    client_info = form_data.get('client_info', {})
    shipping = form_data.get('shipping_info', {})
    payment = form_data.get('payment_info', {})
    fields = [
        ('timestamp', form_data.get('submitted_at', '')),
        ('client_type', client_info.get('client_type', '')),
        ('company_name', client_info.get('company_name', '')),
        ('contact_name', client_info.get('contact_name', '')),
        ('contact_email', client_info.get('contact_email', '')),
        ('contact_phone', client_info.get('contact_phone', '')),
        ('shipping_address', shipping.get('shipping_address', '')),
        ('billing_address', shipping.get('billing_address', '')),
        ('drop_shipping', shipping.get('drop_shipping', '')),
        ('drop_shipping_instructions', shipping.get('drop_shipping_instructions', '')),
        ('in_hands_date', shipping.get('in_hands_date', '')),
        ('impact_cards', payment.get('impact_cards', '')),
        ('impact_card_selection', payment.get('impact_card_selection', '')),
        ('payment_preference', payment.get('payment_preference', '')),
        ('payment_method', payment.get('payment_method', '')),
        ('special_requests', form_data.get('notes', '')),
    ]
    for i, product in enumerate(form_data.get('products', []), start=1):
        fields.append((f'line_{i}_name', product.get('name', '')))
        fields.append((f'line_{i}_qty', str(product.get('quantity', ''))))
        fields.append((f'line_{i}_notes', product.get('customization_notes', '')))

    # Place each value in its column; remember any that have nowhere to go
    row = [''] * len(headers)
    unmatched = []
    for key, value in fields:
        if not str(value).strip():
            continue
        col_name = find_response_column(headers, key)
        if col_name is None:
            unmatched.append(RESPONSE_COLUMNS.get(key, key))
        else:
            row[headers.index(col_name)] = value

    # Dropshipping file name (if uploaded)
    add_file_column = False
    if file_name:
        file_col = find_response_column(headers, 'dropshipping_file')
        if file_col:
            row[headers.index(file_col)] = file_name
        else:
            add_file_column = True
            row.append(file_name)

    return row, unmatched, add_file_column


# ponytail: two identical orders submitted in the same second count as one; add a hidden ID column if that ever matters
def _row_already_present(existing_rows, row):
    """True if a sheet row already holds every filled-in value of row (same timestamp included)."""
    for existing in existing_rows:
        if all(value == '' or (i < len(existing) and existing[i] == value) for i, value in enumerate(row)):
            return True
    return False


def sync_submission(proposal_id, session_id):
    """
    Copy one received order from the backup tab into Form Responses.

    Safe to run any number of times: if the row is already in Form Responses
    (an earlier attempt wrote it but could not mark the backup), it is not
    written again. The backup is marked "submitted" once the row is there.

    Returns:
        tuple: (success: bool, message: str)
    """
    drafts = _get_drafts_sheet()
    if drafts is None:
        return False, "Failed to connect to drafts sheet"
    try:
        backup = _find_backup(_read_backup_rows(drafts), proposal_id, session_id)
    except Exception as e:
        return False, f"Error syncing form: {str(e)}"
    if backup is None:
        return False, "No backup found"
    return _sync_backup_row(drafts, backup)


def _sync_backup_row(drafts, backup):
    """Copy one already-read backup row (from _read_backup_rows) into Form Responses."""
    with _sync_lock:
        try:
            if backup['status'] == STATUS_SUBMITTED:
                return True, "Already submitted"

            form_data = _deserialize_form_data(backup['json'])
            file_name = backup['file_name'] or None

            worksheet = _open_worksheet(GOOGLE_FORM_CONFIG['response_sheet_id'], GOOGLE_FORM_CONFIG['response_sheet_name'])
            # Read fresh every time: headers being out of date is what lost items before
            all_rows = _retry_on_quota(worksheet.get_all_values)
            if not all_rows or not all_rows[0]:
                return False, "Response sheet has no headers"
            headers = all_rows[0]

            row, unmatched, add_file_column = _build_response_row(headers, form_data, file_name)
            if unmatched:
                # Nothing is written; the order stays pending and staff are warned
                return False, f"Response sheet has no column for {unmatched}"

            if not _row_already_present(all_rows[1:], row):
                if add_file_column:
                    _retry_on_quota(lambda: worksheet.update_cell(1, len(row), RESPONSE_COLUMNS['dropshipping_file']))
                # Write to the row right after the last filled row. append_row lets Google
                # pick the row, and when the tab had a Sheets Table it kept picking row 8.
                next_row = len(all_rows) + 1
                try:
                    _retry_on_quota(lambda: worksheet.update(range_name=f'A{next_row}', values=[row]))
                except Exception as e:
                    if 'exceeds grid limits' not in str(e):
                        raise
                    _retry_on_quota(lambda: worksheet.resize(rows=next_row))
                    _retry_on_quota(lambda: worksheet.update(range_name=f'A{next_row}', values=[row]))

            _retry_on_quota(lambda: drafts.update_cell(backup['row_number'], 8, STATUS_SUBMITTED))
            return True, "Synced"

        except Exception as e:
            return False, f"Error syncing form: {str(e)}"


def retry_pending_syncs():
    """
    Retry every received order not yet copied into Form Responses.
    Called by the main app when it starts.

    Returns:
        list of dict: orders still stuck after STUCK_AFTER_MINUTES
            ({'proposal_id', 'company_name', 'submitted_at', 'reason'}), for a staff warning
    """
    drafts = _get_drafts_sheet()
    if drafts is None:
        return []
    try:
        rows = _read_backup_rows(drafts)
    except Exception as e:
        print(f"Could not check pending client form orders: {e}")
        return []

    stuck = []
    for row in rows:
        if row['status'] != STATUS_PENDING:
            continue
        ok, msg = _sync_backup_row(drafts, row)
        if ok:
            continue
        print(f"Form Responses sync still pending for {row['proposal_id']}: {msg}")
        form_data = _deserialize_form_data(row['json'])
        submitted_at = form_data.get('submitted_at', '')
        try:
            age_minutes = (datetime.now() - datetime.strptime(submitted_at, "%m/%d/%Y %H:%M:%S")).total_seconds() / 60
        except ValueError:
            age_minutes = STUCK_AFTER_MINUTES  # unknown age: warn anyway
        if age_minutes >= STUCK_AFTER_MINUTES:
            stuck.append({
                'proposal_id': row['proposal_id'],
                'company_name': form_data.get('client_info', {}).get('company_name', ''),
                'submitted_at': submitted_at,
                'reason': msg,
            })
    return stuck


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

        all_values = _retry_on_quota(sheet.get_all_values)
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
