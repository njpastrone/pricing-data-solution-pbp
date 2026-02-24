"""
Match Memory Module for PBP Pricing App

This module handles persistent storage of confirmed product-to-slide matches in Google Sheets.
When users confirm fuzzy matches in the PowerPoint generation workflow, those matches are
automatically saved and reused in future sessions.

Storage Structure (saved_matches spreadsheet):
- Match_ID: Unique identifier (MATCH_YYYYMMDD_HHMMSS)
- Product_Name: Normalized product name (for matching)
- Original_Product_Name: Original product name (for display)
- Slide_Index: Index of slide in template (0-based)
- Slide_Title: Title text of the slide
- Dataset: Which dataset was used (demo/real)
- Match_Type: Type of match (fuzzy_confirmed, alternative_selected)
- Confidence: Original confidence score before confirmation
- Created_Date: Timestamp (YYYY-MM-DD HH:MM:SS)
- Template_Name: Name of the template file (e.g., "February All Slides.pptx")
"""

import json
from datetime import datetime
import streamlit as st
from src.data_loader import connect_to_sheets, DATASET_CONFIGS
from src.match_manager import normalize_for_storage


def _get_matches_sheet():
    """
    Internal helper to get the matches sheet.
    Not cached - use sparingly.
    """
    try:
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_matches']['spreadsheet_id'])

        # Get Sheet1 (should already exist)
        try:
            sheet = spreadsheet.worksheet('Sheet1')
        except Exception:
            # If doesn't exist, create it with headers
            sheet = spreadsheet.add_worksheet(title='Sheet1', rows=100, cols=10)
            headers = ['Match_ID', 'Product_Name', 'Original_Product_Name', 'Slide_Index',
                      'Slide_Title', 'Dataset', 'Match_Type', 'Confidence', 'Created_Date', 'Template_Name']
            sheet.update('A1:J1', [headers])

        return sheet
    except Exception as e:
        st.error(f"Error accessing matches sheet: {str(e)}")
        return None


@st.cache_data(ttl=60, show_spinner=False)  # Cache raw data for 1 minute
def _load_all_matches_data():
    """
    Internal helper to load all match data from Google Sheets.
    Cached to minimize API calls.

    Returns:
        list: All rows from the sheet (including header)
    """
    try:
        # Direct access inside cache to ensure caching works properly
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(DATASET_CONFIGS['saved_matches']['spreadsheet_id'])

        try:
            sheet = spreadsheet.worksheet('Sheet1')
        except Exception:
            # Return empty if sheet doesn't exist (will be created on first save)
            return []

        all_values = sheet.get_all_values()
        return all_values
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Quota exceeded" in error_msg:
            print("Google Sheets rate limit reached. Data will be cached. Wait 60 seconds and refresh.")
        else:
            print(f"Error loading matches data: {error_msg}")
        return []


def generate_match_id():
    """
    Generate a unique match ID based on current timestamp.
    Format: MATCH_YYYYMMDD_HHMMSS

    Returns:
        str: Unique match ID
    """
    return datetime.now().strftime("MATCH_%Y%m%d_%H%M%S")


def save_confirmed_match(product_name, slide_index, slide_title, dataset, match_type='fuzzy_confirmed', confidence=0, template_name=''):
    """
    Save a confirmed product-to-slide match to Google Sheets.

    Args:
        product_name (str): Original product name from Google Sheets
        slide_index (int): Index of slide in template (0-based)
        slide_title (str): Title text of the slide
        dataset (str): Dataset used ('demo' or 'real')
        match_type (str): Type of match ('fuzzy_confirmed' or 'alternative_selected')
        confidence (int): Original confidence score (0-100)
        template_name (str): Name of template file (e.g., "February All Slides.pptx")

    Returns:
        tuple: (success: bool, message: str)
    """
    if not product_name or not product_name.strip():
        return False, "Product name is required"

    try:
        sheet = _get_matches_sheet()
        if sheet is None:
            return False, "Failed to connect to matches sheet"

        # Normalize product name for matching
        normalized_name = normalize_for_storage(product_name)

        # Load current data to check for existing match
        all_values = _load_all_matches_data()

        # Look for existing match (same normalized name + dataset + template_name)
        existing_row_idx = None
        for idx, row in enumerate(all_values[1:], start=2):  # Skip header
            if len(row) >= 6:
                row_template = row[9] if len(row) >= 10 else ''
                if row[1] == normalized_name and row[5] == dataset and row_template == template_name:
                    existing_row_idx = idx
                    break

        # Generate unique ID and timestamp
        match_id = generate_match_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare row data (10 columns)
        row_data = [
            match_id,
            normalized_name,
            product_name,  # Original name for display
            slide_index,
            slide_title,
            dataset,
            match_type,
            confidence,
            timestamp,
            template_name
        ]

        if existing_row_idx:
            # Update existing match
            sheet.update(f'A{existing_row_idx}:J{existing_row_idx}', [row_data])
            # Clear cache after update
            _load_all_matches_data.clear()
            return True, f"Match updated for '{product_name}'"
        else:
            # Append new match
            sheet.append_row(row_data)
            # Clear cache after save
            _load_all_matches_data.clear()
            return True, f"Match saved for '{product_name}'"

    except Exception as e:
        return False, f"Error saving match: {str(e)}"


