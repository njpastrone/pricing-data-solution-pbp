"""
Google Forms Helper Functions

This module provides functions for:
- Generating pre-filled Google Form URLs
- Loading form responses from Google Sheets
- Parsing form responses into structured data
- Tracking import status

Created: 2026-01-20
"""

import urllib.parse
from datetime import datetime
import pandas as pd
from src.forms_config import (
    GOOGLE_FORM_CONFIG,
    ALL_ENTRY_IDS,
    RESPONSE_COLUMNS,
    MAX_PRODUCT_LINES,
)


def generate_prefilled_form_url(client_info, products):
    """
    Generate a pre-filled Google Form URL.

    This function creates a URL that pre-populates the Google Form with:
    - Client information (company, contact, email)
    - Selected products with quantities
    - Any customization notes

    Args:
        client_info (dict): Client information with keys:
            - client_type: "New" or "Existing"
            - company_name: str
            - contact_name: str
            - contact_email: str
            - contact_phone: str (optional)

        products (list): List of product dicts with keys:
            - name: Product name (str)
            - quantity: int
            - customization_notes: str (optional)

    Returns:
        str: Full pre-filled form URL ready to share with client

    Example:
        >>> client = {
        ...     'client_type': 'Existing',
        ...     'company_name': 'Acme Corp',
        ...     'contact_name': 'John Smith',
        ...     'contact_email': 'john@acme.com',
        ...     'contact_phone': '555-1234'
        ... }
        >>> products = [
        ...     {'name': '9 oz Hot Honey', 'quantity': 100, 'customization_notes': 'Custom label'},
        ...     {'name': 'Beeswax Candle', 'quantity': 50, 'customization_notes': ''}
        ... ]
        >>> url = generate_prefilled_form_url(client, products)
        >>> 'entry.1110217337=Acme+Corp' in url
        True
    """
    base_url = GOOGLE_FORM_CONFIG['form_url']
    params = []

    # Add client information
    if client_info.get('client_type'):
        params.append(f"{ALL_ENTRY_IDS['client_type']}={urllib.parse.quote(client_info['client_type'])}")

    if client_info.get('company_name'):
        params.append(f"{ALL_ENTRY_IDS['company_name']}={urllib.parse.quote(client_info['company_name'])}")

    if client_info.get('contact_name'):
        params.append(f"{ALL_ENTRY_IDS['contact_name']}={urllib.parse.quote(client_info['contact_name'])}")

    if client_info.get('contact_email'):
        params.append(f"{ALL_ENTRY_IDS['contact_email']}={urllib.parse.quote(client_info['contact_email'])}")

    if client_info.get('contact_phone'):
        params.append(f"{ALL_ENTRY_IDS['contact_phone']}={urllib.parse.quote(client_info['contact_phone'])}")

    # Add products (up to MAX_PRODUCT_LINES)
    for idx, product in enumerate(products[:MAX_PRODUCT_LINES]):
        line_num = idx + 1

        # Product name
        name_key = f'line_{line_num}_name'
        if name_key in ALL_ENTRY_IDS and product.get('name'):
            params.append(f"{ALL_ENTRY_IDS[name_key]}={urllib.parse.quote(product['name'])}")

        # Quantity
        qty_key = f'line_{line_num}_qty'
        if qty_key in ALL_ENTRY_IDS and product.get('quantity'):
            params.append(f"{ALL_ENTRY_IDS[qty_key]}={product['quantity']}")

        # Customization notes (optional)
        notes_key = f'line_{line_num}_notes'
        if notes_key in ALL_ENTRY_IDS and product.get('customization_notes'):
            params.append(f"{ALL_ENTRY_IDS[notes_key]}={urllib.parse.quote(product['customization_notes'])}")

    # Build full URL
    if params:
        full_url = base_url + "?" + "&".join(params)
    else:
        full_url = base_url

    return full_url


