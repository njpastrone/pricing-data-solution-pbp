"""
Match Manager Module
Handles manual match storage, retrieval, and product name normalization.
"""

import json
import os
import re
from typing import Dict, Optional
from datetime import datetime


# Path to manual matches JSON file
MANUAL_MATCHES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "manual_matches.json"
)


def load_manual_matches() -> Dict:
    """
    Load manual matches from JSON file.
    Creates file with empty structure if it doesn't exist.

    Returns:
        Dict with structure:
        {
            "product_matches": {...}
        }
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.dirname(MANUAL_MATCHES_FILE)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Create file with empty structure if it doesn't exist
    if not os.path.exists(MANUAL_MATCHES_FILE):
        empty_structure = {
            "product_matches": {}
        }
        with open(MANUAL_MATCHES_FILE, 'w') as f:
            json.dump(empty_structure, f, indent=2)
        return empty_structure

    # Load existing file
    try:
        with open(MANUAL_MATCHES_FILE, 'r') as f:
            data = json.load(f)

        # Ensure key exists
        if "product_matches" not in data:
            data["product_matches"] = {}

        return data
    except (json.JSONDecodeError, IOError) as e:
        # If file is corrupted, return empty structure
        print(f"Error loading manual matches: {e}")
        return {
            "product_matches": {}
        }


def save_manual_match(
    product_name: str,
    slide_index: int,
    slide_title: str,
    match_category: str = "product"
) -> bool:
    """
    Save a manual match to JSON file.

    Args:
        product_name: Name of product
        slide_index: Index of slide in template (0-based)
        slide_title: Title text of the slide
        match_category: "product"

    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        # Load current matches
        data = load_manual_matches()

        # Normalize product name for consistent storage
        normalized_name = normalize_for_storage(product_name)

        # Determine which section to save to
        if match_category == "product":
            category_key = "product_matches"
        else:
            print(f"Invalid match category: {match_category}")
            return False

        # Create match entry
        match_entry = {
            "slide_index": slide_index,
            "slide_title": slide_title,
            "match_type": "manual",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "confidence": 1.0,
            "original_name": product_name  # Store original for display
        }

        # Save to appropriate category
        data[category_key][normalized_name] = match_entry

        # Write to file
        with open(MANUAL_MATCHES_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    except Exception as e:
        print(f"Error saving manual match: {e}")
        return False


def delete_manual_match(
    product_name: str,
    match_category: str = "product"
) -> bool:
    """
    Delete a manual match from JSON file.

    Args:
        product_name: Name of product to delete
        match_category: "product"

    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        # Load current matches
        data = load_manual_matches()

        # Normalize product name
        normalized_name = normalize_for_storage(product_name)

        # Determine which section to delete from
        if match_category == "product":
            category_key = "product_matches"
        else:
            print(f"Invalid match category: {match_category}")
            return False

        # Check if match exists
        if normalized_name not in data[category_key]:
            print(f"No manual match found for: {product_name}")
            return False

        # Delete the match
        del data[category_key][normalized_name]

        # Write to file
        with open(MANUAL_MATCHES_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    except Exception as e:
        print(f"Error deleting manual match: {e}")
        return False


def get_manual_match(
    product_name: str,
    match_category: str = "product"
) -> Optional[Dict]:
    """
    Get manual match for a specific product or partner.

    Args:
        product_name: Name of product
        match_category: "product"

    Returns:
        Dict with match data if found, None otherwise
        {
            "slide_index": 42,
            "slide_title": "Hand Stitched Bags",
            "match_type": "manual",
            "created_date": "2025-11-05",
            "confidence": 1.0,
            "original_name": "Hand Stitched Bags (Noir)"
        }
    """
    try:
        # Load matches
        data = load_manual_matches()

        # Normalize product name
        normalized_name = normalize_for_storage(product_name)

        # Determine which section to search
        if match_category == "product":
            category_key = "product_matches"
        else:
            return None

        # Return match if exists
        return data[category_key].get(normalized_name)

    except Exception as e:
        print(f"Error getting manual match: {e}")
        return None


def get_all_manual_matches(match_category: str = "product") -> Dict:
    """
    Get all manual matches for a category.

    Args:
        match_category: "product"

    Returns:
        Dict of all matches in the category
        {
            "normalized_name": {
                "slide_index": 42,
                "slide_title": "Hand Stitched Bags",
                ...
            }
        }
    """
    try:
        # Load matches
        data = load_manual_matches()

        # Determine which section to return
        if match_category == "product":
            return data.get("product_matches", {})
        else:
            return {}

    except Exception as e:
        print(f"Error getting all manual matches: {e}")
        return {}


def normalize_for_storage(name: str) -> str:
    """
    Normalize product name for consistent storage key generation.

    Converts to lowercase for case-insensitive storage lookups.
    Used by JSON file storage and Google Sheets storage systems.

    Normalization steps:
    1. Convert to lowercase
    2. Remove content in parentheses: (Noir), (Set), etc.
    3. Remove variant suffixes after dashes: - Set of 3, - Large, - MOF, etc.
    4. Remove extra whitespace

    Examples:
        "Jaggery (Noir)" -> "jaggery"
        "Hand Stitched Bags - Set of 3" -> "hand stitched bags"
        "Basketry - Large" -> "basketry"
        "Product Name - MOF" -> "product name"

    Args:
        name: Original product name

    Returns:
        str: Normalized product name (lowercase)
    """
    # Convert to lowercase
    normalized = name.lower()

    # Remove content in parentheses
    normalized = re.sub(r'\([^)]*\)', '', normalized)

    # Remove variant suffixes after dashes
    variant_patterns = [
        r' - set of \d+',      # - Set of 3, - Set of 5, etc.
        r' - large',           # - Large
        r' - small',           # - Small
        r' - medium',          # - Medium
        r' - mof',             # - MOF
        r' - noir',            # - Noir
        r' - [a-z\s]+$'        # Any other suffix after dash
    ]

    for pattern in variant_patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Remove extra whitespace
    normalized = ' '.join(normalized.split())

    return normalized.strip()