def get_confirmed_match(product_name, dataset, template_name=''):
    """
    Get confirmed match for a specific product in the current dataset and template.

    Args:
        product_name (str): Product name to look up
        dataset (str): Dataset ('demo' or 'real')
        template_name (str): Template name to filter by. If empty, matches legacy rows
                            (rows without template_name column).

    Returns:
        dict or None: Match data if found, None otherwise
        {
            'match_id': 'MATCH_20251117_143025',
            'product_name': 'upcycled laptop sleeve',
            'original_product_name': 'Upcycled Laptop Sleeve (Enfold)',
            'slide_index': 42,
            'slide_title': 'UPCYCLED LAPTOP SLEEVE',
            'dataset': 'demo',
            'match_type': 'fuzzy_confirmed',
            'confidence': 85,
            'created_date': '2025-11-17 14:30:25',
            'template_name': 'February All Slides.pptx'
        }
    """
    try:
        # Use cached data to avoid API calls
        all_values = _load_all_matches_data()

        if not all_values or len(all_values) <= 1:
            return None

        # Normalize product name for lookup
        normalized_name = normalize_for_storage(product_name)

        # Find match (normalized name + dataset + template_name)
        for row in all_values[1:]:  # Skip header
            if len(row) >= 9:
                row_template = row[9] if len(row) >= 10 else ''

                # Match if template names are the same
                # Legacy rows (no template) match when template_name is also empty
                if row[1] == normalized_name and row[5] == dataset and row_template == template_name:
                    return {
                        'match_id': row[0],
                        'product_name': row[1],
                        'original_product_name': row[2],
                        'slide_index': int(row[3]),
                        'slide_title': row[4],
                        'dataset': row[5],
                        'match_type': row[6],
                        'confidence': int(row[7]) if row[7] else 0,
                        'created_date': row[8],
                        'template_name': row_template
                    }

        return None

    except Exception as e:
        print(f"Error getting confirmed match for '{product_name}': {str(e)}")
        return None


def load_all_confirmed_matches(dataset=None, template_name=None):
    """
    Load all confirmed matches, optionally filtered by dataset and/or template.
    Uses cached data to minimize API calls.

    Args:
        dataset (str, optional): Filter by dataset ('demo' or 'real').
                                 If None, returns all matches.
        template_name (str, optional): Filter by template name.
                                       If None, returns all templates.

    Returns:
        list: List of dicts with match data
              Returns empty list if error occurs
    """
    try:
        # Use cached data
        all_values = _load_all_matches_data()

        if not all_values or len(all_values) <= 1:  # Only headers or empty
            return []

        matches = []
        for row in all_values[1:]:  # Skip header row
            if len(row) >= 9:
                # Filter by dataset if specified
                if dataset and row[5] != dataset:
                    continue

                row_template = row[9] if len(row) >= 10 else ''

                # Filter by template_name if specified
                if template_name is not None and row_template != template_name:
                    continue

                matches.append({
                    'match_id': row[0],
                    'product_name': row[1],
                    'original_product_name': row[2],
                    'slide_index': int(row[3]),
                    'slide_title': row[4],
                    'dataset': row[5],
                    'match_type': row[6],
                    'confidence': int(row[7]) if row[7] else 0,
                    'created_date': row[8],
                    'template_name': row_template
                })

        # Sort by date (newest first)
        matches.sort(key=lambda x: x['created_date'], reverse=True)

        return matches

    except Exception as e:
        st.error(f"Error loading confirmed matches: {str(e)}")
        return []


