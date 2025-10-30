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
            # Show placeholder text if quantity is empty
            quantity_display = quantity if quantity else '<span style="color: #7f8c8d; font-style: italic;">[Input Qty]</span>'
            html_form += f"""
        <tr>
            <td class="product-table">{product_name}</td>
            <td class="product-table">{quantity_display}</td>
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
    st.header("Order & Client Info - Input Order & Client Details")
    st.divider()

    # ============================================================
    # PROPOSAL PRODUCTS SELECTION (if available)
    # ============================================================
    if len(st.session_state.proposal_products) > 0:
        st.header("Option A: Import Products from Proposal")
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
    # PARTNER & PRODUCT SELECTION
    # ============================================================
    st.header("Option B: Manual Product Selection")
    st.caption("Add products to your order, then configure settings for each product below")

    # Create dropdowns for filtering
    col1, col2 = st.columns([2, 1])

    with col1:
        col_partner, col_product = st.columns(2)

        with col_partner:
            # Partner dropdown (using "Partner" column from Template sheet)
            partners = sorted(df_template["Partner"].unique().tolist())
            selected_partner = st.selectbox("Select Partner", partners, key="add_partner_select")

        with col_product:
            # Filter products based on partner selection (using "Product/Service" column)
            available_products = df_template[df_template["Partner"] == selected_partner]["Product/Service"].unique().tolist()
            selected_product = st.selectbox("Select Product/Service", available_products, key="add_product_select")

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Add to Order", type="primary", use_container_width=True):
            # Get selected product details
            product_data = df_template[
                (df_template["Partner"] == selected_partner) &
                (df_template["Product/Service"] == selected_product)
            ].iloc[0]

            # Get default customization costs from spreadsheet
            default_setup_fee = clean_price(product_data.get('Customization Setup Fee', '')) or 0.0
            default_per_unit = clean_price(product_data.get('Customization Cost per Unit', '')) or 0.0

            # Add product with defaults
            new_item = {
                'product_name': product_data.get('Product/Service', 'Unknown Product'),
                'partner': product_data.get('Partner', 'Unknown Partner'),
                'product_data': product_data.to_dict(),
                'quantity': 1,
                'markup_percent': 100.0,
                'include_customization': False,
                'customization_setup_fee': float(default_setup_fee),
                'customization_per_unit': float(default_per_unit),
                'customization_minimum_qty': 0,
                'apply_custom_minimum': False,
                'include_tariff': False,
                'is_custom': False
            }

            # Calculate pricing for this item (will be recalculated when edited)
            base_price, tier_range, tier_column = get_unit_price_new_system(product_data, 1)

            if base_price:
                # Add calculated fields
                new_item.update({
                    'base_price': base_price,
                    'tier_range': tier_range,
                    'tier_column': tier_column,
                    'product_ref': product_data.get('Partner Product SKU/REF', 'N/A'),
                    'country_of_origin': product_data.get('Country of Origin', 'N/A'),
                    'customization_description': product_data.get('Customization Info', ''),
                    'product_subtotal': base_price * 1,
                    'customization_setup_total': 0.0,
                    'customization_unit_total': 0.0,
                    'subtotal_before_markup': base_price * 1,
                    'markup_amount': (base_price * 1) * (100.0 / 100),
                    'product_total': (base_price * 1) + ((base_price * 1) * (100.0 / 100)),
                    'total_per_unit': ((base_price * 1) + ((base_price * 1) * (100.0 / 100))) / 1,
                    'tariff_rate_percent': 0.0,
                    'tariff_amount': 0.0
                })

                st.session_state.order_items.append(new_item)
                st.rerun()
            else:
                st.error("Could not determine pricing for this product")

    # Show product details in expander
    product_data_preview = df_template[
        (df_template["Partner"] == selected_partner) &
        (df_template["Product/Service"] == selected_product)
    ].iloc[0]

    origin = product_data_preview.get("Country of Origin", "N/A")
    has_tiers = product_data_preview.get("Pricing Tiers (Y/N)", "N/A")

    with st.expander("Show Product Details"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Partner:** {product_data_preview['Partner']}")
            st.markdown(f"**Product/Service:** {product_data_preview['Product/Service']}")
        with col2:
            st.markdown(f"**Country of Origin:** {origin if origin else 'N/A'}")
            st.markdown(f"**Tiered Pricing:** {has_tiers}")

        # Show product description if available
        description = product_data_preview.get("Marketing Description", "")
        if description and description.strip():
            st.markdown("---")
            st.markdown("**Marketing Description:**")
            st.write(description)

        # Show pricing tier info if applicable
        tier_info = product_data_preview.get("Pricing Tiers Info", "")
        if tier_info and tier_info.strip() and tier_info != "NA":
            st.markdown("---")
            st.markdown("**Pricing Tier Information:**")
            st.markdown("This product uses tiered pricing - the price per unit decreases as you order more. The tier ranges below show which price applies based on your order quantity.")
            st.markdown("")
            st.markdown(f"**Tier Ranges:** {tier_info}")
            st.caption("Your order quantity will automatically match to the correct tier and price.")

    st.divider()

    # ============================================================
    # CURRENT ORDER (with inline editing)
    # ============================================================
    st.header("2. Current Order")

    if len(st.session_state.order_items) == 0:
        st.info("No products in order yet. Add products above to get started.")
    else:
        st.caption("Edit settings for each product below. Changes update totals in real-time.")
        st.write("")

        # Iterate through order items and display editable cards
        items_to_remove = []

        for idx, item in enumerate(st.session_state.order_items):
            # Skip custom items for now (they have different structure)
            if item.get('is_custom', False):
                st.write("---")
                st.subheader(f"{item['product_name']}")
                st.caption(f"Custom Line Item")

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**Description:** {item.get('custom_description', 'N/A')}")
                    st.write(f"**Quantity:** {item['quantity']} | **Unit Price:** ${item['total_per_unit']:.2f} | **Total:** ${item['product_total']:.2f}")
                with col2:
                    if st.button("Remove", key=f"remove_custom_{idx}", type="secondary"):
                        items_to_remove.append(idx)
                continue

            # Regular product card
            st.write("---")

            # Header with product name and remove button
            col_header, col_remove = st.columns([5, 1])
            with col_header:
                st.subheader(f"{item['product_name']}")
                st.caption(f"Partner: {item['partner']} | Origin: {item.get('country_of_origin', 'N/A')}")
            with col_remove:
                if st.button("Remove", key=f"remove_product_{idx}", type="secondary"):
                    items_to_remove.append(idx)

            # Get product data for recalculations
            product_data = item['product_data']

            # QUANTITY & PRICING SECTION
            st.markdown("##### Quantity & Pricing")

            col_qty, col_markup = st.columns(2)

            with col_qty:
                new_quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    value=item['quantity'],
                    step=1,
                    key=f"prod_qty_{idx}",
                    help="Number of units to order"
                )

                # Highlight if quantity is 1 (warning)
                if new_quantity == 1:
                    st.warning("Quantity is 1 - did you mean to order more?")

                # Show tier info
                base_price, tier_range, tier_column = get_unit_price_new_system(product_data, new_quantity)
                if tier_range == "No Tiers":
                    st.caption(f"Flat pricing: ${base_price:.2f} per unit")
                else:
                    st.caption(f"Using tier: {tier_range} units | ${base_price:.2f}/unit")

            with col_markup:
                new_markup = st.number_input(
                    "Markup %",
                    min_value=0.0,
                    value=item['markup_percent'],
                    step=5.0,
                    key=f"prod_markup_{idx}",
                    help="Your profit margin. 100% = double the cost (2x)"
                )

                # Calculate and show client price (base + markup, before customization)
                if base_price:
                    product_subtotal_calc = base_price * new_quantity
                    markup_amount_calc = product_subtotal_calc * (new_markup / 100)
                    client_price_raw = product_subtotal_calc + markup_amount_calc
                    client_price_per_unit = client_price_raw / new_quantity

                    st.caption(f"Client price: ${client_price_per_unit:.2f}/unit (before customization)")

            # CUSTOMIZATION SECTION (always available)
            customization_info = product_data.get("Customization Info", "")
            st.markdown("##### Customization (Optional)")
            if customization_info and customization_info.strip():
                st.caption(f"Available: {customization_info}")
            else:
                st.caption("No customization details from spreadsheet - set custom values below if needed")

            new_include_custom = st.checkbox(
                "Include Customization",
                value=item.get('include_customization', False),
                key=f"prod_custom_{idx}"
            )

            if new_include_custom:
                    col_setup, col_perunit = st.columns(2)

                    with col_setup:
                        # Always read default from product_data, use item value if user has edited it
                        default_setup = clean_price(product_data.get('Customization Setup Fee', '')) or 0.0
                        stored_setup = item.get('customization_setup_fee', 0.0)
                        # Use stored value if it's non-zero OR if no default exists, otherwise use default
                        display_setup = stored_setup if (stored_setup > 0 or default_setup == 0) else default_setup

                        new_setup_fee = st.number_input(
                            "Setup Fee",
                            min_value=0.0,
                            value=float(display_setup),
                            step=1.0,
                            key=f"prod_setup_{idx}"
                        )

                    with col_perunit:
                        # Always read default from product_data, use item value if user has edited it
                        default_perunit = clean_price(product_data.get('Customization Cost per Unit', '')) or 0.0
                        stored_perunit = item.get('customization_per_unit', 0.0)
                        # Use stored value if it's non-zero OR if no default exists, otherwise use default
                        display_perunit = stored_perunit if (stored_perunit > 0 or default_perunit == 0) else default_perunit

                        new_perunit_cost = st.number_input(
                            "Per-Unit Cost",
                            min_value=0.0,
                            value=float(display_perunit),
                            step=0.1,
                            key=f"prod_perunit_{idx}"
                        )

                    # Customization minimum
                    new_apply_minimum = st.checkbox(
                        "Apply minimum quantity for customization",
                        value=item.get('apply_custom_minimum', False),
                        key=f"prod_apply_min_{idx}",
                        help="Charge for minimum units even if ordering fewer"
                    )

                    if new_apply_minimum:
                        # Get stored minimum or default to max(100, current_quantity)
                        stored_min = item.get('customization_minimum_qty', 0)
                        default_min = max(100, new_quantity)
                        display_min = stored_min if stored_min > 0 else default_min

                        new_custom_min_qty = st.number_input(
                            "Minimum Customization Quantity",
                            min_value=1,
                            value=display_min,
                            step=1,
                            key=f"prod_min_qty_{idx}"
                        )

                        if new_custom_min_qty > new_quantity:
                            st.info(f"Charging for {new_custom_min_qty} customization units (ordering {new_quantity} product units)")
                    else:
                        new_custom_min_qty = 0
            else:
                new_setup_fee = 0.0
                new_perunit_cost = 0.0
                new_apply_minimum = False
                new_custom_min_qty = 0

            # RECALCULATE PRICING
            # Get base price for new quantity
            base_price, tier_range, tier_column = get_unit_price_new_system(product_data, new_quantity)

            if base_price:
                # Calculate customization costs
                if new_include_custom:
                    effective_custom_qty = new_custom_min_qty if (new_apply_minimum and new_custom_min_qty > new_quantity) else new_quantity
                    customization_setup_total = new_setup_fee
                    customization_unit_total = new_perunit_cost * effective_custom_qty
                else:
                    customization_setup_total = 0.0
                    customization_unit_total = 0.0

                # Calculate totals
                product_subtotal = base_price * new_quantity
                subtotal_before_markup = product_subtotal + customization_setup_total + customization_unit_total
                markup_amount = product_subtotal * (new_markup / 100)
                product_total = subtotal_before_markup + markup_amount
                total_per_unit = product_total / new_quantity

                # Update item in session state
                st.session_state.order_items[idx].update({
                    'quantity': new_quantity,
                    'markup_percent': new_markup,
                    'include_customization': new_include_custom,
                    'customization_setup_fee': new_setup_fee,
                    'customization_per_unit': new_perunit_cost,
                    'apply_custom_minimum': new_apply_minimum,
                    'customization_minimum_qty': new_custom_min_qty,
                    'base_price': base_price,
                    'tier_range': tier_range,
                    'tier_column': tier_column,
                    'product_subtotal': product_subtotal,
                    'customization_setup_total': customization_setup_total,
                    'customization_unit_total': customization_unit_total,
                    'subtotal_before_markup': subtotal_before_markup,
                    'markup_amount': markup_amount,
                    'product_total': product_total,
                    'total_per_unit': total_per_unit
                })

                # PRICING BREAKDOWN DISPLAY
                st.markdown("##### Pricing Breakdown")

                breakdown_data = []

                # Base product cost and markup (together)
                breakdown_data.append(["Base Cost (Partner)", f"${base_price:.2f}/unit", f"${product_subtotal:.2f}"])
                breakdown_data.append([f"Your Markup ({new_markup:.0f}%)", f"${markup_amount/new_quantity:.2f}/unit", f"${markup_amount:.2f}"])
                breakdown_data.append(["", "", ""])

                # Product price to customer (before customization)
                product_price_to_client = product_subtotal + markup_amount
                breakdown_data.append(["Product Price to Client", f"${product_price_to_client/new_quantity:.2f}/unit", f"${product_price_to_client:.2f}"])

                # Customization (added separately, no markup)
                if customization_setup_total > 0 or customization_unit_total > 0:
                    breakdown_data.append(["", "", ""])

                if customization_setup_total > 0:
                    breakdown_data.append(["Customization Setup", "one-time", f"${customization_setup_total:.2f}"])

                if customization_unit_total > 0:
                    # Calculate effective quantity for customization
                    effective_custom_qty = new_custom_min_qty if (new_apply_minimum and new_custom_min_qty > new_quantity) else new_quantity

                    # Show per-unit cost with quantity used
                    if new_apply_minimum and new_custom_min_qty > new_quantity:
                        perunit_display = f"${new_perunit_cost:.2f}/unit × {effective_custom_qty} units"
                    else:
                        perunit_display = f"${new_perunit_cost:.2f}/unit"

                    breakdown_data.append(["Customization Per-Unit", perunit_display, f"${customization_unit_total:.2f}"])

                # Final customer price
                breakdown_data.append(["", "", ""])
                breakdown_data.append(["**Customer Price**", f"**${total_per_unit:.2f}/unit**", f"**${product_total:.2f}**"])

                breakdown_df = pd.DataFrame(breakdown_data, columns=["Item", "Per Unit", "Total"])
                st.table(breakdown_df)

                # Add note if minimum customization quantity is applied
                if new_include_custom and new_apply_minimum and new_custom_min_qty > new_quantity:
                    st.caption(f"Note: Customization minimum of {new_custom_min_qty} units applied (ordering {new_quantity} product units)")

        # Remove items marked for deletion
        for idx in sorted(items_to_remove, reverse=True):
            st.session_state.order_items.pop(idx)

        if items_to_remove:
            st.rerun()

        st.write("---")

        # Clear order button
        if st.button("Clear Entire Order", type="secondary"):
            st.session_state.order_items = []
            st.rerun()

    # ============================================================
    # ORDER SETTINGS
    # ============================================================
    st.divider()
    st.header("3. Order Settings")

    if len(st.session_state.order_items) == 0:
        st.caption("Add products to your order first, then configure order settings here.")
    else:
        # Shipping & Tariffs - Side by Side
        st.subheader("Shipping & Tariffs")

        col_shipping, col_tariff = st.columns(2)

        with col_shipping:
            st.session_state.order_shipping = st.number_input(
                "Shipping Cost ($)",
                min_value=0.0,
                value=st.session_state.order_shipping,
                step=10.0,
                key="shipping_input",
                help="One-time shipping cost for the entire order (not per product)"
            )

        with col_tariff:
            # Calculate total tariff for expander label
            total_tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)

            with st.expander(f"Tariff Configuration (Total: ${total_tariff:.2f})", expanded=False):
                st.caption("Default rates applied based on country of origin. Expand to customize per product.")
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

                st.caption("Tariff is calculated on product cost + markup (excludes customization fees and shipping)")

        # Order Adjustments - Consolidated Section
        st.divider()
        st.subheader("Order Adjustments")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Discount as dropdown (like in Proposals tab)
            discount_options = ["None", "NGO (5%)", "Custom"]
            current_discount = "None"
            if st.session_state.order_discount_type == "preset":
                current_discount = "NGO (5%)"
            elif st.session_state.order_discount_type == "custom":
                current_discount = "Custom"

            discount_selection = st.selectbox(
                "Client Discount",
                options=discount_options,
                index=discount_options.index(current_discount),
                key="order_discount_select"
            )

            # Update session state based on selection
            if discount_selection == "NGO (5%)":
                st.session_state.order_discount_type = "preset"
                st.session_state.order_discount_preset = "NGO Discount (5%)"
                st.session_state.order_discount_custom_value = 0.0
                st.session_state.order_discount_custom_desc = ""
            elif discount_selection == "Custom":
                st.session_state.order_discount_type = "custom"
                # Show custom discount input below
            else:
                st.session_state.order_discount_type = "none"
                st.session_state.order_discount_custom_value = 0.0
                st.session_state.order_discount_custom_desc = ""

        with col2:
            st.session_state.order_use_marketing_rounding = st.checkbox(
                "Apply marketing rounding (e.g., $60 → $59)",
                value=st.session_state.order_use_marketing_rounding,
                key="marketing_rounding_checkbox"
            )

        with col3:
            st.session_state.apply_cc_fee = st.checkbox(
                "Credit card fee",
                value=st.session_state.apply_cc_fee,
                key="cc_fee_checkbox",
                help="Add credit card processing fee to total (default 2.9%)"
            )

        # Row 2: Conditional inputs for Custom Discount and CC Fee
        if discount_selection == "Custom" or st.session_state.apply_cc_fee:
            col1_row2, col2_row2, col3_row2 = st.columns(3)

            with col1_row2:
                if discount_selection == "Custom":
                    st.session_state.order_discount_custom_value = st.number_input(
                        "Custom discount %",
                        min_value=0.0,
                        max_value=100.0,
                        value=st.session_state.order_discount_custom_value,
                        step=0.5,
                        key="order_custom_discount_input"
                    )

            with col2_row2:
                pass  # Empty column for alignment

            with col3_row2:
                if st.session_state.apply_cc_fee:
                    st.session_state.cc_fee_percent = st.number_input(
                        "CC fee %",
                        min_value=0.0,
                        max_value=10.0,
                        value=st.session_state.cc_fee_percent,
                        step=0.1,
                        key="cc_fee_percent_input",
                        help="Percentage fee charged for credit card payments"
                    )

        # Custom Line Items & Order Notes - Side by Side
        st.divider()

        # Count custom items and filled notes
        custom_item_count = sum(1 for item in st.session_state.order_items if item.get('is_custom', False))
        filled_notes_count = sum(1 for note in st.session_state.order_notes.values() if note and note.strip())

        col_custom, col_notes = st.columns(2)

        with col_custom:
            with st.expander(f"Add Custom Line Item ({custom_item_count} added)", expanded=False):
                st.caption("Add unique services or customizations not in the catalog")

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

        with col_notes:
            with st.expander(f"Add Order Notes ({filled_notes_count} filled)", expanded=False):
                st.caption("Add specific details for this order")

                st.session_state.order_notes['kitting_specs'] = st.text_area(
                    "Kitting Specifications",
                    value=st.session_state.order_notes.get('kitting_specs', ''),
                    placeholder="Box size, packaging requirements...",
                    height=70,
                    help="Details about how products should be kitted/packaged"
                )

                st.session_state.order_notes['client_requests'] = st.text_area(
                    "Client Requests",
                    value=st.session_state.order_notes.get('client_requests', ''),
                    placeholder="Rush delivery, special handling...",
                    height=70,
                    help="Special requests from the client"
                )

                st.session_state.order_notes['addon_samples'] = st.text_area(
                    "Add-on Samples",
                    value=st.session_state.order_notes.get('addon_samples', ''),
                    placeholder="Extra units, samples for approval...",
                    height=70,
                    help="Additional samples to include with order"
                )

                st.session_state.order_notes['artwork_attachments'] = st.text_area(
                    "Artwork Attachments",
                    value=st.session_state.order_notes.get('artwork_attachments', ''),
                    placeholder="logo_final.ai, label_design_v3.pdf...",
                    height=70,
                    help="List of artwork files attached to this order"
                )

                st.session_state.order_notes['general_notes'] = st.text_area(
                    "General Notes",
                    value=st.session_state.order_notes.get('general_notes', ''),
                    placeholder="Any other important details...",
                    height=70,
                    help="Catch-all for any other notes or details"
                )

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
    # TOTAL ORDER CALCULATION
    # ============================================================
    st.divider()
    st.header("4. Order Summary")

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

        # Break down each product into base cost + customization
        for item in st.session_state.order_items:
            # If custom line item, show as-is
            if item.get('is_custom', False):
                summary_items.append([
                    item['product_name'],
                    item['quantity'],
                    f"${item['total_per_unit']:.2f}",
                    f"${item['product_total']:.2f}"
                ])
                continue

            # Regular product: show base + markup
            product_with_markup = item.get('product_subtotal', 0) + item.get('markup_amount', 0)
            product_with_markup_per_unit = product_with_markup / item['quantity'] if item['quantity'] > 0 else 0

            summary_items.append([
                f"{item['product_name']} (Base + Markup)",
                item['quantity'],
                f"${product_with_markup_per_unit:.2f}",
                f"${product_with_markup:.2f}"
            ])

            # Show customization separately if present
            customization_setup = item.get('customization_setup_total', 0)
            customization_units = item.get('customization_unit_total', 0)

            if customization_setup > 0:
                summary_items.append([
                    f"  └ Customization Setup",
                    "one-time",
                    "",
                    f"${customization_setup:.2f}"
                ])

            if customization_units > 0:
                effective_custom_qty = item.get('customization_minimum_qty', item['quantity']) if item.get('apply_custom_minimum', False) else item['quantity']
                custom_per_unit = item.get('customization_per_unit', 0)

                summary_items.append([
                    f"  └ Customization Per-Unit",
                    effective_custom_qty,
                    f"${custom_per_unit:.2f}",
                    f"${customization_units:.2f}"
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
    # CLIENT INFORMATION UI
    # ============================================================
    st.divider()
    st.header("5. Client & Order Information")

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

    # ============================================================
    # CONFIRM ORDER
    # ============================================================
    st.divider()

    # Initialize order_confirmed state if not exists
    if 'order_confirmed' not in st.session_state:
        st.session_state.order_confirmed = False

    if not st.session_state.order_confirmed:
        st.markdown("### Ready to finalize your order?")
        st.caption("Review the order summary above and client information, then confirm to proceed to Tab 3.")

        if st.button("Confirm Order", type="primary", use_container_width=True):
            st.session_state.order_confirmed = True
            st.rerun()
    else:
        st.success("Order complete! Your order summary is ready.")
        st.info("Go to **Tab 3: Execution & Accounting** to generate Invoice & Purchase Order for this order.")

        # Optional: Add button to go back and edit
        if st.button("Edit Order", type="secondary"):
            st.session_state.order_confirmed = False
            st.rerun()

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
        st.caption("Complete form matching the bookkeeper template requirements")

        # ============================================================
        # TABLE 1: CLIENT/COMPANY INFORMATION
        # ============================================================
        st.markdown("#### 1. Client/Company Information")

        client_info_data = []

        # Company/Client Name
        company_status = "New" if client_info.get('is_new_client', False) else "Existing"
        company_name = client_info.get('company_name', 'Not specified')
        client_info_data.append(["Company/Client Name", f"{company_name} ({company_status})"])

        # Contact + Email
        contact_name = client_info.get('contact_name', 'Not specified')
        contact_email = client_info.get('contact_email', 'Not specified')
        client_info_data.append(["Contact + Email", f"{contact_name} <{contact_email}>"])

        # Company Billing Address + Email
        billing_address = client_info.get('billing_address', 'Not specified')
        billing_email = client_info.get('contact_email', 'Not specified')  # Using contact email as billing email
        client_info_data.append(["Company Billing Address + Email", f"{billing_address} | {billing_email}"])

        # Company Shipping Address
        shipping_address = client_info.get('shipping_address', 'Not specified')
        shipping_type = client_info.get('shipping_type', 'Not specified')
        client_info_data.append(["Company Shipping Address", f"{shipping_address} ({shipping_type})"])

        # Client PO #
        po_number = client_info.get('client_po', 'N/A')
        client_info_data.append(["Client PO #", po_number])

        # Display as table
        client_info_df = pd.DataFrame(client_info_data, columns=["Field", "Value"])
        st.table(client_info_df)

        st.divider()

        # ============================================================
        # TABLE 2: PARTNERS + POINT OF CONTACTS
        # ============================================================
        st.markdown("#### 2. Partners + Point of Contacts")

        # Get unique partners from order items
        partners_in_order = list(set(item['partner'] for item in st.session_state.order_items if not item.get('is_custom', False)))

        partners_data = []
        if partners_in_order and hasattr(st.session_state, 'partner_contacts'):
            for partner_name in partners_in_order:
                partner_contact = st.session_state.partner_contacts.get(partner_name, {})
                poc_name = partner_contact.get('poc_name', 'Not specified')
                poc_email = partner_contact.get('poc_email', 'Not specified')
                partners_data.append({
                    "Partner": partner_name,
                    "Point of Contact (POC)": f"{poc_name} <{poc_email}>"
                })
        else:
            partners_data.append({
                "Partner": "No partners in order",
                "Point of Contact (POC)": "N/A"
            })

        partners_df = pd.DataFrame(partners_data)
        st.table(partners_df)

        st.divider()

        # ============================================================
        # TABLE 3: ORDER DETAILS (DATES, SHIPPING, PAYMENT)
        # ============================================================
        st.markdown("#### 3. Order Details")

        order_details_data = []

        # Client In-Hands Date
        client_in_hands = client_info.get('client_in_hands_date', 'Not specified')
        order_details_data.append(["Client In-Hands Date", str(client_in_hands)])

        # Ship Method
        ship_method = client_info.get('shipping_type', 'Not specified')
        order_details_data.append(["Ship Method", ship_method])

        # Payment Terms
        payment_terms = client_info.get('payment_timeline', 'Not specified')
        order_details_data.append(["Payment Terms", payment_terms])

        # Payment Method
        payment_method = client_info.get('payment_preference', 'Not specified')
        order_details_data.append(["Payment Method", payment_method])

        # Order Submitted By + Date
        order_submitted_by = client_info.get('order_submitted_by', 'Not specified')
        order_submitted_date = client_info.get('order_submitted_date', datetime.now().date())
        order_details_data.append(["Order Submitted By", f"{order_submitted_by} (Date: {order_submitted_date})"])

        # Cost Submitted By + Date
        cost_submitted_by = client_info.get('cost_submitted_by', 'Not specified')
        cost_submitted_date = client_info.get('cost_submitted_date', 'Not specified')
        order_details_data.append(["Cost Submitted By", f"{cost_submitted_by} (Date: {cost_submitted_date if cost_submitted_date else 'Not specified'})"])

        # Display as table
        order_details_df = pd.DataFrame(order_details_data, columns=["Field", "Value"])
        st.table(order_details_df)

        st.divider()

        # ============================================================
        # TABLE 4: INVOICE AND PURCHASE ORDER ITEM DETAILS
        # ============================================================
        st.markdown("#### 4. Invoice and Purchase Order Item Details")
        st.caption("""
        This cost-to-sell segment outlines our partners' cost, our sell price to client,
        and our partners' requested in-hands date. Our in-hands date for clients may be
        later than the in-hands date to Peace by Piece for kitting purposes.
        """)

        # Build line items table with per-unit and total columns
        invoice_line_items = []
        for item in st.session_state.order_items:
            # Check if custom item
            if item.get('is_custom', False):
                partner = "Custom"
                items_specs = item.get('custom_description', 'Custom line item')
                partner_in_hands = "N/A"
                qty = item['quantity']
                cost_per_unit = item.get('total_per_unit', 0)
                cost_total = item.get('product_total', 0)
                cost_verified = "N/A"

                invoice_line_items.append({
                    'PARTNER': partner,
                    'ITEMS + SPECS': items_specs,
                    'QTY': qty,
                    'IN-HANDS from Partner': partner_in_hands,
                    'COST/UNIT': f"${cost_per_unit:.2f}",
                    'TOTAL COST': f"${cost_total:.2f}",
                    'COST VERIFIED?': cost_verified,
                    'SELL PRICE/UNIT': f"${cost_per_unit:.2f}",
                    'TOTAL SELL PRICE': f"${cost_total:.2f}"
                })
            else:
                # Regular product
                partner = item['partner']
                product_name = item['product_name']
                product_specs = item.get('product_specs', item.get('tier_range', ''))
                items_specs = f"{product_name}\n{product_specs}"
                qty = item['quantity']

                partner_in_hands = item.get('partner_in_hands_date', 'TBD')
                if partner_in_hands and partner_in_hands != 'TBD':
                    partner_in_hands = str(partner_in_hands)

                # Partner cost (before markup)
                partner_cost_per_unit = item.get('partner_cost_per_unit', item.get('base_price', 0))
                partner_cost_total = item.get('product_subtotal', 0)  # base_price * quantity

                cost_verified = item.get('cost_verified', 'Pending')

                # Sell price for base product ONLY (product + markup, NO customization)
                # This prevents double counting since customization is shown as separate line items
                product_subtotal = item.get('product_subtotal', 0)
                markup_amount = item.get('markup_amount', 0)
                sell_price_total = product_subtotal + markup_amount
                sell_price_per_unit = sell_price_total / qty if qty > 0 else 0

                # Add base product line
                invoice_line_items.append({
                    'PARTNER': partner,
                    'ITEMS + SPECS': items_specs,
                    'QTY': qty,
                    'IN-HANDS from Partner': partner_in_hands,
                    'COST/UNIT': f"${partner_cost_per_unit:.2f}",
                    'TOTAL COST': f"${partner_cost_total:.2f}",
                    'COST VERIFIED?': cost_verified,
                    'SELL PRICE/UNIT': f"${sell_price_per_unit:.2f}",
                    'TOTAL SELL PRICE': f"${sell_price_total:.2f}"
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
                            'ITEMS + SPECS': f"  └ Setup Fee: {customization_desc}",
                            'QTY': 1,
                            'IN-HANDS from Partner': partner_in_hands,
                            'COST/UNIT': f"${customization_setup:.2f}",
                            'TOTAL COST': f"${customization_setup:.2f}",
                            'COST VERIFIED?': cost_verified,
                            'SELL PRICE/UNIT': f"${customization_setup:.2f}",
                            'TOTAL SELL PRICE': f"${customization_setup:.2f}"
                        })

                    # Per-unit customization line item
                    if customization_unit_total > 0:
                        invoice_line_items.append({
                            'PARTNER': partner,
                            'ITEMS + SPECS': f"  └ Customization: {customization_desc}",
                            'QTY': qty,
                            'IN-HANDS from Partner': partner_in_hands,
                            'COST/UNIT': f"${customization_per_unit:.2f}",
                            'TOTAL COST': f"${customization_unit_total:.2f}",
                            'COST VERIFIED?': cost_verified,
                            'SELL PRICE/UNIT': f"${customization_per_unit:.2f}",
                            'TOTAL SELL PRICE': f"${customization_unit_total:.2f}"
                        })

                # Add tariff line item if applicable
                if item.get('tariff_amount', 0) > 0:
                    tariff_amount_total = item.get('tariff_amount', 0)
                    tariff_rate = item.get('tariff_rate_percent', 0)
                    tariff_per_unit = tariff_amount_total / qty if qty > 0 else 0

                    invoice_line_items.append({
                        'PARTNER': partner,
                        'ITEMS + SPECS': f"  └ Tariff ({tariff_rate}%)",
                        'QTY': qty,
                        'IN-HANDS from Partner': "N/A",
                        'COST/UNIT': f"${tariff_per_unit:.2f}",
                        'TOTAL COST': f"${tariff_amount_total:.2f}",
                        'COST VERIFIED?': "Yes",
                        'SELL PRICE/UNIT': f"${tariff_per_unit:.2f}",
                        'TOTAL SELL PRICE': f"${tariff_amount_total:.2f}"
                    })

        # Display line items table with better column sizing
        invoice_df = pd.DataFrame(invoice_line_items)
        st.dataframe(
            invoice_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PARTNER": st.column_config.TextColumn("PARTNER", width="small"),
                "ITEMS + SPECS": st.column_config.TextColumn("ITEMS + SPECS", width="large"),
                "QTY": st.column_config.NumberColumn("QTY", width="small"),
                "IN-HANDS from Partner": st.column_config.TextColumn("IN-HANDS from Partner", width="small"),
                "COST/UNIT": st.column_config.TextColumn("COST/UNIT", width="small"),
                "TOTAL COST": st.column_config.TextColumn("TOTAL COST", width="small"),
                "COST VERIFIED?": st.column_config.TextColumn("COST VERIFIED?", width="small"),
                "SELL PRICE/UNIT": st.column_config.TextColumn("SELL PRICE/UNIT", width="small"),
                "TOTAL SELL PRICE": st.column_config.TextColumn("TOTAL SELL PRICE", width="small")
            }
        )

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
                'COST/UNIT': '',
                'TOTAL COST': '',
                'COST VERIFIED?': '',
                'SELL PRICE/UNIT': '',
                'TOTAL SELL PRICE': total_item[1]
            }])
            invoice_complete = pd.concat([invoice_complete, total_row], ignore_index=True)

        # Add notes section
        notes_row = pd.DataFrame([{
            'PARTNER': '',
            'ITEMS + SPECS': '',
            'QTY': '',
            'IN-HANDS from Partner': '',
            'COST/UNIT': '',
            'TOTAL COST': '',
            'COST VERIFIED?': '',
            'SELL PRICE/UNIT': '',
            'TOTAL SELL PRICE': ''
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
                    'COST/UNIT': '',
                    'TOTAL COST': '',
                    'COST VERIFIED?': '',
                    'SELL PRICE/UNIT': '',
                    'TOTAL SELL PRICE': ''
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
