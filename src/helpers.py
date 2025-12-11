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


def round_to_nearest_fifty_cents(price, enabled=True):
    """
    Round price to nearest $0.50 increment.

    Args:
        price (float): Original price
        enabled (bool): Whether to apply rounding

    Returns:
        float: Price rounded to nearest $0.50

    Examples:
        >>> round_to_nearest_fifty_cents(24.37, enabled=True)
        24.50
        >>> round_to_nearest_fifty_cents(24.23, enabled=True)
        24.00
        >>> round_to_nearest_fifty_cents(24.75, enabled=True)
        25.00
        >>> round_to_nearest_fifty_cents(24.25, enabled=True)
        24.50
        >>> round_to_nearest_fifty_cents(24.37, enabled=False)
        24.37
    """
    if enabled:
        return round(price * 2) / 2
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


def calculate_credit_card_fee(total, apply_fee=False, fee_percent=3.0):
    """
    Calculate credit card processing fee if applicable.
    Default rate: 3%

    Args:
        total (float): Order total
        apply_fee (bool): Whether to apply credit card fee
        fee_percent (float): Credit card fee percentage (default 3%)

    Returns:
        float: Credit card fee amount (0.0 if not applicable)

    Examples:
        >>> calculate_credit_card_fee(1000.0, apply_fee=True, fee_percent=3.0)
        30.0
        >>> calculate_credit_card_fee(1000.0, apply_fee=False)
        0.0
    """
    if apply_fee:
        return total * (fee_percent / 100)
    return 0.0


def calculate_markup_from_price(base_cost, client_price):
    """
    Calculate markup percentage given base cost and desired client price.
    Formula: markup = ((client_price / base_cost) - 1) * 100

    Args:
        base_cost (float): Base cost of the product
        client_price (float): Desired client price

    Returns:
        float: Markup percentage (e.g., 100.0 for 100% markup)
               Returns 0.0 if base_cost is 0 or negative

    Examples:
        >>> calculate_markup_from_price(50.0, 100.0)
        100.0
        >>> calculate_markup_from_price(50.0, 75.0)
        50.0
        >>> calculate_markup_from_price(50.0, 50.0)
        0.0
        >>> calculate_markup_from_price(50.0, 40.0)
        -20.0
    """
    if base_cost <= 0:
        return 0.0

    markup = ((client_price / base_cost) - 1) * 100
    return round(markup, 2)  # Round to 2 decimal places for display


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

    # Check for at least one contact with email
    contacts = client_info.get('contacts', [])
    if not contacts:
        missing.append("At least one contact is required")
    else:
        # Check if primary contact has email
        primary_contact = contacts[0] if contacts else {}
        if not primary_contact.get('email'):
            missing.append("Primary Contact Email is required")
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

    # Store quoted price (product + markup, before customization) for comparison in Tab 2
    quoted_price_per_unit = (product_cost_subtotal + markup_amount) / quantity

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
        'quoted_price_per_unit': quoted_price_per_unit,  # Price quoted in proposal (for comparison)
        'proposal_quantity': quantity,  # Original quantity from proposal
        'proposal_markup_percent': markup_percent,  # Original markup from proposal
        'proposal_tier_range': tier_info if tier_info else '',  # Original tier from proposal
        'proposal_tier_column': f'T{tier_num}' if tier_num else '',  # Original tier number

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
        'product_specs': product_data.get('Marketing Description', ''),

        # Editable description field (empty by default, user can customize)
        'edited_description': ''
    }

    return order_item


# ========== HTML FORM PARSING ==========

