"""
Peace by Piece International - Order Management System
3-tab workflow: Proposals → Order & Client Info → Execution & Accounting
Version: 4.0 (UI Polish Complete - Proposal-to-Order Connection + CSV Downloads + Editable Summary)
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Import extracted modules
from src.data_loader import load_pricing_data
from src.helpers import (
    clean_price,
    apply_marketing_rounding,
    round_to_nearest_five,
    calculate_moq,
    calculate_credit_card_fee,
    extract_partner_contacts,
    validate_invoice_completeness,
    parse_tier_info,
    parse_tariff_rate,
    calculate_product_tariff,
    convert_proposal_to_order
)
from src.pricing_engine import (
    determine_tier_number,
    get_unit_price_new_system,
    get_price_for_quantity,
    calculate_additional_costs,
    calculate_customization_costs,
    calculate_product_quote,
    calculate_order_total
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="PBP Order Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="auto"
)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
# Initialize order_items if not exists
if 'order_items' not in st.session_state:
    st.session_state.order_items = []

# Initialize edit_index (None = adding new item, number = editing existing item)
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None

# Initialize order history
if 'order_history' not in st.session_state:
    st.session_state.order_history = []

# Initialize shipping in session state
if 'order_shipping' not in st.session_state:
    st.session_state.order_shipping = 0.0

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
        'shipping_type': 'Ground',  # MODIFIED: Changed to dropdown default
        'shipping_address': '',
        'payment_timeline': 'Net 30',  # MODIFIED: Changed to dropdown default
        'payment_preference': 'Check',  # MODIFIED: Changed to dropdown default
        'client_in_hands_date': None,  # NEW: Target delivery date for client
        'order_submitted_by': '',  # NEW: Person submitting order
        'order_submitted_date': datetime.now().date(),  # NEW: Auto-filled submission date
        'cost_submitted_by': '',  # NEW: Person submitting costs
        'cost_submitted_date': None  # NEW: Date costs were submitted
    }

# Initialize order notes
if 'order_notes' not in st.session_state:
    st.session_state.order_notes = {
        'kitting_specs': '',  # Details about kitting requirements
        'client_requests': '',  # Special client requests
        'addon_samples': '',  # Additional samples to include
        'artwork_attachments': '',  # List of artwork files
        'general_notes': ''  # Catch-all for other notes
    }

# Initialize credit card fee settings
if 'apply_cc_fee' not in st.session_state:
    st.session_state.apply_cc_fee = False
if 'cc_fee_percent' not in st.session_state:
    st.session_state.cc_fee_percent = 2.9

# Initialize proposal-specific session state (Phase 2)
if 'proposal_products' not in st.session_state:
    st.session_state.proposal_products = []

if 'proposal_marketing_rounding' not in st.session_state:
    st.session_state.proposal_marketing_rounding = False

if 'configuring_product' not in st.session_state:
    st.session_state.configuring_product = None

if 'editing_proposal_index' not in st.session_state:
    st.session_state.editing_proposal_index = None

if 'proposal_filters' not in st.session_state:
    st.session_state.proposal_filters = {
        'min_price': 0.0,
        'max_price': None,
        'partners': [],
        'countries': []
    }

if 'proposal_kitting_pricing' not in st.session_state:
    st.session_state.proposal_kitting_pricing = """• Impact Cards (about maker communities): No Charge
• Custom Message Cards: $65 set up/$1.50 per card
• Insertion of a card you provide: No Charge
• Kitting for domestic shipments: $10.50/box
• Kitting for international shipments: $19.00/box
• Label making & shipping coordination: $2/box

*kitting includes shipping logistics but does not include actual shipping charges
*international kitting includes customs documentation, etc."""

if 'proposal_terms' not in st.session_state:
    # Load from config file if exists
    try:
        with open('config/terms_conditions.txt', 'r') as f:
            st.session_state.proposal_terms = f.read()
    except:
        st.session_state.proposal_terms = """• Drop shipping and kitting are available
• For shipments to California zip codes, sales tax will be added
• Payment terms
• 50% to initiate a custom order
• 50% upon shipment
• Customs charges for gifts shipped internationally will be billed to client, which may take up to 120 days post shipment
• Due to the current uncertainty around US-imposed tariffs, Peace by Piece will bill client for any charges, which may take up to 120 days post shipment
• No cancellations will be accepted after any custom order has been initiated
• Gifts returned to Peace by Piece due to incorrect recipient information will incur a $20 fee plus any additional returned shipping charges from the carrier. If a new address is not provided within 30 days of the gift's return, the gift will be shipped back to the client for distribution"""

if 'using_proposal_data' not in st.session_state:
    st.session_state.using_proposal_data = False

# ============================================================
# HEADER
# ============================================================
st.title("Peace by Piece Order Management System")
st.markdown("""
**Welcome to the PBP Order Management System** — Manage the complete order lifecycle:

**→ Tab 1: Proposals** - Browse products, create proposals for prospective clients
**→ Tab 2: Order & Client Info** - Build orders, collect client details *(Full workflow - Start here)*
**→ Tab 3: Execution & Accounting** - Generate invoices and purchase orders
""")
st.divider()

# ============================================================
# SIDEBAR - APP INFORMATION
# ============================================================
with st.sidebar:
    st.markdown("## Instructions & Tools")

    # Section 1: Progress Indicator
    st.markdown("### Workflow Progress")

    # Determine completion status for each tab
    has_proposals = len(st.session_state.proposal_products) > 0
    has_order = len(st.session_state.order_items) > 0
    has_client_info = st.session_state.client_info.get('company_name', '').strip() != ''

    # Tab 1: Proposals
    tab1_status = "✓" if has_proposals else "○"
    tab1_color = "green" if has_proposals else "gray"
    st.markdown(f":{tab1_color}[{tab1_status}] **Tab 1:** Proposals ({len(st.session_state.proposal_products)} products)")

    # Tab 2: Order & Client Info
    tab2_status = "✓" if (has_order and has_client_info) else "○"
    tab2_color = "green" if (has_order and has_client_info) else "gray"
    st.markdown(f":{tab2_color}[{tab2_status}] **Tab 2:** Order & Client ({len(st.session_state.order_items)} products)")

    # Tab 3: Invoice/PO ready indicator
    tab3_ready = has_order and has_client_info
    tab3_status = "✓" if tab3_ready else "○"
    tab3_color = "green" if tab3_ready else "gray"
    tab3_label = "Ready" if tab3_ready else "Not ready"
    st.markdown(f":{tab3_color}[{tab3_status}] **Tab 3:** Invoice/PO ({tab3_label})")

    st.caption("Complete Tab 2 to generate Invoice/PO in Tab 3")

    st.markdown("---")

    # Section 2: Clear All Data Button
    st.markdown("### Session Management")

    if st.button("Clear All Data", type="secondary", use_container_width=True):
        st.session_state.confirm_clear = True

    if st.session_state.get('confirm_clear', False):
        st.warning("Are you sure? This will clear all proposals, orders, and client info.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Clear", type="primary", use_container_width=True):
                # Clear all session state data
                st.session_state.proposal_products = []
                st.session_state.order_items = []
                st.session_state.client_info = {
                    'is_new_client': True,
                    'company_name': '',
                    'contact_name': '',
                    'contact_email': '',
                    'client_po': '',
                    'billing_address': '',
                    'shipping_type': 'Ground',
                    'shipping_address': '',
                    'payment_timeline': 'Net 30',
                    'payment_preference': 'Check',
                    'client_in_hands_date': None,
                    'order_submitted_by': '',
                    'order_submitted_date': datetime.now().date(),
                    'cost_submitted_by': '',
                    'cost_submitted_date': None
                }
                st.session_state.order_notes = {
                    'kitting_specs': '',
                    'client_requests': '',
                    'addon_samples': '',
                    'artwork_attachments': '',
                    'general_notes': ''
                }
                st.session_state.order_shipping = 0.0
                st.session_state.order_discount_type = "none"
                st.session_state.order_history = []
                st.session_state.confirm_clear = False
                st.rerun()
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()

    st.markdown("---")

    # Section 3: Instructions
    with st.expander("How to Use This App", expanded=False):
        st.markdown("""
        **3-Tab Workflow:**

        **Tab 1: Proposals** (for prospective clients)
        - Browse product catalog with filters
        - Add products to proposal
        - Configure quantity, markup, MSRP comparison
        - Generate MOQ-based proposal tables
        - Download client order form

        **Tab 2: Order & Client Info** (main workflow)
        1. Enter client information (company, contact, payment)
        2. Select partner and product from dropdowns
        3. Set quantity, markup, and customization options
        4. Add to order (repeat for multiple products)
        5. Configure shipping, discounts, custom items
        6. Add order notes (kitting, artwork, requests)
        7. Review order summary

        **Tab 3: Execution & Accounting** (final step)
        - View order summary and validation warnings
        - Generate invoice and purchase order
        - Download CSV for bookkeeping
        - Export to accounting (coming soon)

        **Tips:**
        - Start with Tab 2 for actual orders
        - Use Tab 1 for quick quotes/proposals
        - Tab 3 requires completed order in Tab 2
        """)

    st.markdown("---")

    # Section 4: Recent Orders
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

    # Section 5: Data Status
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

        # Add per-product tariff lines
        for item in st.session_state.order_items:
            tariff_amount = item.get('tariff_amount', 0)
            if tariff_amount > 0:
                country = item.get('country_of_origin', 'Unknown')
                tariff_rate = item.get('tariff_rate_percent', 0)
                writer.writerow([f"Tariff: {item['product_name']} ({tariff_rate}% - {country})", "", "", f"${tariff_amount:.2f}"])

        # Calculate total tariff
        total_tariff = sum(item.get('tariff_amount', 0) for item in st.session_state.order_items)
        total_quote = products_subtotal + st.session_state.order_shipping + total_tariff
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

# ============================================================
# DATA LOADING
# ============================================================
try:
    if 'df_template' not in st.session_state:
        df_template, df_metadata, df_partner_info = load_pricing_data()
        st.session_state.df_template = df_template
        st.session_state.df_metadata = df_metadata
        st.session_state.df_partner_info = df_partner_info
        st.session_state.data_loaded_at = datetime.now()

        # Extract and store partner contacts
        st.session_state.partner_contacts = extract_partner_contacts(df_partner_info)

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

# ============================================================
# TAB STRUCTURE
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "Proposals",
    "Order & Client Info",
    "Execution & Accounting"
])