def delete_confirmed_match(product_name, dataset, template_name=''):
    """
    Delete a confirmed match from Google Sheets.

    Args:
        product_name (str): Product name to delete
        dataset (str): Dataset ('demo' or 'real')
        template_name (str): Template name to filter by

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sheet = _get_matches_sheet()
        if sheet is None:
            return False, "Failed to connect to matches sheet"

        # Normalize product name for lookup
        normalized_name = normalize_for_storage(product_name)

        all_values = _load_all_matches_data()

        # Find row with matching product name + dataset + template
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 6 and row[1] == normalized_name and row[5] == dataset:
                row_template = row[9] if len(row) >= 10 else ''
                if row_template == template_name:
                    sheet.delete_rows(i)
                    # Clear cache after delete
                    _load_all_matches_data.clear()
                    return True, f"Match deleted for '{product_name}'"

        return False, f"No match found for '{product_name}' in {dataset} dataset"

    except Exception as e:
        return False, f"Error deleting match: {str(e)}"


def clear_all_confirmed_matches(dataset=None):
    """
    Clear all confirmed matches, optionally filtered by dataset.

    Args:
        dataset (str, optional): Clear only matches for this dataset ('demo' or 'real').
                                 If None, clears all matches.

    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    try:
        sheet = _get_matches_sheet()
        if sheet is None:
            return False, "Failed to connect to matches sheet", 0

        all_values = _load_all_matches_data()

        if not all_values or len(all_values) <= 1:  # Only headers or empty
            return True, "No matches to clear", 0

        # Find rows to delete (iterate backwards to avoid index issues)
        rows_to_delete = []
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 6:
                # Filter by dataset if specified
                if dataset is None or row[5] == dataset:
                    rows_to_delete.append(i)

        if not rows_to_delete:
            return True, f"No matches found for {dataset} dataset" if dataset else "No matches to clear", 0

        # Delete rows in reverse order (bottom to top)
        for row_idx in sorted(rows_to_delete, reverse=True):
            sheet.delete_rows(row_idx)

        # Clear cache after clearing matches
        _load_all_matches_data.clear()

        count = len(rows_to_delete)
        dataset_msg = f" for {dataset} dataset" if dataset else ""
        return True, f"Cleared {count} confirmed match{'es' if count != 1 else ''}{dataset_msg}", count

    except Exception as e:
        return False, f"Error clearing matches: {str(e)}", 0


def bulk_update_confirmed_matches(product_names, new_slide_index, new_slide_title, dataset, template_name=''):
    """
    Update multiple confirmed matches to point to a new slide.
    Useful for fixing incorrect matches in bulk.

    Args:
        product_names (list): List of product names to update
        new_slide_index (int): New slide index
        new_slide_title (str): New slide title
        dataset (str): Dataset ('demo' or 'real')
        template_name (str): Template name

    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    if not product_names:
        return False, "No products selected", 0

    try:
        updated_count = 0
        failed_products = []

        for product_name in product_names:
            # Use save_confirmed_match which handles update/insert
            success, message = save_confirmed_match(
                product_name=product_name,
                slide_index=new_slide_index,
                slide_title=new_slide_title,
                dataset=dataset,
                match_type='bulk_updated',
                confidence=0,
                template_name=template_name
            )

            if success:
                updated_count += 1
            else:
                failed_products.append(product_name)

        if updated_count == len(product_names):
            return True, f"Successfully updated {updated_count} match{'es' if updated_count != 1 else ''}", updated_count
        elif updated_count > 0:
            failed_msg = f" (failed: {', '.join(failed_products)})" if failed_products else ""
            return True, f"Updated {updated_count} of {len(product_names)} matches{failed_msg}", updated_count
        else:
            return False, f"Failed to update any matches", 0

    except Exception as e:
        return False, f"Error bulk updating matches: {str(e)}", 0
