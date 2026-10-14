"""
Photo Storage Module for PBP Pricing App

Stores product photos as base64 chunks in a dedicated Google Sheet.
Photos are split into 40,000-character chunks (well under Sheets' 50K cell limit).
Each photo gets a unique ID. The interface matches the original Drive-based design
so order_manager.py and app.py don't need changes.

Sheet structure: Photo_ID | Order_ID | Product_Name | Photo_Index | Filename | Chunk_Index | Base64_Chunk
"""

import base64
import uuid
import gspread
from src.data_loader import connect_to_sheets

# Maximum characters per cell (Google Sheets limit is 50,000, we use 40,000 for safety)
CHUNK_SIZE = 40000

# Spreadsheet ID for photo storage (uses the saved_orders spreadsheet, "Photos" sheet)
PHOTOS_SHEET_NAME = "Photos"


def _get_photos_sheet():
    """
    Get or create the Photos sheet in the saved_orders spreadsheet.

    Returns:
        gspread.Worksheet or None
    """
    try:
        from src.data_loader import DATASET_CONFIGS
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_orders']['spreadsheet_id'])

        try:
            sheet = spreadsheet.worksheet(PHOTOS_SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=PHOTOS_SHEET_NAME, rows=1000, cols=7)
            headers = ['Photo_ID', 'Order_ID', 'Product_Name', 'Photo_Index', 'Filename', 'Chunk_Index', 'Base64_Chunk']
            sheet.update('A1:G1', [headers])

        return sheet

    except Exception as e:
        print(f"Error accessing photos sheet: {e}")
        return None


def upload_photo(file_bytes, filename, order_id=""):
    """
    Store a photo as base64 chunks in Google Sheets.

    Args:
        file_bytes (bytes): Raw photo bytes
        filename (str): Original filename (e.g., "ORDER_123_Jam_1.png")
        order_id (str): Order ID for grouping (passed via filename convention)

    Returns:
        str or None: Photo ID if successful, None if failed
    """
    try:
        sheet = _get_photos_sheet()
        if sheet is None:
            return None

        # Generate unique photo ID
        photo_id = str(uuid.uuid4())[:8]

        # Encode to base64
        b64_string = base64.b64encode(file_bytes).decode('utf-8')

        # Split into chunks
        chunks = [b64_string[i:i + CHUNK_SIZE] for i in range(0, len(b64_string), CHUNK_SIZE)]

        # Parse order_id and product info from filename convention: ORDER_ID_ProductName_Index.ext
        # We just store the filename as-is for simplicity
        parts = filename.rsplit('.', 1)[0].split('_', 2) if '_' in filename else [filename]
        stored_order_id = order_id or (parts[0] + '_' + parts[1] if len(parts) > 1 else "")

        # Write all chunks as rows
        rows = []
        for chunk_idx, chunk in enumerate(chunks):
            rows.append([photo_id, stored_order_id, "", str(chunk_idx), filename, str(chunk_idx), chunk])

        if rows:
            sheet.append_rows(rows)

        return photo_id

    except Exception as e:
        print(f"Error uploading photo '{filename}': {e}")
        return None


def download_photo(file_id):
    """
    Download a photo from Google Sheets by photo ID.

    Args:
        file_id (str): Photo ID (stored when photo was uploaded)

    Returns:
        bytes or None: Photo bytes if successful, None if failed
    """
    try:
        sheet = _get_photos_sheet()
        if sheet is None:
            return None

        # Find all rows with this photo_id
        all_values = sheet.get_all_values()

        # Collect chunks for this photo
        chunks = {}
        for row in all_values[1:]:  # Skip header
            if len(row) >= 7 and row[0] == file_id:
                chunk_idx = int(row[5])
                chunks[chunk_idx] = row[6]

        if not chunks:
            print(f"Photo not found: {file_id}")
            return None

        # Reassemble in order
        b64_string = ''.join(chunks[i] for i in sorted(chunks.keys()))

        # Decode from base64
        return base64.b64decode(b64_string)

    except Exception as e:
        print(f"Error downloading photo (id={file_id}): {e}")
        return None


def delete_photos(file_ids):
    """
    Delete photos from Google Sheets by their IDs. Best-effort: logs failures.

    Args:
        file_ids (list): List of photo IDs to delete

    Returns:
        int: Number of photos successfully deleted
    """
    if not file_ids:
        return 0

    try:
        sheet = _get_photos_sheet()
        if sheet is None:
            return 0

        all_values = sheet.get_all_values()

        # Find rows to delete (collect indices, delete from bottom up)
        rows_to_delete = []
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 1 and row[0] in file_ids:
                rows_to_delete.append(i)

        # Delete from bottom up to avoid shifting indices
        deleted_ids = set()
        for row_idx in sorted(rows_to_delete, reverse=True):
            try:
                # Track which photo IDs we're deleting
                row_data = all_values[row_idx - 1]  # -1 because all_values is 0-indexed
                if row_data:
                    deleted_ids.add(row_data[0])
                sheet.delete_rows(row_idx)
            except Exception as e:
                print(f"Warning: Could not delete row {row_idx}: {e}")

        return len(deleted_ids)

    except Exception as e:
        print(f"Error deleting photos: {e}")
        return 0
