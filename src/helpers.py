"""
Helper Functions for PBP Pricing App

This module contains utility functions for:
- Data type conversions and cleaning
- Price rounding and formatting
- Partner contact extraction
- Validation and data integrity checks
- Utility calculations (MOQ, credit card fees)
"""

import pandas as pd
import math


# ========== PRICING UTILITIES ==========

def clean_price(price_string):
    """
    Convert price string like '$48.00' or '$1,500.00' to float.
    Returns None if empty or invalid.

    Args:
        price_string: String representation of price (e.g., "$48.00", "1500.00")

    Returns:
        float: Cleaned price value, or None if invalid

    Examples:
        >>> clean_price("$48.00")
        48.0
        >>> clean_price("$1,500.00")
        1500.0
        >>> clean_price("")
        None
    """
    if not price_string or price_string == '':
        return None
    try:
        # Remove $, commas, whitespace
        cleaned = str(price_string).replace('$', '').replace(',', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def apply_marketing_rounding(price, enabled=True):
    """
    Apply charm pricing: if price is a multiple of 10, subtract $1 (e.g., $60 -> $59, $100 -> $99).
    Does NOT round - only applies to prices already ending in 0.

    Args:
        price (float): Original price
        enabled (bool): Whether to apply charm pricing

    Returns:
        float: Rounded price

    Examples:
        >>> apply_marketing_rounding(60.0, enabled=True)
        59.0
        >>> apply_marketing_rounding(96.0, enabled=True)
        96.0
        >>> apply_marketing_rounding(100.0, enabled=True)
        99.0
        >>> apply_marketing_rounding(1247.35, enabled=True)
        1247.35
        >>> apply_marketing_rounding(60.0, enabled=False)
        60.0
    """
    if enabled and price % 10 == 0:
        return price - 1
    return price


def round_to_nearest_five(price, enabled=True):
    """
    Round price to the nearest multiple of 5 (e.g., $17.50 -> $20, $12.30 -> $10).

    Args:
        price (float): Original price
        enabled (bool): Whether to apply rounding

    Returns:
        float: Rounded price

    Examples:
        >>> round_to_nearest_five(17.50, enabled=True)
        20.0
        >>> round_to_nearest_five(12.30, enabled=True)
        10.0
    """
    if enabled:
        return round(price / 5) * 5
    return price


# ========== ORDER CALCULATIONS ==========

def calculate_moq(unit_price):
    """
    Calculate Minimum Order Quantity based on $1,000 minimum order value.
    Formula: MOQ = ceil(1000 / Unit Price)

    Args:
        unit_price (float): Price per unit

    Returns:
        int: Minimum order quantity, or None if invalid unit price

    Examples:
        >>> calculate_moq(50.0)
        20
        >>> calculate_moq(75.0)
        14
        >>> calculate_moq(0)
        None
    """
    if unit_price <= 0:
        return None
    return math.ceil(1000 / unit_price)


def calculate_credit_card_fee(total, apply_fee=False, fee_percent=2.9):
    """
    Calculate credit card processing fee if applicable.
    Default rate: 2.9%

    Args:
        total (float): Order total
        apply_fee (bool): Whether to apply credit card fee
        fee_percent (float): Credit card fee percentage (default 2.9%)

    Returns:
        float: Credit card fee amount (0.0 if not applicable)

    Examples:
        >>> calculate_credit_card_fee(1000.0, apply_fee=True, fee_percent=2.9)
        29.0
        >>> calculate_credit_card_fee(1000.0, apply_fee=False)
        0.0
    """
    if apply_fee:
        return total * (fee_percent / 100)
    return 0.0


# ========== PARTNER & DATA EXTRACTION ==========

def extract_partner_contacts(df_partner_info):
    """
    Extract partner contact information from Partner-Specific Info sheet.
    Returns dict: {partner_name: {poc_name, poc_email, poc_phone}}

    Args:
        df_partner_info (DataFrame): Partner-Specific Info sheet data

    Returns:
        dict: Partner contacts mapping

    Example:
        >>> contacts = extract_partner_contacts(df)
        >>> contacts['Partner X']
        {'poc_name': 'John Smith', 'poc_email': 'john@partnerx.com', 'poc_phone': '555-1234'}
    """
    partner_contacts = {}

    for _, row in df_partner_info.iterrows():
        partner_name = row.get('Partner', '').strip()
        if not partner_name:
            continue

        partner_contacts[partner_name] = {
            'poc_name': row.get('POC Name', '').strip() or row.get('Contact Name', '').strip() or '',
            'poc_email': row.get('POC Email', '').strip() or row.get('Email', '').strip() or '',
            'poc_phone': row.get('POC Phone', '').strip() or row.get('Phone', '').strip() or ''
        }

    return partner_contacts


# ========== VALIDATION ==========

def validate_invoice_completeness(client_info, order_items):
    """
    Check if all required fields are filled before invoice/PO generation.
    Returns list of missing/invalid fields as warning messages.

    Args:
        client_info (dict): Client information dictionary
        order_items (list): List of order items

    Returns:
        list: List of warning messages for missing/invalid fields

    Example:
        >>> warnings = validate_invoice_completeness(client_info, order_items)
        >>> if warnings:
        ...     print("Missing fields:", warnings)
    """
    missing = []

    # Check client info required fields
    if not client_info.get('company_name'):
        missing.append("Company Name is required")
    if not client_info.get('contact_email'):
        missing.append("Contact Email is required")
    if not client_info.get('client_in_hands_date'):
        missing.append("Client In-Hands Date is required")
    if not client_info.get('order_submitted_by'):
        missing.append("Order Submitted By is required")
    if not client_info.get('cost_submitted_by'):
        missing.append("Cost Submitted By is required")

    # Check line items
    for idx, item in enumerate(order_items, 1):
        if not item.get('is_custom', False):
            if not item.get('partner_in_hands_date'):
                missing.append(f"Item #{idx} ({item.get('product_name', 'Unknown')}): Partner In-Hands Date not set")
            if item.get('cost_verified') == 'Pending':
                missing.append(f"Item #{idx} ({item.get('product_name', 'Unknown')}): Cost not verified")

    return missing


# ========== TIER PARSING ==========

def parse_tier_info(tier_string):
    """
    Parse 'T1: 1-25, T2: 26-50, ...' into dict of tier ranges.
    Returns: {1: (1, 25), 2: (26, 50), ...}

    Args:
        tier_string (str): Tier info string from spreadsheet

    Returns:
        dict: Mapping of tier number to (min_qty, max_qty) tuple

    Examples:
        >>> parse_tier_info("T1: 1-25, T2: 26-50, T3: 51-100")
        {1: (1, 25), 2: (26, 50), 3: (51, 100)}
        >>> parse_tier_info("T1: 1-25, T2: 26-50, T3: 51+")
        {1: (1, 25), 2: (26, 50), 3: (51, inf)}
        >>> parse_tier_info("")
        {}
    """
    if pd.isna(tier_string) or tier_string == "" or tier_string == "NA":
        return {}

    tier_dict = {}
    parts = tier_string.split(',')
    for part in parts:
        if ':' not in part:
            continue
        # Extract "T1: 1-25" → tier_num=1, range=(1, 25)
        tier_label, range_str = part.split(':')
        tier_num = int(tier_label.strip().replace('T', ''))
        range_str = range_str.strip()
        if '-' in range_str:
            min_qty, max_qty = range_str.split('-')
            tier_dict[tier_num] = (int(min_qty), int(max_qty))
        elif '+' in range_str:
            # Handle "1000+" format
            min_qty = int(range_str.replace('+', ''))
            tier_dict[tier_num] = (min_qty, float('inf'))

    return tier_dict


def parse_tariff_rate(tariff_string):
    """
    Parse tariff percentage from spreadsheet strings.

    Examples:
        "50.00%" -> 50.0
        "50%" -> 50.0
        "25.5%" -> 25.5
        "" -> 0.0
        "NA" -> 0.0

    Args:
        tariff_string (str): Tariff rate string from spreadsheet

    Returns:
        float: Tariff rate as decimal percentage (0.0 if invalid)

    Examples:
        >>> parse_tariff_rate("50.00%")
        50.0
        >>> parse_tariff_rate("25.5%")
        25.5
        >>> parse_tariff_rate("")
        0.0
    """
    if not tariff_string or tariff_string == '' or tariff_string == 'NA':
        return 0.0
    try:
        cleaned = str(tariff_string).replace('%', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


# ========== TARIFF CALCULATIONS ==========

def calculate_product_tariff(product_cost_with_markup, tariff_rate_percent):
    """
    Calculate tariff on product cost.

    Args:
        product_cost_with_markup: Base product cost (price + markup, excluding customization)
        tariff_rate_percent: Tariff rate as percentage (e.g., 50.0 for 50%)

    Returns:
        float: Tariff dollar amount

    Example:
        >>> calculate_product_tariff(4000.0, 50.0)
        2000.0
        >>> calculate_product_tariff(2000.0, 0.0)
        0.0
    """
    if tariff_rate_percent <= 0:
        return 0.0
    return product_cost_with_markup * (tariff_rate_percent / 100)


# ========== PROPOSAL TO ORDER CONVERSION ==========

def convert_proposal_to_order(proposal_item, get_unit_price_func, calculate_tariff_func):
    """
    Convert a proposal item from Tab 1 to an order item for Tab 2.

    Proposal items have different structure than order items, so we need to
    transform the data while preserving ONLY core settings:
    - Product selection
    - Quantity
    - Markup %

    All other settings (customization, rounding, etc.) are reset to defaults
    so they can be configured fresh in the order.

    Args:
        proposal_item (dict): Item from st.session_state.proposal_products
        get_unit_price_func: Function to get unit price (get_unit_price_new_system)
        calculate_tariff_func: Function to calculate tariff (calculate_product_tariff)

    Returns:
        dict: Order item compatible with st.session_state.order_items

    Example:
        >>> from src.pricing_engine import get_unit_price_new_system
        >>> order_item = convert_proposal_to_order(proposal_item, get_unit_price_new_system, calculate_product_tariff)
    """
    product_data = proposal_item.get('product_data', {})

    # PRESERVE: Quantity and markup from proposal
    quantity = proposal_item.get('quantity', 1)
    markup_percent = proposal_item.get('markup_percent', 100.0)

    # Get base price for this quantity
    base_price_per_unit, tier_info, tier_num = get_unit_price_func(product_data, quantity)

    # RESET: Customization settings to defaults (user will configure in order)
    customization_setup_total = 0.0
    customization_unit_total = 0.0
    customization_per_unit = 0.0

    # Calculate product cost (base price × quantity)
    product_cost_subtotal = base_price_per_unit * quantity

    # Calculate markup (on product cost only, not customization)
    markup_amount = product_cost_subtotal * (markup_percent / 100)

    # Calculate total for this line item
    product_total = product_cost_subtotal + markup_amount + customization_setup_total + customization_unit_total

    # Calculate per-unit total
    total_per_unit = product_total / quantity

    # Parse tariff info
    tariff_rate_percent = parse_tariff_rate(product_data.get('Tariff Rate', ''))
    tariff_base = product_cost_subtotal  # Tariff on product cost only (excludes customization)
    tariff_amount = calculate_tariff_func(tariff_base, tariff_rate_percent)

    # Build order item (matching structure from Tab 2 line 1606-1640)
    order_item = {
        # Product identification
        'product_name': product_data.get('Product/Service', 'Unknown Product'),
        'product_ref': product_data.get('Purchase Description', ''),
        'partner': product_data.get('Partner', 'Unknown Partner'),
        'product_data': product_data,  # Store full product row for inline editing
        'product_data_row': product_data,  # Keep for backward compatibility
        'is_custom': False,  # Regular product (not custom line item)

        # Quantity & pricing
        'quantity': quantity,
        'base_price': base_price_per_unit,
        'tier_range': tier_info if tier_info else '',
        'tier_column': f'T{tier_num}' if tier_num else '',

        # Markup
        'markup_percent': markup_percent,
        'markup_amount': markup_amount,

        # Customization (RESET to defaults - user will configure in order)
        # Pull default costs from spreadsheet but leave customization disabled
        'include_customization': False,
        'customization_description': product_data.get('Customization Info', ''),
        'customization_setup_fee': float(clean_price(product_data.get('Customization Setup Fee', '')) or 0.0),
        'customization_per_unit': float(clean_price(product_data.get('Customization Cost per Unit', '')) or 0.0),
        'customization_setup_total': 0.0,
        'customization_unit_total': 0.0,
        'apply_custom_minimum': False,
        'customization_minimum_qty': 0,

        # Subtotals and totals
        'product_subtotal': product_cost_subtotal,  # Base price × qty
        'subtotal_before_markup': product_cost_subtotal + customization_setup_total + customization_unit_total,
        'product_total': product_total,  # Product + markup + customization
        'total_per_unit': total_per_unit,  # Total divided by quantity

        # Tariff
        'country_of_origin': product_data.get('Country of Origin', 'Unknown'),
        'tariff_rate_percent': tariff_rate_percent,
        'tariff_info': product_data.get('Tariff Info', ''),
        'tariff_base': tariff_base,
        'tariff_amount': tariff_amount,

        # MSRP (if included in proposal)
        'partner_msrp_per_unit': proposal_item.get('msrp_value', 0.0) if proposal_item.get('show_msrp', False) else 0.0,
        'show_msrp_comparison': proposal_item.get('show_msrp', False),

        # Metadata
        'minimum_qty': '',  # Not in new structure
        'source': 'proposal',  # Track that this came from proposal

        # Order fulfillment (to be filled in Tab 2 if needed)
        'partner_in_hands_date': '',
        'cost_verified': 'Pending',
        'product_specs': product_data.get('Marketing Description', '')
    }

    return order_item