def parse_client_order_form_html(html_content):
    """
    Parse completed HTML client order form and extract client information and products.

    Extracts data from fill-in fields in the HTML form that clients complete,
    including client details and product names from the Order Details table.

    Args:
        html_content: String containing the HTML form content

    Returns:
        dict: Extracted data with keys:
            - client_type: "Existing" or "New"
            - company_name: str
            - contact_name: str
            - contact_email: str
            - drop_shipping: "Yes" or "No"
            - shipping_address: str
            - dropshipping_info: str
            - billing_address: str
            - client_in_hands_date: str (format: MM/DD/YYYY)
            - impact_card_preference: str
            - payment_preference: str
            - products: list of str (product names from Order Details table)
            - parse_errors: list of strings (warnings about fields that couldn't be parsed)

    Example:
        >>> html = "<td class=\"fill-in\">Acme Corp</td>"
        >>> data = parse_client_order_form_html(html)
        >>> data['company_name']
        'Acme Corp'
        >>> data['products']
        ['Jaggery - Organic', 'Reusable Shopping Bag']
    """
    import re
    from html.parser import HTMLParser

    extracted_data = {
        'client_type': '',
        'company_name': '',
        'contact_name': '',
        'contact_email': '',
        'drop_shipping': '',
        'shipping_address': '',
        'dropshipping_info': '',
        'billing_address': '',
        'client_in_hands_date': '',
        'impact_card_preference': '',
        'payment_preference': '',
        'products': [],  # List of product names from Order Details table
        'parse_errors': []
    }

    # Strategy: Parse table rows to extract label-value pairs
    # Supports both our generated HTML (class="fill-in") and Google Docs HTML (class="c1")

    # Clean up HTML tags and decode entities
    def clean_cell_content(content):
        # Remove HTML tags
        content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)  # Convert <br> to newline
        content = re.sub(r'<[^>]+>', '', content)  # Remove all HTML tags
        content = content.strip()
        # Remove placeholder text in brackets
        if content.startswith('[') and content.endswith(']'):
            return ''  # Empty if still placeholder
        return content

    # Use a better approach: extract each <tr> tag separately, then parse its contents
    # This avoids regex crossing row boundaries
    tr_pattern = r'<tr[^>]*>(.*?)</tr>'
    all_rows = re.findall(tr_pattern, html_content, re.DOTALL | re.IGNORECASE)

    # Build a dictionary mapping labels to values
    field_map = {}
    for row_content in all_rows:
        # Extract label and value from this specific row
        td_pattern = r'<td[^>]*>(.*?)</td>'
        tds = re.findall(td_pattern, row_content, re.DOTALL | re.IGNORECASE)

        # Skip rows with colspan (section headers)
        if len(tds) < 2:
            continue

        # Check if first TD has colspan="2" or higher (section headers)
        # Google Docs adds colspan="1" to all TDs, so we need to check the value
        first_td = row_content.split('</td>')[0]
        colspan_match = re.search(r'colspan="?(\d+)"?', first_td)
        if colspan_match and int(colspan_match.group(1)) > 1:
            continue  # Skip section headers

        # We need exactly 2 TDs for label-value pairs
        if len(tds) == 2:
            label_html = tds[0]
            value_html = tds[1]

            # Detect if this looks like a label-value pair:
            # - Our generated HTML: second TD has class="fill-in"
            # - Google Docs HTML: second TD has italic text (class="c1" or style)
            # - Skip if first TD looks like a header (all caps, no asterisk)

            label_text = re.sub(r'<[^>]+>', '', label_html).strip()

            # Skip header rows (all content is uppercase or contains "Product Name", "Quantity", etc.)
            if label_text.isupper() or 'Product Name' in label_text or 'Quantity' in label_text:
                continue

            # This looks like a data row if:
            # 1. Our format: has class="fill-in" OR
            # 2. Google Docs: has italic/styled text (class="c1" or font-style:italic) OR
            # 3. Label has asterisk (required field marker)
            is_data_row = (
                'class="fill-in"' in row_content or
                "class='fill-in'" in row_content or
                'class="c1"' in value_html or
                "class='c1'" in value_html or
                'font-style:italic' in value_html or
                '*' in label_text
            )

            if is_data_row:
                # Clean label: remove all HTML tags, asterisks, and normalize whitespace
                label_clean = re.sub(r'<[^>]+>', '', label_html).strip().lower()
                label_clean = re.sub(r'\s+', ' ', label_clean)  # Normalize whitespace
                label_clean = label_clean.rstrip('*').strip()  # Remove trailing asterisk (required field marker)

                value_clean = clean_cell_content(value_html)
                field_map[label_clean] = value_clean

    # Map to our structure using field labels
    if 'client type' in field_map:
        client_type = field_map['client type']
        if 'Existing' in client_type and 'New' not in client_type:
            extracted_data['client_type'] = 'Existing'
        elif 'New' in client_type and 'Existing' not in client_type:
            extracted_data['client_type'] = 'New'
        else:
            extracted_data['client_type'] = client_type

    if 'company name' in field_map:
        extracted_data['company_name'] = field_map['company name']

    if 'contact name' in field_map:
        extracted_data['contact_name'] = field_map['contact name']

    if 'contact email' in field_map:
        extracted_data['contact_email'] = field_map['contact email']

    if 'drop shipping?' in field_map:
        drop_shipping = field_map['drop shipping?']
        if 'Yes' in drop_shipping and 'No' not in drop_shipping:
            extracted_data['drop_shipping'] = 'Yes'
        elif 'No' in drop_shipping and 'Yes' not in drop_shipping:
            extracted_data['drop_shipping'] = 'No'
        else:
            extracted_data['drop_shipping'] = drop_shipping

    # Match "shipping address" with or without helper text
    for key in field_map.keys():
        if 'shipping address' in key:
            extracted_data['shipping_address'] = field_map[key]
            break

    if 'dropshipping information' in field_map:
        extracted_data['dropshipping_info'] = field_map['dropshipping information']

    if 'billing address' in field_map:
        extracted_data['billing_address'] = field_map['billing address']

    if 'client in-hands date' in field_map:
        extracted_data['client_in_hands_date'] = field_map['client in-hands date']

    if 'impact card preference' in field_map:
        value = field_map['impact card preference']
        # Look for the selected option
        impact_options = ['Peace by Piece Impact Card', 'Custom Impact Card', 'Custom Message Card', 'Send us your own card']
        for option in impact_options:
            if option in value and all(opt not in value or opt == option for opt in impact_options):
                extracted_data['impact_card_preference'] = option
                break

    if 'payment preference' in field_map:
        value = field_map['payment preference']
        # Look for the selected option
        payment_options = ['ACH', 'Check', 'Credit Card']
        for option in payment_options:
            if option in value and all(opt not in value or opt == option for opt in payment_options):
                extracted_data['payment_preference'] = option
                break

    # Validate required fields
    required_fields = ['company_name', 'contact_name', 'contact_email', 'client_in_hands_date']
    for field in required_fields:
        if not extracted_data[field]:
            extracted_data['parse_errors'].append(f"Required field '{field}' is empty or could not be parsed")

    # ============================================================
    # EXTRACT PRODUCTS FROM ORDER DETAILS TABLE
    # ============================================================
    # Find the ORDER DETAILS section and extract product names
    # Table structure:
    # <tr><td colspan="3">ORDER DETAILS</td></tr>
    # <tr><th>Product Name</th><th>Quantity</th><th>Customization/Branding Details</th></tr>
    # <tr><td>Product 1</td><td>100</td><td>...</td></tr>
    # ...

    in_order_details = False
    for row_content in all_rows:
        # Check if this is the ORDER DETAILS section header
        if 'ORDER DETAILS' in row_content and 'colspan' in row_content:
            in_order_details = True
            continue

        # Check if we've left the ORDER DETAILS section (hit another section header)
        if in_order_details and 'colspan' in row_content and any(
            section in row_content.upper() for section in ['IMPACT CARDS', 'PAYMENT', 'ADDITIONAL']
        ):
            in_order_details = False
            break

        # If we're in ORDER DETAILS section, extract product rows
        if in_order_details:
            # Extract all TD tags from this row
            td_pattern = r'<td[^>]*>(.*?)</td>'
            tds = re.findall(td_pattern, row_content, re.DOTALL | re.IGNORECASE)

            # Skip header row (contains <th> tags)
            if '<th' in row_content.lower():
                continue

            # Product rows should have 3 columns
            if len(tds) >= 1:
                # Extract product name from first column
                product_name = clean_cell_content(tds[0])

                # Skip empty rows or placeholder text
                if product_name and not product_name.startswith('[') and product_name.lower() not in ['product name', '']:
                    extracted_data['products'].append(product_name)

    return extracted_data


