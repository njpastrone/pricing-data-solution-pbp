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