def load_form_responses(gc):
    """
    Load all form responses from Google Sheets.

    Args:
        gc: Authorized gspread client (from data_loader.connect_to_sheets())

    Returns:
        pd.DataFrame: DataFrame with all responses, including:
            - All form fields
            - Tracking columns (Imported?, Order ID, etc.)
            - Empty DataFrame if sheet not found or error

    Example:
        >>> from src.data_loader import connect_to_sheets
        >>> gc = connect_to_sheets()
        >>> df = load_form_responses(gc)
        >>> print(len(df))
        5  # 5 responses
    """
    try:
        # Open response sheet
        sheet_id = GOOGLE_FORM_CONFIG['response_sheet_id']
        spreadsheet = gc.open_by_key(sheet_id)

        # Get the responses worksheet
        worksheet = spreadsheet.worksheet(GOOGLE_FORM_CONFIG['response_sheet_name'])

        # Get all data
        data = worksheet.get_all_records()

        # Convert to DataFrame
        df = pd.DataFrame(data)

        return df

    except Exception as e:
        print(f"Error loading form responses: {e}")
        return pd.DataFrame()


def parse_form_response(response_row):
    """
    Parse a single form response row into structured data.

    Extracts:
    - Client information (11 fields)
    - Products (up to 10 line items)
    - Shipping details
    - Payment preferences
    - Special requests

    Args:
        response_row (pd.Series or dict): Single row from response DataFrame

    Returns:
        dict: Structured data with keys:
            - client_info: dict with client details
            - products: list of product dicts
            - shipping_info: dict with addresses and dates
            - payment_info: dict with payment terms
            - notes: str with special requests
            - metadata: dict with timestamp, email, etc.

    Example:
        >>> row = df_responses.iloc[0]
        >>> data = parse_form_response(row)
        >>> data['client_info']['company_name']
        'Acme Corp'
        >>> len(data['products'])
        3
    """
    # Helper function to safely get value
    def get_value(key, default=''):
        col_name = RESPONSE_COLUMNS.get(key, key)
        value = response_row.get(col_name, default)
        # Convert empty strings to default
        return value if value and str(value).strip() else default

    # Extract client information
    client_info = {
        'client_type': get_value('client_type'),
        'company_name': get_value('company_name'),
        'contact_name': get_value('contact_name'),
        'contact_email': get_value('contact_email'),
        'contact_phone': get_value('contact_phone'),
    }

    # Extract products (up to 10 lines)
    products = []
    for i in range(1, MAX_PRODUCT_LINES + 1):
        product_name = get_value(f'line_{i}_name')
        quantity = get_value(f'line_{i}_qty', 0)
        customization_notes = get_value(f'line_{i}_notes')

        # Only add if product name is provided
        if product_name:
            try:
                qty_int = int(quantity) if quantity else 1
            except (ValueError, TypeError):
                qty_int = 1

            products.append({
                'name': product_name,
                'quantity': qty_int,
                'customization_notes': customization_notes,
            })

    # Extract shipping information
    shipping_info = {
        'shipping_address': get_value('shipping_address'),
        'billing_address': get_value('billing_address'),
        'drop_shipping': get_value('drop_shipping'),
        'drop_shipping_instructions': get_value('drop_shipping_instructions'),
        'in_hands_date': get_value('in_hands_date'),
    }

    # Extract payment information
    payment_info = {
        'impact_cards': get_value('impact_cards'),
        'impact_card_selection': get_value('impact_card_selection'),
        'payment_preference': get_value('payment_preference'),
        'payment_method': get_value('payment_method'),
    }

    # Extract notes
    notes = get_value('special_requests')

    # Extract metadata
    metadata = {
        'timestamp': get_value('timestamp'),
        'email': get_value('email'),
        'imported': get_value('imported'),
        'order_id': get_value('order_id'),
        'imported_by': get_value('imported_by'),
        'import_date': get_value('import_date'),
    }

    return {
        'client_info': client_info,
        'products': products,
        'shipping_info': shipping_info,
        'payment_info': payment_info,
        'notes': notes,
        'metadata': metadata,
    }