# ========== SHIPPING UTILITIES ==========

def get_shipping_costs(product_data):
    """
    Extract shipping costs from product data, handling both new and legacy column structures.

    New structure (Real dataset):
    - 'Shipping Cost (PBP)': What PBP pays to partner
    - 'Shipping Price (Client)': What client pays

    Legacy structure (Demo dataset):
    - 'Shipping': Single value used for both PBP and client

    Args:
        product_data (dict): Product data dictionary from spreadsheet

    Returns:
        tuple: (pbp_cost, client_price) - both as float or 0.0 if not available

    Examples:
        >>> # New structure
        >>> get_shipping_costs({'Shipping Cost (PBP)': '$10', 'Shipping Price (Client)': '$15'})
        (10.0, 15.0)

        >>> # Legacy structure
        >>> get_shipping_costs({'Shipping': '$12.50'})
        (12.5, 12.5)

        >>> # Missing data
        >>> get_shipping_costs({})
        (0.0, 0.0)
    """
    # Try new column structure first
    if 'Shipping Cost (PBP)' in product_data and 'Shipping Price (Client)' in product_data:
        pbp_cost = clean_price(product_data.get('Shipping Cost (PBP)', '')) or 0.0
        client_price = clean_price(product_data.get('Shipping Price (Client)', '')) or 0.0
        return (pbp_cost, client_price)

    # Fall back to legacy single column
    elif 'Shipping' in product_data:
        shipping_value = clean_price(product_data.get('Shipping', '')) or 0.0
        return (shipping_value, shipping_value)  # Use same value for both

    # No shipping data available
    return (0.0, 0.0)


