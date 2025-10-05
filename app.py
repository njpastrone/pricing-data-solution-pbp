"""
Peace by Piece International - Pricing & Quoting App
Simple MVP for product selection, quote calculation, and proposal/invoice generation.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

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

        1. **Select Product** - Choose partner and product from dropdowns
        2. **Customize Product** - Enter quantity and markup percentage
        3. **Add Labels (Optional)** - Check box if customer wants custom branding
        4. **Review Preview** - Check the pricing breakdown
        5. **Add to Order** - Click "Add to Order" button
        6. **Repeat** - Add more products if needed
        7. **Set Order Settings** - Enter shipping and tariff costs
        8. **Review Total** - Check the order summary and total quote
        9. **Generate Outputs** - Copy proposal or invoice tables
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
            st.session_state.pricing_df = load_pricing_data()
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
    if 'pricing_df' in st.session_state:
        csv_pricing = st.session_state.pricing_df.to_csv(index=False)

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
    Load pricing data from jaggery_demo Google Sheet.
    New structure: Row 1 is empty, Row 2 has headers, data starts Row 3.
    Returns a pandas DataFrame.
    """
    gc = connect_to_sheets()
    sheet = gc.open("jaggery_demo").sheet1

    # Get all values from sheet
    all_values = sheet.get_all_values()

    # Row 2 (index 1) contains column headers
    # IMPORTANT: Strip whitespace from column names
    headers = [col.strip() for col in all_values[1]]

    # Data starts at row 3 (index 2)
    data_rows = all_values[2:]

    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=headers)

    # Remove empty rows (where Product Ref. No. is empty)
    df = df[df['Product Ref. No.'].str.strip() != '']

    return df

# Load data
try:
    if 'pricing_df' not in st.session_state:
        st.session_state.pricing_df = load_pricing_data()
        st.session_state.data_loaded_at = datetime.now()
    df = st.session_state.pricing_df
    st.success(f"Loaded {len(df)} products from jaggery_demo")
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

# ===== PRODUCT SELECTION =====
st.header("1. Select Products")

# Create dropdowns for filtering
col1, col2 = st.columns(2)

with col1:
    # Partner dropdown (using "Artisan Partner" column)
    partners = ["All Partners"] + sorted(df["Artisan Partner"].unique().tolist())
    selected_partner = st.selectbox("Select Partner", partners)

with col2:
    # Filter products based on partner selection (using "Gift Name" column)
    if selected_partner == "All Partners":
        available_products = df["Gift Name"].unique().tolist()
    else:
        available_products = df[df["Artisan Partner"] == selected_partner]["Gift Name"].unique().tolist()

    selected_product = st.selectbox("Select Product", available_products)

# Get selected product details
if selected_partner == "All Partners":
    product_data = df[df["Gift Name"] == selected_product].iloc[0]
else:
    product_data = df[(df["Artisan Partner"] == selected_partner) & (df["Gift Name"] == selected_product)].iloc[0]

# Display product details in cleaner layout
st.markdown("##### Product Details")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**Partner:** {product_data['Artisan Partner']}")
    st.markdown(f"**Product Ref:** {product_data['Product Ref. No.']}")
with col2:
    minimum_qty = product_data.get("Minimum Qty", "N/A")
    st.markdown(f"**Minimum Qty:** {minimum_qty if minimum_qty else 'N/A'}")
    origin = product_data.get("Origin Country", "N/A")
    st.markdown(f"**Origin:** {origin if origin else 'N/A'}")

# Show product description if available
description = product_data.get("Description", "")
if description:
    with st.expander("Product Description"):
        st.write(description)

st.markdown("<br>", unsafe_allow_html=True)

# ===== PRODUCT CUSTOMIZATION =====
st.header("2. Customize Product")

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

# Label options
include_labels = st.checkbox(
    "Add custom labels to this product",
    value=False,
    key="input_labels",
    help="Custom branding labels for the product. Minimum 100 labels required (Jaggery partner). Includes art setup fee."
)

# Minimum quantity validation
minimum_qty_str = product_data.get("Minimum Qty", "")
if minimum_qty_str:
    try:
        minimum_qty = int(clean_price(minimum_qty_str)) if clean_price(minimum_qty_str) else 0
        if minimum_qty > 0 and quantity < minimum_qty:
            st.warning(f"Minimum order quantity for this product is {minimum_qty} units. You've entered {quantity} units.")
    except (ValueError, TypeError):
        pass  # Skip validation if minimum qty is invalid

st.markdown("<br>", unsafe_allow_html=True)

# ===== PRODUCT PREVIEW & ADD TO ORDER =====
st.header("3. Product Preview")

# Get price for quantity (tiered pricing)
base_price, tier_range, tier_column = get_price_for_quantity(product_data, quantity)

