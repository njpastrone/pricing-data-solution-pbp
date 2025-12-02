"""
Order Manager Module for PBP Pricing App

This module handles saving, loading, and managing orders in Google Sheets.
Orders are stored in the saved_orders spreadsheet with the following columns:
- Order_ID: Unique identifier (ORDER_YYYYMMDD_HHMMSS)
- Order_Name: User-provided name
- Created_By: Optional creator name/email
- Created_Date: Timestamp (YYYY-MM-DD HH:MM:SS)
- Dataset: Which dataset was used (demo/real)
- Order_Data_JSON: Serialized JSON of order state
"""

import json
from datetime import datetime, date
import streamlit as st
import gspread
from src.data_loader import connect_to_sheets, DATASET_CONFIGS


def convert_dates_to_strings(obj):
    """
    Recursively convert datetime.date and datetime.datetime objects to ISO format strings.
    This allows the object to be JSON serializable.

    Args:
        obj: Any object (dict, list, date, datetime, or primitive)

    Returns:
        The same object with all date/datetime objects converted to strings
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_dates_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates_to_strings(item) for item in obj]
    else:
        return obj


def convert_strings_to_dates(obj):
    """
    Recursively convert ISO format date strings back to date objects.
    This reverses the conversion done by convert_dates_to_strings.

    Args:
        obj: Any object (dict, list, string, or primitive)

    Returns:
        The same object with date strings converted back to date objects
    """
    if isinstance(obj, str):
        # Try to parse as date (YYYY-MM-DD format)
        try:
            return datetime.strptime(obj, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # Not a date string, return as-is
            return obj
    elif isinstance(obj, dict):
        return {key: convert_strings_to_dates(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_strings_to_dates(item) for item in obj]
    else:
        return obj


def initialize_orders_sheet():
    """
    Initialize the saved_orders sheet with headers if empty.

    Returns:
        gspread.Worksheet: The orders worksheet
    """
    try:
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_orders']['spreadsheet_id'])

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
        if not first_row or first_row[0] != 'Order_ID':
            # Initialize with headers
            headers = ['Order_ID', 'Order_Name', 'Created_By', 'Created_Date', 'Dataset', 'Order_Data_JSON']
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
            print(f"Error initializing orders sheet: {error_msg}")
        return None


def generate_order_id():
    """
    Generate a unique order ID based on current timestamp.
    Format: ORDER_YYYYMMDD_HHMMSS

    Returns:
        str: Unique order ID
    """
    return datetime.now().strftime("ORDER_%Y%m%d_%H%M%S")


def save_order(name, created_by, order_data, dataset):
    """
    Save an order to Google Sheets.

    Args:
        name (str): Order name (required)
        created_by (str): Creator name/email (optional)
        order_data (dict): Order state data to save
        dataset (str): Dataset used ('demo' or 'real')

    Returns:
        tuple: (success: bool, message: str, order_id: str or None)
    """
    if not name or not name.strip():
        return False, "Order name is required", None

    try:
        sheet = initialize_orders_sheet()
        if sheet is None:
            return False, "Failed to connect to orders sheet", None

        # Check if order name already exists
        all_values = sheet.get_all_values()
        existing_names = [row[1] for row in all_values[1:] if len(row) > 1]  # Skip header row

        if name in existing_names:
            # Suggest versioned name
            version = 2
            new_name = f"{name} (v{version})"
            while new_name in existing_names:
                version += 1
                new_name = f"{name} (v{version})"
            return False, f"Order '{name}' already exists. Save as '{new_name}' instead?", new_name

        # Generate unique ID and timestamp
        order_id = generate_order_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Convert any date/datetime objects to strings before JSON serialization
        order_data_serializable = convert_dates_to_strings(order_data)

        # Serialize order data to JSON
        order_json = json.dumps(order_data_serializable)

        # Append row to sheet
        row_data = [
            order_id,
            name,
            created_by or "",
            timestamp,
            dataset,
            order_json
        ]

        sheet.append_row(row_data)

        return True, f"Order '{name}' saved successfully!", order_id

    except Exception as e:
        return False, f"Error saving order: {str(e)}", None


def load_all_orders():
    """
    Load all saved orders (metadata only, not full data).

    Returns:
        list: List of dicts with keys: order_id, name, created_by, created_date, dataset
              Returns empty list if error occurs
    """
    try:
        sheet = initialize_orders_sheet()
        if sheet is None:
            return []

        all_values = sheet.get_all_values()

        if len(all_values) <= 1:  # Only headers or empty
            return []

        orders = []
        for row in all_values[1:]:  # Skip header row
            if len(row) >= 5:  # Must have at least ID, name, creator, date, dataset
                orders.append({
                    'order_id': row[0],
                    'name': row[1],
                    'created_by': row[2],
                    'created_date': row[3],
                    'dataset': row[4]
                })

        # Sort by date (newest first)
        orders.sort(key=lambda x: x['created_date'], reverse=True)

        return orders

    except Exception as e:
        # Silently fail - error already shown by initialize_orders_sheet if needed
        print(f"Error loading orders: {str(e)}")
        return []


def load_order_data(order_id):
    """
    Load full order data for a specific order ID.

    Args:
        order_id (str): Unique order ID

    Returns:
        tuple: (success: bool, data: dict or None, dataset: str or None)
    """
    try:
        sheet = initialize_orders_sheet()
        if sheet is None:
            return False, None, None

        all_values = sheet.get_all_values()

        # Find row with matching order_id
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 6 and row[0] == order_id:
                # Deserialize JSON data
                order_data = json.loads(row[5])

                # Convert date strings back to date objects
                order_data = convert_strings_to_dates(order_data)

                dataset = row[4]
                return True, order_data, dataset

        return False, None, None

    except Exception as e:
        st.error(f"Error loading order data: {str(e)}")
        return False, None, None


def delete_order(order_id):
    """
    Delete an order from Google Sheets.

    Args:
        order_id (str): Unique order ID to delete

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sheet = initialize_orders_sheet()
        if sheet is None:
            return False, "Failed to connect to orders sheet"

        all_values = sheet.get_all_values()

        # Find row with matching order_id
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 1 and row[0] == order_id:
                sheet.delete_rows(i)
                return True, "Order deleted successfully"

        return False, "Order not found"

    except Exception as e:
        return False, f"Error deleting order: {str(e)}"
