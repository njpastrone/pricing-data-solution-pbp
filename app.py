"""
Peace by Piece International - Pricing & Quoting App
Simple MVP for product selection, quote calculation, and proposal/invoice generation.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ===== HELPER FUNCTIONS =====
def apply_marketing_rounding(price, enabled=True):
    """Apply charm pricing: round whole dollar amounts down by $1 (e.g., $60 -> $59)"""
    if enabled and price % 1 == 0:
        return price - 1
    return price

def calculate_moq(unit_price):
    """
    Calculate Minimum Order Quantity based on $1,000 minimum order value.
    Formula: MOQ = ceil(1000 / Unit Price)
    """
    import math
    if unit_price <= 0:
        return None
    return math.ceil(1000 / unit_price)

def calculate_credit_card_fee(total, apply_fee=False, fee_percent=2.9):
    """
    Calculate credit card processing fee if applicable.
    Default rate: 2.9%
    """
    if apply_fee:
        return total * (fee_percent / 100)
    return 0.0

def parse_tier_info(tier_string):
    """
    Parse 'T1: 1-25, T2: 26-50, ...' into dict of tier ranges.
    Returns: {1: (1, 25), 2: (26, 50), ...}
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

def determine_tier_number(quantity, tier_info_string, has_tiers):
    """
    Returns tier number (1-6) based on quantity, or None if no tiers.
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
    Get correct unit price based on new tier logic from master_pricing_template_10_14.
    Handles both tiered and non-tiered pricing.
    """
    has_tiers = str(row.get('Pricing Tiers (Y/N)', '')).strip().upper()

    if has_tiers != 'Y':
        # Use flat rate
        flat_price = clean_price(row.get('PBP Cost (No Tiers)', ''))
        if flat_price is not None:
            return flat_price, "No Tiers", "PBP Cost (No Tiers)"
        else:
            return None, None, None

    # Determine tier and get price
    tier_info = row.get('Pricing Tiers Info', '')
    tier_num = determine_tier_number(quantity, tier_info, has_tiers)

    if tier_num is None:
        return None, None, None

    tier_col = f'PBP Cost: Tier {tier_num}'
    price = clean_price(row.get(tier_col, ''))

    if price is not None:
        # Get tier range for display
        tier_ranges = parse_tier_info(tier_info)
        if tier_num in tier_ranges:
            min_qty, max_qty = tier_ranges[tier_num]
            if max_qty == float('inf'):
                tier_range = f"{min_qty}+"
            else:
                tier_range = f"{min_qty}-{max_qty}"
            return price, tier_range, tier_col

    return None, None, None

# Page configuration
st.set_page_config(
    page_title="PBP Pricing App",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="auto"
)

# ===== SESSION STATE INITIALIZATION (MUST BE EARLY) =====
# Initialize order_items if not exists
if 'order_items' not in st.session_state:
    st.session_state.order_items = []

# Initialize edit_index (None = adding new item, number = editing existing item)
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

# Initialize order history
if 'order_history' not in st.session_state:
    st.session_state.order_history = []

# Initialize shipping and tariff in session state
if 'order_shipping' not in st.session_state:
    st.session_state.order_shipping = 0.0
if 'order_tariff' not in st.session_state:
    st.session_state.order_tariff = 0.0

# Initialize discount settings in session state
if 'order_discount_type' not in st.session_state:
    st.session_state.order_discount_type = "none"
if 'order_discount_preset' not in st.session_state:
    st.session_state.order_discount_preset = "NGO Discount (5%)"
if 'order_discount_custom_desc' not in st.session_state:
    st.session_state.order_discount_custom_desc = ""
if 'order_discount_custom_value' not in st.session_state:
    st.session_state.order_discount_custom_value = 0.0

# Initialize marketing rounding setting
if 'order_use_marketing_rounding' not in st.session_state:
    st.session_state.order_use_marketing_rounding = False

# Initialize client information
if 'client_info' not in st.session_state:
    st.session_state.client_info = {
        'is_new_client': True,
        'company_name': '',
        'contact_name': '',
        'contact_email': '',
        'client_po': '',
        'billing_address': '',
        'shipping_type': 'One Location',
        'shipping_address': '',
        'payment_timeline': '50% upfront, 50% on delivery',
        'payment_preference': 'Wire Transfer'
    }

# Initialize credit card fee settings
if 'apply_cc_fee' not in st.session_state:
    st.session_state.apply_cc_fee = False
if 'cc_fee_percent' not in st.session_state:
    st.session_state.cc_fee_percent = 2.9

st.title("Peace by Piece Pricing & Quoting App")