if base_price is None:
    st.error("No pricing available for this quantity. Please contact the partner.")
    # DEBUG: Show available pricing columns
    with st.expander("Debug: Available Pricing Data"):
        pricing_cols = [
            'PBP Cost w/o shipping (1-25)',
            'PBP Cost w/o shipping (26-50)',
            'PBP Cost w/o shipping (51-100)',
            'PBP Cost w/o shipping (101-250)',
            'PBP Cost w/o shipping (251-500)',
            'PBP Cost w/o shipping (501-1000)',
            'PBP Cost w/o shipping (1000+)'
        ]
        for col in pricing_cols:
            if col in product_data.index:
                raw_value = product_data[col]
                cleaned_value = clean_price(raw_value)
                st.write(f"- {col}: raw='{raw_value}' | cleaned={cleaned_value}")
            else:
                st.write(f"- {col}: COLUMN NOT FOUND")
    st.stop()

# Show which tier is being used
st.caption(f"Using pricing tier: {tier_range} units | Base price: ${base_price:.2f} per unit")

# Calculate additional costs
additional_costs = calculate_additional_costs(product_data, quantity, include_labels)

# Show label warning if applicable
if additional_costs.get('label_warning'):
    st.warning(additional_costs['label_warning'])

# Calculate product totals (without shipping/tariff)
product_subtotal = base_price * quantity
art_setup_total = additional_costs['art_setup_fee_total']
label_cost_total = additional_costs.get('label_cost_total', 0)
subtotal_before_markup = product_subtotal + art_setup_total + label_cost_total
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
        'product_name': product_data["Gift Name"],
        'product_ref': product_data["Product Ref. No."],
        'partner': product_data["Artisan Partner"],
        'quantity': quantity,
        'markup_percent': markup_percent,
        'include_labels': include_labels,
        'base_price': base_price,
        'tier_range': tier_range,
        'tier_column': tier_column,
        'additional_costs': additional_costs,
        'product_subtotal': product_subtotal,
        'art_setup_total': art_setup_total,
        'label_cost_total': label_cost_total,
        'subtotal_before_markup': subtotal_before_markup,
        'markup_amount': markup_amount,
        'product_total': product_total,
        'total_per_unit': total_per_unit
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

    if include_labels:
        if art_setup_total > 0:
            breakdown_items.append(["Art Setup Fee", f"${art_setup_total / quantity:.2f}", f"${art_setup_total:.2f}"])
        if label_cost_total > 0:
            labels_charged = additional_costs.get('labels_charged', 0)
            label_unit_cost = additional_costs.get('label_cost_per_label', 0)
            breakdown_items.append([f"Labels ({labels_charged} @ ${label_unit_cost:.2f})", f"${label_cost_total / quantity:.2f}", f"${label_cost_total:.2f}"])

    breakdown_items.append(["**Subtotal**", f"**${subtotal_before_markup / quantity:.2f}**", f"**${subtotal_before_markup:.2f}**"])
    breakdown_items.append([f"Markup ({markup_percent}% on product only)", f"${markup_amount / quantity:.2f}", f"${markup_amount:.2f}"])
    breakdown_items.append(["**Product Total**", f"**${total_per_unit:.2f}**", f"**${product_total:.2f}**"])

    breakdown_df = pd.DataFrame(breakdown_items, columns=["Item", "Per Unit", "Total"])
    st.table(breakdown_df)

# ===== CURRENT ORDER SUMMARY =====
st.divider()
st.header("4. Current Order")

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
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**Partner:** {item['partner']}")
                st.write(f"**Product Ref:** {item['product_ref']}")
                st.write(f"**Quantity:** {item['quantity']}")
                st.write(f"**Pricing Tier:** {item['tier_range']}")
                st.write(f"**Base Price:** ${item['base_price']:.2f} per unit")
                st.write(f"**Markup:** {item['markup_percent']:.1f}%")
                st.write(f"**Labels:** {'Yes' if item['include_labels'] else 'No'}")

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

            if item['art_setup_total'] > 0:
                breakdown_items.append(["Art Setup Fee", f"${item['art_setup_total'] / item['quantity']:.2f}", f"${item['art_setup_total']:.2f}"])
            if item['label_cost_total'] > 0:
                breakdown_items.append(["Label Costs", f"${item['label_cost_total'] / item['quantity']:.2f}", f"${item['label_cost_total']:.2f}"])

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
st.header("5. Order Settings")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order first, then set shipping and tariff costs here.")
else:
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

# Use session state values for calculations
shipping = st.session_state.order_shipping
tariff = st.session_state.order_tariff