def mark_response_imported(gc, row_index, order_id, imported_by=''):
    """
    Mark a form response as imported in the tracking columns.

    Updates the response sheet with:
    - Imported? = TRUE
    - Order ID = provided order_id
    - Imported By = user email or name
    - Import Date = current timestamp

    Args:
        gc: Authorized gspread client
        row_index (int): Row number in sheet (1-indexed, including header)
        order_id (str): Order ID from the app
        imported_by (str): User who imported (email or name)

    Returns:
        bool: True if successful, False otherwise

    Example:
        >>> success = mark_response_imported(gc, 5, "ORD-2026-001", "john@pbp.com")
        >>> print(success)
        True
    """
    try:
        # Open response sheet
        sheet_id = GOOGLE_FORM_CONFIG['response_sheet_id']
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(GOOGLE_FORM_CONFIG['response_sheet_name'])

        # Get all headers to find tracking column positions
        headers = worksheet.row_values(1)

        # Find column indices for tracking fields
        imported_col = None
        order_id_col = None
        imported_by_col = None
        import_date_col = None

        for idx, header in enumerate(headers, start=1):
            if header == RESPONSE_COLUMNS['imported']:
                imported_col = idx
            elif header == RESPONSE_COLUMNS['order_id']:
                order_id_col = idx
            elif header == RESPONSE_COLUMNS['imported_by']:
                imported_by_col = idx
            elif header == RESPONSE_COLUMNS['import_date']:
                import_date_col = idx

        # Update cells
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        updates = []
        if imported_col:
            updates.append({
                'range': f'{chr(64 + imported_col)}{row_index}',
                'values': [['TRUE']]
            })
        if order_id_col:
            updates.append({
                'range': f'{chr(64 + order_id_col)}{row_index}',
                'values': [[order_id]]
            })
        if imported_by_col:
            updates.append({
                'range': f'{chr(64 + imported_by_col)}{row_index}',
                'values': [[imported_by]]
            })
        if import_date_col:
            updates.append({
                'range': f'{chr(64 + import_date_col)}{row_index}',
                'values': [[current_datetime]]
            })

        # Batch update
        if updates:
            worksheet.batch_update(updates)
            return True
        else:
            print("Warning: Tracking columns not found in response sheet")
            return False

    except Exception as e:
        print(f"Error marking response as imported: {e}")
        return False


def get_unimported_responses(gc):
    """
    Get all form responses that haven't been imported yet.

    Convenience function that loads responses and filters to unimported only.

    Args:
        gc: Authorized gspread client

    Returns:
        pd.DataFrame: DataFrame with only unimported responses

    Example:
        >>> df = get_unimported_responses(gc)
        >>> print(f"Found {len(df)} unimported responses")
        Found 3 unimported responses
    """
    df_all = load_form_responses(gc)

    if df_all.empty:
        return df_all

    # Filter to unimported (where Imported? is not TRUE)
    imported_col = RESPONSE_COLUMNS['imported']

    if imported_col in df_all.columns:
        # Handle various representations of "not imported"
        df_unimported = df_all[
            (df_all[imported_col] != 'TRUE') &
            (df_all[imported_col] != True) &
            (df_all[imported_col] != 'true')
        ]
        return df_unimported
    else:
        # If no tracking column, return all (assume none imported)
        return df_all


def format_product_summary(products):
    """
    Format product list as human-readable summary.

    Args:
        products (list): List of product dicts from parse_form_response()

    Returns:
        str: Formatted summary like "3 products: Honey (100), Candles (50), Soap (25)"

    Example:
        >>> products = [
        ...     {'name': 'Honey', 'quantity': 100},
        ...     {'name': 'Candles', 'quantity': 50}
        ... ]
        >>> print(format_product_summary(products))
        2 products: Honey (100), Candles (50)
    """
    if not products:
        return "No products"

    count = len(products)
    items = [f"{p['name']} ({p['quantity']})" for p in products]
    items_str = ", ".join(items)

    return f"{count} product{'s' if count != 1 else ''}: {items_str}"