def format_shipping_display(product_data):
    """
    Format shipping costs for display in UI.

    Args:
        product_data (dict): Product data dictionary

    Returns:
        str: Formatted shipping string for display

    Examples:
        >>> # Both costs available
        >>> format_shipping_display({'Shipping Cost (PBP)': '$10', 'Shipping Price (Client)': '$15'})
        'PBP: $10.00 | Client: $15.00'

        >>> # Single legacy cost
        >>> format_shipping_display({'Shipping': '$12.50'})
        'Shipping: $12.50'

        >>> # No shipping
        >>> format_shipping_display({})
        'No shipping data'
    """
    pbp_cost, client_price = get_shipping_costs(product_data)

    # Both costs available (new structure)
    if 'Shipping Cost (PBP)' in product_data and 'Shipping Price (Client)' in product_data:
        if pbp_cost > 0 or client_price > 0:
            return f"PBP: ${pbp_cost:.2f} | Client: ${client_price:.2f}"

    # Single cost (legacy structure)
    elif 'Shipping' in product_data and pbp_cost > 0:
        return f"Shipping: ${pbp_cost:.2f}"

    return "No shipping data"


# ========== SPLIT TOTALS CALCULATIONS ==========

def calculate_split_totals(order_items, markup_only=False):
    """
    Calculate PBP costs and client prices separately for order items.

    Args:
        order_items (list): List of order items with pricing information
        markup_only (bool): If True, only return product costs with markup (no customization)

    Returns:
        dict: Dictionary containing:
            - products_pbp_cost: Total PBP cost for products
            - products_client_price: Total client price for products (with markup)
            - customization_pbp_cost: Total PBP cost for customization
            - customization_client_price: Total client price for customization
            - products_only_client_price: Products with markup (no customization)
            - total_pbp_cost: Combined PBP cost
            - total_client_price: Combined client price
    """
    results = {
        'products_pbp_cost': 0.0,
        'products_client_price': 0.0,
        'customization_pbp_cost': 0.0,
        'customization_client_price': 0.0,
        'products_only_client_price': 0.0,
        'total_pbp_cost': 0.0,
        'total_client_price': 0.0
    }

    for item in order_items:
        # Skip custom line items (they have different structure)
        if item.get('is_custom', False):
            # Custom items are already marked up, so both cost and price are the same
            custom_total = item.get('product_total', 0)
            results['products_pbp_cost'] += custom_total
            results['products_client_price'] += custom_total
            results['products_only_client_price'] += custom_total
            continue

        # Regular products
        # Product base cost (what PBP pays)
        product_cost = item.get('product_subtotal', 0)
        results['products_pbp_cost'] += product_cost

        # Product client price (with markup)
        markup_amount = item.get('markup_amount', 0)
        product_with_markup = product_cost + markup_amount
        results['products_client_price'] += product_with_markup
        results['products_only_client_price'] += product_with_markup

        # Customization costs (if not markup_only)
        if not markup_only:
            # Setup fee (one-time)
            setup_pbp = item.get('customization_setup_cost', 0)
            setup_client = item.get('customization_setup_total', 0)
            results['customization_pbp_cost'] += setup_pbp
            results['customization_client_price'] += setup_client

            # Per-unit customization
            per_unit_pbp = item.get('customization_unit_cost', 0)
            per_unit_client = item.get('customization_unit_total', 0)
            results['customization_pbp_cost'] += per_unit_pbp
            results['customization_client_price'] += per_unit_client

    # Calculate totals
    results['total_pbp_cost'] = results['products_pbp_cost'] + results['customization_pbp_cost']
    results['total_client_price'] = results['products_client_price'] + results['customization_client_price']

    return results


def format_pricing_breakdown_row(description, units, pbp_per_unit, pbp_total, client_per_unit, client_total):
    """
    Format a row for the pricing breakdown table.

    Args:
        description (str): Line item description
        units (int/str): Number of units or "one-time"
        pbp_per_unit (float): PBP cost per unit
        pbp_total (float): Total PBP cost
        client_per_unit (float): Client price per unit
        client_total (float): Total client price

    Returns:
        list: Formatted row data for DataFrame with columns:
        [Description, Units, PBP Cost (Per Unit), PBP Cost, Client Price (Per Unit), Client Price]
    """
    # Format units column
    units_str = str(units) if units != "one-time" else "1"

    # Format per unit columns
    pbp_per_unit_str = f"${pbp_per_unit:.2f}" if pbp_per_unit > 0 else ""
    client_per_unit_str = f"${client_per_unit:.2f}" if client_per_unit > 0 else ""

    # Format totals
    pbp_str = f"${pbp_total:.2f}" if pbp_total > 0 else "$0.00"
    client_str = f"${client_total:.2f}" if client_total > 0 else "$0.00"

    # Return in the new logical order: Description, Units, PBP Per Unit, PBP Total, Client Per Unit, Client Total
    return [description, units_str, pbp_per_unit_str, pbp_str, client_per_unit_str, client_str]