# ===== TOTAL ORDER CALCULATION =====
if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to see the total quote calculation.")
else:
    # Calculate totals
    products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)
    total_quote = products_subtotal + shipping + tariff
    total_units = sum(item['quantity'] for item in st.session_state.order_items)

    # Display summary
    st.subheader("Order Summary")

    summary_items = []
    for item in st.session_state.order_items:
        summary_items.append([
            item['product_name'],
            item['quantity'],
            f"${item['total_per_unit']:.2f}",
            f"${item['product_total']:.2f}"
        ])

    summary_items.append(["**Products Subtotal**", "", "", f"**${products_subtotal:.2f}**"])
    summary_items.append(["Shipping", "", "", f"${shipping:.2f}"])
    summary_items.append(["Tariff", "", "", f"${tariff:.2f}"])
    summary_items.append(["**TOTAL QUOTE**", f"**{total_units} total units**", "", f"**${total_quote:.2f}**"])

    summary_df = pd.DataFrame(summary_items, columns=["Product", "Qty", "Per Unit", "Total"])
    st.table(summary_df)

    # Display total
    avg_per_unit = total_quote / total_units if total_units > 0 else 0
    st.success(f"Total Quote: ${total_quote:.2f}  ({total_units} total units @ ${avg_per_unit:.2f} avg per unit)")

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
            'tariff': tariff
        }
        st.session_state.order_history.append(order_entry)
        st.success("Quote saved to history!")
        st.rerun()

# ===== PROPOSAL GENERATION =====
st.divider()
st.header("7. Proposal")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate a proposal.")
else:
    st.subheader("Quote Proposal")

    # Calculate totals
    products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)
    total_quote = products_subtotal + shipping + tariff
    total_units = sum(item['quantity'] for item in st.session_state.order_items)

    # Build proposal items
    proposal_items = []

    # Add each product
    for idx, item in enumerate(st.session_state.order_items, 1):
        proposal_items.append([f"**Product {idx}**", item['product_name']])
        proposal_items.append(["  Partner", item['partner']])
        proposal_items.append(["  Product Ref.", item['product_ref']])
        proposal_items.append(["  Quantity", item['quantity']])
        proposal_items.append(["  Pricing Tier", item['tier_range']])
        proposal_items.append(["  Base Price (per unit)", f"${item['base_price']:.2f}"])

        if item['art_setup_total'] > 0:
            proposal_items.append(["  Art Setup Fee", f"${item['art_setup_total']:.2f}"])
        if item['label_cost_total'] > 0:
            labels_charged = item['additional_costs'].get('labels_charged', 0)
            proposal_items.append([f"  Labels ({labels_charged} units)", f"${item['label_cost_total']:.2f}"])

        proposal_items.append(["  Subtotal Before Markup", f"${item['subtotal_before_markup']:.2f}"])
        proposal_items.append([f"  Markup ({item['markup_percent']:.1f}%)", f"${item['markup_amount']:.2f}"])
        proposal_items.append(["  **Product Total**", f"**${item['product_total']:.2f}**"])
        proposal_items.append(["", ""])  # Blank row for spacing

    # Add order totals
    proposal_items.extend([
        ["**Products Subtotal**", f"**${products_subtotal:.2f}**"],
        ["Shipping", f"${shipping:.2f}"],
        ["Tariff", f"${tariff:.2f}"],
        ["**Total Quote**", f"**${total_quote:.2f}**"],
        ["**Total Units**", f"**{total_units}**"],
        ["**Average Price Per Unit**", f"**${total_quote / total_units:.2f}**"]
    ])

    proposal_df = pd.DataFrame(proposal_items, columns=["Item", "Details"])
    st.table(proposal_df)

    st.caption("Copy this table and paste into your proposal template.")

# ===== INVOICE GENERATION =====
st.divider()
st.header("8. Invoice")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate an invoice.")
else:
    st.subheader("Invoice")
    invoice_date = datetime.now().strftime("%Y-%m-%d")

    st.write(f"**Invoice Date:** {invoice_date}")
    st.write("")  # Spacing

    # Calculate totals
    products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)
    total_quote = products_subtotal + shipping + tariff

    # Build line items table
    invoice_line_items = []
    for item in st.session_state.order_items:
        invoice_line_items.append({
            'Product/Service Name': item['product_name'],
            'Description': f"Product Ref: {item['product_ref']}, Partner: {item['partner']}",
            'Quantity': item['quantity'],
            'Pricing Tier': item['tier_range'],
            'Price (Per-Unit)': f"${item['total_per_unit']:.2f}",
            'Total (Per-Item)': f"${item['product_total']:.2f}"
        })

    # Display line items table
    invoice_df = pd.DataFrame(invoice_line_items)
    st.table(invoice_df)

    # Display totals section
    st.write("")  # Spacing
    totals_data = [
        ["Subtotal (Pre-Tax)", f"${products_subtotal:.2f}"],
        ["Shipping", f"${shipping:.2f}"],
        ["Tariff", f"${tariff:.2f}"],
        ["**Final Total**", f"**${total_quote:.2f}**"]
    ]
    totals_df = pd.DataFrame(totals_data, columns=["", ""])
    st.table(totals_df)

    st.caption("Copy this table and paste into your invoice template.")

# ===== FOOTER =====
st.divider()
st.caption(f"Last data refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Click menu → 'Rerun' to refresh pricing data from Google Sheets")
