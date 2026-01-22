"""
Core pricing calculation engine.
Handles tier selection, price lookup, customization costs, and tariff calculations.
"""

import pandas as pd
from src.helpers import parse_tier_info, parse_tariff_rate, clean_price, get_column_value


def determine_tier_number(quantity, tier_info_string, has_tiers):
    """
    Returns tier number (1-6) based on quantity, or None if no tiers.

    Args:
        quantity: Order quantity
        tier_info_string: String like "T1: 1-25, T2: 26-50, ..."
        has_tiers: 'Y' if product has tiers, else 'N'

    Returns:
        int: Tier number (1-6) or None if no tiers

    Example:
        >>> determine_tier_number(50, "T1: 1-25, T2: 26-50, T3: 51-100", "Y")
        2
    """
    if has_tiers != 'Y':
        return None

    tier_ranges = parse_tier_info(tier_info_string)

    if not tier_ranges:
        return None

    for tier_num, (min_qty, max_qty) in tier_ranges.items():
        if min_qty <= quantity <= max_qty:
            return tier_num

    # If quantity exceeds all ranges, use highest tier
    if tier_ranges:
        return max(tier_ranges.keys())

    return None


def get_unit_price_new_system(row, quantity):
    """
    Get correct unit price based on tier logic.
    Handles both tiered and non-tiered pricing.

    Updated January 2026: Now uses consolidated "PBP Cost (No Tiers/Tier 1)" column.
    Automatically normalizes cost to per-unit basis using "Units Per Package" column.

    Args:
        row: DataFrame row containing product data
        quantity: Order quantity

    Returns:
        tuple: (price, tier_range, column_name) or (None, None, None) if not found

    Example:
        >>> get_unit_price_new_system(product_row, 100)
        (48.0, '51-100', 'PBP Cost: Tier 3')
    """
    has_tiers = str(row.get('Pricing Tiers (Y/N)', '')).strip().upper()

    if has_tiers != 'Y':
        # Use consolidated column for flat rate
        # Try new schema name first, fall back to old name for backward compatibility
        flat_price = get_column_value(row, 'PBP Cost (No Tiers/Tier 1)', 'PBP Cost (No Tiers)', None)
        flat_price = clean_price(flat_price) if flat_price is not None else None

        if flat_price is not None:
            # Normalize to per-unit cost
            units_per_package = row.get('Units per Package', 1)
            # Convert to float if string (Google Sheets may return as string)
            try:
                units_per_package = float(units_per_package) if units_per_package else 1
            except (ValueError, TypeError):
                units_per_package = 1

            if units_per_package > 0:
                flat_price = flat_price / units_per_package
            return flat_price, "No Tiers", "PBP Cost (No Tiers/Tier 1)"
        else:
            return None, None, None

    # Determine tier and get price
    tier_info = row.get('Pricing Tiers Info', '')
    tier_num = determine_tier_number(quantity, tier_info, has_tiers)

    if tier_num is None:
        return None, None, None

    # Use consolidated column for Tier 1
    if tier_num == 1:
        tier_col_name = 'PBP Cost (No Tiers/Tier 1)'
        price = get_column_value(row, 'PBP Cost (No Tiers/Tier 1)', 'PBP Cost: Tier 1', None)
        price = clean_price(price) if price is not None else None
    else:
        # Use tier-specific columns for Tier 2-6
        tier_col_name = f'PBP Cost: Tier {tier_num}'
        price = clean_price(row.get(tier_col_name, ''))

    if price is not None:
        # Normalize to per-unit cost
        units_per_package = row.get('Units per Package', 1)
        # Convert to float if string (Google Sheets may return as string)
        try:
            units_per_package = float(units_per_package) if units_per_package else 1
        except (ValueError, TypeError):
            units_per_package = 1

        if units_per_package > 0:
            price = price / units_per_package

        # Get tier range for display
        tier_ranges = parse_tier_info(tier_info)
        if tier_num in tier_ranges:
            min_qty, max_qty = tier_ranges[tier_num]
            if max_qty == float('inf'):
                tier_range = f"{min_qty}+"
            else:
                tier_range = f"{min_qty}-{max_qty}"
            return price, tier_range, tier_col_name

    return None, None, None