# Purpose statement
st.markdown("""
**Welcome to the PBP Pricing App** — This tool helps you create quotes and invoices
for artisan products. Select products, customize your order, and generate professional
proposals with detailed pricing breakdowns.
""")
st.divider()

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## Instructions & Tools")

    # Section 1: Instructions
    with st.expander("How to Use This App", expanded=False):
        st.markdown("""
        **Step-by-step guide:**

        1. **Enter Client Information** - Company, contact, payment terms (optional but recommended)
        2. **Select Partner & Product** - Choose from dropdowns
        3. **Enter Quantity** - Tiered pricing applies automatically
        4. **Set Markup** - Your profit margin percentage
        5. **Add Customization (Optional)** - Custom labels, branding, etc.
        6. **Review Preview** - Check the pricing breakdown
        7. **Add to Order** - Click "Add to Order" button
        8. **Repeat** - Add more products if needed
        9. **Set Order Settings** - Shipping, tariff, discounts, credit card fees
        10. **Generate Deliverables** - Proposal (with MOQ), Invoice, or Purchase Order
        """)

    st.markdown("---")

    # Section 2: Recent Orders
    st.markdown("### Recent Orders")
    if len(st.session_state.order_history) == 0:
        st.caption("No recent orders this session")
    else:
        # Show last 5 orders, most recent first
        for idx, order in enumerate(reversed(st.session_state.order_history[-5:])):
            with st.container():
                timestamp_str = order['timestamp'].strftime('%I:%M %p')
                product_preview = ', '.join(order['product_names'][:2])
                if len(order['product_names']) > 2:
                    product_preview += f" +{len(order['product_names'])-2} more"

                st.caption(f"{timestamp_str} - {product_preview}")
                st.caption(f"${order['total_quote']:.2f} ({order['total_units']} units)")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_order_{idx}", use_container_width=True):
                        # Reload this order
                        st.session_state.order_items = order['order_items'].copy()
                        st.session_state.order_shipping = order['shipping']
                        st.session_state.order_tariff = order['tariff']
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"delete_order_{idx}", use_container_width=True):
                        # Remove from history
                        actual_idx = len(st.session_state.order_history) - 1 - idx
                        st.session_state.order_history.pop(actual_idx)
                        st.rerun()

                if idx < min(4, len(st.session_state.order_history) - 1):
                    st.markdown("---")

    st.markdown("---")

    # Section 3: Data Status
    st.markdown("### Data Status")
    if 'data_loaded_at' in st.session_state:
        load_time = st.session_state.data_loaded_at
        time_ago = datetime.now() - load_time

        if time_ago.seconds < 60:
            time_str = "Just now"
        elif time_ago.seconds < 3600:
            time_str = f"{time_ago.seconds // 60} min ago"
        else:
            time_str = load_time.strftime('%I:%M %p')

        st.caption(f"Last updated: {time_str}")

        if st.button("Refresh Data", use_container_width=True):
            # Clear cached data and reload
            df_template, df_metadata, df_partner_info = load_pricing_data()
            st.session_state.df_template = df_template
            st.session_state.df_metadata = df_metadata
            st.session_state.df_partner_info = df_partner_info
            st.session_state.data_loaded_at = datetime.now()
            st.rerun()
    else:
        st.caption("Data status: Unknown")

    st.markdown("---")

    # Section 4: Download Options
    st.markdown("### Download Options")

    # Download current order as CSV
    if len(st.session_state.order_items) > 0:
        import io
        import csv

        # Build CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Product", "Quantity", "Per Unit", "Total"])

        # Order items
        for item in st.session_state.order_items:
            writer.writerow([
                item['product_name'],
                item['quantity'],
                f"${item['total_per_unit']:.2f}",
                f"${item['product_total']:.2f}"
            ])

        # Add totals
        products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)
        writer.writerow(["Shipping", "", "", f"${st.session_state.order_shipping:.2f}"])
        writer.writerow(["Tariff", "", "", f"${st.session_state.order_tariff:.2f}"])
        total_quote = products_subtotal + st.session_state.order_shipping + st.session_state.order_tariff
        writer.writerow(["TOTAL", "", "", f"${total_quote:.2f}"])

        csv_content = output.getvalue()

        st.download_button(
            label="Download Order (CSV)",
            data=csv_content,
            file_name=f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.caption("Add products to download order")

    # Download master pricing data
    if 'df_template' in st.session_state:
        csv_pricing = st.session_state.df_template.to_csv(index=False)

        st.download_button(
            label="Download Pricing Data (CSV)",
            data=csv_pricing,
            file_name=f"pricing_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ===== HELPER FUNCTIONS =====

def clean_price(price_string):
    """
    Convert price string like '$48.00' or '$1,500.00' to float.
    Returns None if empty or invalid.
    """
    if not price_string or price_string == '':
        return None
    try:
        # Remove $, commas, whitespace
        cleaned = str(price_string).replace('$', '').replace(',', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def get_price_for_quantity(product_row, quantity):
    """
    Select the appropriate price tier based on quantity.
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
    Calculate additional costs (setup fees, labels, etc.)
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


# ===== GOOGLE SHEETS CONNECTION =====
@st.cache_resource
def connect_to_sheets():
    """
    Connect to Google Sheets using service account credentials.
    Cached so we don't reconnect on every rerun.
    """
    creds_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_pricing_data():
    """
    Load pricing data from master_pricing_template_10_14 Google Sheet.
    Loads three sheets: Template, Metadata, Partner-Specific Info
    Returns three DataFrames.
    """
    gc = connect_to_sheets()
    spreadsheet = gc.open("master_pricing_template_10_14")

    # Load Template sheet (header at row 6, index 5)
    template_sheet = spreadsheet.worksheet("Template")
    template_values = template_sheet.get_all_values()

    # Row 6 has headers, but first column is empty - skip it
    raw_headers = template_values[5]
    raw_data = template_values[6:]

    # Find first non-empty column index
    first_col_idx = 0
    for i, header in enumerate(raw_headers):
        if header.strip():
            first_col_idx = i
            break

    # Extract headers and data starting from first non-empty column
    template_headers = [col.strip() for col in raw_headers[first_col_idx:]]
    template_data = [row[first_col_idx:] for row in raw_data]

    df_template = pd.DataFrame(template_data, columns=template_headers)

    # Remove empty rows (where Partner column is empty)
    df_template = df_template[df_template['Partner'].str.strip() != '']

    # Load Metadata sheet (header at row 2, index 1)
    metadata_sheet = spreadsheet.worksheet("Metadata")
    metadata_values = metadata_sheet.get_all_values()
    metadata_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(metadata_values[1])]  # Row 2 (index 1)
    metadata_data = metadata_values[2:]
    df_metadata = pd.DataFrame(metadata_data, columns=metadata_headers)

    # Load Partner-Specific Info sheet (header at row 2, index 1)
    partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
    partner_values = partner_sheet.get_all_values()

    # Row 2 has headers, may have empty first column - skip it
    raw_partner_headers = partner_values[1]
    raw_partner_data = partner_values[2:]

    # Find first non-empty column index for partner sheet
    first_partner_col_idx = 0
    for i, header in enumerate(raw_partner_headers):
        if header.strip():
            first_partner_col_idx = i
            break

    # Extract headers and data starting from first non-empty column
    partner_headers = [col.strip() if col else f"Unnamed_{i}" for i, col in enumerate(raw_partner_headers[first_partner_col_idx:])]
    partner_data = [row[first_partner_col_idx:] for row in raw_partner_data]

    df_partner_info = pd.DataFrame(partner_data, columns=partner_headers)

    # Remove empty rows from partner info (only if Partner column exists)
    if 'Partner' in df_partner_info.columns:
        df_partner_info = df_partner_info[df_partner_info['Partner'].str.strip() != '']

    return df_template, df_metadata, df_partner_info

# Load data
try:
    if 'df_template' not in st.session_state:
        df_template, df_metadata, df_partner_info = load_pricing_data()
        st.session_state.df_template = df_template
        st.session_state.df_metadata = df_metadata
        st.session_state.df_partner_info = df_partner_info
        st.session_state.data_loaded_at = datetime.now()

    df_template = st.session_state.df_template
    df_metadata = st.session_state.df_metadata
    df_partner_info = st.session_state.df_partner_info

    # Count unique partner-product combinations
    unique_products = len(df_template)
    unique_partners = len(df_template['Partner'].unique())

    st.success(f"Loaded {unique_products} products from {unique_partners} partners (master_pricing_template_10_14)")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Order status indicator
total_products = len(st.session_state.order_items)
if total_products > 0:
    st.info(f"Current order: {total_products} product(s)")
else:
    st.info("Current order: empty — Add your first product below")

st.divider()

# ===== CLIENT INFORMATION =====
st.header("1. Client & Order Information")

with st.expander("Client Details", expanded=False):
    st.markdown("Enter client information for invoices and purchase orders.")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.client_info['is_new_client'] = st.checkbox(
            "New Client?",
            value=st.session_state.client_info['is_new_client']
        )

        st.session_state.client_info['company_name'] = st.text_input(
            "Company Name",
            value=st.session_state.client_info['company_name'],
            placeholder="e.g., Acme Corp"
        )

        st.session_state.client_info['contact_name'] = st.text_input(
            "Contact Name",
            value=st.session_state.client_info['contact_name'],
            placeholder="e.g., John Smith"
        )

        st.session_state.client_info['contact_email'] = st.text_input(
            "Contact Email",
            value=st.session_state.client_info['contact_email'],
            placeholder="e.g., john@acme.com"
        )

        st.session_state.client_info['client_po'] = st.text_input(
            "Client PO Number (optional)",
            value=st.session_state.client_info['client_po'],
            placeholder="e.g., PO-2025-001"
        )

    with col2:
        st.session_state.client_info['billing_address'] = st.text_area(
            "Billing Address",
            value=st.session_state.client_info['billing_address'],
            placeholder="123 Main St\nCity, State ZIP",
            height=100
        )

        st.session_state.client_info['shipping_type'] = st.selectbox(
            "Shipping Type",
            options=['One Location', 'Drop Shipping'],
            index=0 if st.session_state.client_info['shipping_type'] == 'One Location' else 1
        )

        if st.session_state.client_info['shipping_type'] == 'One Location':
            st.session_state.client_info['shipping_address'] = st.text_area(
                "Shipping Address",
                value=st.session_state.client_info['shipping_address'],
                placeholder="456 Shipping Lane\nCity, State ZIP",
                height=100
            )
        else:
            st.session_state.client_info['shipping_address'] = ''
            st.caption("Drop shipping details to be arranged separately")

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.session_state.client_info['payment_timeline'] = st.text_input(
            "Payment Timeline",
            value=st.session_state.client_info['payment_timeline'],
            placeholder="e.g., 50% upfront, 50% on delivery"
        )

    with col4:
        st.session_state.client_info['payment_preference'] = st.selectbox(
            "Payment Preference",
            options=['Wire Transfer', 'Credit Card', 'ACH', 'Check'],
            index=['Wire Transfer', 'Credit Card', 'ACH', 'Check'].index(
                st.session_state.client_info['payment_preference']
            ) if st.session_state.client_info['payment_preference'] in ['Wire Transfer', 'Credit Card', 'ACH', 'Check'] else 0
        )

st.divider()

# ===== PRODUCT SELECTION =====
st.header("2. Select Products")

# Create dropdowns for filtering
col1, col2 = st.columns(2)

with col1:
    # Partner dropdown (using "Partner" column from Template sheet)
    partners = sorted(df_template["Partner"].unique().tolist())
    selected_partner = st.selectbox("Select Partner", partners)

with col2:
    # Filter products based on partner selection (using "Product/Service" column)
    available_products = df_template[df_template["Partner"] == selected_partner]["Product/Service"].unique().tolist()
    selected_product = st.selectbox("Select Product/Service", available_products)

# Get selected product details
product_data = df_template[
    (df_template["Partner"] == selected_partner) &
    (df_template["Product/Service"] == selected_product)
].iloc[0]

# Display product details in cleaner layout
st.markdown("##### Product Details")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Partner:** {product_data['Partner']}")
    st.markdown(f"**Product/Service:** {product_data['Product/Service']}")
with col2:
    origin = product_data.get("Country of Origin", "N/A")
    st.markdown(f"**Country of Origin:** {origin if origin else 'N/A'}")
    has_tiers = product_data.get("Pricing Tiers (Y/N)", "N/A")
    st.markdown(f"**Tiered Pricing:** {has_tiers}")

# Show product description if available
description = product_data.get("Marketing Description", "")
if description and description.strip():
    with st.expander("Marketing Description"):
        st.write(description)

# Show pricing tier info if applicable
tier_info = product_data.get("Pricing Tiers Info", "")
if tier_info and tier_info.strip() and tier_info != "NA":
    with st.expander("Pricing Tier Information"):
        st.write(tier_info)

st.markdown("<br>", unsafe_allow_html=True)

# ===== PRODUCT CUSTOMIZATION =====
st.header("3. Customize Product")

col1, col2 = st.columns(2)

with col1:
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1, key="input_quantity")

with col2:
    # Default markup is 100% (meaning 2x the base price)
    markup_percent = st.number_input(
        "Markup %",
        min_value=0.0,
        value=100.0,
        step=5.0,
        key="input_markup",
        help="Your profit margin. 100% = double the cost (2x), 50% = 1.5x the cost, 200% = triple the cost (3x)"
    )

# Customization options
customization_info = product_data.get("Customization Info", "")
if customization_info and customization_info.strip():
    st.info(f"Customization options: {customization_info}")

include_customization = st.checkbox(
    "Add customization to this product",
    value=False,
    key="input_customization",
    help="Adds setup fee and per-unit customization cost (e.g., custom labels, branding, engraving)"
)

st.markdown("<br>", unsafe_allow_html=True)

# ===== PRODUCT PREVIEW & ADD TO ORDER =====
st.header("4. Product Preview")

# Get price for quantity using new system
base_price, tier_range, tier_column = get_unit_price_new_system(product_data, quantity)

if base_price is None:
    st.error("No pricing available for this quantity. Please contact the partner.")
    # DEBUG: Show available pricing data
    with st.expander("Debug: Available Pricing Data"):
        st.write(f"Pricing Tiers (Y/N): {product_data.get('Pricing Tiers (Y/N)', 'N/A')}")
        st.write(f"Pricing Tiers Info: {product_data.get('Pricing Tiers Info', 'N/A')}")
        st.write(f"PBP Cost (No Tiers): {product_data.get('PBP Cost (No Tiers)', 'N/A')}")
        for i in range(1, 7):
            col_name = f'PBP Cost: Tier {i}'
            st.write(f"{col_name}: {product_data.get(col_name, 'N/A')}")
    st.stop()

# Show which tier is being used
if tier_range == "No Tiers":
    st.caption(f"Flat pricing: ${base_price:.2f} per unit")
else:
    st.caption(f"Using pricing tier: {tier_range} units | Base price: ${base_price:.2f} per unit")

# Calculate customization costs
customization_setup_fee = 0
customization_per_unit = 0

if include_customization:
    setup_fee_raw = clean_price(product_data.get('Customization Setup Fee', ''))
    customization_setup_fee = setup_fee_raw if setup_fee_raw is not None else 0

    per_unit_raw = clean_price(product_data.get('Customization Cost per Unit', ''))
    customization_per_unit = per_unit_raw if per_unit_raw is not None else 0

# Calculate product totals (without shipping/tariff)
product_subtotal = base_price * quantity
customization_setup_total = customization_setup_fee
customization_unit_total = customization_per_unit * quantity
subtotal_before_markup = product_subtotal + customization_setup_total + customization_unit_total
markup_amount = product_subtotal * (markup_percent / 100)
product_total = subtotal_before_markup + markup_amount

# Per-unit for this product
total_per_unit = product_total / quantity

# Display product summary
st.success(f"Product Total: ${product_total:.2f}  ({quantity} units @ ${total_per_unit:.2f} each)")

# Add to Order button
button_label = "Update Product in Order" if st.session_state.edit_index is not None else "Add to Order"
if st.button(button_label, type="primary", use_container_width=True):
    # Create order item
    order_item = {
        'product_name': product_data["Product/Service"],
        'product_ref': product_data.get("Purchase Description", ""),
        'partner': product_data["Partner"],
        'minimum_qty': "",  # Not in new structure
        'quantity': quantity,
        'markup_percent': markup_percent,
        'include_customization': include_customization,
        'base_price': base_price,
        'tier_range': tier_range,
        'tier_column': tier_column,
        'customization_setup_fee': customization_setup_fee,
        'customization_per_unit': customization_per_unit,
        'product_subtotal': product_subtotal,
        'customization_setup_total': customization_setup_total,
        'customization_unit_total': customization_unit_total,
        'subtotal_before_markup': subtotal_before_markup,
        'markup_amount': markup_amount,
        'product_total': product_total,
        'total_per_unit': total_per_unit,
        'product_data_row': product_data  # Store full product row for proposal generation
    }

    # Add or update item
    if st.session_state.edit_index is not None:
        st.session_state.order_items[st.session_state.edit_index] = order_item
        st.session_state.edit_index = None
        st.success("Product updated in order!")
    else:
        st.session_state.order_items.append(order_item)
        st.success("Product added to order!")

    st.rerun()

# Show detailed breakdown in expander
with st.expander("Detailed Price Breakdown"):
    breakdown_items = [
        ["Base Price (tier: " + tier_range + ")", f"${base_price:.2f}", f"${product_subtotal:.2f}"]
    ]

    if include_customization:
        if customization_setup_total > 0:
            breakdown_items.append(["Customization Setup Fee", f"${customization_setup_total / quantity:.2f}", f"${customization_setup_total:.2f}"])
        if customization_unit_total > 0:
            breakdown_items.append([f"Customization per Unit ({quantity} @ ${customization_per_unit:.2f})", f"${customization_per_unit:.2f}", f"${customization_unit_total:.2f}"])

    breakdown_items.append(["**Subtotal**", f"**${subtotal_before_markup / quantity:.2f}**", f"**${subtotal_before_markup:.2f}**"])
    breakdown_items.append([f"Markup ({markup_percent}% on product only)", f"${markup_amount / quantity:.2f}", f"${markup_amount:.2f}"])
    breakdown_items.append(["**Product Total**", f"**${total_per_unit:.2f}**", f"**${product_total:.2f}**"])

    breakdown_df = pd.DataFrame(breakdown_items, columns=["Item", "Per Unit", "Total"])
    st.table(breakdown_df)

# ===== CURRENT ORDER SUMMARY =====
st.divider()
st.header("5. Current Order")

if len(st.session_state.order_items) == 0:
    st.info("""
    **Your order is empty.**

    Select a product from Section 1, customize the details in Section 2,
    then click "Add to Order" in Section 3 to add items here.
    """)
else:
    st.success(f"{len(st.session_state.order_items)} product(s) in order")

    # Display order items
    for idx, item in enumerate(st.session_state.order_items):
        with st.expander(f"{item['product_name']}  -  {item['quantity']} units @ ${item['total_per_unit']:.2f} each  =  ${item['product_total']:.2f}"):
            # Check if custom item
            if item.get('is_custom', False):
                # Custom item display
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Type:** Custom Line Item")
                    st.write(f"**Description:** {item.get('custom_description', 'N/A')}")
                    st.write(f"**Quantity:** {item['quantity']}")
                    st.write(f"**Unit Price:** ${item['total_per_unit']:.2f}")
                    st.write(f"**Total Price:** ${item['product_total']:.2f}")

                with col2:
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state.order_items.pop(idx)
                        st.rerun()

            else:
                # Regular product display
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Partner:** {item['partner']}")
                    st.write(f"**Product Ref:** {item['product_ref']}")
                    st.write(f"**Quantity:** {item['quantity']}")
                    st.write(f"**Pricing Tier:** {item['tier_range']}")
                    st.write(f"**Base Price:** ${item['base_price']:.2f} per unit")
                    st.write(f"**Markup:** {item['markup_percent']:.1f}%")
                    st.write(f"**Customization:** {'Yes' if item.get('include_customization', False) else 'No'}")

                with col2:
                    if st.button("✏️ Edit", key=f"edit_{idx}"):
                        st.session_state.edit_index = idx
                        st.rerun()

                with col3:
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state.order_items.pop(idx)
                        st.rerun()

                # Show breakdown
                st.write("**Cost Breakdown:**")
                breakdown_items = [
                    ["Base Price", f"${item['base_price']:.2f}", f"${item['product_subtotal']:.2f}"]
                ]

                customization_setup = item.get('customization_setup_total', 0)
                customization_unit = item.get('customization_unit_total', 0)

                if customization_setup > 0:
                    breakdown_items.append(["Customization Setup Fee", f"${customization_setup / item['quantity']:.2f}", f"${customization_setup:.2f}"])
                if customization_unit > 0:
                    breakdown_items.append(["Customization per Unit", f"${customization_unit / item['quantity']:.2f}", f"${customization_unit:.2f}"])

                breakdown_items.append(["**Subtotal**", f"**${item['subtotal_before_markup'] / item['quantity']:.2f}**", f"**${item['subtotal_before_markup']:.2f}**"])
                breakdown_items.append([f"Markup ({item['markup_percent']:.1f}%)", f"${item['markup_amount'] / item['quantity']:.2f}", f"${item['markup_amount']:.2f}"])
                breakdown_items.append(["**Product Total**", f"**${item['total_per_unit']:.2f}**", f"**${item['product_total']:.2f}**"])

                breakdown_df = pd.DataFrame(breakdown_items, columns=["Item", "Per Unit", "Total"])
                st.table(breakdown_df)

    # Clear order button
    if st.button("Clear Entire Order", type="secondary"):
        st.session_state.order_items = []
        st.session_state.edit_index = None
        st.rerun()

# ===== ORDER SETTINGS =====
st.divider()
st.header("6. Order Settings")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order first, then configure order settings here.")
else:
    # Shipping & Tariff
    st.subheader("Shipping & Tariff")
    col1, col2 = st.columns(2)

    with col1:
        st.session_state.order_shipping = st.number_input(
            "Shipping Cost ($)",
            min_value=0.0,
            value=st.session_state.order_shipping,
            step=10.0,
            key="shipping_input",
            help="One-time shipping cost for the entire order (not per product)"
        )

    with col2:
        st.session_state.order_tariff = st.number_input(
            "Tariff Cost ($)",
            min_value=0.0,
            value=st.session_state.order_tariff,
            step=10.0,
            key="tariff_input",
            help="Import taxes or customs fees for the entire order. Leave at $0 if not applicable."
        )

    # Discount Options
    st.divider()
    st.subheader("Discount Options")

    discount_type = st.radio(
        "Select discount type:",
        options=["none", "preset", "custom"],
        format_func=lambda x: {"none": "No Discount", "preset": "Preset Discount", "custom": "Custom Discount"}[x],
        horizontal=True,
        key="discount_type_radio"
    )
    st.session_state.order_discount_type = discount_type

    if discount_type == "preset":
        preset_options = [
            "NGO Discount (5%)"
        ]
        st.session_state.order_discount_preset = st.selectbox(
            "Select preset discount:",
            options=preset_options,
            key="discount_preset_select"
        )

    elif discount_type == "custom":
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.order_discount_custom_desc = st.text_input(
                "Discount Description",
                value=st.session_state.order_discount_custom_desc,
                key="discount_custom_desc",
                placeholder="e.g., Early Bird Special"
            )
        with col2:
            st.session_state.order_discount_custom_value = st.number_input(
                "Discount Percentage (%)",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.order_discount_custom_value,
                step=1.0,
                key="discount_custom_value"
            )

    # Additional Options
    st.divider()
    st.subheader("Additional Options")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.order_use_marketing_rounding = st.checkbox(
            "Apply marketing rounding (e.g., $60 → $59)",
            value=st.session_state.order_use_marketing_rounding,
            key="marketing_rounding_checkbox",
            help="Rounds whole dollar amounts down by $1 for charm pricing effect"
        )

    with col2:
        st.session_state.apply_cc_fee = st.checkbox(
            "Apply credit card processing fee",
            value=st.session_state.apply_cc_fee,
            key="cc_fee_checkbox",
            help="Add credit card processing fee to total (default 2.9%)"
        )

    if st.session_state.apply_cc_fee:
        st.session_state.cc_fee_percent = st.number_input(
            "Credit Card Fee Percentage (%)",
            min_value=0.0,
            max_value=10.0,
            value=st.session_state.cc_fee_percent,
            step=0.1,
            key="cc_fee_percent_input",
            help="Percentage fee charged for credit card payments"
        )

    # Custom Line Items
    st.divider()
    st.subheader("Custom Line Items")

    with st.expander("➕ Add Custom Line Item", expanded=False):
        st.caption("Add unique services or customizations not in the catalog")

        col1, col2 = st.columns(2)
        with col1:
            custom_name = st.text_input(
                "Product/Service Name*",
                key="custom_name_input",
                placeholder="e.g., Custom Engraving Service"
            )
            custom_quantity = st.number_input(
                "Quantity*",
                min_value=1,
                value=1,
                step=1,
                key="custom_quantity_input"
            )

        with col2:
            custom_description = st.text_input(
                "Description",
                key="custom_description_input",
                placeholder="e.g., Laser engraving on wooden items"
            )
            custom_price = st.number_input(
                "Total Price ($)*",
                min_value=0.0,
                value=0.0,
                step=10.0,
                key="custom_price_input",
                help="Total price for this line item (quantity × unit price)"
            )

        if st.button("Add Custom Item to Order", type="secondary", use_container_width=True, key="add_custom_item_btn"):
            # Validation
            if not custom_name or custom_price <= 0:
                st.error("Please fill in Product/Service Name and set Total Price greater than $0")
            else:
                # Create custom item
                custom_item = {
                    'product_name': custom_name,
                    'product_ref': "CUSTOM",
                    'partner': "Custom",
                    'quantity': custom_quantity,
                    'markup_percent': 0.0,
                    'include_labels': False,
                    'base_price': custom_price / custom_quantity,
                    'tier_range': "N/A",
                    'tier_column': "N/A",
                    'additional_costs': {},
                    'product_subtotal': custom_price,
                    'art_setup_total': 0,
                    'label_cost_total': 0,
                    'subtotal_before_markup': custom_price,
                    'markup_amount': 0,
                    'product_total': custom_price,
                    'total_per_unit': custom_price / custom_quantity,
                    'is_custom': True,
                    'custom_description': custom_description if custom_description else "Custom line item"
                }

                st.session_state.order_items.append(custom_item)
                st.success(f"Added custom item: {custom_name}")
                st.rerun()

# Use session state values for calculations
shipping = st.session_state.order_shipping
tariff = st.session_state.order_tariff

# Calculate discount
discount_percent = 0.0
discount_description = ""

if st.session_state.order_discount_type == "preset":
    # Extract percentage from preset string (e.g., "NGO Discount (5%)" -> 5.0)
    preset = st.session_state.order_discount_preset
    discount_description = preset
    # Parse percentage from string like "NGO Discount (5%)"
    if "(" in preset and "%" in preset:
        percent_str = preset.split("(")[1].split("%")[0]
        discount_percent = float(percent_str)

elif st.session_state.order_discount_type == "custom":
    discount_percent = st.session_state.order_discount_custom_value
    discount_description = st.session_state.order_discount_custom_desc if st.session_state.order_discount_custom_desc else f"Custom Discount ({discount_percent}%)"

# ===== TOTAL ORDER CALCULATION =====
st.divider()
st.header("7. Order Summary")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to see the total quote calculation.")
else:
    # Calculate totals
    products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)
    discount_amount = products_subtotal * (discount_percent / 100)
    subtotal_after_discount = products_subtotal - discount_amount

    # Calculate base total before CC fee
    total_before_cc = subtotal_after_discount + shipping + tariff

    # Calculate credit card fee (applied to total before CC fee)
    cc_fee_amount = calculate_credit_card_fee(total_before_cc, st.session_state.apply_cc_fee, st.session_state.cc_fee_percent)

    # Final total
    total_quote = total_before_cc + cc_fee_amount

    # Apply marketing rounding if enabled
    total_quote = apply_marketing_rounding(total_quote, st.session_state.order_use_marketing_rounding)

    total_units = sum(item['quantity'] for item in st.session_state.order_items)

    summary_items = []
    for item in st.session_state.order_items:
        summary_items.append([
            item['product_name'],
            item['quantity'],
            f"${item['total_per_unit']:.2f}",
            f"${item['product_total']:.2f}"
        ])

    summary_items.append(["**Products Subtotal**", "", "", f"**${products_subtotal:.2f}**"])

    # Add discount line if applicable
    if discount_percent > 0:
        summary_items.append([f"Discount ({discount_description})", "", "", f"-${discount_amount:.2f}"])

    summary_items.append(["Shipping", "", "", f"${shipping:.2f}"])
    summary_items.append(["Tariff", "", "", f"${tariff:.2f}"])

    # Add credit card fee if applicable
    if st.session_state.apply_cc_fee and cc_fee_amount > 0:
        summary_items.append([f"Credit Card Fee ({st.session_state.cc_fee_percent}%)", "", "", f"${cc_fee_amount:.2f}"])

    summary_items.append(["**TOTAL QUOTE**", f"**{total_units} total units**", "", f"**${total_quote:.2f}**"])

    summary_df = pd.DataFrame(summary_items, columns=["Product", "Qty", "Per Unit", "Total"])
    st.table(summary_df)

    # Display total
    avg_per_unit = total_quote / total_units if total_units > 0 else 0
    st.success(f"Total Quote: ${total_quote:.2f}  ({total_units} total units @ ${avg_per_unit:.2f} avg per unit)")

    # Add download button for order summary
    summary_csv = summary_df.to_csv(index=False)
    st.download_button(
        label="Download Order Summary (CSV)",
        data=summary_csv,
        file_name=f"order_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_order_summary"
    )

    # Save to history button
    if st.button("Save Quote to History", type="secondary"):
        # Create order history entry
        order_entry = {
            'timestamp': datetime.now(),
            'total_quote': total_quote,
            'total_units': total_units,
            'num_products': len(st.session_state.order_items),
            'product_names': [item['product_name'] for item in st.session_state.order_items],
            'order_items': [item.copy() for item in st.session_state.order_items],
            'shipping': shipping,
            'tariff': tariff,
            'discount_type': st.session_state.order_discount_type,
            'discount_description': discount_description,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'use_marketing_rounding': st.session_state.order_use_marketing_rounding
        }
        st.session_state.order_history.append(order_entry)
        st.success("Quote saved to history!")
        st.rerun()

# ===== PROPOSAL GENERATION =====
st.divider()
st.header("8. Proposal")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate a proposal.")
else:
    st.subheader("Quote Proposal")

    st.markdown("Each product is presented in a separate table with MOQ pricing and discount information.")
    st.markdown("")

    # Generate a separate table for each product
    for idx, item in enumerate(st.session_state.order_items, 1):
        # Check if custom item
        if item.get('is_custom', False):
            # Custom items: show simplified format
            st.markdown(f"### Product {idx}: {item['product_name']}")

            custom_table = pd.DataFrame([
                {
                    "Description": item.get('custom_description', 'Custom line item'),
                    "Quantity": item['quantity'],
                    "Unit Price": f"${item['total_per_unit']:.2f}",
                    "Total": f"${item['product_total']:.2f}"
                }
            ])
            st.table(custom_table)
            st.caption("Custom line item")

            # Add download button for custom item
            custom_csv = custom_table.to_csv(index=False)
            st.download_button(
                label=f"Download Product {idx} Proposal (CSV)",
                data=custom_csv,
                file_name=f"proposal_product_{idx}_{item['product_name'].replace(' ', '_')}.csv",
                mime="text/csv",
                key=f"download_proposal_{idx}"
            )

        else:
            # Standard products: use new 4-column proposal format
            st.markdown(f"### Product {idx}: {item['product_name']}")

            # Calculate MOQ based on $1,000 minimum order value
            # First, get a preliminary unit price (use current order quantity as reference)
            product_row = item.get('product_data_row')
            if product_row is not None:
                # Get base price using current quantity to estimate MOQ
                preliminary_base_price, _, _ = get_unit_price_new_system(product_row, item['quantity'])

                if preliminary_base_price is not None:
                    # Calculate per-unit price including markup and customization
                    temp_customization_per_unit = 0
                    if item.get('include_customization', False):
                        # Estimate customization per unit (setup fee amortized + per-unit cost)
                        temp_setup = item.get('customization_setup_fee', 0)
                        temp_per_unit = item.get('customization_per_unit', 0)
                        # Use quantity of 100 as baseline for setup amortization estimate
                        temp_customization_per_unit = (temp_setup / 100) + temp_per_unit

                    # Estimate total per-unit price with markup
                    temp_markup_multiplier = 1 + (item['markup_percent'] / 100)
                    estimated_unit_price = (preliminary_base_price + temp_customization_per_unit) * temp_markup_multiplier

                    # Calculate MOQ based on $1,000 minimum
                    moq = calculate_moq(estimated_unit_price)
                    if moq is None:
                        moq = 5  # Fallback

                    # Now get actual base price for MOQ quantity using new system
                    moq_base_price, moq_tier_range, _ = get_unit_price_new_system(product_row, moq)
                else:
                    moq = 5  # Fallback
                    moq_base_price, moq_tier_range, _ = get_unit_price_new_system(product_row, moq)

                if moq_base_price is not None:
                    # Calculate customization costs at MOQ
                    moq_customization_setup = 0
                    moq_customization_unit = 0

                    if item.get('include_customization', False):
                        moq_customization_setup = item.get('customization_setup_fee', 0)
                        moq_customization_unit = item.get('customization_per_unit', 0) * moq

                    # Calculate per-unit price at MOQ
                    moq_product_cost = moq_base_price * moq
                    moq_subtotal = moq_product_cost + moq_customization_setup + moq_customization_unit

                    # Apply markup (on product cost only)
                    moq_markup_amount = moq_product_cost * (item['markup_percent'] / 100)
                    moq_total = moq_subtotal + moq_markup_amount
                    moq_price_per_unit = moq_total / moq

                    # Calculate discount price per unit
                    moq_discount_price = moq_price_per_unit * (1 - discount_percent / 100)

                    # Build column headers
                    col_moq = "MOQ"
                    col_price = f"Price Ea (@ Qty {moq})"

                    # Discount column header
                    if discount_percent > 0:
                        col_discount = f"Price Ea {discount_description}"
                    else:
                        col_discount = "Price Ea (No Discount)"

                    col_delivery = "Delivery"

                    # Build proposal table
                    proposal_table = pd.DataFrame([
                        {
                            col_moq: moq,
                            col_price: f"${moq_price_per_unit:.2f}",
                            col_discount: f"${moq_discount_price:.2f}",
                            col_delivery: ""
                        }
                    ])

                    st.table(proposal_table)

                    # Show MOQ calculation note
                    moq_total_value = moq * moq_price_per_unit
                    st.caption(f"MOQ calculated based on $1,000 minimum order value (MOQ {moq} units = ${moq_total_value:.2f})")

                    # Build customization fees row
                    fees_parts = []
                    if moq_customization_setup > 0:
                        fees_parts.append(f"Customization Set-Up: ${moq_customization_setup:.2f}")

                    if item.get('include_customization', False) and item.get('customization_per_unit', 0) > 0:
                        customization_cost_per_unit = item.get('customization_per_unit', 0)
                        fees_parts.append(f"Customization: ${customization_cost_per_unit:.2f} per unit")

                    if fees_parts:
                        st.caption("; ".join(fees_parts))
                    else:
                        st.caption("No additional customization fees")

                    # Add download button for this product's proposal table
                    proposal_csv = proposal_table.to_csv(index=False)
                    st.download_button(
                        label=f"Download Product {idx} Proposal (CSV)",
                        data=proposal_csv,
                        file_name=f"proposal_product_{idx}_{item['product_name'].replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"download_proposal_{idx}"
                    )
                else:
                    st.warning(f"Unable to calculate MOQ pricing for {item['product_name']}")
            else:
                st.warning(f"Product data not available for {item['product_name']}")

        st.markdown("")  # Spacing between products

    st.caption("Copy these tables and paste into your proposal template.")

# ===== INVOICE GENERATION =====
st.divider()
st.header("9. Invoice")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate an invoice.")
else:
    st.subheader("Invoice")
    invoice_date = datetime.now().strftime("%Y-%m-%d")

    # Display client information header
    st.markdown("#### Client Information")
    client_info = st.session_state.client_info

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Company:** {client_info['company_name'] if client_info['company_name'] else 'Not specified'}")
        st.write(f"**Contact:** {client_info['contact_name'] if client_info['contact_name'] else 'Not specified'}")
        st.write(f"**Email:** {client_info['contact_email'] if client_info['contact_email'] else 'Not specified'}")
        if client_info['client_po']:
            st.write(f"**Client PO:** {client_info['client_po']}")
    with col2:
        st.write(f"**Invoice Date:** {invoice_date}")
        st.write(f"**New Client:** {'Yes' if client_info['is_new_client'] else 'No'}")
        st.write(f"**Payment Terms:** {client_info['payment_timeline']}")
        st.write(f"**Payment Method:** {client_info['payment_preference']}")

    if client_info['billing_address']:
        st.write(f"**Billing Address:** {client_info['billing_address']}")

    if client_info['shipping_type'] == 'One Location' and client_info['shipping_address']:
        st.write(f"**Shipping Address:** {client_info['shipping_address']}")
    elif client_info['shipping_type'] == 'Drop Shipping':
        st.write(f"**Shipping:** Drop Shipping (details to be arranged)")

    st.divider()

    # Calculate totals (same as order summary)
    products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)
    discount_amount = products_subtotal * (discount_percent / 100)
    subtotal_after_discount = products_subtotal - discount_amount
    total_before_cc = subtotal_after_discount + shipping + tariff
    cc_fee_amount = calculate_credit_card_fee(total_before_cc, st.session_state.apply_cc_fee, st.session_state.cc_fee_percent)
    total_quote = total_before_cc + cc_fee_amount

    # Apply marketing rounding if enabled
    total_quote = apply_marketing_rounding(total_quote, st.session_state.order_use_marketing_rounding)

    # Build line items table
    invoice_line_items = []
    for item in st.session_state.order_items:
        # Check if custom item
        if item.get('is_custom', False):
            description = item.get('custom_description', 'Custom line item')
            tier = "Custom"
        else:
            description = f"Product Ref: {item['product_ref']}, Partner: {item['partner']}"
            tier = item['tier_range']

        invoice_line_items.append({
            'Product/Service Name': item['product_name'],
            'Description': description,
            'Quantity': item['quantity'],
            'Pricing Tier': tier,
            'Price (Per-Unit)': f"${item['total_per_unit']:.2f}",
            'Total (Per-Item)': f"${item['product_total']:.2f}"
        })

    # Display line items table
    invoice_df = pd.DataFrame(invoice_line_items)
    st.table(invoice_df)

    # Display totals section
    st.write("")  # Spacing
    totals_data = [
        ["Subtotal (Pre-Tax)", f"${products_subtotal:.2f}"]
    ]

    # Add discount line if applicable
    if discount_percent > 0:
        totals_data.append([f"Discount ({discount_description})", f"-${discount_amount:.2f}"])

    totals_data.extend([
        ["Shipping", f"${shipping:.2f}"],
        ["Tariff", f"${tariff:.2f}"]
    ])

    # Add credit card fee if applicable
    if st.session_state.apply_cc_fee and cc_fee_amount > 0:
        totals_data.append([f"Credit Card Fee ({st.session_state.cc_fee_percent}%)", f"${cc_fee_amount:.2f}"])

    totals_data.append(["**Final Total**", f"**${total_quote:.2f}**"])

    totals_df = pd.DataFrame(totals_data, columns=["Item", "Amount"])
    st.table(totals_df)

    st.caption("Copy this table and paste into your invoice template.")

    # Add download button for complete invoice
    # Combine line items and totals into one downloadable file
    invoice_complete = invoice_df.copy()

    # Add blank row
    blank_row = pd.DataFrame([{col: "" for col in invoice_df.columns}])
    invoice_complete = pd.concat([invoice_complete, blank_row], ignore_index=True)

    # Add totals section
    for total_item in totals_data:
        total_row = pd.DataFrame([{
            'Product/Service Name': total_item[0],
            'Description': '',
            'Quantity': '',
            'Pricing Tier': '',
            'Price (Per-Unit)': '',
            'Total (Per-Item)': total_item[1]
        }])
        invoice_complete = pd.concat([invoice_complete, total_row], ignore_index=True)

    invoice_csv = invoice_complete.to_csv(index=False)
    st.download_button(
        label="Download Complete Invoice (CSV)",
        data=invoice_csv,
        file_name=f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_invoice_complete"
    )

# ===== PURCHASE ORDER GENERATION =====
st.divider()
st.header("10. Purchase Order")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate a purchase order.")
else:
    st.subheader("Purchase Order")
    po_date = datetime.now().strftime("%Y-%m-%d")
    po_number = f"PO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Display PO header information
    st.markdown("#### Purchase Order Information")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**PO Number:** {po_number}")
        st.write(f"**PO Date:** {po_date}")
        st.write(f"**Total Units:** {sum(item['quantity'] for item in st.session_state.order_items)}")
        st.write(f"**Total Amount:** ${total_quote:.2f}")

    with col2:
        client_info = st.session_state.client_info
        st.write(f"**Client:** {client_info['company_name'] if client_info['company_name'] else 'Not specified'}")
        st.write(f"**Contact:** {client_info['contact_name'] if client_info['contact_name'] else 'Not specified'}")
        st.write(f"**Email:** {client_info['contact_email'] if client_info['contact_email'] else 'Not specified'}")
        if client_info['client_po']:
            st.write(f"**Client PO Reference:** {client_info['client_po']}")

    st.divider()

    # Build PO line items table
    st.markdown("#### Order Details")

    po_line_items = []
    for item in st.session_state.order_items:
        if item.get('is_custom', False):
            partner = "Custom"
            product_ref = "N/A"
            description = item.get('custom_description', 'Custom line item')
        else:
            partner = item['partner']
            product_ref = item['product_ref']
            description = f"Tier: {item['tier_range']}"

        po_line_items.append({
            'Partner': partner,
            'Product/Service': item['product_name'],
            'Product Ref': product_ref,
            'Quantity': item['quantity'],
            'Unit Cost': f"${item['total_per_unit']:.2f}",
            'Total': f"${item['product_total']:.2f}",
            'Notes': description
        })

    po_df = pd.DataFrame(po_line_items)
    st.table(po_df)

    # Display order summary
    st.markdown("#### Order Summary")

    summary_data = [
        ["Products Subtotal", f"${products_subtotal:.2f}"]
    ]

    if discount_percent > 0:
        summary_data.append([f"Discount ({discount_description})", f"-${discount_amount:.2f}"])

    summary_data.extend([
        ["Shipping", f"${shipping:.2f}"],
        ["Tariff", f"${tariff:.2f}"]
    ])

    if st.session_state.apply_cc_fee and cc_fee_amount > 0:
        summary_data.append([f"Credit Card Fee ({st.session_state.cc_fee_percent}%)", f"${cc_fee_amount:.2f}"])

    summary_data.append(["**Total Order Value**", f"**${total_quote:.2f}**"])

    summary_df = pd.DataFrame(summary_data, columns=["Item", "Amount"])
    st.table(summary_df)

    # Payment and shipping information
    st.markdown("#### Payment & Shipping")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Payment Terms:** {client_info['payment_timeline']}")
        st.write(f"**Payment Method:** {client_info['payment_preference']}")
    with col2:
        st.write(f"**Shipping Type:** {client_info['shipping_type']}")
        if client_info['shipping_type'] == 'One Location' and client_info['shipping_address']:
            st.write(f"**Shipping Address:**")
            st.caption(client_info['shipping_address'])

    if client_info['billing_address']:
        st.write(f"**Billing Address:**")
        st.caption(client_info['billing_address'])

    st.caption("Copy this purchase order for your records.")

    # Download button for PO
    po_complete = po_df.copy()

    # Add summary section
    blank_row = pd.DataFrame([{col: "" for col in po_df.columns}])
    po_complete = pd.concat([po_complete, blank_row], ignore_index=True)

    for summary_item in summary_data:
        summary_row = pd.DataFrame([{
            'Partner': summary_item[0],
            'Product/Service': '',
            'Product Ref': '',
            'Quantity': '',
            'Unit Cost': '',
            'Total': summary_item[1],
            'Notes': ''
        }])
        po_complete = pd.concat([po_complete, summary_row], ignore_index=True)

    po_csv = po_complete.to_csv(index=False)
    st.download_button(
        label="Download Purchase Order (CSV)",
        data=po_csv,
        file_name=f"purchase_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        key="download_po"
    )

# ===== FOOTER =====
st.divider()
st.caption(f"Last data refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Click menu → 'Rerun' to refresh pricing data from Google Sheets")