# ============================================================
# TAB 1: PROPOSALS
# ============================================================
with tab1:
    st.header("Proposals - Product Catalog & Proposal Generation")
    st.caption("Browse products, configure proposals, and generate client quotes")
    st.divider()

    # ============================================================
    # SECTION 1: FILTERS
    # ============================================================
    st.subheader("1. Filter Products")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Max Price**")
        max_price = st.number_input(
            "Max price per unit ($) - Optional",
            min_value=0.0,
            value=st.session_state.proposal_filters.get('max_price') or 0.0,
            step=1.0,
            key="filter_max_price"
        )

    with col2:
        st.markdown("**Partner/Maker**")
        all_partners = sorted(df_template["Partner"].unique().tolist())
        selected_partners = st.multiselect(
            "Select partners (leave empty for all)",
            options=all_partners,
            default=st.session_state.proposal_filters.get('partners', []),
            key="filter_partners"
        )

    with col3:
        st.markdown("**Country of Origin**")
        all_countries = sorted(df_template["Country of Origin"].dropna().unique().tolist())
        selected_countries = st.multiselect(
            "Select countries (leave empty for all)",
            options=all_countries,
            default=st.session_state.proposal_filters.get('countries', []),
            key="filter_countries"
        )

    # Update filters in session state
    st.session_state.proposal_filters['max_price'] = max_price if max_price > 0 else None
    st.session_state.proposal_filters['partners'] = selected_partners
    st.session_state.proposal_filters['countries'] = selected_countries

    # Apply filters
    filtered_df = df_template.copy()

    if selected_partners:
        filtered_df = filtered_df[filtered_df["Partner"].isin(selected_partners)]

    if selected_countries:
        filtered_df = filtered_df[filtered_df["Country of Origin"].isin(selected_countries)]

    # Price filtering (estimate based on MOQ)
    if max_price and max_price > 0:
        price_filtered_indices = []
        for idx, row in filtered_df.iterrows():
            # Get price estimate at quantity 100
            base_price, _, _ = get_unit_price_new_system(row, 100)
            if base_price:
                if max_price > 0 and base_price > max_price:
                    continue
                price_filtered_indices.append(idx)
        filtered_df = filtered_df.loc[price_filtered_indices]

    st.info(f"Showing {len(filtered_df)} products matching filters")

    st.divider()

    # ============================================================
    # SECTION 2: PRODUCT CATALOG
    # ============================================================
    st.subheader("2. Product Catalog")

    if len(filtered_df) == 0:
        st.warning("No products match your filters. Try adjusting the filter criteria above.")
    else:
        # Display success message if a product was just added
        if 'show_success_message' in st.session_state and st.session_state.show_success_message:
            st.success(f"✓ Added **{st.session_state.success_product_name}** to proposal!")
            st.session_state.show_success_message = False

        # Table-style header
        header_col1, header_col2, header_col3, header_col4 = st.columns([3, 1.5, 1, 1.5])
        with header_col1:
            st.markdown("**Product Name**")
        with header_col2:
            st.markdown("**Partner**")
        with header_col3:
            st.markdown("**Price/Unit**")
        with header_col4:
            st.markdown("**Actions**")

        st.divider()

        # Display filtered products in a compact table-style format
        for idx, row in filtered_df.iterrows():
            product_data = row

            # Calculate price for display
            preliminary_price, _, _ = get_unit_price_new_system(product_data, 100)
            estimated_moq = calculate_moq(preliminary_price * 2) if preliminary_price else None
            moq_price, _, _ = get_unit_price_new_system(product_data, estimated_moq) if estimated_moq else (None, None, None)

            # Compact row with all essential info
            col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1.5])

            with col1:
                st.markdown(f"**{product_data['Product/Service']}**")

            with col2:
                st.markdown(f"{product_data['Partner']}")

            with col3:
                if moq_price:
                    st.markdown(f"${moq_price:.2f}")
                else:
                    st.markdown("—")

            with col4:
                # Add button - adds product to proposal with 100% markup default
                if st.button("Add to Proposal", key=f"add_{idx}", use_container_width=True, type="primary"):
                    proposal_item = {
                        'product_data': product_data.to_dict(),
                        'markup_percent': 100.0
                    }
                    st.session_state.proposal_products.append(proposal_item)

                    # Set success message
                    st.session_state.show_success_message = True
                    st.session_state.success_product_name = product_data['Product/Service']
                    st.rerun()

            # Expandable details section
            with st.expander(f"View details for {product_data['Product/Service']}", expanded=False):
                st.caption(f"**Partner:** {product_data['Partner']} | **Country:** {product_data.get('Country of Origin', 'N/A')} | **Tiered Pricing:** {product_data.get('Pricing Tiers (Y/N)', 'N/A')}")

                # Show estimated price at MOQ
                if moq_price and estimated_moq:
                    st.caption(f"**Est. Price at MOQ ({estimated_moq} units):** ${moq_price:.2f}/unit")

                # Show description if available
                desc = product_data.get("Marketing Description", "")
                if desc and str(desc).strip() and str(desc).strip() != 'nan':
                    st.write(desc)
                else:
                    st.caption("No description available")

            st.divider()

    # ============================================================
    # SECTION 3: PROPOSAL PREVIEW & SETTINGS
    # ============================================================
    st.divider()
    st.subheader("3. Proposal Preview & Settings")

    if len(st.session_state.proposal_products) == 0:
        st.info("No products added to proposal yet. Add products from the catalog above.")
    else:
        st.success(f"{len(st.session_state.proposal_products)} product(s) in proposal")

        # Proposal Settings Section
        st.markdown("### Proposal Settings")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Client Budget filter for volume pricing calculations
            client_budget = st.number_input(
                "Client Budget ($)",
                min_value=0.0,
                value=st.session_state.get('proposal_client_budget', 0.0),
                step=100.0,
                help="Total potential spend by client. Used to calculate volume pricing if budget allows higher quantities.",
                key="proposal_client_budget_input"
            )
            st.session_state.proposal_client_budget = client_budget

        with col2:
            # Discount options
            discount_type = st.selectbox(
                "Client Discount",
                options=["None", "NGO (5%)", "Custom"],
                index=0 if not st.session_state.get('proposal_discount_type') else
                      (1 if st.session_state.get('proposal_discount_type') == 'NGO' else 2),
                key="proposal_discount_type_select"
            )

            if discount_type == "NGO (5%)":
                st.session_state.proposal_discount_type = 'NGO'
                st.session_state.proposal_discount_percent = 5.0
            elif discount_type == "Custom":
                st.session_state.proposal_discount_type = 'Custom'
                custom_discount = st.number_input(
                    "Custom discount %",
                    min_value=0.0,
                    max_value=100.0,
                    value=st.session_state.get('proposal_discount_percent', 0.0),
                    step=0.5,
                    key="proposal_custom_discount"
                )
                st.session_state.proposal_discount_percent = custom_discount
            else:
                st.session_state.proposal_discount_type = None
                st.session_state.proposal_discount_percent = 0.0

        with col3:
            # Marketing rounding
            st.session_state.proposal_marketing_rounding = st.checkbox(
                "Apply marketing rounding (e.g., $60 → $59)",
                value=st.session_state.proposal_marketing_rounding,
                key="proposal_marketing_rounding_checkbox"
            )

        st.divider()

        # Product table with MSRP and editable markup
        st.markdown("### Products in Proposal")

        # Table header
        header_col1, header_col2, header_col3, header_col4 = st.columns([3, 1.5, 1.5, 1])
        with header_col1:
            st.markdown("**Product**")
        with header_col2:
            st.markdown("**MSRP** (if available)")
        with header_col3:
            st.markdown("**Markup %**")
        with header_col4:
            st.markdown("**Remove**")

        st.divider()

        # Display each product in table format
        for idx, item in enumerate(st.session_state.proposal_products):
            product_data = item['product_data']

            col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])

            with col1:
                st.markdown(f"{product_data['Product/Service']}")
                st.caption(f"Partner: {product_data['Partner']}")

            with col2:
                # Show MSRP if available
                msrp = clean_price(product_data.get('MSRP', ''))
                if msrp and msrp > 0:
                    st.markdown(f"${msrp:.2f}")
                else:
                    st.markdown("—")

            with col3:
                # Editable markup field
                new_markup = st.number_input(
                    f"Markup for {idx}",
                    min_value=0.0,
                    value=item['markup_percent'],
                    step=5.0,
                    key=f"markup_{idx}",
                    label_visibility="collapsed"
                )
                # Update markup if changed
                if new_markup != item['markup_percent']:
                    st.session_state.proposal_products[idx]['markup_percent'] = new_markup

            with col4:
                if st.button("✕", key=f"remove_{idx}", help=f"Remove {product_data['Product/Service']}", use_container_width=True):
                    st.session_state.proposal_products.pop(idx)
                    st.rerun()

            st.divider()

    # ============================================================
    # SECTION 4: GENERATE PROPOSAL TABLES
    # ============================================================
    st.divider()
    st.subheader("4. Generate Proposal Tables")

    if len(st.session_state.proposal_products) == 0:
        st.caption("Add products to generate proposal tables")
    else:
        st.markdown("Each product is presented in a separate table with MOQ pricing.")
        st.markdown("")

        # Generate a separate table for each product
        for idx, item in enumerate(st.session_state.proposal_products, 1):
            st.markdown(f"### Product {idx}: {item['product_data']['Product/Service']}")

            product_row = item['product_data']

            # Calculate MOQ using a standard preliminary quantity (100 units)
            preliminary_base_price, _, _ = get_unit_price_new_system(product_row, 100)

            if preliminary_base_price is not None:
                # Estimate total per-unit price with markup (no customization in MOQ calc)
                temp_markup_multiplier = 1 + (item['markup_percent'] / 100)
                estimated_unit_price = preliminary_base_price * temp_markup_multiplier

                # Calculate MOQ
                moq = calculate_moq(estimated_unit_price)
                if moq is None:
                    moq = 5

                # Get actual base price for MOQ quantity
                moq_base_price, moq_tier_range, _ = get_unit_price_new_system(product_row, moq)

                if moq_base_price is not None:
                    # Calculate product price WITHOUT customization (for main table)
                    moq_product_cost = moq_base_price * moq
                    moq_markup_amount = moq_product_cost * (item['markup_percent'] / 100)
                    moq_product_only_total = moq_product_cost + moq_markup_amount
                    moq_product_price_per_unit = moq_product_only_total / moq

                    # Apply marketing rounding if enabled
                    if st.session_state.proposal_marketing_rounding:
                        moq_product_price_per_unit = apply_marketing_rounding(moq_product_price_per_unit, True)

                    # Calculate Client Price based on discount and budget
                    client_price = moq_product_price_per_unit
                    client_price_note = ""

                    # Get client budget and discount settings
                    client_budget = st.session_state.get('proposal_client_budget', 0.0)
                    discount_percent = st.session_state.get('proposal_discount_percent', 0.0)

                    # Check if client budget allows for higher quantity (better pricing)
                    volume_pricing_applied = False
                    volume_pricing_quantity = None
                    if client_budget > 0:
                        moq_total = moq * moq_product_price_per_unit
                        if client_budget > moq_total:
                            # Calculate what quantity the client could afford at MOQ price
                            potential_quantity = int(client_budget / moq_product_price_per_unit)

                            # Get price at that higher quantity
                            budget_qty_base_price, _, _ = get_unit_price_new_system(product_row, potential_quantity)

                            if budget_qty_base_price is not None:
                                # Calculate price at higher quantity with markup
                                budget_qty_product_cost = budget_qty_base_price * potential_quantity
                                budget_qty_markup_amount = budget_qty_product_cost * (item['markup_percent'] / 100)
                                budget_qty_product_only_total = budget_qty_product_cost + budget_qty_markup_amount
                                budget_qty_price_per_unit = budget_qty_product_only_total / potential_quantity

                                # Apply marketing rounding if enabled
                                if st.session_state.proposal_marketing_rounding:
                                    budget_qty_price_per_unit = apply_marketing_rounding(budget_qty_price_per_unit, True)

                                # Use the better price if different from MOQ price
                                if budget_qty_price_per_unit < moq_product_price_per_unit:
                                    client_price = budget_qty_price_per_unit
                                    volume_pricing_applied = True
                                    volume_pricing_quantity = potential_quantity

                    # Apply discount to client price
                    discount_applied = False
                    if discount_percent > 0:
                        client_price = client_price * (1 - discount_percent / 100)
                        discount_applied = True

                        # Apply marketing rounding again after discount if enabled
                        if st.session_state.proposal_marketing_rounding:
                            client_price = apply_marketing_rounding(client_price, True)

                    # Build price note for column header
                    client_price_header = "Client Price"
                    if discount_applied or volume_pricing_applied:
                        notes = []
                        if volume_pricing_applied:
                            notes.append(f"Price ea @ Qty {volume_pricing_quantity}")
                        if discount_applied:
                            discount_type = st.session_state.get('proposal_discount_type')
                            if discount_type == 'NGO':
                                notes.append("5% NGO discount")
                            else:
                                notes.append(f"{discount_percent:.1f}% discount")
                        client_price_header = f"Client Price ({', '.join(notes)})"

                    # Build proposal table
                    col_moq = "MOQ"
                    col_price = f"Price Ea (@ Qty {moq})"
                    col_client_price = client_price_header
                    col_delivery = "Delivery"

                    proposal_table = pd.DataFrame([{
                        col_moq: moq,
                        col_price: f"${moq_product_price_per_unit:.2f}",
                        col_client_price: f"${client_price:.2f}",
                        col_delivery: ""
                    }])

                    st.table(proposal_table)

                    # Show MOQ calculation note
                    moq_total_value = moq * moq_product_price_per_unit
                    st.caption(f"MOQ calculated based on \\$1,000 minimum order value (MOQ {moq} units = \\${moq_total_value:.2f})")

                    # ALWAYS show customization costs from product data
                    # Get customization costs from the product data
                    setup_fee = clean_price(product_row.get('Customization Setup Fee', '')) or 0.0
                    per_unit_cost = clean_price(product_row.get('Customization Cost per Unit', '')) or 0.0

                    # Display customization costs at the bottom
                    if setup_fee > 0 or per_unit_cost > 0:
                        st.caption(f"**Customization available:** Artwork set-up: \\${setup_fee:.2f} / Branding per piece: \\${per_unit_cost:.2f}")
                    else:
                        st.caption("**Customization available:** Contact for pricing")

                    # Add download button for this product's proposal table
                    proposal_csv = proposal_table.to_csv(index=False)
                    st.download_button(
                        label=f"Download Product {idx} Proposal (CSV)",
                        data=proposal_csv,
                        file_name=f"proposal_product_{idx}_{item['product_data']['Product/Service'].replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"download_proposal_{idx}"
                    )
                else:
                    st.warning(f"Unable to calculate MOQ pricing for {item['product_data']['Product/Service']}")
            else:
                st.warning(f"Product data not available for {item['product_data']['Product/Service']}")

            st.markdown("")

        st.caption("Copy these tables and paste into your proposal template.")

        # Download all proposals as CSV
        st.markdown("---")
        if st.button("Download All Proposal Tables (CSV)", use_container_width=True, type="primary"):
            # Generate comprehensive CSV
            csv_lines = []
            csv_lines.append("PEACE BY PIECE - PRODUCT PROPOSAL")
            csv_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            csv_lines.append("")

            for idx, prop_item in enumerate(st.session_state.proposal_products, 1):
                product_data = prop_item.get('product_data', {})

                csv_lines.append(f"=== PRODUCT {idx}: {product_data.get('Product/Service', 'Unknown Product')} ===")
                csv_lines.append(f"Partner: {product_data.get('Partner', 'N/A')}")
                csv_lines.append(f"Country of Origin: {product_data.get('Country of Origin', 'N/A')}")
                csv_lines.append("")

                # Calculate MOQ
                base_price, _, _ = get_unit_price_new_system(product_data, 100)
                moq = calculate_moq(base_price)

                # Build tier table
                csv_lines.append("Quantity,Unit Price,Customization,Markup,Total per Unit,Total Order")

                # Calculate for different quantities (MOQ, 2×MOQ, 3×MOQ, 5×MOQ)
                quantities = [moq, moq * 2, moq * 3, moq * 5]

                for qty in quantities:
                    unit_price, _, _ = get_unit_price_new_system(product_data, qty)

                    # Customization cost
                    custom_per_unit = prop_item.get('customization_per_unit', 0.0) if prop_item.get('include_customization', False) else 0.0
                    custom_setup = prop_item.get('customization_setup_fee', 0.0) if prop_item.get('include_customization', False) else 0.0

                    # Markup
                    markup_percent = prop_item.get('markup_percent', 0)
                    product_cost = unit_price * qty
                    markup_amount = product_cost * (markup_percent / 100)

                    # Total per unit
                    total_per_unit = unit_price + custom_per_unit + (markup_amount / qty)

                    # Marketing rounding
                    if st.session_state.get('proposal_marketing_rounding', False):
                        total_per_unit = apply_marketing_rounding(total_per_unit)

                    # Total order
                    total_order = (total_per_unit * qty) + custom_setup

                    csv_lines.append(f"{qty},${unit_price:.2f},${custom_per_unit:.2f},${markup_amount:.2f},${total_per_unit:.2f},${total_order:.2f}")

                # Customization note
                if prop_item.get('include_customization', False):
                    csv_lines.append("")
                    csv_lines.append(f"Note: Includes ${custom_setup:.2f} setup fee + ${custom_per_unit:.2f} per unit for customization")

                csv_lines.append("")
                csv_lines.append("")

            # Pricing for Cards & Kitting
            csv_lines.append("=== PRICING FOR CARDS & KITTING ===")
            csv_lines.append(st.session_state.proposal_kitting_pricing)
            csv_lines.append("")
            csv_lines.append("")

            # Terms & Conditions
            csv_lines.append("=== TERMS & CONDITIONS ===")
            csv_lines.append(st.session_state.proposal_terms)

            proposal_csv = "\n".join(csv_lines)

            st.download_button(
                label="Click to Download CSV",
                data=proposal_csv,
                file_name=f"proposal_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_all_proposals_csv",
                use_container_width=True
            )

    # ============================================================
    # SECTION 5: PRICING FOR CARDS & KITTING
    # ============================================================
    st.divider()
    st.subheader("5. Pricing for Cards & Kitting")

    st.session_state.proposal_kitting_pricing = st.text_area(
        "Edit kitting pricing if needed",
        value=st.session_state.proposal_kitting_pricing,
        height=200,
        key="proposal_kitting_pricing_input"
    )

    # Add copy button for kitting pricing
    if st.button("Copy Pricing for Cards & Kitting", key="copy_kitting_pricing", use_container_width=True):
        st.code(st.session_state.proposal_kitting_pricing, language=None)
        st.info("Select the text above and copy it (Ctrl+C or Cmd+C)")

    # ============================================================
    # SECTION 6: TERMS & CONDITIONS
    # ============================================================
    st.divider()
    st.subheader("6. Terms & Conditions")

    st.session_state.proposal_terms = st.text_area(
        "Edit terms & conditions if needed",
        value=st.session_state.proposal_terms,
        height=200,
        key="proposal_terms_input"
    )

    # Add copy button for terms & conditions
    if st.button("Copy Terms & Conditions", key="copy_terms", use_container_width=True):
        st.code(st.session_state.proposal_terms, language=None)
        st.info("Select the text above and copy it (Ctrl+C or Cmd+C)")

    # ============================================================
    # SECTION 7: CLIENT ORDER FORM
    # ============================================================
    st.divider()
    st.subheader("7. Client Order Form")

    st.markdown("""
    Download the HTML form below and paste it into your email to send to clients.
    The table will look professional and clients can fill it out directly.
    """)

    # Generate HTML table
    html_form = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; background-color: #ffffff; }
        h2 { color: #2c3e50; background-color: #ffffff; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        .instructions-box { background-color: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; color: #000000; }
        .instructions-box p { margin: 5px 0; color: #000000; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; background-color: #ffffff; }
        th { background-color: #3498db !important; color: #ffffff !important; padding: 12px; text-align: left; font-weight: bold; }
        td { border: 1px solid #ddd; padding: 10px; background-color: #ffffff; color: #000000; }
        td:first-child { background-color: #f8f9fa !important; color: #000000 !important; font-weight: 500; width: 35%; vertical-align: top; }
        .section-header { background-color: #2c3e50 !important; color: #ffffff !important; font-weight: bold; padding: 10px; }
        .fill-in { background-color: #ffffff !important; color: #7f8c8d !important; min-height: 20px; font-style: italic; }
        .product-table { margin: 10px 0; }
        .product-table td { background-color: #ffffff !important; color: #000000 !important; }
        .helper-text { color: #7f8c8d; font-size: 0.85em; display: block; margin-top: 3px; }
        .required { color: #e74c3c !important; font-weight: bold; }
    </style>
</head>
<body>
    <h2>PEACE BY PIECE CLIENT ORDER FORM</h2>

    <div class="instructions-box">
        <p><strong>HOW TO FILL OUT THIS FORM:</strong></p>
        <p>1. Copy & paste the entire form into Docs, Word, or directly into your email reply (the format should copy along with the text)</p>
        <p>2. Click in the gray areas to type your answers</p>
        <p>3. For multiple choice questions, delete the options you DON'T want and keep the one you DO want</p>
        <p>4. When finished, select all (Ctrl+A or Cmd+A), copy, and paste into your email reply</p>
        <p>5. Fields marked with <span class="required">*</span> are required</p>
    </div>

    <table>
        <tr>
            <td colspan="2" class="section-header">CLIENT INFORMATION</td>
        </tr>
        <tr>
            <td>Client Type <span class="required">*</span></td>
            <td class="fill-in">[Delete one: Existing / New]</td>
        </tr>
        <tr>
            <td>Company Name <span class="required">*</span></td>
            <td class="fill-in">[Type company name here]</td>
        </tr>
        <tr>
            <td>Contact Name <span class="required">*</span></td>
            <td class="fill-in">[Type your name here]</td>
        </tr>
        <tr>
            <td>Contact Email <span class="required">*</span></td>
            <td class="fill-in">[Type your email here]</td>
        </tr>
    </table>

    <table>
        <tr>
            <td colspan="2" class="section-header">SHIPPING & DELIVERY</td>
        </tr>
        <tr>
            <td>Drop Shipping? <span class="required">*</span></td>
            <td class="fill-in">[Delete one: Yes / No]</td>
        </tr>
        <tr>
            <td>Shipping Address<span class="helper-text">(if single location)</span></td>
            <td class="fill-in">[Type full shipping address here, or N/A if drop shipping]</td>
        </tr>
        <tr>
            <td>Destination Breakdown<span class="helper-text">(if drop shipping internationally)</span></td>
            <td class="fill-in">[Example: 50 units to CA, 30 units to TX, or N/A if single location]</td>
        </tr>
        <tr>
            <td>Billing Address</td>
            <td class="fill-in">[Type billing address here, or "Same as shipping"]</td>
        </tr>
        <tr>
            <td>Client In-Hands Date <span class="required">*</span></td>
            <td class="fill-in">[Type date in format: MM/DD/YYYY]</td>
        </tr>
    </table>

    <table>
        <tr>
            <td colspan="3" class="section-header">ORDER DETAILS</td>
        </tr>
        <tr>
            <th>Product Name</th>
            <th>Quantity</th>
            <th>Customization/Branding Details</th>
        </tr>"""

    # Add product rows - either from proposal or blank rows
    if len(st.session_state.proposal_products) > 0:
        for prop_item in st.session_state.proposal_products:
            product_name = prop_item.get('product_data', {}).get('Product/Service', 'Unknown Product')
            quantity = prop_item.get('quantity', '')
            html_form += f"""
        <tr>
            <td class="product-table">{product_name}</td>
            <td class="product-table">{quantity}</td>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">[Describe any customization, logo placement, colors, etc.]</td>
        </tr>"""
    else:
        # Add 3 blank rows if no products in proposal
        for i in range(3):
            html_form += """
        <tr>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">[Product name]</td>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">[Qty]</td>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">[Customization details]</td>
        </tr>"""

    html_form += """
    </table>

    <table>
        <tr>
            <td colspan="2" class="section-header">IMPACT CARDS</td>
        </tr>
        <tr>
            <td>Impact Card Preference <span class="required">*</span></td>
            <td class="fill-in">[Delete all except the ONE option you want]<br/><br/>
                Peace by Piece Impact Card<br/>
                Custom Impact Card<br/>
                Custom Message Card<br/>
                Send us your own card
            </td>
        </tr>
    </table>

    <table>
        <tr>
            <td colspan="2" class="section-header">PAYMENT</td>
        </tr>
        <tr>
            <td>Payment Preference <span class="required">*</span></td>
            <td class="fill-in">[Delete all except the ONE option you want]<br/><br/>
                ACH<br/>
                Check<br/>
                Credit Card (3% processing fee applies)
            </td>
        </tr>
    </table>

</body>
</html>"""

    # Show preview in expander
    with st.expander("Preview HTML Form", expanded=False):
        st.components.v1.html(html_form, height=800, scrolling=True)

    # Download buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Download HTML Form",
            data=html_form,
            file_name=f"client_order_form_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            key="download_client_form_html",
            type="primary"
        )

    with col2:
        # Keep TXT version for backup
        client_form_text = """CLIENT ORDER FORM

Client Type: [ ] Existing  [ ] New
Company Name: _______________________
Contact: _______________________
Contact Email: _______________________
Drop Shipping? [ ] Y  [ ] N
Shipping address if one location: _______________________
Destination breakdown if drop shipping internationally: _______________________
Billing address: _______________________
Client In-Hands Date: _______________________

Order Details:
Product Name | Quantity | Customization/Branding Details
___________|_________|_____________________________
___________|_________|_____________________________
___________|_________|_____________________________

Impact Cards: [ ] Peace by Piece Impact Card  [ ] Custom Impact Card
              [ ] Custom Message Card  [ ] Send us their own card

Payment Preference: [ ] ACH  [ ] Check  [ ] Credit Card (3% processing fee)
"""
        st.download_button(
            label="Download TXT (Backup)",
            data=client_form_text,
            file_name="client_order_form.txt",
            mime="text/plain",
            key="download_client_form_txt"
        )

    with col3:
        # Generate CSV version
        csv_lines = []
        csv_lines.append("FIELD,VALUE")
        csv_lines.append("Client Type,")
        csv_lines.append("Company Name,")
        csv_lines.append("Contact Name,")
        csv_lines.append("Contact Email,")
        csv_lines.append("Drop Shipping?,")
        csv_lines.append("Shipping Address,")
        csv_lines.append("Destination Breakdown,")
        csv_lines.append("Billing Address,")
        csv_lines.append("Client In-Hands Date,")
        csv_lines.append("")
        csv_lines.append("ORDER DETAILS")
        csv_lines.append("Product Name,Quantity,Customization Details")

        # Add placeholder rows for each product in proposal
        if len(st.session_state.proposal_products) > 0:
            for prop_item in st.session_state.proposal_products:
                product_name = prop_item.get('product_data', {}).get('Product/Service', 'Unknown Product')
                quantity = prop_item.get('quantity', '')
                csv_lines.append(f"{product_name},{quantity},")
        else:
            # Add 3 blank rows
            for i in range(3):
                csv_lines.append(",,")

        csv_lines.append("")
        csv_lines.append("IMPACT CARDS")
        csv_lines.append("Impact Card Type,")
        csv_lines.append("")
        csv_lines.append("PAYMENT")
        csv_lines.append("Payment Preference,")

        client_form_csv = "\n".join(csv_lines)

        st.download_button(
            label="Download CSV (Backup)",
            data=client_form_csv,
            file_name=f"client_order_form_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_client_form_csv"
        )

    st.info("Tip: Download the HTML form, open it in your browser, then copy the entire page and paste it into your email. It will preserve all formatting!")

    # ============================================================
    # NEXT STEPS GUIDANCE
    # ============================================================
    st.divider()

    if len(st.session_state.proposal_products) > 0:
        st.success(f"""
        **What's Next?**

        1. Download and send the proposal to your client
        2. Once your client confirms interest, move to **Tab 2: Order & Client Info** to finalize the order
        3. Your {len(st.session_state.proposal_products)} proposal product(s) will be available for quick import in Tab 2
        """)
    else:
        st.info("""
        **What's Next?**

        After adding products to your proposal, you can:
        - Download proposal tables and client order forms
        - Send to your client for review
        - Move to **Tab 2: Order & Client Info** when client confirms
        """)

# ============================================================
# TAB 2: ORDER & CLIENT INFO (ALL CURRENT FUNCTIONALITY)
# ============================================================
with tab2:
    st.header("Order & Client Information")
    st.caption("Complete order workflow - All existing functionality is here")
    st.divider()

    # Proposal products availability banner
    proposal_count = len(st.session_state.proposal_products)
    if proposal_count > 0:
        st.success(f"✓ {proposal_count} product(s) ready to import from Proposal (Tab 1)")

    # Order status indicator
    total_products = len(st.session_state.order_items)
    if total_products > 0:
        st.info(f"Current order: {total_products} product(s)")
    else:
        st.info("Current order: empty — Add your first product below")

    st.divider()

    # ============================================================
    # PROPOSAL PRODUCTS SELECTION (if available)
    # ============================================================
    if len(st.session_state.proposal_products) > 0:
        st.header("Quick Add: Products from Proposal")
        st.info(f"{len(st.session_state.proposal_products)} product(s) available from Proposal (Tab 1). Select below to add to order.")
        st.session_state.using_proposal_data = True

        # Import All button at top level
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Import All Products from Proposal", type="primary", use_container_width=True, key="import_all_proposal"):
                # Import all proposal products to order
                imported_count = 0
                for prop_item in st.session_state.proposal_products:
                    order_item = convert_proposal_to_order(
                        prop_item,
                        get_unit_price_new_system,
                        calculate_product_tariff
                    )
                    st.session_state.order_items.append(order_item)
                    imported_count += 1

                st.success(f"Imported all {imported_count} product(s) from proposal!")
                st.rerun()

        with col2:
            st.caption("Or select individually below:")

        with st.expander("Select Individual Products from Proposal", expanded=False):
            st.markdown("Select specific products from your proposal to add to this order. You can edit quantities and settings after adding.")

            # Build selection checkboxes
            selected_proposal_indices = []

            for idx, prop_item in enumerate(st.session_state.proposal_products):
                product_data = prop_item.get('product_data', {})

                col1, col2 = st.columns([4, 1])

                with col1:
                    is_selected = st.checkbox(
                        f"{product_data.get('Product/Service', 'Unknown Product')} - {product_data.get('Partner', 'N/A')}",
                        key=f"select_proposal_{idx}"
                    )

                    # Show proposal details
                    st.caption(f"Quantity: {prop_item.get('quantity', 'N/A')} | Markup: {prop_item.get('markup_percent', 0)}%")

                    if prop_item.get('include_customization', False):
                        setup_fee = prop_item.get('customization_setup_fee', 0)
                        per_unit = prop_item.get('customization_per_unit', 0)
                        st.caption(f"Customization: ${setup_fee:.2f} setup + ${per_unit:.2f}/unit")

                with col2:
                    if is_selected:
                        selected_proposal_indices.append(idx)

            # Add selected button
            if len(selected_proposal_indices) > 0:
                if st.button(f"Add {len(selected_proposal_indices)} Selected Product(s) to Order", type="primary", use_container_width=True):
                    # Convert and add to order
                    for idx in selected_proposal_indices:
                        order_item = convert_proposal_to_order(
                            st.session_state.proposal_products[idx],
                            get_unit_price_new_system,
                            calculate_product_tariff
                        )
                        st.session_state.order_items.append(order_item)

                    st.success(f"Added {len(selected_proposal_indices)} product(s) to order!")
                    st.rerun()
            else:
                st.caption("Select at least one product above to add to order.")

        st.divider()
    else:
        st.session_state.using_proposal_data = False

    # ============================================================
    # CLIENT INFORMATION UI
    # ============================================================
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
        st.markdown("**Payment & Delivery Terms**")

        col3, col4 = st.columns(2)

        with col3:
            # Updated to dropdown
            payment_terms_options = ['Net 30', 'Net 60', 'Due on Receipt', '50% Deposit']
            current_timeline = st.session_state.client_info.get('payment_timeline', 'Net 30')
            if current_timeline not in payment_terms_options:
                payment_terms_options.append(current_timeline)

            st.session_state.client_info['payment_timeline'] = st.selectbox(
                "Payment Terms",
                options=payment_terms_options,
                index=payment_terms_options.index(current_timeline) if current_timeline in payment_terms_options else 0
            )

        with col4:
            # Updated to match template options
            payment_method_options = ['Check', 'ACH', 'Credit Card', 'Wire Transfer']
            current_preference = st.session_state.client_info.get('payment_preference', 'Check')
            if current_preference not in payment_method_options:
                payment_method_options.append(current_preference)

            st.session_state.client_info['payment_preference'] = st.selectbox(
                "Payment Method",
                options=payment_method_options,
                index=payment_method_options.index(current_preference) if current_preference in payment_method_options else 0
            )

        col5, col6 = st.columns(2)

        with col5:
            # NEW: Ship method dropdown
            ship_method_options = ['Ground', 'Air', 'Freight', 'Other']
            current_ship_type = st.session_state.client_info.get('shipping_type', 'Ground')
            # Map old values to new
            if current_ship_type == 'One Location':
                current_ship_type = 'Ground'
            elif current_ship_type == 'Drop Shipping':
                current_ship_type = 'Other'

            if current_ship_type not in ship_method_options:
                ship_method_options.append(current_ship_type)

            # Note: We're overriding shipping_type to use ship method
            ship_method = st.selectbox(
                "Ship Method",
                options=ship_method_options,
                index=ship_method_options.index(current_ship_type) if current_ship_type in ship_method_options else 0,
                help="How products will be shipped to client"
            )

        with col6:
            # NEW: Client in-hands date
            st.session_state.client_info['client_in_hands_date'] = st.date_input(
                "Client In-Hands Date",
                value=st.session_state.client_info.get('client_in_hands_date'),
                help="Target delivery date for client to receive products"
            )

        st.markdown("---")
        st.markdown("**Order Submission Details**")

        col7, col8 = st.columns(2)

        with col7:
            st.session_state.client_info['order_submitted_by'] = st.text_input(
                "Order Submitted By",
                value=st.session_state.client_info.get('order_submitted_by', ''),
                placeholder="Your name",
                help="Person creating this order"
            )

            st.session_state.client_info['cost_submitted_by'] = st.text_input(
                "Cost Submitted By",
                value=st.session_state.client_info.get('cost_submitted_by', ''),
                placeholder="Finance contact name",
                help="Person who submitted/verified costs"
            )

        with col8:
            # Order submitted date (auto-filled, read-only display)
            order_date = st.session_state.client_info.get('order_submitted_date', datetime.now().date())
            st.date_input(
                "Order Submitted Date",
                value=order_date,
                disabled=True,
                help="Auto-filled when order created"
            )

            st.session_state.client_info['cost_submitted_date'] = st.date_input(
                "Cost Submitted Date",
                value=st.session_state.client_info.get('cost_submitted_date'),
                help="Date when costs were submitted/verified"
            )

    st.divider()

    # ============================================================
    # PRODUCT SELECTION UI
    # ============================================================
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
            st.markdown("**How Pricing Tiers Work:**")
            st.markdown("This product uses tiered pricing - the price per unit decreases as you order more. The tier ranges below show which price applies based on your order quantity.")
            st.markdown("")
            st.markdown(f"**Tier Ranges:** {tier_info}")
            st.caption("Your order quantity will automatically match to the correct tier and price.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # QUANTITY & PRICING UI
    # ============================================================
    st.header("3. Quantity & Pricing")

    # 3.1 - Quantity Selection
    st.subheader("Quantity Selection")
    quantity = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1,
        key="input_quantity"
    )

    # Show tier being used
    base_price_preview, tier_range_preview, tier_column_preview = get_unit_price_new_system(product_data, quantity)
    if base_price_preview:
        if tier_range_preview == "No Tiers":
            st.caption(f"Flat pricing: ${base_price_preview:.2f} per unit")
        else:
            st.caption(f"Using pricing tier: {tier_range_preview} units | Base price: ${base_price_preview:.2f} per unit")

    st.divider()

    # 3.2 - Partner MSRP (Reference)
    st.subheader("Partner MSRP (Reference)")

    show_msrp = st.checkbox(
        "Show Partner MSRP comparison",
        value=False,
        key="show_msrp_checkbox",
        help="Display partner's suggested retail price for reference"
    )

    partner_msrp = 0.0
    if show_msrp:
        # Check if MSRP exists in spreadsheet
        default_msrp = clean_price(product_data.get('Partner MSRP', '')) or 0.0

        partner_msrp = st.number_input(
            "Partner MSRP (per unit)",
            min_value=0.0,
            value=float(default_msrp),
            step=1.0,
            key="input_partner_msrp",
            help="Optional - Partner's suggested retail price for reference"
        )

        st.caption("This is the partner's suggested retail price - for reference only")

    st.divider()

    # 3.3 - Markup Configuration
    st.subheader("Markup Configuration")

    markup_percent = st.number_input(
        "Markup %",
        min_value=0.0,
        value=100.0,
        step=5.0,
        key="input_markup",
        help="Your profit margin. 100% = double the cost (2x), 50% = 1.5x the cost, 200% = triple the cost (3x)"
    )

    # Rounding option
    round_to_five = st.checkbox(
        "Round to nearest multiple of $5",
        value=False,
        key="round_to_five_checkbox",
        help="Rounds the customer price per unit to the nearest $5 (e.g., $17.50 becomes $20, $12.30 becomes $10)"
    )

    # Calculate pricing breakdown (no customization yet)
    if base_price_preview:
        product_subtotal_preview = base_price_preview * quantity
        markup_amount_preview = product_subtotal_preview * (markup_percent / 100)
        customer_price_no_custom_raw = product_subtotal_preview + markup_amount_preview
        customer_price_per_unit_raw = customer_price_no_custom_raw / quantity

        # Apply rounding if enabled
        customer_price_per_unit = round_to_nearest_five(customer_price_per_unit_raw, round_to_five)
        customer_price_no_custom = customer_price_per_unit * quantity

        # Display pricing breakdown
        st.markdown("**Pricing Breakdown (Before Customization)**")

        breakdown_data = [
            ["Base Cost (Partner)", f"${base_price_preview:.2f}/unit", f"${product_subtotal_preview:.2f} total"],
            ["Your Markup ({:.0f}%)".format(markup_percent), f"${markup_amount_preview/quantity:.2f}/unit", f"${markup_amount_preview:.2f} total"],
            ["", "", ""],
            ["**Customer Price (No Custom)**", f"**${customer_price_per_unit:.2f}/unit**", f"**${customer_price_no_custom:.2f}**"]
        ]

        # Show rounding note if enabled
        if round_to_five:
            breakdown_data.append(["", "", ""])
            breakdown_data.append(["Rounding Applied", f"(${customer_price_per_unit_raw:.2f} → ${customer_price_per_unit:.2f})", ""])

        breakdown_df = pd.DataFrame(breakdown_data, columns=["Item", "Per Unit", "Total"])
        st.table(breakdown_df)

        st.caption("This is the base product price before customization, tariffs, or shipping")

        # MSRP Comparison (if enabled)
        if show_msrp and partner_msrp > 0:
            st.markdown("**Compare to Partner MSRP:**")

            msrp_diff = customer_price_per_unit - partner_msrp
            msrp_diff_percent = (msrp_diff / partner_msrp * 100) if partner_msrp > 0 else 0

            comparison_data = [
                ["Partner MSRP", f"${partner_msrp:.2f}/unit"],
                ["Your Price", f"${customer_price_per_unit:.2f}/unit"],
                ["Difference", f"${msrp_diff:.2f} ({msrp_diff_percent:+.1f}%)"]
            ]

            comparison_df = pd.DataFrame(comparison_data, columns=["Item", "Price"])
            st.table(comparison_df)

            if msrp_diff < 0:
                st.caption(f"Your price is {abs(msrp_diff_percent):.1f}% below Partner MSRP")
            elif msrp_diff > 0:
                st.caption(f"Your price is {msrp_diff_percent:.1f}% above Partner MSRP")
            else:
                st.caption("Your price matches Partner MSRP")

    # ============================================================
    # CUSTOMIZATION OPTIONS UI
    # ============================================================
    st.divider()
    st.header("4. Customization Options")

    # Customization options
    customization_info = product_data.get("Customization Info", "")
    if customization_info and customization_info.strip():
        st.markdown(f"**Customization Options:** {customization_info}")

    include_customization = st.checkbox(
        "Add customization to this product",
        value=False,
        key="input_customization",
        help="Adds setup fee and per-unit customization cost (e.g., custom labels, branding, engraving)"
    )

    # Show editable customization cost fields when customization is enabled
    if include_customization:
        st.divider()
        st.subheader("Customization Minimum Quantity")

        apply_custom_minimum = st.checkbox(
            "Apply minimum quantity for customization",
            value=False,
            key="apply_custom_minimum_checkbox",
            help="Charge for a minimum quantity of customization units even if ordering fewer items"
        )

        customization_minimum_qty = 0
        if apply_custom_minimum:
            customization_minimum_qty = st.number_input(
                "Minimum Customization Quantity",
                min_value=1,
                value=max(100, quantity),
                step=1,
                key="input_custom_minimum_qty",
                help="Minimum number of units to charge for customization"
            )

            if customization_minimum_qty > quantity:
                st.info(f"Customer will be charged for {customization_minimum_qty} customization units (ordering {quantity} product units)")
            else:
                st.caption(f"Minimum ({customization_minimum_qty}) is not higher than order quantity ({quantity}) - no effect")

        st.divider()
        st.markdown("##### Customization Costs")
        st.caption("Default values are from the spreadsheet. You can override them if needed.")

        col1, col2 = st.columns(2)

        with col1:
            default_setup_fee = clean_price(product_data.get('Customization Setup Fee', '')) or 0
            customization_setup_fee_input = st.number_input(
                "Customization Setup Fee",
                min_value=0.0,
                value=float(default_setup_fee),
                step=1.0,
                key="input_setup_fee",
                help="One-time setup fee for this customization"
            )

        with col2:
            default_per_unit = clean_price(product_data.get('Customization Cost per Unit', '')) or 0
            customization_per_unit_input = st.number_input(
                "Customization Cost per Unit",
                min_value=0.0,
                value=float(default_per_unit),
                step=0.1,
                key="input_per_unit",
                help="Additional cost per unit for customization"
            )

        # Show customization cost summary
        st.markdown("**Total Customization Cost:**")

        # Determine effective quantity for customization charges
        if apply_custom_minimum and customization_minimum_qty > quantity:
            effective_custom_qty = customization_minimum_qty
        else:
            effective_custom_qty = quantity

        customization_setup_total_preview = customization_setup_fee_input
        customization_unit_total_preview = customization_per_unit_input * effective_custom_qty
        total_customization_preview = customization_setup_total_preview + customization_unit_total_preview
        per_unit_impact = total_customization_preview / quantity if quantity > 0 else 0

        summary_data = [
            ["Setup Fee", f"${customization_setup_total_preview:.2f} (one-time)"],
            ["Per-Unit Cost", f"${customization_per_unit_input:.2f} x {effective_custom_qty} = ${customization_unit_total_preview:.2f}"],
        ]

        # Show note if minimum is applied
        if apply_custom_minimum and customization_minimum_qty > quantity:
            summary_data.append(["", ""])
            summary_data.append(["Note", f"Charging for {customization_minimum_qty} units (minimum)"])

        summary_data.extend([
            ["", ""],
            ["**Total**", f"**${total_customization_preview:.2f}**"],
            ["**Per-Unit Impact**", f"**${per_unit_impact:.2f}/unit**"]
        ])

        summary_df = pd.DataFrame(summary_data, columns=["Item", "Amount"])
        st.table(summary_df)
    else:
        customization_setup_fee_input = 0
        customization_per_unit_input = 0
        apply_custom_minimum = False
        customization_minimum_qty = 0

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # PRODUCT PREVIEW & ADD TO ORDER
    # ============================================================
    st.header("5. Product Preview")

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

    # Calculate customization costs - use user input values
    customization_setup_fee = 0
    customization_per_unit = 0

    if include_customization:
        customization_setup_fee = customization_setup_fee_input
        customization_per_unit = customization_per_unit_input

        # Apply minimum if set
        if apply_custom_minimum and customization_minimum_qty > quantity:
            effective_custom_qty = customization_minimum_qty
        else:
            effective_custom_qty = quantity
    else:
        effective_custom_qty = quantity

    # Calculate product totals (without shipping/tariff)
    product_subtotal = base_price * quantity
    customization_setup_total = customization_setup_fee
    customization_unit_total = customization_per_unit * effective_custom_qty
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
        # Parse tariff data from product
        tariff_estimate_raw = product_data.get('Tariff Estimate (if available)', '')
        default_tariff_rate = parse_tariff_rate(tariff_estimate_raw)

        # Calculate tariff base (product + markup, no customization)
        tariff_base = product_subtotal + markup_amount
        tariff_amount = calculate_product_tariff(tariff_base, default_tariff_rate)

        # Create order item
        order_item = {
            'product_name': product_data["Product/Service"],
            'product_ref': product_data.get("Purchase Description", ""),
            'partner': product_data["Partner"],
            'minimum_qty': "",  # Not in new structure
            'quantity': quantity,
            'markup_percent': markup_percent,
            'include_customization': include_customization,
            'customization_description': customization_info if customization_info else "Custom work",
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
            'product_data_row': product_data,  # Store full product row for proposal generation
            'country_of_origin': product_data.get("Country of Origin", ""),
            'tariff_rate_percent': default_tariff_rate,
            'tariff_info': product_data.get("Tariff Info", ""),
            'tariff_base': tariff_base,
            'tariff_amount': tariff_amount,
            'partner_msrp_per_unit': partner_msrp if show_msrp else 0.0,
            'show_msrp_comparison': show_msrp,
            'round_to_five': round_to_five,
            'apply_custom_minimum': apply_custom_minimum if include_customization else False,
            'customization_minimum_qty': customization_minimum_qty if (include_customization and apply_custom_minimum) else 0,
            'effective_custom_qty': effective_custom_qty if include_customization else 0,
            # NEW FIELDS for invoice/PO template
            'product_specs': product_data.get("Product Description", "").strip() or f"{product_data.get('Product/Service', '')} - {tier_range}",
            'partner_in_hands_date': None,  # To be set in UI
            'partner_cost_per_unit': base_price,  # Partner cost before markup
            'cost_verified': 'Pending',  # Default to Pending
            'sell_price_total': product_total,  # Total sell price to client
            'sell_price_per_unit': total_per_unit  # Per-unit sell price to client
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
                if apply_custom_minimum and customization_minimum_qty > quantity:
                    breakdown_items.append([f"Customization per Unit ({effective_custom_qty} units @ ${customization_per_unit:.2f}) [minimum applied]", f"${customization_per_unit:.2f}", f"${customization_unit_total:.2f}"])
                else:
                    breakdown_items.append([f"Customization per Unit ({quantity} @ ${customization_per_unit:.2f})", f"${customization_per_unit:.2f}", f"${customization_unit_total:.2f}"])

        breakdown_items.append(["**Subtotal**", f"**${subtotal_before_markup / quantity:.2f}**", f"**${subtotal_before_markup:.2f}**"])
        breakdown_items.append([f"Markup ({markup_percent}% on product only)", f"${markup_amount / quantity:.2f}", f"${markup_amount:.2f}"])
        breakdown_items.append(["**Product Total**", f"**${total_per_unit:.2f}**", f"**${product_total:.2f}**"])

        breakdown_df = pd.DataFrame(breakdown_items, columns=["Item", "Per Unit", "Total"])
        st.table(breakdown_df)

    # ============================================================
    # CURRENT ORDER SUMMARY
    # ============================================================
    st.divider()
    st.header("6. Current Order")

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
            # Calculate what will show as separate line items in deliverables
            has_customization = item.get('include_customization', False)
            customization_setup = item.get('customization_setup_total', 0) if has_customization else 0
            customization_unit = item.get('customization_unit_total', 0) if has_customization else 0

            # Count line items for display
            line_item_count = 1  # Base product
            if customization_setup > 0:
                line_item_count += 1
            if customization_unit > 0:
                line_item_count += 1

            line_count_text = f" ({line_item_count} line items)" if has_customization and line_item_count > 1 else ""

            with st.expander(f"{item['product_name']}  -  {item['quantity']} units @ ${item['total_per_unit']:.2f} each  =  ${item['product_total']:.2f}{line_count_text}"):
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
                        if has_customization:
                            customization_desc = item.get('customization_description', 'Custom work')
                            st.write(f"**Customization:** {customization_desc}")

                            # Show minimum if applied
                            if item.get('apply_custom_minimum', False):
                                custom_min = item.get('customization_minimum_qty', 0)
                                if custom_min > item['quantity']:
                                    st.write(f"**Customization Minimum:** {custom_min} units (applied)")

                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{idx}"):
                            st.session_state.edit_index = idx
                            st.rerun()

                    with col3:
                        if st.button("Remove", key=f"remove_{idx}"):
                            st.session_state.order_items.pop(idx)
                            st.rerun()

                    # Show line item breakdown - how this will appear in invoices/proposals
                    if has_customization and (customization_setup > 0 or customization_unit > 0):
                        st.write("**Line Items (as they will appear in deliverables):**")

                        # Calculate base product price (without customization)
                        base_product_only = item['product_subtotal'] + item['markup_amount']

                        line_items_display = [
                            [f"1. {item['product_name']}", item['quantity'], f"${base_product_only / item['quantity']:.2f}", f"${base_product_only:.2f}"]
                        ]

                        line_num = 2
                        if customization_setup > 0:
                            customization_desc = item.get('customization_description', 'Custom work')
                            line_items_display.append([f"{line_num}. Setup Fee: {customization_desc}", 1, f"${customization_setup:.2f}", f"${customization_setup:.2f}"])
                            line_num += 1

                        if customization_unit > 0:
                            customization_desc = item.get('customization_description', 'Custom work')
                            line_items_display.append([f"{line_num}. Customization: {customization_desc}", item['quantity'], f"${customization_unit / item['quantity']:.2f}", f"${customization_unit:.2f}"])
                            line_num += 1

                        # Add tariff line item if applicable
                        tariff_amount = item.get('tariff_amount', 0)
                        if tariff_amount > 0:
                            country = item.get('country_of_origin', 'Unknown')
                            tariff_rate = item.get('tariff_rate_percent', 0)
                            line_items_display.append([
                                f"{line_num}. Tariff ({tariff_rate}% - {country})",
                                1,
                                f"${tariff_amount:.2f}",
                                f"${tariff_amount:.2f}"
                            ])

                        line_items_display.append(["**TOTAL**", "", "", f"**${item['product_total']:.2f}**"])

                        line_items_df = pd.DataFrame(line_items_display, columns=["Item", "Qty", "Per Unit", "Total"])
                        st.table(line_items_df)
                    else:
                        st.write("**Line Item:**")
                        simple_display = pd.DataFrame([
                            {
                                "Item": item['product_name'],
                                "Qty": item['quantity'],
                                "Per Unit": f"${item['total_per_unit']:.2f}",
                                "Total": f"${item['product_total']:.2f}"
                            }
                        ])
                        st.table(simple_display)

                    # Show detailed cost breakdown with toggle
                    show_breakdown = st.checkbox("Show detailed cost breakdown", key=f"breakdown_{idx}")
                    if show_breakdown:
                        breakdown_items = [
                            ["Base Price", f"${item['base_price']:.2f}", f"${item['product_subtotal']:.2f}"]
                        ]

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

    # ============================================================
    # ORDER SETTINGS
    # ============================================================
    st.divider()
    st.header("7. Order Settings")

    if len(st.session_state.order_items) == 0:
        st.caption("Add products to your order first, then configure order settings here.")
    else:
        # Shipping
        st.subheader("Shipping")
        st.session_state.order_shipping = st.number_input(
            "Shipping Cost ($)",
            min_value=0.0,
            value=st.session_state.order_shipping,
            step=10.0,
            key="shipping_input",
            help="One-time shipping cost for the entire order (not per product)"
        )

        # Tariff Configuration
        st.divider()
        st.subheader("Tariff Configuration")

        st.markdown("""
    Tariffs are import duties based on product country of origin.
    Rates default to current estimates but can be adjusted as needed.
    """)

        # Build editable tariff table with detailed breakdown
        tariff_table_rows = []

        for idx, item in enumerate(st.session_state.order_items):
            # Get tariff base (product cost + markup, excludes customization)
            tariff_base = item.get('tariff_base', 0.0)
            tariff_base_per_unit = tariff_base / item['quantity'] if item['quantity'] > 0 else 0

            # Display product info
            st.markdown(f"**{idx + 1}. {item['product_name']}**")

            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                country = item.get('country_of_origin', 'N/A')
                st.write(f"**Country:** {country if country else 'N/A'}")
                st.write(f"**Quantity:** {item['quantity']} units")

            with col2:
                st.write(f"**Unit Cost:** ${tariff_base_per_unit:.2f}")
                st.write(f"**Total Cost:** ${tariff_base:.2f}")
                st.caption("(Product + Markup, excludes customization)")

            with col3:
                # Editable tariff rate
                current_rate = item.get('tariff_rate_percent', 0.0)
                new_rate = st.number_input(
                    "Tariff Rate (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=current_rate,
                    step=0.5,
                    key=f"tariff_rate_{idx}",
                    format="%.1f"
                )

                # Update if changed
                if new_rate != current_rate:
                    item['tariff_rate_percent'] = new_rate
                    item['tariff_amount'] = calculate_product_tariff(tariff_base, new_rate)

                tariff_amount = item.get('tariff_amount', 0.0)
                st.write(f"**Tariff Amount:** ${tariff_amount:.2f}")
                if tariff_base > 0 and new_rate > 0:
                    st.caption(f"${tariff_base:.2f} × {new_rate}% = ${tariff_amount:.2f}")

            # Show tariff info if available
            tariff_info = item.get('tariff_info', '')
            if tariff_info and tariff_info.strip():
                st.caption(f"ℹ️ {tariff_info}")

            st.markdown("")  # Spacing

        # Show total tariff
        total_tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)
        st.markdown(f"**Total Tariff for Order:** ${total_tariff:.2f}")

        st.caption("Tariff is calculated on product cost + markup (excludes customization fees and shipping)")

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
                        'custom_description': custom_description if custom_description else "Custom line item",
                        'country_of_origin': '',
                        'tariff_rate_percent': 0.0,
                        'tariff_info': '',
                        'tariff_base': 0.0,
                        'tariff_amount': 0.0
                    }

                    st.session_state.order_items.append(custom_item)
                    st.success(f"Added custom item: {custom_name}")
                    st.rerun()

    # Use session state values for calculations
    shipping = st.session_state.order_shipping
    # Calculate total tariff from all products
    tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)

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

    # ============================================================
    # ORDER NOTES
    # ============================================================
    st.divider()
    st.header("7.5. Order Notes")

    st.markdown("Add any specific details for this order (kitting specs, client requests, artwork files, etc.)")

    with st.expander("Add Order Notes", expanded=False):
        col_notes1, col_notes2 = st.columns(2)

        with col_notes1:
            st.session_state.order_notes['kitting_specs'] = st.text_area(
                "Kitting Specifications",
                value=st.session_state.order_notes.get('kitting_specs', ''),
                placeholder="Box size, packaging requirements, assembly instructions...",
                height=100,
                help="Details about how products should be kitted/packaged"
            )

            st.session_state.order_notes['client_requests'] = st.text_area(
                "Client Requests",
                value=st.session_state.order_notes.get('client_requests', ''),
                placeholder="Rush delivery, special handling, custom messaging...",
                height=100,
                help="Special requests from the client"
            )

            st.session_state.order_notes['addon_samples'] = st.text_area(
                "Add-on Samples",
                value=st.session_state.order_notes.get('addon_samples', ''),
                placeholder="Extra units for display, samples for approval...",
                height=100,
                help="Additional samples to include with order"
            )

        with col_notes2:
            st.session_state.order_notes['artwork_attachments'] = st.text_area(
                "Artwork Attachments",
                value=st.session_state.order_notes.get('artwork_attachments', ''),
                placeholder="logo_final.ai, label_design_v3.pdf...",
                height=100,
                help="List of artwork files attached to this order"
            )

            st.session_state.order_notes['general_notes'] = st.text_area(
                "General Notes",
                value=st.session_state.order_notes.get('general_notes', ''),
                placeholder="Any other important details...",
                height=100,
                help="Catch-all for any other notes or details"
            )

    # ============================================================
    # TOTAL ORDER CALCULATION
    # ============================================================
    st.divider()
    st.header("8. Order Summary")

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

        # Add tariff for each product (if > 0)
        for item in st.session_state.order_items:
            tariff_amount = item.get('tariff_amount', 0)
            if tariff_amount > 0:
                country = item.get('country_of_origin', 'Unknown')
                tariff_rate = item.get('tariff_rate_percent', 0)
                summary_items.append([
                    f"Tariff: {item['product_name']} ({tariff_rate}% - {country})",
                    "",
                    "",
                    f"${tariff_amount:.2f}"
                ])

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

    # ============================================================
    # NEXT STEP: GENERATE INVOICE & PURCHASE ORDER
    # ============================================================
    st.divider()
    st.success("Order complete! Your order summary is ready.")
    st.info("Go to **Tab 3: Execution & Accounting** to generate Invoice & Purchase Order for this order.")

# ============================================================
# TAB 3: EXECUTION & ACCOUNTING
# ============================================================
with tab3:
    st.header("Execution & Accounting - Invoice & Purchase Order Management")
    st.caption("Generate invoices and purchase orders for confirmed orders")
    st.divider()

    # Check if order exists in Tab 2
    if len(st.session_state.order_items) == 0:
        st.info("No order found. Please build an order in Tab 2 first.")
        st.markdown("### To create an invoice/PO:")
        st.markdown("1. Go to **Tab 2: Order & Client Info**")
        st.markdown("2. Complete Sections 1-8 (client info, products, settings, summary)")
        st.markdown("3. Return to this tab to generate Invoice/PO")
    else:
        # ============================================================
        # SECTION 1: ORDER SUMMARY PREVIEW
        # ============================================================
        st.subheader("1. Order Summary")

        # Quick summary display
        total_products = len(st.session_state.order_items)
        total_units = sum(item['quantity'] for item in st.session_state.order_items)

        # Calculate order total (same logic as Tab 2)
        products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)

        # Get discount info
        discount_percent = 0.0
        discount_description = ""
        if st.session_state.order_discount_type == "preset":
            preset = st.session_state.order_discount_preset
            discount_description = preset
            if "(" in preset and "%" in preset:
                percent_str = preset.split("(")[1].split("%")[0]
                discount_percent = float(percent_str)
        elif st.session_state.order_discount_type == "custom":
            discount_percent = st.session_state.order_discount_custom_value
            discount_description = st.session_state.order_discount_custom_desc if st.session_state.order_discount_custom_desc else f"Custom Discount ({discount_percent}%)"

        discount_amount = products_subtotal * (discount_percent / 100)
        subtotal_after_discount = products_subtotal - discount_amount

        # Add shipping and tariff
        shipping = st.session_state.order_shipping
        tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)

        total_before_cc = subtotal_after_discount + shipping + tariff
        cc_fee_amount = calculate_credit_card_fee(total_before_cc, st.session_state.apply_cc_fee, st.session_state.cc_fee_percent)
        total_quote = total_before_cc + cc_fee_amount
        total_quote = apply_marketing_rounding(total_quote, st.session_state.order_use_marketing_rounding)

        # Display quick summary
        client_name = st.session_state.client_info.get('company_name', 'Not specified')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Client", client_name)
        with col2:
            st.metric("Products", f"{total_products} items ({total_units} units)")
        with col3:
            st.metric("Total Quote", f"${total_quote:,.2f}")

        st.divider()

        # ============================================================
        # SECTION 2: COMPLETENESS CHECK
        # ============================================================
        st.subheader("2. Completeness Check")

        client_info = st.session_state.client_info
        validation_warnings = validate_invoice_completeness(client_info, st.session_state.order_items)

        if validation_warnings:
            with st.expander("Validation Warnings - Click to Review", expanded=True):
                st.warning("The following fields are missing or incomplete. The invoice/PO can still be generated, but these should be completed before sending to the bookkeeper:")
                for warning in validation_warnings:
                    st.write(f"- {warning}")
        else:
            st.success("All required fields complete - ready to generate Invoice/PO")

        st.divider()

        # ============================================================
        # EDITABLE ORDER SUMMARY
        # ============================================================
        with st.expander("View/Edit Order Summary", expanded=False):
            st.markdown("### Order Summary (Editable)")
            st.markdown("Make quick adjustments to order settings here. Changes sync to Tab 2.")

            # Shipping
            st.subheader("Shipping & Additional Costs")
            col1, col2 = st.columns(2)

            with col1:
                new_shipping = st.number_input(
                    "Shipping Cost ($)",
                    min_value=0.0,
                    value=st.session_state.order_shipping,
                    step=10.0,
                    key="tab3_shipping_edit"
                )

                if new_shipping != st.session_state.order_shipping:
                    st.session_state.order_shipping = new_shipping
                    st.success("Shipping updated")

            with col2:
                # Show tariff total (read-only, calculated from products)
                total_tariff = sum(item.get('tariff_amount', 0) for item in st.session_state.order_items)
                st.metric("Total Tariff", f"${total_tariff:.2f}")
                st.caption("Tariff calculated from product origins. Edit per-product in Tab 2.")

            st.divider()

            # Discount
            st.subheader("Discount")

            discount_type = st.selectbox(
                "Discount Type",
                options=["none", "preset", "custom"],
                format_func=lambda x: {"none": "No Discount", "preset": "Preset (NGO 5%)", "custom": "Custom Amount"}[x],
                index=["none", "preset", "custom"].index(st.session_state.order_discount_type),
                key="tab3_discount_type"
            )

            if discount_type != st.session_state.order_discount_type:
                st.session_state.order_discount_type = discount_type
                st.success("Discount type updated")

            if discount_type == "preset":
                st.session_state.order_discount_preset = "NGO Discount (5%)"
                st.info("NGO Discount: 5% applied to products subtotal")
            elif discount_type == "custom":
                custom_discount = st.number_input(
                    "Custom Discount ($)",
                    min_value=0.0,
                    value=st.session_state.get('order_discount_custom_value', 0.0),
                    step=10.0,
                    key="tab3_custom_discount"
                )

                if custom_discount != st.session_state.get('order_discount_custom_value', 0.0):
                    st.session_state.order_discount_custom_value = custom_discount
                    st.success("Custom discount updated")

            st.divider()

            # Credit Card Fee
            st.subheader("Payment Processing")

            apply_cc_fee = st.checkbox(
                "Apply Credit Card Processing Fee",
                value=st.session_state.get('apply_cc_fee', False),
                key="tab3_cc_fee_checkbox"
            )

            if apply_cc_fee != st.session_state.get('apply_cc_fee', False):
                st.session_state.apply_cc_fee = apply_cc_fee
                st.success("CC fee setting updated")

            if apply_cc_fee:
                cc_fee_percent = st.number_input(
                    "CC Fee (%)",
                    min_value=0.0,
                    max_value=10.0,
                    value=st.session_state.get('cc_fee_percent', 2.9),
                    step=0.1,
                    key="tab3_cc_fee_percent"
                )

                if cc_fee_percent != st.session_state.get('cc_fee_percent', 2.9):
                    st.session_state.cc_fee_percent = cc_fee_percent
                    st.success("CC fee percentage updated")

            st.divider()

            # Calculate and display totals
            st.subheader("Order Totals")

            # Calculate same as Tab 2 Section 8
            products_subtotal = sum(item['product_total'] for item in st.session_state.order_items)

            # Shipping
            shipping_total = st.session_state.order_shipping

            # Tariff
            tariff_total = sum(item.get('tariff_amount', 0) for item in st.session_state.order_items)

            # Discount
            discount_amount = 0.0
            if st.session_state.order_discount_type == "preset":
                discount_amount = products_subtotal * 0.05
            elif st.session_state.order_discount_type == "custom":
                discount_amount = st.session_state.get('order_discount_custom_value', 0.0)

            # Subtotal before CC fee
            subtotal_before_cc = products_subtotal + shipping_total + tariff_total - discount_amount

            # CC fee
            cc_fee_amount = 0.0
            if st.session_state.get('apply_cc_fee', False):
                cc_fee_amount = calculate_credit_card_fee(
                    subtotal_before_cc,
                    st.session_state.get('cc_fee_percent', 2.9)
                )

            # Final total
            final_total = subtotal_before_cc + cc_fee_amount

            # Marketing rounding
            if st.session_state.get('order_use_marketing_rounding', False):
                final_total = apply_marketing_rounding(final_total)

            # Display breakdown
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Products Subtotal:** ${products_subtotal:,.2f}")
                st.write(f"**Shipping:** ${shipping_total:,.2f}")
                st.write(f"**Tariff:** ${tariff_total:,.2f}")
                st.write(f"**Discount:** -${discount_amount:,.2f}")

            with col2:
                st.write(f"**Subtotal:** ${subtotal_before_cc:,.2f}")
                if cc_fee_amount > 0:
                    st.write(f"**CC Fee ({st.session_state.get('cc_fee_percent', 2.9)}%):** ${cc_fee_amount:,.2f}")
                st.write(f"**TOTAL:** ${final_total:,.2f}")

            st.info("Changes made here automatically sync to Tab 2.")

        st.divider()

        # ============================================================
        # SECTION 3: INVOICE & PURCHASE ORDER GENERATION
        # ============================================================
        st.subheader("3. Generate Invoice & Purchase Order")

        st.markdown("### INVOICE AND PURCHASE ORDER REQUEST FORM")

        # === HEADER SECTION ===
        st.markdown("#### Header Information")

        col1, col2 = st.columns(2)
        with col1:
            company_status = "New" if client_info.get('is_new_client', False) else "Existing"
            st.write(f"**Company:** {client_info.get('company_name', 'Not specified')} ({company_status})")
            st.write(f"**Contact + Email:** {client_info.get('contact_name', 'Not specified')} ({client_info.get('contact_email', 'Not specified')})")

            if client_info.get('is_new_client', False) and client_info.get('billing_address'):
                st.write(f"**IF NEW - Billing Address:** {client_info['billing_address']}")

            po_number = client_info.get('client_po', 'N/A')
            st.write(f"**Client PO #:** {po_number}")

        with col2:
            order_submitted_by = client_info.get('order_submitted_by', 'Not specified')
            order_submitted_date = client_info.get('order_submitted_date', datetime.now().date())
            st.write(f"**Order Submitted by:** {order_submitted_by}")
            st.write(f"**Date:** {order_submitted_date}")

            cost_submitted_by = client_info.get('cost_submitted_by', 'Not specified')
            cost_submitted_date = client_info.get('cost_submitted_date', 'Not specified')
            st.write(f"**Cost Submitted by:** {cost_submitted_by}")
            st.write(f"**Date:** {cost_submitted_date if cost_submitted_date else 'Not specified'}")

        st.markdown("---")

        # === PARTNER(S) + POC SECTION ===
        st.markdown("**Partner(s) + POC:**")

        # Get unique partners from order items
        partners_in_order = list(set(item['partner'] for item in st.session_state.order_items if not item.get('is_custom', False)))

        if partners_in_order and hasattr(st.session_state, 'partner_contacts'):
            for partner_name in partners_in_order:
                partner_contact = st.session_state.partner_contacts.get(partner_name, {})
                poc_name = partner_contact.get('poc_name', 'Not specified')
                poc_email = partner_contact.get('poc_email', 'Not specified')
                st.write(f"- {partner_name} - {poc_name} ({poc_email})")
        else:
            st.write("No partners in order")

        st.markdown("---")

        # === DELIVERY & PAYMENT DETAILS ===
        col3, col4 = st.columns(2)
        with col3:
            client_in_hands = client_info.get('client_in_hands_date', 'Not specified')
            st.write(f"**Client In-Hands Date:** {client_in_hands}")
            st.write(f"**Payment Terms:** {client_info.get('payment_timeline', 'Not specified')}")

        with col4:
            ship_method = client_info.get('shipping_type', 'Not specified')
            st.write(f"**Ship Method:** {ship_method}")
            st.write(f"**Payment Method:** {client_info.get('payment_preference', 'Not specified')}")

        st.divider()

        # === ITEMIZED TABLE SECTION ===
        st.markdown("#### INVOICE AND PURCHASE ORDER ITEM DETAILS")
        st.caption("""
        This cost-to-sell segment outlines our partners' cost, our sell price to client,
        and our partners' requested in-hands date. Our in-hands date for clients may be
        later than the in-hands date to Peace by Piece for kitting purposes.
        """)

        # Build line items table in NEW template format
        invoice_line_items = []
        for item in st.session_state.order_items:
            # Check if custom item
            if item.get('is_custom', False):
                partner = "Custom"
                items_specs = item.get('custom_description', 'Custom line item')
                partner_in_hands = "N/A"
                cost = f"${item.get('total_per_unit', 0):.2f}"
                cost_verified = "N/A"
                sell_price = f"${item.get('product_total', 0):.2f}"

                invoice_line_items.append({
                    'PARTNER': partner,
                    'ITEMS + SPECS': items_specs,
                    'QTY': item['quantity'],
                    'IN-HANDS from Partner': partner_in_hands,
                    'COST': cost,
                    'COST VERIFIED?': cost_verified,
                    'SELL PRICE': sell_price
                })
            else:
                # Regular product
                partner = item['partner']
                product_name = item['product_name']
                product_specs = item.get('product_specs', item.get('tier_range', ''))
                items_specs = f"{product_name}\n{product_specs}"

                partner_in_hands = item.get('partner_in_hands_date', 'TBD')
                if partner_in_hands and partner_in_hands != 'TBD':
                    partner_in_hands = str(partner_in_hands)

                # Partner cost (before markup)
                partner_cost = item.get('partner_cost_per_unit', item.get('base_price', 0))
                cost = f"${partner_cost:.2f}"

                cost_verified = item.get('cost_verified', 'Pending')

                # Sell price (total to client for this line)
                sell_price_total = item.get('sell_price_total', item.get('product_total', 0))
                sell_price = f"${sell_price_total:.2f}"

                # Add base product line
                invoice_line_items.append({
                    'PARTNER': partner,
                    'ITEMS + SPECS': items_specs,
                    'QTY': item['quantity'],
                    'IN-HANDS from Partner': partner_in_hands,
                    'COST': cost,
                    'COST VERIFIED?': cost_verified,
                    'SELL PRICE': sell_price
                })

                # Add customization line items if present
                if item.get('include_customization', False):
                    customization_desc = item.get('customization_description', 'Custom work')
                    customization_setup = item.get('customization_setup_total', 0)
                    customization_unit_total = item.get('customization_unit_total', 0)
                    customization_per_unit = item.get('customization_per_unit', 0)

                    # Setup fee line item
                    if customization_setup > 0:
                        invoice_line_items.append({
                            'PARTNER': partner,
                            'ITEMS + SPECS': f"Setup Fee: {customization_desc}",
                            'QTY': 1,
                            'IN-HANDS from Partner': partner_in_hands,
                            'COST': f"${customization_setup:.2f}",
                            'COST VERIFIED?': cost_verified,
                            'SELL PRICE': f"${customization_setup:.2f}"
                        })

                    # Per-unit customization line item
                    if customization_unit_total > 0:
                        invoice_line_items.append({
                            'PARTNER': partner,
                            'ITEMS + SPECS': f"Customization: {customization_desc}",
                            'QTY': item['quantity'],
                            'IN-HANDS from Partner': partner_in_hands,
                            'COST': f"${customization_per_unit:.2f}",
                            'COST VERIFIED?': cost_verified,
                            'SELL PRICE': f"${customization_unit_total:.2f}"
                        })

                # Add tariff line item if applicable
                if item.get('tariff_amount', 0) > 0:
                    tariff_amount = item.get('tariff_amount', 0)
                    tariff_rate = item.get('tariff_rate_percent', 0)

                    invoice_line_items.append({
                        'PARTNER': partner,
                        'ITEMS + SPECS': f"Tariff ({tariff_rate}%)",
                        'QTY': 1,
                        'IN-HANDS from Partner': "N/A",
                        'COST': f"${tariff_amount:.2f}",
                        'COST VERIFIED?': "Yes",
                        'SELL PRICE': f"${tariff_amount:.2f}"
                    })

        # Display line items table
        invoice_df = pd.DataFrame(invoice_line_items)
        st.table(invoice_df)

        # Display totals section
        st.write("")  # Spacing
        st.markdown("**Summary Totals:**")
        totals_data = [
            ["Subtotal", f"${products_subtotal:.2f}"]
        ]

        # Add discount line if applicable
        if discount_percent > 0:
            totals_data.append([f"Discount ({discount_description})", f"-${discount_amount:.2f}"])

        totals_data.append(["Shipping", f"${shipping:.2f}"])

        # Tariff is already in line items, so we show it separately
        if tariff > 0:
            totals_data.append(["Tariff", f"${tariff:.2f}"])

        # Add credit card fee if applicable
        if st.session_state.apply_cc_fee and cc_fee_amount > 0:
            totals_data.append([f"Credit Card Fee ({st.session_state.cc_fee_percent}%)", f"${cc_fee_amount:.2f}"])

        totals_data.append(["**TOTAL**", f"**${total_quote:.2f}**"])

        totals_df = pd.DataFrame(totals_data, columns=["Item", "Amount"])
        st.table(totals_df)

        st.divider()

        # === NOTES SECTION ===
        st.markdown("#### NOTES")
        st.caption("""
        Enter any specific details, kitting specs, client requests, add-on samples for
        Peace by Piece to be added to purchase orders. Remember to attach titled artwork
        that matches your purchase order request and any additional spec sheets for our partners.
        """)

        order_notes = st.session_state.order_notes

        # Display notes if any are filled
        notes_content = []
        if order_notes.get('kitting_specs'):
            notes_content.append(f"**Kitting Specs:**\n{order_notes['kitting_specs']}")
        if order_notes.get('client_requests'):
            notes_content.append(f"**Client Requests:**\n{order_notes['client_requests']}")
        if order_notes.get('addon_samples'):
            notes_content.append(f"**Add-on Samples:**\n{order_notes['addon_samples']}")
        if order_notes.get('artwork_attachments'):
            notes_content.append(f"**Artwork Attachments:**\n{order_notes['artwork_attachments']}")
        if order_notes.get('general_notes'):
            notes_content.append(f"**General Notes:**\n{order_notes['general_notes']}")

        if notes_content:
            for note in notes_content:
                st.markdown(note)
        else:
            st.caption("No notes added")

        st.divider()

        # === DOWNLOAD SECTION ===
        st.markdown("#### Download Invoice & Purchase Order")

        # Add download button for complete invoice/PO
        # Combine line items and totals into one downloadable file
        invoice_complete = invoice_df.copy()

        # Add blank row
        blank_row = pd.DataFrame([{col: "" for col in invoice_df.columns}])
        invoice_complete = pd.concat([invoice_complete, blank_row], ignore_index=True)

        # Add totals section (map to new column names)
        for total_item in totals_data:
            total_row = pd.DataFrame([{
                'PARTNER': '',
                'ITEMS + SPECS': total_item[0],
                'QTY': '',
                'IN-HANDS from Partner': '',
                'COST': '',
                'COST VERIFIED?': '',
                'SELL PRICE': total_item[1]
            }])
            invoice_complete = pd.concat([invoice_complete, total_row], ignore_index=True)

        # Add notes section
        notes_row = pd.DataFrame([{
            'PARTNER': '',
            'ITEMS + SPECS': '',
            'QTY': '',
            'IN-HANDS from Partner': '',
            'COST': '',
            'COST VERIFIED?': '',
            'SELL PRICE': ''
        }])
        invoice_complete = pd.concat([invoice_complete, notes_row], ignore_index=True)

        # Add notes content
        if notes_content:
            for note in notes_content:
                notes_row = pd.DataFrame([{
                    'PARTNER': '',
                    'ITEMS + SPECS': note.replace('**', '').replace('\n', ' '),
                    'QTY': '',
                    'IN-HANDS from Partner': '',
                    'COST': '',
                    'COST VERIFIED?': '',
                    'SELL PRICE': ''
                }])
                invoice_complete = pd.concat([invoice_complete, notes_row], ignore_index=True)

        invoice_csv = invoice_complete.to_csv(index=False)
        st.download_button(
            label="Download Invoice & Purchase Order (CSV)",
            data=invoice_csv,
            file_name=f"invoice_po_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_invoice_po_complete"
        )

        st.caption("Download the CSV and send to bookkeeper, or copy the tables above into your template.")

        st.divider()

        # ============================================================
        # SECTION 4: ACCOUNTING EXPORT (FUTURE)
        # ============================================================
        st.subheader("4. Export for Accounting")
        st.caption("Future: QuickBooks export, accounting reports, etc.")
        st.info("Accounting export features will be added in Phase 4")