def get_price_for_quantity(product_row, quantity):
    """
    OLD SYSTEM: Select the appropriate price tier based on quantity.

    DEPRECATED: This function uses the old jaggery_demo tier structure.
    For new system, use get_unit_price_new_system() instead.

    Returns (price, tier_range, column_name) or (None, None, None) if not found.
    """
    # Define tier columns and their ranges (soft-coded for easy modification)
    tier_columns = [
        {'min': 1, 'max': 25, 'column': 'PBP Cost w/o shipping (1-25)'},
        {'min': 26, 'max': 50, 'column': 'PBP Cost w/o shipping (26-50)'},
        {'min': 51, 'max': 100, 'column': 'PBP Cost w/o shipping (51-100)'},
        {'min': 101, 'max': 250, 'column': 'PBP Cost w/o shipping (101-250)'},
        {'min': 251, 'max': 500, 'column': 'PBP Cost w/o shipping (251-500)'},
        {'min': 501, 'max': 1000, 'column': 'PBP Cost w/o shipping (501-1000)'},
        {'min': 1001, 'max': float('inf'), 'column': 'PBP Cost w/o shipping (1000+)'}
    ]

    # Find matching tier
    for i, tier in enumerate(tier_columns):
        if tier['min'] <= quantity <= tier['max']:
            # Try exact tier match
            if tier['column'] in product_row.index:
                price = clean_price(product_row[tier['column']])
                if price is not None:
                    tier_range = f"{tier['min']}-{tier['max']}" if tier['max'] != float('inf') else f"{tier['min']}+"
                    return price, tier_range, tier['column']

            # Fallback: try higher tiers
            for higher_tier in tier_columns[i+1:]:
                if higher_tier['column'] in product_row.index:
                    price = clean_price(product_row[higher_tier['column']])
                    if price is not None:
                        tier_range = f"{higher_tier['min']}-{higher_tier['max']}" if higher_tier['max'] != float('inf') else f"{higher_tier['min']}+"
                        return price, tier_range, higher_tier['column']

            # Fallback: try lower tiers
            for lower_tier in reversed(tier_columns[:i]):
                if lower_tier['column'] in product_row.index:
                    price = clean_price(product_row[lower_tier['column']])
                    if price is not None:
                        tier_range = f"{lower_tier['min']}-{lower_tier['max']}" if lower_tier['max'] != float('inf') else f"{lower_tier['min']}+"
                        return price, tier_range, lower_tier['column']

    return None, None, None


def calculate_additional_costs(product_row, quantity, include_labels=False):
    """
    OLD SYSTEM: Calculate additional costs (setup fees, labels, etc.)

    DEPRECATED: This function uses old column names (Art Setup Fee, Labels).
    For new system, use calculate_customization_costs() instead.

    Art Setup Fee only applies when labels are selected.
    Returns dict with all additional costs.
    """
    additional_costs = {}

    # Label Costs (optional, user chooses)
    if include_labels:
        # Art Setup Fee (one-time per order) - only when labels are selected
        setup_fee = clean_price(product_row.get('Art Setup Fee', ''))
        if setup_fee is None:
            setup_fee = 0
        additional_costs['art_setup_fee_total'] = setup_fee
        additional_costs['art_setup_fee_per_unit'] = setup_fee / quantity if quantity > 0 else 0

        # Label unit cost and minimum
        label_cost_per_label = clean_price(product_row.get('Labels up to 1" x 2.5\'', ''))
        if label_cost_per_label is None:
            label_cost_per_label = 0

        label_minimum_raw = clean_price(product_row.get('Minimum for labels', ''))
        label_minimum = int(label_minimum_raw) if label_minimum_raw else 100

        # Apply minimum: customer pays for at least label_minimum labels
        labels_to_charge = max(quantity, label_minimum)
        additional_costs['labels_charged'] = labels_to_charge
        additional_costs['label_cost_per_label'] = label_cost_per_label
        additional_costs['label_cost_total'] = label_cost_per_label * labels_to_charge
        additional_costs['label_cost_per_unit'] = (label_cost_per_label * labels_to_charge) / quantity if quantity > 0 else 0

        # Warning message if minimum applies
        if quantity < label_minimum:
            additional_costs['label_warning'] = f"Minimum {label_minimum} labels required. Charging for {labels_to_charge} labels even though ordering {quantity} units."
    else:
        # No labels requested - no costs apply
        additional_costs['art_setup_fee_total'] = 0
        additional_costs['art_setup_fee_per_unit'] = 0
        additional_costs['label_cost_total'] = 0
        additional_costs['labels_charged'] = 0
        additional_costs['label_warning'] = None

    return additional_costs


def calculate_customization_costs(row, quantity, include_customization, customization_minimum=None):
    """
    NEW SYSTEM: Calculate customization costs (setup fee + per-unit costs).

    Args:
        row: DataFrame row containing product data
        quantity: Order quantity
        include_customization: Boolean - whether to include customization costs
        customization_minimum: Minimum quantity for customization (optional)

    Returns:
        dict: Breakdown of customization costs

    Example:
        >>> calculate_customization_costs(product_row, 100, True, 100)
        {
            'setup_fee': 50.0,
            'per_unit_cost': 2.0,
            'units_charged': 100,
            'total_customization': 250.0,
            'warning': None
        }
    """
    customization = {}

    if not include_customization:
        customization['setup_fee'] = 0.0
        customization['per_unit_cost'] = 0.0
        customization['units_charged'] = 0
        customization['total_customization'] = 0.0
        customization['warning'] = None
        return customization

    # Extract customization costs from new system columns
    # Use backward compatibility helper to support both old and new column names
    setup_fee_raw = get_column_value(row, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', '')
    per_unit_raw = get_column_value(row, 'Client Price: Customization Cost per Unit', 'Customization Cost per Unit', '')
    setup_fee = clean_price(setup_fee_raw) or 0.0
    per_unit = clean_price(per_unit_raw) or 0.0

    # Get customization minimum from row if not provided
    if customization_minimum is None:
        min_raw = clean_price(row.get('Customization Minimum', ''))
        customization_minimum = int(min_raw) if min_raw else quantity

    # Apply minimum: customer pays for at least customization_minimum units
    units_charged = max(quantity, customization_minimum)

    customization['setup_fee'] = setup_fee
    customization['per_unit_cost'] = per_unit
    customization['units_charged'] = units_charged
    customization['total_customization'] = setup_fee + (per_unit * units_charged)

    # Warning if minimum applies
    if quantity < customization_minimum:
        customization['warning'] = f"Customization minimum {customization_minimum} units. Charging for {units_charged} units even though ordering {quantity}."
    else:
        customization['warning'] = None

    return customization


def calculate_product_quote(row, quantity, markup_percent, include_customization=False,
                           customization_minimum=None, shipping=0.0, tariff_rate_percent=0.0):
    """
    Calculate complete quote for a single product.

    Args:
        row: DataFrame row containing product data
        quantity: Order quantity
        markup_percent: Markup percentage to apply to product cost
        include_customization: Whether to include customization costs
        customization_minimum: Minimum quantity for customization
        shipping: Shipping cost (optional, default 0)
        tariff_rate_percent: Tariff rate as percentage (e.g., 50.0 for 50%)

    Returns:
        dict: Detailed quote breakdown

    Formula:
        Product Cost = Unit Price × Quantity
        Markup = Product Cost × (Markup% / 100)
        Customization = Setup Fee + (Per-Unit × Quantity)
        Tariff = (Product Cost + Markup) × (Tariff% / 100)
        Total = Product Cost + Markup + Customization + Shipping + Tariff
    """
    quote = {}

    # Get unit price
    unit_price, tier_range, price_column = get_unit_price_new_system(row, quantity)

    if unit_price is None:
        return None  # Could not determine price

    # Calculate base product cost
    product_cost = unit_price * quantity

    # Calculate markup (applies to product cost only)
    markup_amount = product_cost * (markup_percent / 100)
    product_cost_with_markup = product_cost + markup_amount

    # Calculate customization costs
    customization = calculate_customization_costs(row, quantity, include_customization, customization_minimum)

    # Calculate tariff (applies to product cost with markup, NOT customization)
    from src.helpers import calculate_product_tariff
    tariff_amount = calculate_product_tariff(product_cost_with_markup, tariff_rate_percent)

    # Calculate total
    total = product_cost_with_markup + customization['total_customization'] + shipping + tariff_amount

    quote['unit_price'] = unit_price
    quote['tier_range'] = tier_range
    quote['price_column'] = price_column
    quote['quantity'] = quantity
    quote['product_cost'] = product_cost
    quote['markup_percent'] = markup_percent
    quote['markup_amount'] = markup_amount
    quote['product_cost_with_markup'] = product_cost_with_markup
    quote['customization'] = customization
    quote['shipping'] = shipping
    quote['tariff_rate'] = tariff_rate_percent
    quote['tariff_amount'] = tariff_amount
    quote['total'] = total

    return quote


def calculate_pbp_msrp(product_data, quantity, user_markup_override=None):
    """
    Calculate PBP MSRP using one of three pricing methods.
    Part of January 2026 schema transition.

    Pricing Methods:
    1. "MSRP + % of cost" - Add shipping recovery to vendor MSRP
    2. "MSRP capped – ship absorbed" - Use vendor MSRP exactly
    3. "Standard markup" - Traditional cost × (1 + markup%)

    Args:
        product_data: Product row from spreadsheet
        quantity: Order quantity
        user_markup_override: Optional user override for markup % (Standard markup only)

    Returns:
        dict: {
            'pbp_msrp': float,              # Final calculated price
            'method_used': str,             # Which pricing method was used
            'calculation_details': dict,     # Breakdown of calculation
            'spreadsheet_msrp': float,      # MSRP from spreadsheet (for comparison)
            'validation_status': str        # 'match', 'mismatch', or 'no_spreadsheet_value'
        }

    Example:
        >>> result = calculate_pbp_msrp(product_data, quantity=100)
        >>> result['pbp_msrp']
        11.00
        >>> result['method_used']
        'MSRP + % of cost'
    """
    from src.helpers import (
        get_pricing_logic,
        get_shipping_addon_percent,
        get_column_value,
        normalize_cost_to_per_item
    )

    # Step 1: Get base cost for quantity (from existing get_unit_price_new_system)
    base_cost, tier_info, tier_num = get_unit_price_new_system(product_data, quantity)

    if base_cost is None:
        # Cannot calculate price without cost
        return {
            'pbp_msrp': 0.0,
            'method_used': 'Error',
            'calculation_details': {'error': 'Could not determine base cost'},
            'spreadsheet_msrp': None,
            'validation_status': 'error'
        }

    # Step 2: Normalize cost to per-item basis
    per_item_cost = normalize_cost_to_per_item(product_data, base_cost)

    # Step 3: Get pricing logic method
    pricing_logic = get_pricing_logic(product_data)

    # Step 4: Calculate based on method
    calculation_details = {
        'per_item_cost': per_item_cost,
        'quantity': quantity,
        'tier_info': tier_info
    }

    pbp_msrp = None
    method_used = pricing_logic

    if pricing_logic == "MSRP + % of cost":
        # Method 1: MSRP + shipping add-on
        vendor_msrp = get_column_value(product_data, 'Vendor Published MSRP', None, None)

        if vendor_msrp is None or vendor_msrp == 0:
            # Fallback: No MSRP available, use Standard markup
            print(f"⚠️ Warning: No MSRP available for '{product_data.get('Product/Service', 'Unknown')}' - using Standard markup instead")
            pricing_logic = "Standard markup"
            # Will fall through to Standard markup logic
        else:
            shipping_addon_pct = get_shipping_addon_percent(product_data)
            shipping_addon_amount = (shipping_addon_pct / 100) * per_item_cost
            pbp_msrp = vendor_msrp + shipping_addon_amount

            calculation_details.update({
                'vendor_msrp': vendor_msrp,
                'shipping_addon_pct': shipping_addon_pct,
                'shipping_addon_amount': shipping_addon_amount
            })

            method_used = "MSRP + % of cost"

    if pricing_logic == "MSRP capped – ship absorbed":
        # Method 2: MSRP exactly
        vendor_msrp = get_column_value(product_data, 'Vendor Published MSRP', None, None)

        if vendor_msrp is None or vendor_msrp == 0:
            # Fallback: No MSRP available, use Standard markup
            print(f"⚠️ Warning: No MSRP available for '{product_data.get('Product/Service', 'Unknown')}' - using Standard markup instead")
            pricing_logic = "Standard markup"
            # Will fall through to Standard markup logic
        else:
            pbp_msrp = vendor_msrp

            calculation_details.update({
                'vendor_msrp': vendor_msrp,
                'shipping_absorbed': True
            })

            method_used = "MSRP capped – ship absorbed"

    if pricing_logic == "Standard markup" or pbp_msrp is None:
        # Method 3: Traditional markup
        if user_markup_override is not None:
            markup_percent = user_markup_override
        else:
            # Default to 100% markup (cost × 2.0)
            markup_percent = 100.0

        pbp_msrp = per_item_cost * (1 + markup_percent / 100)

        calculation_details.update({
            'markup_percent': markup_percent,
            'markup_amount': per_item_cost * (markup_percent / 100)
        })

        method_used = "Standard markup"

    # Step 5: Get spreadsheet calculated MSRP for validation
    spreadsheet_msrp = get_column_value(product_data, 'PBP MSRP (Per-Unit, No Tiers, Calculated)', None, None)

    # Convert to float if needed
    if spreadsheet_msrp is not None:
        try:
            spreadsheet_msrp = float(spreadsheet_msrp)
        except (ValueError, TypeError):
            spreadsheet_msrp = None

    # Step 6: Validate against spreadsheet
    if spreadsheet_msrp is not None:
        # Compare with epsilon tolerance
        if abs(pbp_msrp - spreadsheet_msrp) < 0.01:
            validation_status = 'match'
        else:
            validation_status = 'mismatch'
            print(f"⚠️ Validation: Price mismatch for '{product_data.get('Product/Service', 'Unknown')}'")
            print(f"   Spreadsheet: ${spreadsheet_msrp:.2f} | Calculated: ${pbp_msrp:.2f}")
    else:
        validation_status = 'no_spreadsheet_value'

    return {
        'pbp_msrp': pbp_msrp,
        'method_used': method_used,
        'calculation_details': calculation_details,
        'spreadsheet_msrp': spreadsheet_msrp,
        'validation_status': validation_status
    }


def calculate_vendor_markup(product_data, per_item_cost):
    """
    Calculate vendor's implied markup percentage.
    Part of January 2026 schema transition - diagnostic field.

    Formula: ((Vendor MSRP / per-item cost) - 1) × 100

    Args:
        product_data: Product row from spreadsheet
        per_item_cost: Normalized per-item cost

    Returns:
        dict: {
            'vendor_markup_pct': float or None,
            'spreadsheet_value': float or None,
            'validation_status': str
        }

    Example:
        >>> calculate_vendor_markup(product_data, 4.0)
        {'vendor_markup_pct': 150.0, 'spreadsheet_value': 150.0, 'validation_status': 'match'}
    """
    from src.helpers import get_column_value

    vendor_msrp = get_column_value(product_data, 'Vendor Published MSRP', None, None)

    # Convert to float if needed
    if vendor_msrp is not None:
        try:
            vendor_msrp = float(vendor_msrp)
        except (ValueError, TypeError):
            vendor_msrp = None

    if vendor_msrp is None or vendor_msrp == 0 or per_item_cost == 0:
        return {
            'vendor_markup_pct': None,
            'spreadsheet_value': None,
            'validation_status': 'no_msrp'
        }

    # Calculate markup
    vendor_markup_pct = ((vendor_msrp / per_item_cost) - 1) * 100

    # Get spreadsheet value for comparison
    spreadsheet_value = get_column_value(product_data, 'Vendor Markup (No Tiers, Calculated)', None, None)

    # Convert to float if needed
    if spreadsheet_value is not None:
        try:
            spreadsheet_value = float(spreadsheet_value)
        except (ValueError, TypeError):
            spreadsheet_value = None

    # Validate
    if spreadsheet_value is not None:
        if abs(vendor_markup_pct - spreadsheet_value) < 0.5:  # 0.5% tolerance
            validation_status = 'match'
        else:
            validation_status = 'mismatch'
    else:
        validation_status = 'no_spreadsheet_value'

    return {
        'vendor_markup_pct': vendor_markup_pct,
        'spreadsheet_value': spreadsheet_value,
        'validation_status': validation_status
    }


def calculate_pbp_markup(pbp_msrp, per_item_cost, product_data):
    """
    Calculate PBP's final markup percentage.
    Part of January 2026 schema transition - diagnostic field.

    Formula: ((PBP MSRP / per-item cost) - 1) × 100

    Args:
        pbp_msrp: PBP's calculated MSRP
        per_item_cost: Normalized per-item cost
        product_data: Product row from spreadsheet

    Returns:
        dict: {
            'pbp_markup_pct': float,
            'spreadsheet_value': float or None,
            'validation_status': str
        }

    Example:
        >>> calculate_pbp_markup(11.0, 4.0, product_data)
        {'pbp_markup_pct': 175.0, 'spreadsheet_value': 175.0, 'validation_status': 'match'}
    """
    from src.helpers import get_column_value

    if per_item_cost == 0:
        return {
            'pbp_markup_pct': 0.0,
            'spreadsheet_value': None,
            'validation_status': 'invalid_cost'
        }

    # Calculate markup
    pbp_markup_pct = ((pbp_msrp / per_item_cost) - 1) * 100

    # Get spreadsheet value for comparison
    spreadsheet_value = get_column_value(product_data, 'PBP Markup (Vendor+Add-On, No Tiers)', None, None)

    # Convert to float if needed
    if spreadsheet_value is not None:
        try:
            spreadsheet_value = float(spreadsheet_value)
        except (ValueError, TypeError):
            spreadsheet_value = None

    # Validate
    if spreadsheet_value is not None:
        if abs(pbp_markup_pct - spreadsheet_value) < 0.5:  # 0.5% tolerance
            validation_status = 'match'
        else:
            validation_status = 'mismatch'
    else:
        validation_status = 'no_spreadsheet_value'

    return {
        'pbp_markup_pct': pbp_markup_pct,
        'spreadsheet_value': spreadsheet_value,
        'validation_status': validation_status
    }


def calculate_order_total(order_items, shipping=0.0, order_tariff=0.0,
                         discount_percent=0.0, apply_rounding=False):
    """
    Calculate total for multi-product order.

    Args:
        order_items: List of order item dicts (each with product details and costs)
        shipping: Order-level shipping cost
        order_tariff: Order-level tariff amount
        discount_percent: Discount percentage to apply to subtotal
        apply_rounding: Whether to apply marketing rounding (charm pricing)

    Returns:
        dict: Order summary with totals

    Example:
        >>> calculate_order_total(
        ...     [{'total': 1000}, {'total': 500}],
        ...     shipping=100,
        ...     order_tariff=200,
        ...     discount_percent=5.0
        ... )
        {
            'subtotal': 1500,
            'discount_amount': 75,
            'subtotal_after_discount': 1425,
            'shipping': 100,
            'tariff': 200,
            'grand_total': 1725
        }
    """
    from src.helpers import apply_marketing_rounding

    summary = {}

    # Calculate subtotal (sum of all item totals)
    subtotal = sum(item.get('total', 0) for item in order_items)

    # Apply discount to subtotal
    discount_amount = subtotal * (discount_percent / 100)
    subtotal_after_discount = subtotal - discount_amount

    # Add shipping and tariff
    grand_total = subtotal_after_discount + shipping + order_tariff

    # Apply marketing rounding if requested
    if apply_rounding:
        grand_total = apply_marketing_rounding(grand_total)

    summary['subtotal'] = subtotal
    summary['discount_percent'] = discount_percent
    summary['discount_amount'] = discount_amount
    summary['subtotal_after_discount'] = subtotal_after_discount
    summary['shipping'] = shipping
    summary['tariff'] = order_tariff
    summary['grand_total'] = grand_total

    return summary
