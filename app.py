"""
Peace by Piece International - Order Management System
4-tab workflow: Proposals → Client Order Forms → Order & Client Info → Execution & Accounting
Version: 6.13 (Multi-Variant Product Consolidation in PowerPoint)
"""

# MEMORY OPTIMIZATION TOGGLE
# Set to False to disable memory optimization and use full caching (if issues arise)
# Disabled since upgrading to Render Standard tier (2GB RAM) - caching improves UX
USE_MEMORY_OPTIMIZATION = False

import streamlit as st
import gc  # For memory optimization
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import time
import copy  # For deep copying client info during backup/restore

# Import extracted modules
from src.data_loader import load_pricing_data, DATASET_CONFIGS
from src.helpers import (
    clean_price,
    apply_marketing_rounding,
    round_to_nearest_five,
    round_to_nearest_fifty_cents,
    calculate_moq,
    calculate_credit_card_fee,
    calculate_markup_from_price,
    extract_partner_contacts,
    validate_invoice_completeness,
    parse_tier_info,
    parse_tariff_rate,
    calculate_product_tariff,
    convert_proposal_to_order,
    parse_client_order_form_html,
    get_shipping_costs,
    format_shipping_display
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
from src.slide_matcher import SlideMatcher
from src.proposal_manager import (
    save_proposal,
    load_all_proposals,
    load_proposal_data,
    delete_proposal
)
from src.order_manager import (
    save_order,
    load_all_orders,
    load_order_data,
    delete_order
)
from src.template_loader import (
    get_template_path,
    get_template_name,
    TEMPLATE_CONFIG
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def calculate_msrp_markup(product_data):
    """
    Calculate markup percentage required to match MSRP price.
    Returns the markup if MSRP is available and valid, otherwise returns 100.0 (default).

    Args:
        product_data (dict): Product data dictionary containing MSRP and pricing info

    Returns:
        float: Markup percentage (0 if MSRP is below cost, calculated value if valid, 100.0 if no MSRP)
    """
    # Get MSRP
    msrp = clean_price(product_data.get('MSRP', ''))

    if msrp and msrp > 0:
        # Get base cost at quantity 100 as reference
        base_cost, _, _ = get_unit_price_new_system(product_data, 100)

        if base_cost and base_cost > 0:
            # Calculate required markup % to reach MSRP
            # Formula: MSRP = cost * (1 + markup/100)
            # Therefore: markup = ((MSRP / cost) - 1) * 100
            required_markup = ((msrp / base_cost) - 1) * 100

            # Don't allow negative markup (selling below cost)
            return max(0.0, required_markup)

    # No valid MSRP or cost, return default 100% markup
    return 100.0

def compute_proposal_hash(proposal_products):
    """
    Compute a hash of the proposal products for change detection.
    Includes product IDs, quantities, markups, and key settings.
    """
    import hashlib
    import json

    # Extract key fields that matter for saving
    proposal_data = []
    for item in proposal_products:
        key_fields = {
            'product': item.get('Product/Service', ''),
            'partner': item.get('Partner', ''),
            'quantity': item.get('quantity', 1),
            'markup': item.get('markup_percentage', 100.0)
        }
        proposal_data.append(key_fields)

    # Convert to JSON string and hash
    data_str = json.dumps(proposal_data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

def compute_order_hash(order_items, client_info):
    """
    Compute a hash of the order items and client info for change detection.
    Includes all order data and client information fields.
    """
    import hashlib
    import json

    # Extract key fields from order items
    order_data = []
    for item in order_items:
        key_fields = {
            'product': item.get('Product/Service', ''),
            'partner': item.get('Partner', ''),
            'quantity': item.get('quantity', 1),
            'markup': item.get('markup_percentage', 100.0),
            'customization': item.get('has_customization', False)
        }
        order_data.append(key_fields)

    # Include client info in hash
    combined_data = {
        'order_items': order_data,
        'client_info': {
            'company': client_info.get('company_name', ''),
            'contact': client_info.get('contact_name', ''),
            'email': client_info.get('contact_email', ''),
            'client_type': client_info.get('client_type', '')
        }
    }

    # Convert to JSON string and hash
    data_str = json.dumps(combined_data, sort_keys=True, default=str)
    return hashlib.md5(data_str.encode()).hexdigest()

def has_unsaved_proposal_changes():
    """
    Check if there are unsaved changes in the current proposal.
    Returns True if products or settings have changed since last save.
    """
    if 'proposal_products' not in st.session_state or not st.session_state.proposal_products:
        return False

    current_hash = compute_proposal_hash(st.session_state.proposal_products)
    last_saved_hash = st.session_state.get('last_saved_proposal_hash', None)

    return last_saved_hash is None or current_hash != last_saved_hash

def has_unsaved_order_changes():
    """
    Check if there are unsaved changes in the current order.
    Returns True if order or client data changed since last save.
    """
    if 'order_items' not in st.session_state or not st.session_state.order_items:
        return False

    current_hash = compute_order_hash(
        st.session_state.order_items,
        st.session_state.client_info
    )
    last_saved_hash = st.session_state.get('last_saved_order_hash', None)

    return last_saved_hash is None or current_hash != last_saved_hash

def format_time_since_save(save_type):
    """
    Format the time since last save in a user-friendly way.
    save_type: 'proposal' or 'order'
    Returns string like "Saved 2 minutes ago" or "Last saved at 3:45 PM"
    """
    from datetime import datetime, timedelta

    time_key = f'last_{save_type}_save_time'
    last_save = st.session_state.get(time_key, None)

    if last_save is None:
        return None

    now = datetime.now()
    delta = now - last_save

    # If saved in the last minute
    if delta.total_seconds() < 60:
        return "Just saved"
    # If saved in the last hour
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"Saved {minutes} minute{'s' if minutes != 1 else ''} ago"
    # If saved today
    elif delta.days == 0:
        return f"Last saved at {last_save.strftime('%-I:%M %p')}"
    # If saved yesterday
    elif delta.days == 1:
        return f"Last saved yesterday at {last_save.strftime('%-I:%M %p')}"
    else:
        return f"Last saved {delta.days} days ago"

def update_last_save_time(save_type):
    """
    Update the last save time for a given save type.
    save_type: 'proposal' or 'order'
    """
    from datetime import datetime
    st.session_state[f'last_{save_type}_save_time'] = datetime.now()

    # Also update the hash to match current state
    if save_type == 'proposal':
        st.session_state['last_saved_proposal_hash'] = compute_proposal_hash(
            st.session_state.proposal_products
        )
    elif save_type == 'order':
        st.session_state['last_saved_order_hash'] = compute_order_hash(
            st.session_state.order_items,
            st.session_state.client_info
        )

@st.cache_data(ttl=60)  # Cache for 60 seconds
def cached_load_all_proposals(refresh_counter=0):
    """
    Cached version of load_all_proposals to reduce API calls.
    Cache expires after 60 seconds to allow for updates.
    refresh_counter: Used to force cache refresh when needed.
    """
    return load_all_proposals()

@st.cache_data(ttl=60)  # Cache for 60 seconds
def cached_load_all_orders(refresh_counter=0):
    """
    Cached version of load_all_orders to reduce API calls.
    Cache expires after 60 seconds to allow for updates.
    refresh_counter: Used to force cache refresh when needed.
    """
    return load_all_orders()

def clear_saved_data_cache():
    """
    Clear the cache for saved proposals and orders.
    Call this after saving, deleting, or modifying saved data.
    """
    # Increment counter to force cache refresh
    if 'saved_data_refresh_counter' not in st.session_state:
        st.session_state.saved_data_refresh_counter = 0
    st.session_state.saved_data_refresh_counter += 1

    # Also clear the cache directly
    cached_load_all_proposals.clear()
    cached_load_all_orders.clear()

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="PBP Order Management",
    page_icon="🕊️",  # Peace dove icon
    layout="wide",
    initial_sidebar_state="auto"
)

# ============================================================
# KEEP-ALIVE PING ROUTE (for GitHub Actions)
# ============================================================
# Lightweight endpoint to keep Streamlit Cloud app awake
# Responds instantly without loading data or UI
if st.query_params.get("ping"):
    st.write("pong")
    st.stop()

# Prevent automatic page scrolling on widget interaction
st.markdown("""
<style>
    * {
       overflow-anchor: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Restore scroll position after rerun (from sessionStorage)
components.html("""
    <script>
        // Check if we have a saved scroll position
        const savedScrollPos = window.parent.sessionStorage.getItem('streamlit_scroll_position');
        if (savedScrollPos !== null) {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                window.parent.document.querySelector('section.main').scrollTop = parseInt(savedScrollPos);
                // Clear the saved position after restoring
                window.parent.sessionStorage.removeItem('streamlit_scroll_position');
            }, 100);
        }
    </script>
""", height=0)

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
if 'partner_shipping' not in st.session_state:
    st.session_state.partner_shipping = 0.0
if 'sales_tax' not in st.session_state:
    st.session_state.sales_tax = 0.0
if 'kitting_pbp_cost' not in st.session_state:
    st.session_state.kitting_pbp_cost = 0.0
if 'kitting_client_price' not in st.session_state:
    st.session_state.kitting_client_price = 0.0

# Initialize discount settings in session state
if 'order_discount_type' not in st.session_state:
    st.session_state.order_discount_type = "none"
if 'order_discount_preset' not in st.session_state:
    st.session_state.order_discount_preset = "NGO Discount (5%)"
if 'order_discount_custom_desc' not in st.session_state:
    st.session_state.order_discount_custom_desc = ""
if 'order_discount_custom_value' not in st.session_state:
    st.session_state.order_discount_custom_value = 0.0

# Initialize rounding settings
if 'order_use_marketing_rounding' not in st.session_state:
    st.session_state.order_use_marketing_rounding = False

if 'order_fifty_cent_rounding' not in st.session_state:
    st.session_state.order_fifty_cent_rounding = True  # Default to checked

# Initialize order confirmed flag
if 'order_confirmed' not in st.session_state:
    st.session_state.order_confirmed = False

# Initialize order backup for persistence during edit/confirm cycles
# This preserves data entered in Tab 4 when user clicks "Edit Order"
if 'order_backup' not in st.session_state:
    st.session_state.order_backup = {}

# Initialize client information
if 'client_info' not in st.session_state:
    st.session_state.client_info = {
        'is_new_client': True,
        'company_name': '',
        'contacts': [  # NEW: Support multiple contacts
            {
                'name': '',
                'email': '',
                'phone': '',
                'role': 'Primary Contact'
            }
        ],
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

# Migrate old contact fields to new structure if needed
if 'contact_name' in st.session_state.client_info:
    # Old structure detected - migrate to new
    old_name = st.session_state.client_info.get('contact_name', '')
    old_email = st.session_state.client_info.get('contact_email', '')

    # Create contacts array with old data
    st.session_state.client_info['contacts'] = [
        {
            'name': old_name,
            'email': old_email,
            'phone': '',
            'role': 'Primary Contact'
        }
    ]

    # Remove old fields
    if 'contact_name' in st.session_state.client_info:
        del st.session_state.client_info['contact_name']
    if 'contact_email' in st.session_state.client_info:
        del st.session_state.client_info['contact_email']

# Ensure contacts array exists and has at least one contact
if 'contacts' not in st.session_state.client_info:
    st.session_state.client_info['contacts'] = [
        {
            'name': '',
            'email': '',
            'phone': '',
            'role': 'Primary Contact'
        }
    ]
elif len(st.session_state.client_info['contacts']) == 0:
    # Ensure at least one contact exists
    st.session_state.client_info['contacts'].append({
        'name': '',
        'email': '',
        'phone': '',
        'role': 'Primary Contact'
    })

# Initialize custom payment terms
if 'custom_payment_terms' not in st.session_state:
    st.session_state.custom_payment_terms = ''

# Initialize order notes (5 categories for better organization)
if 'order_notes' not in st.session_state:
    st.session_state.order_notes = {
        'kitting_specs': '',      # Kitting/packaging specifications
        'client_requests': '',    # Special client requests
        'addon_samples': '',      # Additional samples needed
        'artwork_attachments': '', # Artwork file references
        'general_notes': ''       # General/miscellaneous notes
    }

# Initialize credit card fee settings
if 'apply_cc_fee' not in st.session_state:
    st.session_state.apply_cc_fee = False
if 'cc_fee_percent' not in st.session_state:
    st.session_state.cc_fee_percent = 3.0

# Initialize proposal-specific session state (Phase 2)
if 'proposal_products' not in st.session_state:
    st.session_state.proposal_products = []

if 'proposal_marketing_rounding' not in st.session_state:
    st.session_state.proposal_marketing_rounding = False

if 'proposal_fifty_cent_rounding' not in st.session_state:
    st.session_state.proposal_fifty_cent_rounding = True  # Default to checked

if 'proposal_use_msrp' not in st.session_state:
    st.session_state.proposal_use_msrp = True  # Default to checked (use MSRP)

# Initialize order MSRP preference
if 'order_use_msrp' not in st.session_state:
    st.session_state.order_use_msrp = True  # Default to checked (use MSRP)

if 'configuring_product' not in st.session_state:
    st.session_state.configuring_product = None

if 'editing_proposal_index' not in st.session_state:
    st.session_state.editing_proposal_index = None

if 'proposal_filters' not in st.session_state:
    st.session_state.proposal_filters = {
        'min_price': 0.0,
        'client_budget': None,
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

# Initialize form customization fields
if 'form_customizations' not in st.session_state:
    st.session_state.form_customizations = {
        'form_instructions': """1. Copy & paste the entire form into Docs, Word, or directly into your email reply (the format should copy along with the text)
2. Click in the gray areas to type your answers
3. For multiple choice questions, delete the options you DON'T want and keep the one you DO want
4. When finished, select all (Ctrl+A or Cmd+A), copy, and paste into your email reply
5. Fields marked with * are required""",
        'dropshipping_instructions': "For drop shipping orders, please provide: destination addresses, quantities per location, and any special delivery instructions",
        'dropshipping_placeholder': "[Input dropshipping info here]",
        'shipping_address_placeholder': "[Type full shipping address here, or N/A if drop shipping]",
        'billing_address_placeholder': '[Type billing address here, or "Same as shipping"]',
        'customization_placeholder': "[Describe any customization, logo placement, colors, etc.]",
        'impact_card_options': """Peace by Piece Impact Card
Custom Impact Card
Custom Message Card
Send us your own card""",
        'payment_options': """ACH
Check
Credit Card (3% processing fee applies)"""
    }

# Legacy compatibility - maintain sync between old and new dropshipping fields
if 'dropshipping_notes' not in st.session_state:
    st.session_state.dropshipping_notes = st.session_state.form_customizations['dropshipping_instructions']
else:
    # If dropshipping_notes exists but differs from form_customizations, sync them
    if st.session_state.dropshipping_notes != st.session_state.form_customizations['dropshipping_instructions']:
        st.session_state.dropshipping_notes = st.session_state.form_customizations['dropshipping_instructions']

if 'using_proposal_data' not in st.session_state:
    st.session_state.using_proposal_data = False

# ============================================================
# HEADER
# ============================================================
st.title("Peace by Piece Order Management System")
st.markdown("**Welcome to the PBP Order Management System** — Manage the complete order lifecycle:")
st.markdown("")
st.markdown("**→ Tab 1: Proposal Generator** - Browse products, create proposals for prospective clients")
st.markdown("**→ Tab 2: Client Order Form Generator** - Create professional order forms to send to clients")
st.markdown("**→ Tab 3: Order & Client Info** - Build orders, collect client details")
st.markdown("**→ Tab 4: Execution & Accounting** - Generate invoices and purchase orders")
st.divider()

# Initialize save tracking
if 'last_saved_proposal_hash' not in st.session_state:
    st.session_state.last_saved_proposal_hash = None
if 'last_saved_order_hash' not in st.session_state:
    st.session_state.last_saved_order_hash = None
if 'last_proposal_save_time' not in st.session_state:
    st.session_state.last_proposal_save_time = None
if 'last_order_save_time' not in st.session_state:
    st.session_state.last_order_save_time = None

# ============================================================
# SIDEBAR - APP INFORMATION
# ============================================================
with st.sidebar:
    st.markdown("## Instructions & Tools")

    # Section 0: Data Source Selector
    st.markdown("### Data Source")

    # Initialize dataset selection in session state
    if 'selected_dataset' not in st.session_state:
        st.session_state.selected_dataset = 'real'

    selected_dataset = st.radio(
        "Select pricing dataset:",
        options=['demo', 'real'],
        format_func=lambda x: DATASET_CONFIGS[x]['name'].replace('Demo Data (', '').replace('Real Pricing Data (', '').replace(')', ''),
        key='selected_dataset',
        help="Demo: Testing data from master_pricing_template_10_14\nReal: Production data from master_pricing"
    )

    # Show visual indicator of active dataset
    if selected_dataset == 'real':
        # Check if real dataset is ready
        if DATASET_CONFIGS['real'].get('status') == 'in_progress':
            st.error("Real pricing data is not yet ready. Please use Demo Data.")
            st.caption(DATASET_CONFIGS['real'].get('notes', 'Dataset structure needs to be completed.'))
        else:
            st.warning("Using REAL production data")
    else:
        st.info("Using demo/testing data")

    st.markdown("---")

    # Section 1: Progress Indicator
    st.markdown("### Workflow Progress")

    # Determine completion status for each tab
    has_proposals = len(st.session_state.proposal_products) > 0
    has_order = len(st.session_state.order_items) > 0
    has_client_info = st.session_state.client_info.get('company_name', '').strip() != ''
    order_confirmed = st.session_state.get('order_confirmed', False)

    # Tab 1: Proposals
    tab1_status = "[X]" if has_proposals else "[ ]"
    tab1_color = "green" if has_proposals else "gray"
    st.markdown(f":{tab1_color}[{tab1_status}] **Tab 1:** Proposals ({len(st.session_state.proposal_products)} products)")

    # Tab 2: Order Forms (always available)
    tab2_status = "[X]"
    tab2_color = "green"
    st.markdown(f":{tab2_color}[{tab2_status}] **Tab 2:** Client Order Forms (always available)")

    # Tab 3: Order & Client Info
    tab3_complete = has_order and has_client_info and order_confirmed
    tab3_status = "[X]" if tab3_complete else "[ ]"
    tab3_color = "green" if tab3_complete else "gray"

    # Debug info to show what's missing
    if not tab3_complete:
        missing = []
        if not has_order:
            missing.append("no order")
        if not has_client_info:
            missing.append("no client info")
        if not order_confirmed:
            missing.append("not confirmed")
        debug_text = f" ({', '.join(missing)})" if missing else ""
    else:
        debug_text = ""

    st.markdown(f":{tab3_color}[{tab3_status}] **Tab 3:** Order & Client ({len(st.session_state.order_items)} products){debug_text}")

    # Tab 4: Invoice/PO ready indicator
    tab4_ready = has_order and has_client_info
    tab4_status = "[X]" if tab4_ready else "[ ]"
    tab4_color = "green" if tab4_ready else "gray"
    tab4_label = "Ready" if tab4_ready else "Not ready"
    st.markdown(f":{tab4_color}[{tab4_status}] **Tab 4:** Invoice/PO ({tab4_label})")

    st.caption("Complete Tab 3 to generate Invoice/PO in Tab 4")

    st.markdown("---")

    # Section 2: Saved Work Management
    st.markdown("### Saved Work")

    # Add refresh button if data seems stale
    if st.button("Refresh Saved Items", key="refresh_saved_work", help="Click to refresh saved proposals and orders", use_container_width=True):
        clear_saved_data_cache()
        st.rerun()

    st.caption("Saved items refresh automatically every 60 seconds")

    # Load saved proposals and orders (cached to reduce API calls)
    refresh_counter = st.session_state.get('saved_data_refresh_counter', 0)
    saved_proposals = cached_load_all_proposals(refresh_counter)
    saved_orders = cached_load_all_orders(refresh_counter)

    # Handle potential None returns from rate limiting
    if saved_proposals is None:
        saved_proposals = []
    if saved_orders is None:
        saved_orders = []

    # Check for unsaved proposal changes
    proposal_unsaved = has_unsaved_proposal_changes()
    proposal_save_status = format_time_since_save('proposal')

    # Build proposal header with indicators
    proposal_header = f"**Saved Proposals ({len(saved_proposals)})**"
    if proposal_unsaved:
        proposal_header += " - Unsaved changes"

    # Saved Proposals subsection
    with st.expander(proposal_header, expanded=False):
        # Show save status if available
        if proposal_save_status:
            st.caption(f"{proposal_save_status}")

        if len(saved_proposals) == 0:
            st.info("No saved proposals yet")
        else:
            # Add manage mode checkbox
            manage_proposals = st.checkbox("Manage proposals (delete)", key="manage_proposals_mode")

            for proposal in saved_proposals[:10]:  # Show max 10 most recent
                if manage_proposals:
                    # Delete mode - show delete buttons
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.caption(f"{proposal['name']}")
                        st.caption(f"   {proposal['created_date'][:10]}")
                    with col2:
                        if st.button("Load", key=f"load_prop_{proposal['proposal_id']}", use_container_width=True):
                            success, proposal_data, dataset = load_proposal_data(proposal['proposal_id'])
                            if success:
                                if dataset != st.session_state.selected_dataset:
                                    st.warning(f"Dataset mismatch: {dataset} → {st.session_state.selected_dataset}")

                                st.session_state.proposal_products = proposal_data.get('proposal_products', [])
                                st.session_state.proposal_marketing_rounding = proposal_data.get('proposal_marketing_rounding', False)
                                st.session_state.proposal_use_msrp = proposal_data.get('proposal_use_msrp', True)
                                st.session_state.proposal_discount_type = proposal_data.get('proposal_discount_type', None)
                                st.session_state.proposal_discount_percent = proposal_data.get('proposal_discount_percent', 0.0)
                                st.session_state.proposal_client_budget = proposal_data.get('proposal_client_budget', 0.0)

                                st.success(f"Loaded: {proposal['name']}")
                                st.rerun()
                    with col3:
                        if st.button("Delete", key=f"del_prop_{proposal['proposal_id']}", use_container_width=True, help="Delete this proposal"):
                            # Store the proposal to delete in session state for confirmation
                            st.session_state.delete_proposal_confirm = proposal
                else:
                    # Normal mode - just load button
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"{proposal['name']}")
                        st.caption(f"   {proposal['created_date'][:10]}")
                    with col2:
                        if st.button("Load", key=f"load_prop_{proposal['proposal_id']}", use_container_width=True):
                            success, proposal_data, dataset = load_proposal_data(proposal['proposal_id'])
                            if success:
                                if dataset != st.session_state.selected_dataset:
                                    st.warning(f"Dataset mismatch: {dataset} → {st.session_state.selected_dataset}")

                                st.session_state.proposal_products = proposal_data.get('proposal_products', [])
                                st.session_state.proposal_marketing_rounding = proposal_data.get('proposal_marketing_rounding', False)
                                st.session_state.proposal_use_msrp = proposal_data.get('proposal_use_msrp', True)
                                st.session_state.proposal_discount_type = proposal_data.get('proposal_discount_type', None)
                                st.session_state.proposal_discount_percent = proposal_data.get('proposal_discount_percent', 0.0)
                                st.session_state.proposal_client_budget = proposal_data.get('proposal_client_budget', 0.0)

                                st.success(f"Loaded: {proposal['name']}")
                                st.rerun()

            # Handle delete confirmation
            if 'delete_proposal_confirm' in st.session_state:
                prop = st.session_state.delete_proposal_confirm
                st.warning(f"Delete '{prop['name']}'?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete", key="confirm_del_prop", type="primary"):
                        success, message = delete_proposal(prop['proposal_id'])
                        if success:
                            clear_saved_data_cache()  # Clear cache after deletion
                            st.success("Deleted successfully")
                            del st.session_state.delete_proposal_confirm
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                with col2:
                    if st.button("Cancel", key="cancel_del_prop"):
                        del st.session_state.delete_proposal_confirm
                        st.rerun()

            if len(saved_proposals) > 10:
                st.caption(f"...and {len(saved_proposals) - 10} more.")

    # Check for unsaved order changes
    order_unsaved = has_unsaved_order_changes()
    order_save_status = format_time_since_save('order')

    # Build order header with indicators
    order_header = f"**Saved Orders ({len(saved_orders)})**"
    if order_unsaved:
        order_header += " - Unsaved changes"

    # Saved Orders subsection
    with st.expander(order_header, expanded=False):
        # Show save status if available
        if order_save_status:
            st.caption(f"{order_save_status}")

        if len(saved_orders) == 0:
            st.info("No saved orders yet")
        else:
            # Add manage mode checkbox
            manage_orders = st.checkbox("Manage orders (delete)", key="manage_orders_mode")

            for order in saved_orders[:10]:  # Show max 10 most recent
                if manage_orders:
                    # Delete mode - show delete buttons
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.caption(f"{order['name']}")
                        st.caption(f"   {order['created_date'][:10]}")
                    with col2:
                        if st.button("Load", key=f"load_ord_{order['order_id']}", use_container_width=True):
                            success, order_data, dataset = load_order_data(order['order_id'])
                            if success:
                                if dataset != st.session_state.selected_dataset:
                                    st.warning(f"Dataset mismatch: {dataset} → {st.session_state.selected_dataset}")

                                st.session_state.order_items = order_data.get('order_items', [])
                                st.session_state.order_shipping = order_data.get('order_shipping', 0.0)
                                st.session_state.partner_shipping = order_data.get('partner_shipping', 0.0)
                                st.session_state.sales_tax = order_data.get('sales_tax', 0.0)
                                st.session_state.kitting_pbp_cost = order_data.get('kitting_pbp_cost', 0.0)
                                st.session_state.kitting_client_price = order_data.get('kitting_client_price', 0.0)
                                st.session_state.order_discount_type = order_data.get('order_discount_type', 'none')
                                st.session_state.order_discount_preset = order_data.get('order_discount_preset', 'NGO Discount (5%)')
                                st.session_state.order_discount_custom_desc = order_data.get('order_discount_custom_desc', '')
                                st.session_state.order_discount_custom_value = order_data.get('order_discount_custom_value', 0.0)
                                st.session_state.order_use_marketing_rounding = order_data.get('order_use_marketing_rounding', False)
                                st.session_state.apply_cc_fee = order_data.get('apply_cc_fee', False)
                                st.session_state.cc_fee_percent = order_data.get('cc_fee_percent', 3.0)
                                st.session_state.client_info = order_data.get('client_info', st.session_state.client_info)
                                # Handle both old and new order_notes structures
                                loaded_notes = order_data.get('order_notes', {})
                                if 'kitting_specs' in loaded_notes:
                                    # New 5-category structure
                                    st.session_state.order_notes = loaded_notes
                                else:
                                    # Old 2-category structure - migrate to new
                                    st.session_state.order_notes = {
                                        'kitting_specs': '',
                                        'client_requests': loaded_notes.get('accounting_notes', ''),
                                        'addon_samples': '',
                                        'artwork_attachments': '',
                                        'general_notes': loaded_notes.get('notes_to_partner', '')
                                    }
                                st.session_state.order_confirmed = order_data.get('order_confirmed', False)

                                st.success(f"Loaded: {order['name']}")
                                st.rerun()
                    with col3:
                        if st.button("Delete", key=f"del_ord_{order['order_id']}", use_container_width=True, help="Delete this order"):
                            # Store the order to delete in session state for confirmation
                            st.session_state.delete_order_confirm = order
                else:
                    # Normal mode - just load button
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"{order['name']}")
                        st.caption(f"   {order['created_date'][:10]}")
                    with col2:
                        if st.button("Load", key=f"load_ord_{order['order_id']}", use_container_width=True):
                            success, order_data, dataset = load_order_data(order['order_id'])
                            if success:
                                if dataset != st.session_state.selected_dataset:
                                    st.warning(f"Dataset mismatch: {dataset} → {st.session_state.selected_dataset}")

                                st.session_state.order_items = order_data.get('order_items', [])
                                st.session_state.order_shipping = order_data.get('order_shipping', 0.0)
                                st.session_state.partner_shipping = order_data.get('partner_shipping', 0.0)
                                st.session_state.sales_tax = order_data.get('sales_tax', 0.0)
                                st.session_state.kitting_pbp_cost = order_data.get('kitting_pbp_cost', 0.0)
                                st.session_state.kitting_client_price = order_data.get('kitting_client_price', 0.0)
                                st.session_state.order_discount_type = order_data.get('order_discount_type', 'none')
                                st.session_state.order_discount_preset = order_data.get('order_discount_preset', 'NGO Discount (5%)')
                                st.session_state.order_discount_custom_desc = order_data.get('order_discount_custom_desc', '')
                                st.session_state.order_discount_custom_value = order_data.get('order_discount_custom_value', 0.0)
                                st.session_state.order_use_marketing_rounding = order_data.get('order_use_marketing_rounding', False)
                                st.session_state.apply_cc_fee = order_data.get('apply_cc_fee', False)
                                st.session_state.cc_fee_percent = order_data.get('cc_fee_percent', 3.0)
                                st.session_state.client_info = order_data.get('client_info', st.session_state.client_info)
                                # Handle both old and new order_notes structures
                                loaded_notes = order_data.get('order_notes', {})
                                if 'kitting_specs' in loaded_notes:
                                    # New 5-category structure
                                    st.session_state.order_notes = loaded_notes
                                else:
                                    # Old 2-category structure - migrate to new
                                    st.session_state.order_notes = {
                                        'kitting_specs': '',
                                        'client_requests': loaded_notes.get('accounting_notes', ''),
                                        'addon_samples': '',
                                        'artwork_attachments': '',
                                        'general_notes': loaded_notes.get('notes_to_partner', '')
                                    }
                                st.session_state.order_confirmed = order_data.get('order_confirmed', False)

                                st.success(f"Loaded: {order['name']}")
                                st.rerun()

            # Handle delete confirmation
            if 'delete_order_confirm' in st.session_state:
                ord = st.session_state.delete_order_confirm
                st.warning(f"Delete '{ord['name']}'?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete", key="confirm_del_ord", type="primary"):
                        success, message = delete_order(ord['order_id'])
                        if success:
                            clear_saved_data_cache()  # Clear cache after deletion
                            st.success("Deleted successfully")
                            del st.session_state.delete_order_confirm
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                with col2:
                    if st.button("Cancel", key="cancel_del_ord"):
                        del st.session_state.delete_order_confirm
                        st.rerun()

            if len(saved_orders) > 10:
                st.caption(f"...and {len(saved_orders) - 10} more.")

    st.markdown("---")

    # Section 3: Clear Current Session Button (renamed from Clear All Data)
    st.markdown("### Session Management")

    # Show current work status
    proposal_count = len(st.session_state.proposal_products)
    order_count = len(st.session_state.order_items)

    if proposal_count > 0 or order_count > 0:
        st.caption(f"Current work: {proposal_count} proposal items, {order_count} order items")

    if st.button("Reset Current Session", type="secondary", use_container_width=True):
        st.session_state.confirm_clear = True

    if st.session_state.get('confirm_clear', False):
        st.warning(f"""
        **Start a fresh session?**

        This will clear your current working session:
        - Current proposal ({proposal_count} items)
        - Current order ({order_count} items)
        - Current client info

        Your {len(saved_proposals)} saved proposals and {len(saved_orders)} saved orders will remain safe.
        """)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Reset", type="primary", use_container_width=True):
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
                st.session_state.partner_shipping = 0.0
                st.session_state.order_discount_type = "none"
                st.session_state.order_history = []
                st.session_state.confirm_clear = False

                # Show success message before rerun
                st.success(f"Session reset successfully! Your {len(saved_proposals)} saved proposals and {len(saved_orders)} saved orders are still available above.")
                time.sleep(1)  # Brief pause to show message
                st.rerun()
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()

    st.markdown("---")

    # Section 3: Instructions
    with st.expander("How to Use This App", expanded=False):
        st.markdown("""
        **4-Tab Workflow:**

        **Tab 1: Proposal Generator** (for prospective clients)
        - Browse product catalog with filters
        - Add products to proposal
        - Configure quantity, markup, MSRP comparison
        - Generate MOQ-based proposal tables
        - Generate PowerPoint presentations

        **Tab 2: Client Order Form Generator**
        - Create professional HTML order forms
        - Pre-fill client information
        - Send to clients for completion

        **Tab 3: Order & Client Info** (main workflow)
        1. Import completed client forms or proposal products
        2. Enter client information (company, contact, payment)
        3. Select partner and product from dropdowns
        4. Set quantity, markup, and customization options
        5. Add to order (repeat for multiple products)
        6. Configure shipping, discounts, custom items
        7. Add order notes (partner notes, accounting notes)
        8. Review order summary

        **Tab 4: Execution & Accounting** (final step)
        - View order summary and validation warnings
        - Generate invoice and purchase order
        - Download CSV for bookkeeping
        - Export to accounting (coming soon)

        **Tips:**
        - Start with Tab 1 for proposals to prospective clients
        - Use Tab 2 to generate client order forms
        - Use Tab 3 for building and managing actual orders
        - Tab 4 requires completed order in Tab 3
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
            # Clear cached data and reload from selected dataset
            df_template, df_metadata, df_partner_info = load_pricing_data(st.session_state.selected_dataset)
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
# MATCH REVIEW UI FUNCTION (PHASE 1, DAY 2)
# ============================================================
def show_match_review_ui(match_results, pptx_product_names, pptx_name_to_index=None):
    """
    Display match review UI for user confirmation of fuzzy matches.

    Args:
        match_results: List of SlideMatchResult objects from SlideMatcher
        pptx_product_names: List of all PowerPoint product names (for alternatives)
        pptx_name_to_index: Dict mapping slide names to indices (for saving confirmations)

    Returns:
        Dict of confirmed matches {gs_product_name: pptx_product_name} or None if cancelled
    """
    # Import match memory functions
    from src.match_memory import save_confirmed_match

    # Get current dataset for saving confirmations
    current_dataset = st.session_state.get('selected_dataset', 'real')
    st.markdown("---")
    st.subheader("Step 1. Review Product Matches")

    # Separate matches by type
    exact_matches = [r for r in match_results if r.match_type == 'exact']
    fuzzy_matches = [r for r in match_results if r.match_type == 'fuzzy' and r.confidence >= 70]
    poor_matches = [r for r in match_results if r.match_type == 'fuzzy' and r.confidence < 70]
    no_matches = [r for r in match_results if r.match_type == 'none']

    # Count items by status for better summary
    already_matched = len(exact_matches)  # Includes exact, previously confirmed, and manual overrides
    needs_review = len(fuzzy_matches) + len(poor_matches) + len(no_matches)

    total_products = already_matched + needs_review

    # Summary at top
    st.markdown(f"""
    **Match Summary:**
    - {already_matched} ready to use (already matched from exact or previous sessions)
    - {needs_review} need your confirmation (auto-matches and no matches)

    Total: {total_products} products
    """)

    if needs_review > 0:
        st.caption("Items are sorted by confidence (lowest first) to help you focus on matches that need the most attention.")

    if len(fuzzy_matches) == 0 and len(exact_matches) == 0:
        st.warning("No usable matches found. Cannot generate PowerPoint presentation.")
        return None

    # Initialize confirmation state if not exists
    if 'match_confirmations' not in st.session_state:
        st.session_state.match_confirmations = {}

    # ============================================================
    # UNIFIED MATCH TABLE - All Products
    # ============================================================
    st.markdown("### Product → Slide Matches")
    st.caption("Review and confirm matches. Items needing review are shown first.")

    # Combine all match types into single list
    all_matches = []

    # Add exact matches
    for result in exact_matches:
        all_matches.append({
            'result': result,
            'type': 'exact',
            'needs_review': False
        })

    # Add fuzzy matches
    for result in fuzzy_matches:
        all_matches.append({
            'result': result,
            'type': 'fuzzy',
            'needs_review': True
        })

    # Add poor/no matches
    if poor_matches or no_matches:
        all_poor = poor_matches + no_matches
        for result in all_poor:
            all_matches.append({
                'result': result,
                'type': 'poor',
                'needs_review': True
            })

    # Sort by review status (needs review first), then by confidence (lowest confidence first within needs_review)
    # This puts the most questionable matches at the top for user attention
    all_matches.sort(key=lambda x: (
        not x['needs_review'],  # Needs review first
        x['result'].confidence if x['needs_review'] else 999,  # Within needs_review: lowest confidence first (ascending)
        x['result'].gs_product_name  # Alphabetical as tiebreaker
    ))

    if all_matches:
        # Add JavaScript to capture scroll position
        components.html("""
            <script>
                const observer = new MutationObserver(function(mutations) {
                    const buttons = window.parent.document.querySelectorAll('button');
                    buttons.forEach(button => {
                        const btnText = button.textContent;
                        if (!button.dataset.scrollCaptureAttached &&
                            (btnText.includes('Confirm') ||
                             btnText.includes('Alt') ||
                             btnText.includes('Skip') ||
                             btnText.includes('Change') ||
                             btnText.includes('Search') ||
                             btnText.includes('Use'))) {
                            button.addEventListener('click', function() {
                                const scrollPos = window.parent.document.querySelector('section.main').scrollTop;
                                window.parent.sessionStorage.setItem('streamlit_scroll_position', scrollPos);
                            });
                            button.dataset.scrollCaptureAttached = 'true';
                        }
                    });
                });
                observer.observe(window.parent.document.body, { childList: true, subtree: true });
                setTimeout(function() {
                    const buttons = window.parent.document.querySelectorAll('button');
                    buttons.forEach(button => {
                        const btnText = button.textContent;
                        if (!button.dataset.scrollCaptureAttached &&
                            (btnText.includes('Confirm') ||
                             btnText.includes('Alt') ||
                             btnText.includes('Skip') ||
                             btnText.includes('Change') ||
                             btnText.includes('Search') ||
                             btnText.includes('Use'))) {
                            button.addEventListener('click', function() {
                                const scrollPos = window.parent.document.querySelector('section.main').scrollTop;
                                window.parent.sessionStorage.setItem('streamlit_scroll_position', scrollPos);
                            });
                            button.dataset.scrollCaptureAttached = 'true';
                        }
                    });
                }, 100);
            </script>
        """, height=0)

        # Table header
        hcol1, hcol2, hcol3, hcol4, hcol5, hcol6 = st.columns([2.2, 2.2, 1.8, 1.0, 1.0, 1.5])
        with hcol1:
            st.markdown("**Product**")
        with hcol2:
            st.markdown("**Matched Slide**")
        with hcol3:
            st.markdown("**Source**")
        with hcol4:
            st.markdown("**Conf%**")
        with hcol5:
            st.markdown("**Status**")
        with hcol6:
            st.markdown("**Actions**")

        st.divider()

        # Display each match in unified table
        for idx, match_item in enumerate(all_matches):
            result = match_item['result']
            match_type = match_item['type']

            # Create unique key
            match_key = f"unified_match_{idx}"

            # Check confirmation status
            confirmation = st.session_state.match_confirmations.get(result.gs_product_name, {})
            is_confirmed = confirmation.get('confirmed', False)
            is_skipped = confirmation.get('skipped', False)
            show_alternatives = confirmation.get('show_alternatives', False)
            show_search = confirmation.get('show_search', False)

            # Determine source and if it needs review
            if match_type == 'exact':
                if result.match_source == 'confirmed':
                    # Show which dataset this was confirmed in
                    source = f"Previously Confirmed"
                    needs_review = False
                elif result.match_source == 'manual':
                    source = "Manual Override"
                    needs_review = False
                else:
                    source = "Exact Match"
                    needs_review = False
            elif match_type == 'fuzzy':
                if is_confirmed:
                    source = "Auto-match"
                    needs_review = False
                elif is_skipped:
                    source = "Auto-match"
                    needs_review = False
                else:
                    source = "Auto-match"
                    needs_review = True
            else:  # poor match
                if is_confirmed:
                    source = "Manual Search"
                    needs_review = False
                elif is_skipped:
                    source = "No match found"
                    needs_review = False
                else:
                    source = "No match found"
                    needs_review = True

            col1, col2, col3, col4, col5, col6 = st.columns([2.2, 2.2, 1.8, 1.0, 1.0, 1.5])

            with col1:
                st.markdown(f"{result.gs_product_name}")

            with col2:
                if is_confirmed:
                    st.markdown(f"{confirmation['pptx_name']}")
                elif is_skipped:
                    st.markdown("(Skipped)")
                elif match_type == 'poor' or (match_type == 'fuzzy' and result.confidence < 70):
                    st.markdown("(No match)")
                else:
                    st.markdown(f"{result.pptx_product_name}")

            with col3:
                st.markdown(source)

            with col4:
                # Show confidence for fuzzy and poor matches
                if match_type == 'fuzzy' or match_type == 'poor':
                    if result.confidence >= 90:
                        st.markdown(f":green[{result.confidence}%]")
                    elif result.confidence >= 70:
                        st.markdown(f":orange[{result.confidence}%]")
                    elif result.confidence > 0:
                        st.markdown(f":red[{result.confidence}%]")
                    else:
                        st.markdown("—")
                else:
                    st.markdown("—")

            with col5:
                if needs_review and not is_confirmed and not is_skipped:
                    st.markdown("Review")
                else:
                    st.markdown("Done")

            with col6:
                if needs_review and not is_confirmed and not is_skipped:
                    # Items needing confirmation: Show "Confirm" and "Change" buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("Confirm", key=f"{match_key}_confirm", help="Confirm this match", use_container_width=True):
                            # Set confirmation in session state FIRST
                            st.session_state.match_confirmations[result.gs_product_name] = {
                                'confirmed': True,
                                'pptx_name': result.pptx_product_name
                            }

                            # Save confirmation to Google Sheets and wait for completion
                            save_success = False
                            try:
                                if pptx_name_to_index and result.pptx_product_name in pptx_name_to_index:
                                    slide_index = pptx_name_to_index[result.pptx_product_name]
                                    save_success, save_message = save_confirmed_match(
                                        product_name=result.gs_product_name,
                                        slide_index=slide_index,
                                        slide_title=result.pptx_product_name,
                                        dataset=current_dataset,
                                        match_type='fuzzy_confirmed' if match_type == 'fuzzy' else 'poor_confirmed',
                                        confidence=result.confidence
                                    )
                                    if not save_success:
                                        st.warning(f"Match confirmed locally but couldn't save to Google Sheets: {save_message}")
                            except Exception as save_error:
                                # Don't block on save error - confirmation is already in session state
                                st.warning(f"Match confirmed locally but couldn't save to Google Sheets: {save_error}")

                            # Only rerun after save completes (successful or not - session state is set either way)
                            st.rerun()
                    with btn_col2:
                        if st.button("Change", key=f"{match_key}_change", help="Choose a different match", use_container_width=True):
                            if match_type == 'poor':
                                # For poor matches, show search
                                st.session_state.match_confirmations[result.gs_product_name] = {
                                    'confirmed': False,
                                    'show_search': True
                                }
                            else:
                                # For fuzzy matches, show alternatives
                                st.session_state.match_confirmations[result.gs_product_name] = {
                                    'confirmed': False,
                                    'show_alternatives': True
                                }
                            st.rerun()
                else:
                    # Items already ready to use: Only show "Change" button
                    if st.button("Change", key=f"{match_key}_change", use_container_width=True):
                        if match_type == 'poor':
                            # For poor matches, show search
                            st.session_state.match_confirmations[result.gs_product_name] = {
                                'confirmed': False,
                                'show_search': True
                            }
                        else:
                            # For exact/fuzzy matches, show alternatives
                            st.session_state.match_confirmations[result.gs_product_name] = {
                                'confirmed': False,
                                'skipped': False,
                                'show_alternatives': True
                            }
                        st.rerun()

            # Show alternatives inline if requested
            if show_alternatives and match_type != 'poor':
                st.markdown("")
                st.markdown(f"**Alternatives for {result.gs_product_name}:**")

                if result.alternatives:
                    st.caption("Select an alternative or search below:")

                    # Show top 3 alternatives
                    for alt_idx, (alt_name, alt_score) in enumerate(result.alternatives[:3]):
                        alt_col1, alt_col2 = st.columns([4, 1])
                        with alt_col1:
                            st.markdown(f"{alt_idx + 1}. {alt_name} ({alt_score}% confidence)")
                        with alt_col2:
                            if st.button(f"Use", key=f"{match_key}_alt_{alt_idx}", use_container_width=True):
                                # Set confirmation in session state
                                st.session_state.match_confirmations[result.gs_product_name] = {
                                    'confirmed': True,
                                    'pptx_name': alt_name
                                }

                                # Save alternative selection to Google Sheets
                                try:
                                    if pptx_name_to_index and alt_name in pptx_name_to_index:
                                        slide_index = pptx_name_to_index[alt_name]
                                        save_confirmed_match(
                                            product_name=result.gs_product_name,
                                            slide_index=slide_index,
                                            slide_title=alt_name,
                                            dataset=current_dataset,
                                            match_type='alternative_selected',
                                            confidence=alt_score
                                        )
                                except Exception as save_error:
                                    # Don't block on save error - confirmation is already in session state
                                    st.warning(f"Match saved locally but couldn't save to Google Sheets: {save_error}")

                                st.rerun()

                # Add search feature
                st.markdown("**Search for different slide:**")
                search_query = st.text_input(
                    "Search slide names",
                    key=f"{match_key}_search_input",
                    placeholder="e.g., 'short sleeve tee'"
                )

                if search_query:
                    matching_slides = [
                        name for name in pptx_product_names
                        if search_query.lower() in name.lower()
                    ]

                    if matching_slides:
                        st.caption(f"Found {len(matching_slides)} matching slides:")
                        for search_idx, slide_name in enumerate(matching_slides[:10]):
                            search_col1, search_col2 = st.columns([4, 1])
                            with search_col1:
                                st.markdown(f"- {slide_name}")
                            with search_col2:
                                if st.button(f"Use", key=f"{match_key}_search_{search_idx}", use_container_width=True):
                                    # Set confirmation in session state
                                    st.session_state.match_confirmations[result.gs_product_name] = {
                                        'confirmed': True,
                                        'pptx_name': slide_name
                                    }

                                    # Save search selection to Google Sheets
                                    try:
                                        if pptx_name_to_index and slide_name in pptx_name_to_index:
                                            slide_index = pptx_name_to_index[slide_name]
                                            save_confirmed_match(
                                                product_name=result.gs_product_name,
                                                slide_index=slide_index,
                                                slide_title=slide_name,
                                                dataset=current_dataset,
                                                match_type='search_selected',
                                                confidence=0
                                            )
                                    except Exception as save_error:
                                        # Don't block on save error - confirmation is already in session state
                                        st.warning(f"Match saved locally but couldn't save to Google Sheets: {save_error}")

                                    st.rerun()

                        if len(matching_slides) > 10:
                            st.caption(f"...and {len(matching_slides) - 10} more. Refine your search.")
                    else:
                        st.info("No slides found. Try different keywords.")

                # Add Skip and Cancel buttons
                st.markdown("")
                col_skip, col_cancel = st.columns(2)
                with col_skip:
                    if st.button("Skip this product", key=f"{match_key}_skip_alt", use_container_width=True):
                        st.session_state.match_confirmations[result.gs_product_name] = {
                            'confirmed': False,
                            'skipped': True
                        }
                        st.rerun()

                with col_cancel:
                    if st.button("Cancel", key=f"{match_key}_cancel_alt", type="secondary",
                                 help="Return without making changes", use_container_width=True):
                        # Clear the show_alternatives flag to close the change interface
                        st.session_state.match_confirmations[result.gs_product_name] = {
                            'confirmed': False,
                            'show_alternatives': False
                        }
                        st.rerun()

                st.markdown("")

            # Show search inline for poor matches
            if show_search and match_type == 'poor':
                st.markdown("")
                st.markdown(f"**Search for slide for {result.gs_product_name}:**")

                search_query = st.text_input(
                    "Enter slide name to search",
                    key=f"{match_key}_poor_search_input",
                    placeholder="e.g., 'honey', 'infused', 'sampler'"
                )

                if search_query:
                    matching_slides = [
                        name for name in pptx_product_names
                        if search_query.lower() in name.lower()
                    ]

                    if matching_slides:
                        st.caption(f"Found {len(matching_slides)} matching slides:")
                        for search_idx, slide_name in enumerate(matching_slides[:15]):
                            search_col1, search_col2 = st.columns([4, 1])
                            with search_col1:
                                st.markdown(f"- {slide_name}")
                            with search_col2:
                                if st.button(f"Use", key=f"{match_key}_poor_search_{search_idx}", use_container_width=True):
                                    # Set confirmation in session state
                                    st.session_state.match_confirmations[result.gs_product_name] = {
                                        'confirmed': True,
                                        'pptx_name': slide_name
                                    }

                                    # Save poor match search selection to Google Sheets
                                    try:
                                        if pptx_name_to_index and slide_name in pptx_name_to_index:
                                            slide_index = pptx_name_to_index[slide_name]
                                            save_confirmed_match(
                                                product_name=result.gs_product_name,
                                                slide_index=slide_index,
                                                slide_title=slide_name,
                                                dataset=current_dataset,
                                                match_type='manual_search',
                                                confidence=0
                                            )
                                    except Exception as save_error:
                                        # Don't block on save error - confirmation is already in session state
                                        st.warning(f"Match saved locally but couldn't save to Google Sheets: {save_error}")

                                    st.rerun()

                        if len(matching_slides) > 15:
                            st.caption(f"...and {len(matching_slides) - 15} more. Refine your search.")
                    else:
                        st.info("No slides found. Try different keywords.")

                # Add Skip and Cancel buttons for poor matches
                st.markdown("")
                col_skip_poor, col_cancel_poor = st.columns(2)
                with col_skip_poor:
                    if st.button("Skip this product", key=f"{match_key}_skip_poor", use_container_width=True):
                        st.session_state.match_confirmations[result.gs_product_name] = {
                            'confirmed': False,
                            'skipped': True
                        }
                        st.rerun()

                with col_cancel_poor:
                    if st.button("Cancel", key=f"{match_key}_cancel_poor", type="secondary",
                                 help="Return without making changes", use_container_width=True):
                        # Clear the show_search flag to close the change interface
                        st.session_state.match_confirmations[result.gs_product_name] = {
                            'confirmed': False,
                            'show_search': False
                        }
                        st.rerun()

                st.markdown("")

        st.divider()

    else:
        st.info("No products to match.")

    st.markdown("---")

    # Check if all fuzzy matches are confirmed
    all_confirmed = True
    pending_confirmations = []

    for result in fuzzy_matches:
        confirmation = st.session_state.match_confirmations.get(result.gs_product_name, {})
        if not confirmation.get('confirmed') and not confirmation.get('skipped'):
            all_confirmed = False
            pending_confirmations.append(result.gs_product_name)

    if not all_confirmed:
        st.warning(f"Please review {len(pending_confirmations)} pending matches before generating PowerPoint.")
        with st.expander("Pending Confirmations"):
            for product in pending_confirmations:
                st.markdown(f"- {product}")
    else:
        # Build final confirmed matches dict
        confirmed_matches = {}

        # Add exact matches (auto-confirmed)
        for result in exact_matches:
            confirmed_matches[result.gs_product_name] = result.pptx_product_name

        # Add fuzzy matches (user-confirmed)
        for result in fuzzy_matches:
            confirmation = st.session_state.match_confirmations.get(result.gs_product_name, {})
            if confirmation.get('confirmed'):
                confirmed_matches[result.gs_product_name] = confirmation['pptx_name']

        # Add poor/no matches (manually selected)
        if poor_matches or no_matches:
            all_poor = poor_matches + no_matches
            for result in all_poor:
                confirmation = st.session_state.match_confirmations.get(result.gs_product_name, {})
                if confirmation.get('confirmed'):
                    confirmed_matches[result.gs_product_name] = confirmation['pptx_name']

        # Show summary
        st.success(f"Ready to generate PowerPoint with {len(confirmed_matches)} products!")

        # ============================================================
        # VARIANT DETECTION AND GROUPING (v6.13)
        # ============================================================
        from src.pptx_generator import detect_variant_groups, check_pricing_consistency, calculate_proposal_pricing

        # Detect if multiple products match to same slide (variant groups)
        variant_groups, single_products = detect_variant_groups(confirmed_matches)

        # Initialize variant grouping preferences and pricing consistency flags if not exists
        if 'variant_grouping_prefs' not in st.session_state:
            st.session_state.variant_grouping_prefs = {}
        if 'variant_pricing_consistent' not in st.session_state:
            st.session_state.variant_pricing_consistent = {}

        # Show variant confirmation UI if variants detected
        if variant_groups:
            st.markdown("---")
            st.subheader("⚠️ Multi-Variant Products Detected")
            st.info(
                "Multiple products matched to the same PowerPoint slide. "
                "These are typically size/flavor variants."
            )

            for slide_name, products in variant_groups.items():
                # Calculate pricing for all variants to check consistency
                pricing_data_list = []
                for gs_name in products:
                    proposal_item = next(
                        (item for item in st.session_state.proposal_products
                         if item['product_data']['Product/Service'] == gs_name),
                        None
                    )
                    if proposal_item:
                        pricing_data = calculate_proposal_pricing(
                            proposal_item,
                            get_unit_price_new_system,
                            st.session_state.get('marketing_rounding', False),
                            st.session_state.get('discount_percent', 0)
                        )
                        if pricing_data:
                            pricing_data_list.append(pricing_data)

                # Check pricing consistency
                has_consistent_pricing = check_pricing_consistency(pricing_data_list)
                st.session_state.variant_pricing_consistent[slide_name] = has_consistent_pricing

                # Expander title with pricing indicator
                if has_consistent_pricing:
                    expander_title = f"{slide_name} ({len(products)} variants) - Consistent Pricing"
                else:
                    expander_title = f"{slide_name} ({len(products)} variants) - Variable Pricing"

                with st.expander(expander_title, expanded=True):
                    st.markdown("**Products matched to this slide:**")

                    # Show each product with its price and MOQ
                    for idx, gs_name in enumerate(products):
                        if idx < len(pricing_data_list):
                            price = pricing_data_list[idx].get('client_price', 0)
                            moq = pricing_data_list[idx].get('moq', 0)
                            st.markdown(f"• {gs_name} - MOQ: {moq}, Price: ${price:.2f}")
                        else:
                            st.markdown(f"• {gs_name}")

                    # Get partner info to check if all variants are from same partner
                    partners = set()
                    for prod in products:
                        prod_item = next(
                            (item for item in st.session_state.proposal_products
                             if item['product_data']['Product/Service'] == prod),
                            None
                        )
                        if prod_item:
                            partner = prod_item['product_data'].get('Partner', '')
                            if partner:
                                partners.add(partner)

                    # Warning if multiple partners
                    if len(partners) > 1:
                        st.warning(
                            f"⚠️ These products are from different partners: {', '.join(partners)}. "
                            "Creating separate slides is recommended."
                        )

                    # Conditional radio button options based on pricing consistency
                    if has_consistent_pricing:
                        options = [
                            "Display single row (all variants have same pricing)",
                            "Display all variants (show each variant in separate row)",
                            "Create separate slides (duplicate slide for each variant)",
                            "Skip these products"
                        ]
                        default_choice = 0  # Simple table by default for consistent pricing
                    else:
                        options = [
                            "Display together (recommended - fills multiple table rows)",
                            "Create separate slides (duplicate slide for each variant)",
                            "Skip these products"
                        ]
                        default_choice = 0 if len(partners) <= 1 else 1  # Default to "together" unless multiple partners

                    # Get existing preference or use default
                    existing_pref = st.session_state.variant_grouping_prefs.get(slide_name, options[default_choice])
                    if existing_pref not in options:
                        existing_pref = options[default_choice]

                    group_choice = st.radio(
                        "How should these be displayed?",
                        options=options,
                        key=f"variant_choice_{slide_name}",
                        index=options.index(existing_pref) if existing_pref in options else default_choice
                    )

                    st.session_state.variant_grouping_prefs[slide_name] = group_choice

        # ============================================================
        # IMPACT SLIDE SELECTION (SIMPLIFIED)
        # ============================================================
        st.markdown("---")
        st.subheader("Step 2: Impact Slides")

        # Import impact slide functions
        from src.slide_matcher import extract_unique_partners, PARTNER_IMPACT_SLIDES, find_all_impact_slides

        # Extract unique partners from proposal
        unique_partners = extract_unique_partners(st.session_state.proposal_products)

        if unique_partners:
            # Initialize impact selections if not exists
            if 'impact_slide_selections' not in st.session_state:
                st.session_state.impact_slide_selections = {}

            # Auto-select from reference table for all partners
            partners_with_slides = []
            partners_without_slides = []

            for partner in unique_partners:
                auto_selected = PARTNER_IMPACT_SLIDES.get(partner)
                if auto_selected:
                    # Auto-select if not already set
                    current_selection = st.session_state.impact_slide_selections.get(partner)
                    if not current_selection or current_selection.get('slide_index') is None:
                        st.session_state.impact_slide_selections[partner] = auto_selected.copy()
                    partners_with_slides.append(partner)
                else:
                    partners_without_slides.append(partner)
                    st.session_state.impact_slide_selections[partner] = {
                        'slide_title': None,
                        'slide_index': None
                    }

            # Show simple summary message
            if partners_with_slides:
                partner_list = ", ".join(partners_with_slides)
                st.success(f"Impact slides found for: {partner_list}")

            if partners_without_slides:
                partner_list = ", ".join(partners_without_slides)
                st.warning(f"No impact slides found for: {partner_list}")

            # Collapsible customization section
            with st.expander("Customize Impact Slides (Optional)", expanded=False):
                st.caption("Change or remove impact slides for specific partners")

                from pathlib import Path

                for partner in unique_partners:
                    active_selection = st.session_state.impact_slide_selections.get(partner, {})

                    st.markdown(f"**{partner}**")

                    # Load all impact slide options (from cloud or local)
                    pptx_template = get_template_path('all_slides', show_loading=False)
                    if pptx_template:
                        all_impact_slides = find_all_impact_slides(pptx_template)
                    else:
                        st.error("Could not load PowerPoint template")
                        continue

                    dropdown_options = ["None - Skip impact slide"]
                    dropdown_options.extend([f"{slide['slide_title']}" for slide in all_impact_slides])

                    # Find current selection index
                    current_title = active_selection.get('slide_title')
                    try:
                        default_index = dropdown_options.index(current_title) if current_title else 0
                    except ValueError:
                        default_index = 0

                    selected_option = st.selectbox(
                        f"Impact slide for {partner}",
                        options=dropdown_options,
                        index=default_index,
                        key=f"impact_select_{partner}",
                        label_visibility="collapsed"
                    )

                    # Update selection immediately on change
                    if selected_option == "None - Skip impact slide":
                        st.session_state.impact_slide_selections[partner] = {
                            'slide_title': None,
                            'slide_index': None
                        }
                    else:
                        selected_slide = next(
                            (slide for slide in all_impact_slides if slide['slide_title'] == selected_option),
                            None
                        )
                        if selected_slide:
                            st.session_state.impact_slide_selections[partner] = {
                                'slide_title': selected_slide['slide_title'],
                                'slide_index': selected_slide['slide_index']
                            }

                    st.markdown("")  # Spacing

        else:
            st.info("No products selected - add products to see impact slides")
            st.session_state.impact_slide_selections = {}

        st.markdown("---")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Reset Confirmations", use_container_width=True):
                st.session_state.match_confirmations = {}
                st.session_state.impact_slide_selections = {}
                st.session_state.generated_pptx = None
                st.rerun()

        with col2:
            if st.button("Generate PowerPoint Presentation", type="primary", use_container_width=True):
                try:
                    import time
                    start_time = time.time()

                    # Memory optimization: clear template cache before generation
                    if USE_MEMORY_OPTIMIZATION:
                        from src.template_loader import clear_template_cache
                        clear_template_cache()
                        gc.collect()
                        st.info("Memory optimization enabled - using direct download mode")

                    # Import generator functions
                    from src.pptx_generator import (
                        create_complete_proposal_presentation,
                        download_presentation
                    )

                    # Load templates from cloud/local (with loading spinner)
                    st.info(f"Using template: **{get_template_name('all_slides')}**")

                    # Load templates with memory optimization if enabled
                    november_template_path = get_template_path('all_slides', show_loading=True, use_cache=not USE_MEMORY_OPTIMIZATION)
                    intro_outro_template_path = get_template_path('intro_outro', show_loading=False, use_cache=not USE_MEMORY_OPTIMIZATION)

                    # Validation checks
                    if not november_template_path:
                        st.error("PowerPoint template could not be loaded. Please check Google Drive access.")
                        return None

                    if not intro_outro_template_path:
                        st.error("Intro/Outro template could not be loaded.")
                        return None

                    if len(confirmed_matches) == 0:
                        st.warning("No products confirmed for generation. Please confirm at least one product match.")
                        return None

                    # Create presentation with progress indicator
                    progress_container = st.empty()
                    progress_container.info(f"Step 1/5: Loading templates...")

                    # Get proposal settings
                    marketing_rounding = st.session_state.get('proposal_marketing_rounding', False)
                    discount_percent = st.session_state.get('proposal_discount_percent', 0.0)

                    # Get selected impact slides (for overrides)
                    # Build impact_slide_overrides dict: {partner: {"slide_index": X, "slide_title": Y}}
                    impact_slide_overrides = {}
                    if 'impact_slide_selections' in st.session_state:
                        for partner, selection in st.session_state.impact_slide_selections.items():
                            if selection.get('slide_index') is not None:
                                impact_slide_overrides[partner] = selection

                    # Count total slides
                    num_products = len(confirmed_matches)
                    num_impacts = len([s for s in impact_slide_overrides.values() if s.get('slide_index') is not None])

                    # Get variant groups and preferences
                    variant_groups_for_generation = variant_groups if variant_groups else None
                    variant_prefs_for_generation = st.session_state.get('variant_grouping_prefs', None)

                    # Debug output
                    if variant_groups_for_generation:
                        print(f"DEBUG: Passing {len(variant_groups_for_generation)} variant groups to generator")
                        for slide_name, products in variant_groups_for_generation.items():
                            print(f"  - {slide_name}: {products}")
                        print(f"DEBUG: Preferences: {variant_prefs_for_generation}")
                    else:
                        print("DEBUG: No variant groups detected")

                    # Create complete presentation (products + impacts + outro only)
                    progress_container.info(f"Step 2/4: Selecting and updating {num_products} product slide(s) + {num_impacts} impact slide(s)...")
                    prs = create_complete_proposal_presentation(
                        str(november_template_path),
                        str(intro_outro_template_path),
                        confirmed_matches,
                        st.session_state.proposal_products,
                        get_unit_price_new_system,
                        marketing_rounding,
                        discount_percent,
                        impact_slide_overrides if impact_slide_overrides else None,
                        variant_groups_for_generation,
                        variant_prefs_for_generation
                    )

                    progress_container.info(f"Step 3/4: Adding outro slides (4 slides)...")

                    # Convert to downloadable format
                    progress_container.info("Step 4/4: Preparing download...")
                    client_name = st.session_state.order_details.get('company_name', 'Client')
                    pptx_file = download_presentation(prs, client_name)

                    # Memory optimization: force garbage collection after generation
                    if USE_MEMORY_OPTIMIZATION:
                        gc.collect()

                    # Calculate generation time
                    generation_time = time.time() - start_time

                    # Store in session state to persist across reruns
                    st.session_state.generated_pptx = pptx_file
                    st.session_state.generated_pptx_filename = f"Proposal_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pptx"
                    st.session_state.pptx_product_count = len(confirmed_matches)
                    st.session_state.pptx_generation_time = generation_time

                    # Clear progress indicator
                    progress_container.empty()

                except Exception as e:
                    st.error(f"PowerPoint generation failed: {str(e)}")
                    st.error("Please check that all products have valid pricing data and try again.")
                    with st.expander("View detailed error (for debugging)"):
                        st.exception(e)
                    return None

        with col3:
            if st.button("Close", use_container_width=True):
                st.session_state.show_pptx_matching = False
                st.session_state.match_confirmations = {}
                st.session_state.generated_pptx = None
                st.rerun()

        # Show download button if presentation was generated
        if 'generated_pptx' in st.session_state and st.session_state.generated_pptx is not None:
            generation_time = st.session_state.get('pptx_generation_time', 0)
            st.success(f"PowerPoint generated successfully in {generation_time:.1f} seconds!")

            # Show generation summary
            col_summary1, col_summary2 = st.columns(2)
            with col_summary1:
                st.metric("Products Included", st.session_state.pptx_product_count)
            with col_summary2:
                st.metric("File Name", st.session_state.generated_pptx_filename)

            # Show instructions for reordering intro slides
            st.info("**Final step:** In PowerPoint, move the 8 intro slides (they're grouped together after products) to the beginning. Select slides → Drag to top (~5 seconds).")

            # Warning about PowerPoint repair message
            st.warning("**Note:** PowerPoint may show a 'repair presentation' warning when opening the file. This is normal - click 'Repair' to proceed. The content will display correctly.")

            st.download_button(
                label="Download PowerPoint Presentation",
                data=st.session_state.generated_pptx,
                file_name=st.session_state.generated_pptx_filename,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
                use_container_width=True
            )

    return None

# ============================================================
# DATA LOADING
# ============================================================
try:
    # Check if we need to reload data (first load or dataset changed)
    need_reload = (
        'df_template' not in st.session_state or
        st.session_state.get('loaded_dataset') != st.session_state.selected_dataset
    )

    if need_reload:
        df_template, df_metadata, df_partner_info = load_pricing_data(st.session_state.selected_dataset)
        st.session_state.df_template = df_template
        st.session_state.df_metadata = df_metadata
        st.session_state.df_partner_info = df_partner_info
        st.session_state.data_loaded_at = datetime.now()
        st.session_state.loaded_dataset = st.session_state.selected_dataset

        # Extract and store partner contacts
        st.session_state.partner_contacts = extract_partner_contacts(df_partner_info)

        # Clear proposal and order data when switching datasets (prevents data mismatch)
        if st.session_state.get('loaded_dataset') != st.session_state.selected_dataset:
            st.session_state.proposal_products = []
            st.session_state.order_items = []
            st.warning("Dataset changed - cleared existing proposals and orders to prevent data mismatch")

    df_template = st.session_state.df_template
    df_metadata = st.session_state.df_metadata
    df_partner_info = st.session_state.df_partner_info

    # Count unique partner-product combinations
    unique_products = len(df_template)
    unique_partners = len(df_template['Partner'].unique())

    # Get active dataset name
    active_dataset_name = DATASET_CONFIGS[st.session_state.selected_dataset]['name']

    st.success(f"Loaded {unique_products} products from {unique_partners} partners ({active_dataset_name})")

    # Status message for proposals and orders
    num_proposals = len(st.session_state.proposal_products)
    num_orders = len(st.session_state.order_items)

    proposal_status = f"{num_proposals} product{'s' if num_proposals != 1 else ''}" if num_proposals > 0 else "Empty"
    order_status = f"{num_orders} product{'s' if num_orders != 1 else ''}" if num_orders > 0 else "Empty"

    st.info(f"Proposals: {proposal_status} | Orders: {order_status}")

except Exception as e:
    error_msg = str(e)

    # Check if this is a real dataset structure issue
    if st.session_state.selected_dataset == 'real' and ('Data' in error_msg or 'worksheet' in error_msg.lower()):
        st.error("Real pricing dataset is not yet properly structured.")
        st.warning("The real data spreadsheet needs to have the same structure as the demo data:\n"
                   "- Sheet 1: 'Data' (pricing data)\n"
                   "- Sheet 2: 'Metadata' (field definitions)\n"
                   "- Sheet 3: 'Partner-Specific Info' (partner contacts)")
        st.info("Please switch to 'Demo Data' in the sidebar, or complete the real dataset structure first.")
        st.stop()
    else:
        st.error(f"Failed to load data: {error_msg}")
        st.stop()

# ============================================================
# TAB STRUCTURE
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Proposal Generator",
    "Client Order Form Generator",
    "Order & Client Info",
    "Execution & Accounting"
])

# ============================================================
# TAB 1: PROPOSAL GENERATOR
# ============================================================
with tab1:
    st.header("Proposal Generator - Product Catalog & Pricing")
    st.caption("Browse products, configure proposals, and generate client quotes (tables & PowerPoint)")
    st.divider()

    # ============================================================
    # SECTION 1: BROWSE & FILTER PRODUCTS (Combined Sections 1+2)
    # ============================================================
    st.subheader("1. Browse & Filter Products")
    st.caption(f"{len(df_template)} total products available")

    # Search bar - prominently placed above all filters
    search_query = st.text_input(
        "Search product names",
        placeholder="Type to search product names...",
        key="product_search",
        help="Search filters products by name only. Use the filters below for partner and country."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Client Budget**")
        client_budget = st.number_input(
            "Max client price per unit ($) - Optional",
            min_value=0.0,
            value=st.session_state.proposal_filters.get('client_budget') or 0.0,
            step=1.0,
            key="filter_client_budget"
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
    st.session_state.proposal_filters['client_budget'] = client_budget if client_budget > 0 else None
    st.session_state.proposal_filters['partners'] = selected_partners
    st.session_state.proposal_filters['countries'] = selected_countries

    # Apply filters
    filtered_df = df_template.copy()

    if selected_partners:
        filtered_df = filtered_df[filtered_df["Partner"].isin(selected_partners)]

    if selected_countries:
        filtered_df = filtered_df[filtered_df["Country of Origin"].isin(selected_countries)]

    # Price filtering based on client price (cost * 2 for 100% markup)
    if client_budget and client_budget > 0:
        price_filtered_indices = []
        for idx, row in filtered_df.iterrows():
            # Get cost estimate at quantity 100
            base_cost, _, _ = get_unit_price_new_system(row, 100)
            if base_cost:
                # Calculate client price (100% markup)
                client_price = base_cost * 2
                if client_price > client_budget:
                    continue
                price_filtered_indices.append(idx)
        filtered_df = filtered_df.loc[price_filtered_indices]

    # Search filtering - only search product names
    if search_query:
        search_lower = search_query.lower()
        search_mask = filtered_df['Product/Service'].str.lower().str.contains(search_lower, na=False)
        filtered_df = filtered_df[search_mask]

    st.divider()

    # Enhanced filter results message
    if search_query and len(filtered_df) == 0:
        st.caption(f"**No products found with name containing '{search_query}'** - Try a different search term")
    elif search_query:
        st.caption(f"**Filtered Results:** {len(filtered_df)} products with names containing '{search_query}'")
    else:
        st.caption(f"**Filtered Results:** {len(filtered_df)} products match your filters")

    # Display success message if a product was just added
    if 'show_success_message' in st.session_state and st.session_state.show_success_message:
        st.toast(f"Added {st.session_state.success_product_name} to proposal!")
        st.session_state.show_success_message = False

    # Bulk add success message
    if 'show_bulk_success_message' in st.session_state and st.session_state.show_bulk_success_message:
        st.toast(st.session_state.bulk_success_message)
        st.session_state.show_bulk_success_message = False

    # ============================================================
    # BULK ACTIONS SECTION
    # ============================================================
    if len(filtered_df) > 0:
        with st.expander("Bulk Actions - Add All Products from Partner(s)", expanded=False):
            st.caption("Quickly add all products from one or more partners to your proposal")

            # Add JavaScript to capture scroll position for bulk add button
            components.html("""
                <script>
                    // Store scroll position before bulk add button click
                    const buttons = window.parent.document.querySelectorAll('button');
                    buttons.forEach(button => {
                        if (button.textContent.includes('Add') && button.textContent.includes('Products')) {
                            button.addEventListener('click', function() {
                                const scrollPos = window.parent.document.querySelector('section.main').scrollTop;
                                window.parent.sessionStorage.setItem('streamlit_scroll_position', scrollPos);
                            });
                        }
                    });
                </script>
            """, height=0)

            # "Add All Products" button at the top (for testing)
            st.markdown("**Quick Add All Products (Testing)**")

            # Count how many products would be added
            existing_products = {item['product_data']['Product/Service'] for item in st.session_state.proposal_products}
            new_products_all = [row for idx, row in filtered_df.iterrows() if row['Product/Service'] not in existing_products]
            new_count_all = len(new_products_all)
            duplicate_count_all = len(filtered_df) - new_count_all

            col_info, col_button = st.columns([3, 1])
            with col_info:
                if new_count_all > 0:
                    st.info(f"Will add **{new_count_all} new product(s)** from filtered results ({len(filtered_df)} total)")
                    if duplicate_count_all > 0:
                        st.caption(f"({duplicate_count_all} already in proposal, will be skipped)")
                else:
                    st.warning(f"All {len(filtered_df)} filtered product(s) are already in your proposal")

            with col_button:
                if new_count_all > 0:
                    if st.button(f"Add All {new_count_all}", type="secondary", use_container_width=True, key="add_all_products_button"):
                        # Add all new products to proposal with MSRP or 100% markup
                        for product_row in new_products_all:
                            # Determine markup: use MSRP if enabled, otherwise 100%
                            if st.session_state.proposal_use_msrp:
                                markup = calculate_msrp_markup(product_row.to_dict())
                            else:
                                markup = 100.0

                            proposal_item = {
                                'product_data': product_row.to_dict(),
                                'markup_percent': markup
                            }
                            st.session_state.proposal_products.append(proposal_item)

                        # Set success message
                        st.session_state.show_bulk_success_message = True
                        st.session_state.bulk_success_message = f"Added **all {new_count_all} filtered products** to proposal!"

                        # Keep catalog expanded after bulk add
                        st.session_state.keep_catalog_expanded = True
                        st.rerun()

            st.divider()
            st.markdown("**Add by Partner**")

            # Get unique partners from filtered results
            available_partners = sorted(filtered_df["Partner"].unique().tolist())

            # Partner selection for bulk add
            bulk_partners = st.multiselect(
                "Select partner(s) to add all their products:",
                options=available_partners,
                key="bulk_add_partners",
                help="All products from selected partners will be added (filtered products only)"
            )

            if bulk_partners:
                # Count how many new products would be added
                products_to_add = filtered_df[filtered_df["Partner"].isin(bulk_partners)]

                # Get existing product names in proposal
                existing_products = {item['product_data']['Product/Service'] for item in st.session_state.proposal_products}

                # Filter out duplicates
                new_products = []
                for idx, row in products_to_add.iterrows():
                    if row['Product/Service'] not in existing_products:
                        new_products.append(row)

                new_count = len(new_products)
                duplicate_count = len(products_to_add) - new_count

                # Show counts
                col1, col2 = st.columns([3, 1])
                with col1:
                    if new_count > 0:
                        st.info(f"Will add **{new_count} new product(s)** from {', '.join(bulk_partners)}")
                        if duplicate_count > 0:
                            st.caption(f"({duplicate_count} already in proposal, will be skipped)")
                    else:
                        st.warning(f"All {len(products_to_add)} product(s) from selected partners are already in your proposal")

                with col2:
                    if new_count > 0:
                        if st.button(f"Add {new_count} Products", type="primary", use_container_width=True, key="bulk_add_button"):
                            # Add all new products to proposal with MSRP or 100% markup
                            for product_row in new_products:
                                # Determine markup: use MSRP if enabled, otherwise 100%
                                if st.session_state.proposal_use_msrp:
                                    markup = calculate_msrp_markup(product_row.to_dict())
                                else:
                                    markup = 100.0

                                proposal_item = {
                                    'product_data': product_row.to_dict(),
                                    'markup_percent': markup
                                }
                                st.session_state.proposal_products.append(proposal_item)

                            # Set success message
                            partner_names = ', '.join(bulk_partners)
                            st.session_state.show_bulk_success_message = True
                            st.session_state.bulk_success_message = f"Added **{new_count} products** from {partner_names} to proposal!"

                            # Keep catalog expanded after bulk add
                            st.session_state.keep_catalog_expanded = True
                            st.rerun()
            else:
                st.caption("Select one or more partners above to see product count")

    if len(filtered_df) == 0:
        if search_query:
            st.warning(f"No products found with name containing '{search_query}'. Try a different search term or adjust filters.")
        else:
            st.warning("No products match your filters. Try adjusting the filter criteria above.")
    else:
        # Keep catalog expanded if user just added a product, otherwise collapse after first product added
        if 'keep_catalog_expanded' in st.session_state and st.session_state.keep_catalog_expanded:
            default_expanded = True
            st.session_state.keep_catalog_expanded = False  # Reset for next time
        else:
            default_expanded = len(st.session_state.proposal_products) == 0

        with st.expander(f"Browse Products ({len(filtered_df)} available)", expanded=default_expanded):
            # Add JavaScript to capture scroll position before button clicks
            components.html("""
                <script>
                    // Store scroll position in sessionStorage before any button click
                    const buttons = window.parent.document.querySelectorAll('button');
                    buttons.forEach(button => {
                        if (button.textContent.includes('Add to Proposal')) {
                            button.addEventListener('click', function() {
                                const scrollPos = window.parent.document.querySelector('section.main').scrollTop;
                                window.parent.sessionStorage.setItem('streamlit_scroll_position', scrollPos);
                            });
                        }
                    });
                </script>
            """, height=0)

            # Table-style header
            header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([3, 1.5, 1, 1.2, 1.5])
            with header_col1:
                st.markdown("**Product Name**")
            with header_col2:
                st.markdown("**Partner**")
            with header_col3:
                st.markdown("**Cost/Unit**")
            with header_col4:
                st.markdown("**Price/Unit (100% markup)**")
            with header_col5:
                st.markdown("**Actions**")

            st.divider()

            # Display filtered products in a compact table-style format
            for idx, row in filtered_df.iterrows():
                product_data = row

                # Calculate cost and client price for display
                preliminary_cost, _, _ = get_unit_price_new_system(product_data, 100)
                estimated_moq = calculate_moq(preliminary_cost * 2) if preliminary_cost else None
                moq_cost, _, _ = get_unit_price_new_system(product_data, estimated_moq) if estimated_moq else (None, None, None)

                # Calculate client price (100% markup)
                moq_client_price = moq_cost * 2 if moq_cost else None

                # Compact row with all essential info
                col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.2, 1.5])

                with col1:
                    st.markdown(f"**{product_data['Product/Service']}**")

                with col2:
                    st.markdown(f"{product_data['Partner']}")

                with col3:
                    if moq_cost:
                        st.markdown(f"${moq_cost:.2f}")
                    else:
                        st.markdown("—")

                with col4:
                    if moq_client_price:
                        st.markdown(f"${moq_client_price:.2f}")
                    else:
                        st.markdown("—")

                with col5:
                    # Add button - adds product to proposal with MSRP or 100% markup
                    if st.button("Add to Proposal", key=f"add_{idx}", use_container_width=True, type="primary"):
                        # Determine markup: use MSRP if enabled, otherwise 100%
                        if st.session_state.proposal_use_msrp:
                            markup = calculate_msrp_markup(product_data.to_dict())
                        else:
                            markup = 100.0

                        proposal_item = {
                            'product_data': product_data.to_dict(),
                            'markup_percent': markup
                        }
                        st.session_state.proposal_products.append(proposal_item)

                        # Set success message
                        st.session_state.show_success_message = True
                        st.session_state.success_product_name = product_data['Product/Service']

                        # Keep catalog expanded after adding product
                        st.session_state.keep_catalog_expanded = True
                        st.rerun()

                # Show additional details inline (no nested expander)
                st.caption(f"Country: {product_data.get('Country of Origin', 'N/A')} | Tiered Pricing: {product_data.get('Pricing Tiers (Y/N)', 'N/A')}")

                # Show MSRP if available
                msrp_raw = product_data.get('MSRP', '')
                if msrp_raw and str(msrp_raw).strip() and str(msrp_raw).strip() not in ['nan', '', '0', '0.0']:
                    from src.helpers import clean_price
                    msrp_value = clean_price(msrp_raw)
                    if msrp_value and msrp_value > 0:
                        st.caption(f"Manufacturer's Suggested Retail Price (MSRP): ${msrp_value:.2f}/unit")

                # Show shipping costs
                shipping_display = format_shipping_display(product_data)
                if shipping_display != "No shipping data":
                    st.caption(f"Shipping: {shipping_display}")

                # Show estimated prices at MOQ
                if moq_cost and estimated_moq:
                    st.caption(f"Est. Cost & Price at MOQ ({estimated_moq} units): ${moq_cost:.2f}/unit cost → ${moq_client_price:.2f}/unit client price (100% markup)")

                # Show description if available
                desc = product_data.get("Marketing Description", "")
                if desc and str(desc).strip() and str(desc).strip() != 'nan':
                    st.caption(f"{desc}")

                st.divider()

    # ============================================================
    # SECTION 2: PROPOSAL PREVIEW & SETTINGS
    # ============================================================
    st.divider()
    st.subheader("2. Proposal Preview & Settings")

    # ============================================================
    # SAVED PROPOSALS SECTION (Always visible)
    # ============================================================
    with st.expander("Saved Proposals", expanded=False):
        st.caption("Save your current proposal or load a previously saved one")

        # Load all saved proposals (cached to reduce API calls)
        refresh_counter = st.session_state.get('saved_data_refresh_counter', 0)
        saved_proposals = cached_load_all_proposals(refresh_counter)

        # Two columns: Load/Delete on left, Save on right
        load_col, save_col = st.columns(2)

        with load_col:
            st.markdown("**Load Proposal**")

            if len(saved_proposals) == 0:
                st.info("No saved proposals yet")
            else:
                # Create dropdown options
                proposal_options = {
                    f"{p['name']} ({p['created_date'][:10]})": p['proposal_id']
                    for p in saved_proposals
                }

                selected_proposal_label = st.selectbox(
                    "Select proposal to load:",
                    options=list(proposal_options.keys()),
                    key="load_proposal_select"
                )

                if selected_proposal_label:
                    selected_proposal_id = proposal_options[selected_proposal_label]

                    # Find full proposal data
                    selected_proposal = next(p for p in saved_proposals if p['proposal_id'] == selected_proposal_id)

                    # Show preview
                    st.caption(f"**Created by:** {selected_proposal['created_by'] or 'Unknown'}")
                    st.caption(f"**Dataset:** {selected_proposal['dataset']}")

                    # Load and Delete buttons
                    load_btn_col, delete_btn_col = st.columns(2)

                    with load_btn_col:
                        if st.button("Load", key="load_proposal_btn", type="primary", use_container_width=True):
                            success, proposal_data, dataset = load_proposal_data(selected_proposal_id)

                            if success:
                                # Check if dataset matches
                                if dataset != st.session_state.selected_dataset:
                                    st.warning(f"WARNING: This proposal was created with {dataset} dataset, but you're currently using {st.session_state.selected_dataset} dataset. Loading anyway...")

                                # Load proposal data into session state
                                st.session_state.proposal_products = proposal_data.get('proposal_products', [])
                                st.session_state.proposal_marketing_rounding = proposal_data.get('proposal_marketing_rounding', False)
                                st.session_state.proposal_use_msrp = proposal_data.get('proposal_use_msrp', True)
                                st.session_state.proposal_discount_type = proposal_data.get('proposal_discount_type', None)
                                st.session_state.proposal_discount_percent = proposal_data.get('proposal_discount_percent', 0.0)
                                st.session_state.proposal_client_budget = proposal_data.get('proposal_client_budget', 0.0)

                                st.success(f"Loaded proposal: {selected_proposal['name']}")
                                st.rerun()
                            else:
                                st.error("Failed to load proposal data")

                    with delete_btn_col:
                        if st.button("Delete", key="delete_proposal_btn", use_container_width=True):
                            # Confirmation dialog using session state
                            if 'confirm_delete_proposal_id' not in st.session_state:
                                st.session_state.confirm_delete_proposal_id = selected_proposal_id
                                st.warning(f"WARNING: Are you sure you want to delete '{selected_proposal['name']}'?")

                                confirm_col1, confirm_col2 = st.columns(2)
                                with confirm_col1:
                                    if st.button("Yes, Delete", key="confirm_delete_yes", type="primary"):
                                        success, message = delete_proposal(st.session_state.confirm_delete_proposal_id)
                                        if success:
                                            clear_saved_data_cache()  # Clear cache after deletion
                                            st.success(message)
                                            del st.session_state.confirm_delete_proposal_id
                                            st.rerun()
                                        else:
                                            st.error(message)
                                with confirm_col2:
                                    if st.button("Cancel", key="confirm_delete_no"):
                                        del st.session_state.confirm_delete_proposal_id
                                        st.rerun()

        with save_col:
            st.markdown("**Save Current Proposal**")

            # Check if there are products to save
            has_products = len(st.session_state.proposal_products) > 0

            if not has_products:
                st.info("Add products to enable saving")

            proposal_name = st.text_input(
                "Proposal name:",
                key="save_proposal_name",
                placeholder="e.g., Client ABC Winter Campaign",
                disabled=not has_products
            )

            created_by = st.text_input(
                "Your name (optional):",
                key="save_proposal_creator",
                placeholder="e.g., John Smith",
                disabled=not has_products
            )

            if st.button("Save Proposal", key="save_proposal_btn", type="primary", use_container_width=True, disabled=not has_products):
                if not proposal_name or not proposal_name.strip():
                    st.error("Please enter a proposal name")
                else:
                    # Prepare proposal data
                    proposal_data = {
                        'proposal_products': st.session_state.proposal_products,
                        'proposal_marketing_rounding': st.session_state.proposal_marketing_rounding,
                        'proposal_use_msrp': st.session_state.proposal_use_msrp,
                        'proposal_discount_type': st.session_state.get('proposal_discount_type'),
                        'proposal_discount_percent': st.session_state.get('proposal_discount_percent', 0.0),
                        'proposal_client_budget': st.session_state.get('proposal_client_budget', 0.0)
                    }

                    success, message, result = save_proposal(
                        name=proposal_name.strip(),
                        created_by=created_by.strip() if created_by else "",
                        proposal_data=proposal_data,
                        dataset=st.session_state.selected_dataset
                    )

                    if success:
                        update_last_save_time('proposal')
                        clear_saved_data_cache()  # Clear cache to show new proposal
                        st.success(message)
                        st.rerun()  # Rerun to clear form
                    else:
                        # Check if it's a naming conflict
                        if result:  # result contains suggested name
                            st.error(message)
                            # Offer to save with suggested name
                            if st.button(f"Save as '{result}'", key="save_with_new_name"):
                                success2, message2, _ = save_proposal(
                                    name=result,
                                    created_by=created_by.strip() if created_by else "",
                                    proposal_data=proposal_data,
                                    dataset=st.session_state.selected_dataset
                                )
                                if success2:
                                    update_last_save_time('proposal')
                                    clear_saved_data_cache()  # Clear cache to show new proposal
                                    st.success(message2)
                                    st.rerun()
                        else:
                            st.error(message)

    st.divider()

    # Product count and status
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
            # Use MSRP pricing checkbox (defaults to checked)
            st.session_state.proposal_use_msrp = st.checkbox(
                "Use MSRP pricing when available",
                value=st.session_state.proposal_use_msrp,
                key="proposal_use_msrp_checkbox",
                help="When enabled, products with MSRP will have markup automatically calculated to match MSRP. Products without MSRP will use 100% markup."
            )

            # $0.50 rounding (new feature, defaults to checked)
            st.session_state.proposal_fifty_cent_rounding = st.checkbox(
                "Round prices to nearest $0.50",
                value=st.session_state.proposal_fifty_cent_rounding,
                key="proposal_fifty_cent_rounding_checkbox",
                help="Rounds all prices to nearest 50 cents (e.g., $24.37 → $24.50)"
            )

            # Marketing rounding
            st.session_state.proposal_marketing_rounding = st.checkbox(
                "Apply marketing rounding (e.g., $60 → $59)",
                value=st.session_state.proposal_marketing_rounding,
                key="proposal_marketing_rounding_checkbox",
                help="Apply charm pricing to prices ending in 0 (e.g., $60 → $59). Applied after $0.50 rounding."
            )

        st.divider()

        # Product table with pricing details and editable markup
        st.markdown("### Products in Proposal")

        # Table header
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([3, 1.2, 1.2, 1.2, 1.2, 0.8])
        with header_col1:
            st.markdown("**Product**")
        with header_col2:
            st.markdown("**PBP Cost**")
        with header_col3:
            st.markdown("**Markup %**")
        with header_col4:
            st.markdown("**Client Price**")
        with header_col5:
            st.markdown("**MSRP**")
        with header_col6:
            st.markdown("**Remove**")

        st.divider()

        # Display each product in table format
        for idx, item in enumerate(st.session_state.proposal_products):
            product_data = item['product_data']

            # Calculate PBP cost and client price at quantity 100 for display
            base_cost, _, _ = get_unit_price_new_system(product_data, 100)

            if base_cost:
                # Calculate client price with markup
                client_price = base_cost * (1 + item['markup_percent'] / 100)

                # Apply $0.50 rounding if enabled
                client_price = round_to_nearest_fifty_cents(
                    client_price,
                    st.session_state.proposal_fifty_cent_rounding
                )

                # Apply marketing rounding if enabled (after $0.50 rounding)
                client_price = apply_marketing_rounding(
                    client_price,
                    st.session_state.proposal_marketing_rounding
                )
            else:
                client_price = None

            col1, col2, col3, col4, col5, col6 = st.columns([3, 1.2, 1.2, 1.2, 1.2, 0.8])

            with col1:
                st.markdown(f"{product_data['Product/Service']}")
                st.caption(f"Partner: {product_data['Partner']}")

            with col2:
                # Show PBP cost
                if base_cost:
                    st.markdown(f"${base_cost:.2f}")
                else:
                    st.markdown("—")

            with col3:
                # Editable markup field
                new_markup = st.number_input(
                    f"Markup for {idx}",
                    min_value=-50.0,  # Allow negative markup for below-cost pricing
                    value=item['markup_percent'],
                    step=5.0,
                    key=f"markup_{idx}",
                    label_visibility="collapsed"
                )
                # Update markup if changed
                if new_markup != item['markup_percent']:
                    st.session_state.proposal_products[idx]['markup_percent'] = new_markup
                    # Set flag to prevent circular updates
                    st.session_state[f'updating_from_markup_{idx}'] = True

            with col4:
                # Editable client price field
                if base_cost and client_price:
                    # Check if we're updating from markup to prevent circular updates
                    if st.session_state.get(f'updating_from_markup_{idx}', False):
                        # Just display the calculated price, don't create input
                        st.markdown(f"${client_price:.2f}")
                        # Clear the flag
                        st.session_state[f'updating_from_markup_{idx}'] = False
                    else:
                        new_price = st.number_input(
                            f"Price for {idx}",
                            min_value=0.01,
                            value=client_price,
                            step=1.0,
                            format="%.2f",
                            key=f"price_{idx}",
                            label_visibility="collapsed"
                        )
                        # Update markup if price changed
                        if abs(new_price - client_price) > 0.01:  # Check if meaningfully different
                            # Calculate new markup from the price
                            new_markup_calc = calculate_markup_from_price(base_cost, new_price)
                            st.session_state.proposal_products[idx]['markup_percent'] = new_markup_calc
                            st.rerun()
                else:
                    st.markdown("—")

            with col5:
                # Show MSRP if available
                msrp = clean_price(product_data.get('MSRP', ''))
                if msrp and msrp > 0:
                    st.markdown(f"${msrp:.2f}")
                else:
                    st.markdown("—")

            with col6:
                if st.button("✕", key=f"remove_{idx}", help=f"Remove {product_data['Product/Service']}", use_container_width=True):
                    st.session_state.proposal_products.pop(idx)
                    st.rerun()

            st.divider()

    # ============================================================
    # SECTION 3: GENERATE PROPOSAL TABLES
    # ============================================================
    st.divider()
    st.subheader("3. Generate Proposal Tables")

    if len(st.session_state.proposal_products) == 0:
        st.caption("Add products to generate proposal tables")
    else:
        # Default to collapsed to save space, user can expand to view
        with st.expander(f"View Proposal Tables ({len(st.session_state.proposal_products)} products)", expanded=False):
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

                        # Apply $0.50 rounding if enabled
                        moq_product_price_per_unit = round_to_nearest_fifty_cents(
                            moq_product_price_per_unit,
                            st.session_state.proposal_fifty_cent_rounding
                        )

                        # Apply marketing rounding if enabled (after $0.50 rounding)
                        moq_product_price_per_unit = apply_marketing_rounding(
                            moq_product_price_per_unit,
                            st.session_state.proposal_marketing_rounding
                        )

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

                                    # Apply $0.50 rounding if enabled
                                    budget_qty_price_per_unit = round_to_nearest_fifty_cents(
                                        budget_qty_price_per_unit,
                                        st.session_state.proposal_fifty_cent_rounding
                                    )

                                    # Apply marketing rounding if enabled (after $0.50 rounding)
                                    budget_qty_price_per_unit = apply_marketing_rounding(
                                        budget_qty_price_per_unit,
                                        st.session_state.proposal_marketing_rounding
                                    )

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

                            # Apply $0.50 rounding after discount if enabled
                            client_price = round_to_nearest_fifty_cents(
                                client_price,
                                st.session_state.proposal_fifty_cent_rounding
                            )

                            # Apply marketing rounding again after discount if enabled
                            client_price = apply_marketing_rounding(
                                client_price,
                                st.session_state.proposal_marketing_rounding
                            )

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
            # Generate comprehensive CSV matching UI display
            csv_lines = []
            csv_lines.append("PEACE BY PIECE - PRODUCT PROPOSAL")
            csv_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            csv_lines.append("")

            for idx, item in enumerate(st.session_state.proposal_products, 1):
                product_row = item.get('product_data', {})

                csv_lines.append(f"=== PRODUCT {idx}: {product_row.get('Product/Service', 'Unknown Product')} ===")
                csv_lines.append(f"Partner: {product_row.get('Partner', 'N/A')}")
                csv_lines.append(f"Country of Origin: {product_row.get('Country of Origin', 'N/A')}")
                csv_lines.append("")

                # Calculate MOQ using same logic as UI display
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

                        # Apply $0.50 rounding if enabled
                        moq_product_price_per_unit = round_to_nearest_fifty_cents(
                            moq_product_price_per_unit,
                            st.session_state.proposal_fifty_cent_rounding
                        )

                        # Apply marketing rounding if enabled (after $0.50 rounding)
                        moq_product_price_per_unit = apply_marketing_rounding(
                            moq_product_price_per_unit,
                            st.session_state.proposal_marketing_rounding
                        )

                        # Calculate Client Price based on discount and budget
                        client_price = moq_product_price_per_unit

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

                                    # Apply $0.50 rounding if enabled
                                    budget_qty_price_per_unit = round_to_nearest_fifty_cents(
                                        budget_qty_price_per_unit,
                                        st.session_state.proposal_fifty_cent_rounding
                                    )

                                    # Apply marketing rounding if enabled (after $0.50 rounding)
                                    budget_qty_price_per_unit = apply_marketing_rounding(
                                        budget_qty_price_per_unit,
                                        st.session_state.proposal_marketing_rounding
                                    )

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

                            # Apply $0.50 rounding after discount if enabled
                            client_price = round_to_nearest_fifty_cents(
                                client_price,
                                st.session_state.proposal_fifty_cent_rounding
                            )

                            # Apply marketing rounding again after discount if enabled
                            client_price = apply_marketing_rounding(
                                client_price,
                                st.session_state.proposal_marketing_rounding
                            )

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

                        # Build CSV table matching UI display
                        csv_lines.append(f"MOQ,Price Ea (@ Qty {moq}),{client_price_header},Delivery")
                        csv_lines.append(f"{moq},${moq_product_price_per_unit:.2f},${client_price:.2f},")

                        # Show MOQ calculation note
                        moq_total_value = moq * moq_product_price_per_unit
                        csv_lines.append("")
                        csv_lines.append(f"MOQ calculated based on $1,000 minimum order value (MOQ {moq} units = ${moq_total_value:.2f})")

                        # ALWAYS show customization costs from product data
                        setup_fee = clean_price(product_row.get('Customization Setup Fee', '')) or 0.0
                        per_unit_cost = clean_price(product_row.get('Customization Cost per Unit', '')) or 0.0

                        # Display customization costs
                        if setup_fee > 0 or per_unit_cost > 0:
                            csv_lines.append(f"Customization available: Artwork set-up: ${setup_fee:.2f} / Branding per piece: ${per_unit_cost:.2f}")
                        else:
                            csv_lines.append("Customization available: Contact for pricing")
                    else:
                        csv_lines.append(f"Unable to calculate MOQ pricing for {product_row.get('Product/Service', 'Unknown Product')}")
                else:
                    csv_lines.append(f"Product data not available for {product_row.get('Product/Service', 'Unknown Product')}")

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
    # LEGACY SECTIONS (HIDDEN BY DEFAULT)
    # ============================================================
    # Toggle for showing legacy sections (pricing tables, copy buttons, etc.)
    SHOW_LEGACY_SECTIONS = st.session_state.get('show_legacy_pricing_sections', False)

    if SHOW_LEGACY_SECTIONS:
        # ============================================================
        # LEGACY SECTION 5: PRICING FOR CARDS & KITTING
        # ============================================================
        st.divider()
        st.subheader("(Legacy) Pricing for Cards & Kitting")

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
        # LEGACY SECTION 6: TERMS & CONDITIONS
        # ============================================================
        st.divider()
        st.subheader("(Legacy) Terms & Conditions")

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
    # SECTION 4: POWERPOINT PROPOSAL GENERATION (PHASE 2.5 COMPLETE)
    # ============================================================
    if len(st.session_state.proposal_products) > 0:
        st.divider()
        st.subheader("4. Generate PowerPoint Proposal")
        st.caption("Automatically create a customized PowerPoint presentation with matched product slides")

        # Add JavaScript to capture scroll position before PowerPoint section button clicks
        components.html("""
            <script>
                const buttons = window.parent.document.querySelectorAll('button');
                buttons.forEach(button => {
                    const btnText = button.textContent;
                    if (btnText.includes('Save Manual Match') ||
                        btnText.includes('Delete') ||
                        btnText.includes('Review Matches & Generate PowerPoint') ||
                        btnText.includes('Yes, use this slide') ||
                        btnText.includes('Show alternatives') ||
                        btnText.includes('Skip this product') ||
                        btnText.includes('Use this') ||
                        btnText.includes('Override') ||
                        btnText.includes('Apply') ||
                        btnText.includes('Cancel') ||
                        btnText.includes('Reset Confirmations') ||
                        btnText.includes('Close')) {
                        button.addEventListener('click', function() {
                            const scrollPos = window.parent.document.querySelector('section.main').scrollTop;
                            window.parent.sessionStorage.setItem('streamlit_scroll_position', scrollPos);
                        });
                    }
                });
            </script>
        """, height=0)

        # Button to trigger matching
        if st.button("Review Matches & Generate PowerPoint", type="primary", use_container_width=True, key="trigger_pptx_matching"):
            st.session_state.show_pptx_matching = True
            st.session_state.generated_pptx = None  # Clear any previous generation
            st.session_state.match_confirmations = {}  # Clear stale confirmations from previous sessions
            st.session_state.pptx_match_results = None  # Force recalculation of matches
            st.rerun()

        # Show matching UI if triggered
        if st.session_state.get('show_pptx_matching', False):
            try:
                # Only load PowerPoint and run matching if not already cached
                if 'pptx_match_results' not in st.session_state or st.session_state.pptx_match_results is None:
                    # Load PowerPoint template from cloud/local
                    from pptx import Presentation

                    # Display template name
                    st.info(f"Using template: **{get_template_name('all_slides')}**")

                    pptx_template = get_template_path('all_slides', show_loading=True)

                    if not pptx_template:
                        st.error("PowerPoint template could not be loaded. Please check Google Drive access.")
                        st.session_state.show_pptx_matching = False
                    else:
                        # Extract product names from PowerPoint
                        with st.spinner("Analyzing PowerPoint slides..."):
                            prs = Presentation(pptx_template)

                            pptx_product_names = []
                            pptx_name_to_index = {}  # Map slide names to indices for saving confirmations
                            slide_list = list(prs.slides)

                            for slide_idx, slide in enumerate(slide_list):
                                if len(slide.shapes) >= 1:
                                    first_shape = slide.shapes[0]
                                    if hasattr(first_shape, "text") and first_shape.text.strip():
                                        product_name = first_shape.text.strip()
                                        if product_name not in pptx_product_names:
                                            pptx_product_names.append(product_name)
                                            pptx_name_to_index[product_name] = slide_idx

                        st.success(f"Loaded {len(pptx_product_names)} product slides from PowerPoint")

                        # Get proposal product names
                        gs_product_names = [item['product_data']['Product/Service'] for item in st.session_state.proposal_products]

                        # Create matcher and run matching (pass dataset for confirmed match lookup)
                        with st.spinner("Matching products to slides..."):
                            # Clear cache to ensure fresh confirmed matches are loaded
                            from src.match_memory import _load_all_matches_data
                            _load_all_matches_data.clear()

                            matcher = SlideMatcher(pptx_product_names)
                            current_dataset = st.session_state.get('selected_dataset', 'real')
                            match_results = matcher.batch_match(gs_product_names, dataset=current_dataset)

                        # Cache results in session state
                        st.session_state.pptx_match_results = match_results
                        st.session_state.pptx_product_names = pptx_product_names
                        st.session_state.pptx_name_to_index = pptx_name_to_index

                # Use cached match results
                if st.session_state.pptx_match_results is not None:
                    match_results = st.session_state.pptx_match_results
                    pptx_product_names = st.session_state.pptx_product_names
                    pptx_name_to_index = st.session_state.pptx_name_to_index

                    # Show match review UI (pass name-to-index mapping for saving confirmations)
                    confirmed_matches = show_match_review_ui(match_results, pptx_product_names, pptx_name_to_index)

                    if confirmed_matches:
                        st.session_state.show_pptx_matching = False
                        st.rerun()

            except Exception as e:
                st.error(f"Error loading PowerPoint: {str(e)}")
                st.session_state.show_pptx_matching = False

    # ============================================================
    # NEXT STEPS GUIDANCE
    # ============================================================
    st.divider()

    if len(st.session_state.proposal_products) > 0:
        st.success(f"""
        **What's Next?**

        1. Download and send the proposal to your client
        2. Move to **Tab 2: Client Order Form Generator** to create a client order form
        3. Your {len(st.session_state.proposal_products)} proposal product(s) will be available for import in Tab 2
        """)
    else:
        st.info("""
        **What's Next?**

        After adding products to your proposal, you can:
        - Download proposal tables and PowerPoint presentations
        - Send to your client for review
        - Move to **Tab 2** to generate a client order form
        """)

    # Save and Navigation buttons at bottom of Tab 1
    st.divider()
    st.markdown("### Save Your Work")

    # Show unsaved changes indicator and save status
    if has_unsaved_proposal_changes():
        st.warning("You have unsaved changes in your proposal")

    save_status = format_time_since_save('proposal')
    if save_status:
        st.caption(f"{save_status}")

    # Check if there are products to save
    has_products = len(st.session_state.proposal_products) > 0

    if has_products:
        col1, col2 = st.columns(2)
        with col1:
            proposal_name = st.text_input(
                "Proposal name:",
                key="save_proposal_name_bottom",
                placeholder="e.g., Client ABC Winter Campaign"
            )
        with col2:
            created_by = st.text_input(
                "Your name (optional):",
                key="save_proposal_creator_bottom",
                placeholder="e.g., John Smith"
            )

        if st.button("Save Proposal", type="primary", use_container_width=True, key="save_proposal_btn_bottom"):
            if not proposal_name or not proposal_name.strip():
                st.error("Please enter a proposal name")
            else:
                # Prepare proposal data
                proposal_data = {
                    'proposal_products': st.session_state.proposal_products,
                    'proposal_marketing_rounding': st.session_state.proposal_marketing_rounding,
                    'proposal_use_msrp': st.session_state.proposal_use_msrp,
                    'proposal_discount_type': st.session_state.get('proposal_discount_type'),
                    'proposal_discount_percent': st.session_state.get('proposal_discount_percent', 0.0),
                    'proposal_client_budget': st.session_state.get('proposal_client_budget', 0.0)
                }

                success, message, result = save_proposal(
                    name=proposal_name.strip(),
                    created_by=created_by.strip() if created_by else "",
                    proposal_data=proposal_data,
                    dataset=st.session_state.selected_dataset
                )

                if success:
                    st.success(f"{message} - You can find it in the sidebar under 'Saved Proposals'")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    # Check if it's a naming conflict
                    if result:  # result contains suggested name
                        st.error(message)
                        if st.button(f"Save as '{result}'", key="save_with_new_name_bottom"):
                            success2, message2, _ = save_proposal(
                                name=result,
                                created_by=created_by.strip() if created_by else "",
                                proposal_data=proposal_data,
                                dataset=st.session_state.selected_dataset
                            )
                            if success2:
                                st.success(f"{message2} - You can find it in the sidebar")
                                time.sleep(1.5)
                                st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("Add products to your proposal to enable saving")

    # Navigation button
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Continue to Tab 2: Client Order Form", type="primary", use_container_width=True, key="tab1_to_tab2"):
            st.session_state.show_tab2_prompt = True
            st.rerun()

    # Show navigation prompt if button was clicked
    if st.session_state.get('show_tab2_prompt', False):
        st.info("Click on the **'Client Order Form Generator'** tab above to continue.")
        st.session_state.show_tab2_prompt = False

# ============================================================
# TAB 2: CLIENT ORDER FORM GENERATOR (NEW)
# ============================================================
with tab2:
    st.header("Client Order Form Generator")
    st.caption("Create professional HTML order forms to send to clients")
    st.divider()

    # ============================================================
    # SECTION 1: ORDER DETAILS
    # ============================================================
    st.subheader("1. Order Details")
    st.caption("Add client information to pre-fill the order form")

    # Initialize order details in session state if not exists
    if 'order_details' not in st.session_state:
        st.session_state.order_details = {
            'client_type': 'New',
            'company_name': '',
            'contact_name': '',
            'contact_email': ''
        }

    col1, col2 = st.columns(2)

    with col1:
        st.session_state.order_details['client_type'] = st.selectbox(
            "Client Type",
            options=['New', 'Existing'],
            index=0 if st.session_state.order_details.get('client_type', 'New') == 'New' else 1,
            key="order_detail_client_type"
        )

        st.session_state.order_details['company_name'] = st.text_input(
            "Company Name",
            value=st.session_state.order_details.get('company_name', ''),
            key="order_detail_company_name"
        )

    with col2:
        st.session_state.order_details['contact_name'] = st.text_input(
            "Contact Name",
            value=st.session_state.order_details.get('contact_name', ''),
            key="order_detail_contact_name"
        )

        st.session_state.order_details['contact_email'] = st.text_input(
            "Contact Email",
            value=st.session_state.order_details.get('contact_email', ''),
            key="order_detail_contact_email"
        )

    # ============================================================
    # FORM CUSTOMIZATION (OPTIONAL)
    # ============================================================
    st.divider()
    with st.expander("Customize Form Template Text (Optional)", expanded=False):
        st.caption("Edit any template text that appears in the client order form")

        # Dropdown to select which field to customize
        field_labels = {
            'form_instructions': 'How to Fill Out This Form (Instructions at top)',
            'dropshipping_instructions': 'Dropshipping Instructions',
            'dropshipping_placeholder': 'Dropshipping Information Placeholder',
            'shipping_address_placeholder': 'Shipping Address Placeholder',
            'billing_address_placeholder': 'Billing Address Placeholder',
            'customization_placeholder': 'Customization/Branding Placeholder',
            'impact_card_options': 'Impact Card Options',
            'payment_options': 'Payment Options'
        }

        selected_field = st.selectbox(
            "Select field to customize",
            options=list(field_labels.keys()),
            format_func=lambda x: field_labels[x],
            index=1,  # Default to dropshipping_instructions
            key="customization_field_selector"
        )

        # Text area for editing the selected field
        current_value = st.session_state.form_customizations.get(selected_field, '')

        # Determine height based on field type
        height = 150 if selected_field in ['form_instructions', 'impact_card_options', 'payment_options'] else 100

        new_value = st.text_area(
            f"Edit: {field_labels[selected_field]}",
            value=current_value,
            height=height,
            key=f"customize_{selected_field}",
            help=f"This text appears in the '{field_labels[selected_field]}' section of the order form"
        )

        # Update session state if value changed
        if new_value != current_value:
            st.session_state.form_customizations[selected_field] = new_value
            # Update legacy dropshipping_notes for compatibility
            if selected_field == 'dropshipping_instructions':
                st.session_state.dropshipping_notes = new_value

    # Button to confirm info is ready (visual feedback)
    st.divider()
    if st.button("Update Order Form with This Info", type="primary", use_container_width=True, key="update_order_form"):
        st.session_state.show_order_form_updated = True
        st.rerun()

    # Show success message if flag is set
    if st.session_state.get('show_order_form_updated', False):
        st.success("Order form updated! The information you entered will appear in the form below.")
        st.session_state.show_order_form_updated = False

    # ============================================================
    # SECTION 2: CLIENT ORDER FORM
    # ============================================================
    st.divider()
    st.subheader("2. Client Order Form")

    st.markdown("""
    Download the HTML form below and paste it into your email to send to clients.
    The table will look professional and clients can fill it out directly.
    """)

    # Generate HTML table
    # Get order details from session state
    client_type = st.session_state.order_details.get('client_type', 'New')
    company_name = st.session_state.order_details.get('company_name', '') or '[Type company name here]'
    contact_name = st.session_state.order_details.get('contact_name', '') or '[Type your name here]'
    contact_email = st.session_state.order_details.get('contact_email', '') or '[Type your email here]'

    html_form = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; padding: 20px; background-color: #ffffff; }}
        h2 {{ color: #2c3e50; background-color: #ffffff; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .instructions-box {{ background-color: #e8f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; color: #000000; }}
        .instructions-box p {{ margin: 5px 0; color: #000000; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; background-color: #ffffff; }}
        th {{ background-color: #3498db !important; color: #ffffff !important; padding: 12px; text-align: left; font-weight: bold; }}
        td {{ border: 1px solid #ddd; padding: 10px; background-color: #ffffff; color: #000000; }}
        td:first-child {{ background-color: #f8f9fa !important; color: #000000 !important; font-weight: 500; width: 35%; vertical-align: top; }}
        .section-header {{ background-color: #2c3e50 !important; color: #ffffff !important; font-weight: bold; padding: 10px; }}
        .fill-in {{ background-color: #ffffff !important; color: #7f8c8d !important; min-height: 20px; font-style: italic; }}
        .product-table {{ margin: 10px 0; }}
        .product-table td {{ background-color: #ffffff !important; color: #000000 !important; }}
        .helper-text {{ color: #7f8c8d; font-size: 0.85em; display: block; margin-top: 3px; }}
        .required {{ color: #e74c3c !important; font-weight: bold; }}
    </style>
</head>
<body>
    <h2>PEACE BY PIECE CLIENT ORDER FORM</h2>

    <div class="instructions-box">
        <p><strong>HOW TO FILL OUT THIS FORM:</strong></p>"""

    # Add customizable instructions (one paragraph per line)
    instructions = st.session_state.form_customizations.get('form_instructions', '').strip()
    for i, line in enumerate(instructions.split('\n'), 1):
        if line.strip():
            html_form += f"""
        <p>{line.strip()}</p>"""

    html_form += f"""
    </div>

    <table>
        <tr>
            <td colspan="2" class="section-header">CLIENT INFORMATION</td>
        </tr>
        <tr>
            <td>Client Type <span class="required">*</span></td>
            <td class="fill-in">{client_type}</td>
        </tr>
        <tr>
            <td>Company Name <span class="required">*</span></td>
            <td class="fill-in">{company_name}</td>
        </tr>
        <tr>
            <td>Contact Name <span class="required">*</span></td>
            <td class="fill-in">{contact_name}</td>
        </tr>
        <tr>
            <td>Contact Email <span class="required">*</span></td>
            <td class="fill-in">{contact_email}</td>
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
            <td class="fill-in">""" + st.session_state.form_customizations.get('shipping_address_placeholder', '[Type full shipping address here, or N/A if drop shipping]') + """</td>
        </tr>
        <tr>
            <td style="font-weight: bold;">Dropshipping Instructions</td>
            <td style="background-color: #f8f9fa !important; padding: 10px; color: #000000 !important;">""" + st.session_state.form_customizations.get('dropshipping_instructions', '').replace('\n', '<br/>') + """</td>
        </tr>
        <tr>
            <td>Dropshipping Information</td>
            <td class="fill-in">""" + st.session_state.form_customizations.get('dropshipping_placeholder', '[Input dropshipping info here]') + """</td>
        </tr>
        <tr>
            <td>Billing Address</td>
            <td class="fill-in">""" + st.session_state.form_customizations.get('billing_address_placeholder', '[Type billing address here, or "Same as shipping"]') + """</td>
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
    customization_placeholder = st.session_state.form_customizations.get('customization_placeholder', '[Describe any customization, logo placement, colors, etc.]')
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
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">{customization_placeholder}</td>
        </tr>"""
    else:
        # Add 3 blank rows if no products in proposal
        for i in range(3):
            html_form += f"""
        <tr>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">[Product name]</td>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">[Qty]</td>
            <td class="product-table" style="color: #7f8c8d; font-style: italic;">{customization_placeholder}</td>
        </tr>"""

    html_form += """
    </table>

    <table>
        <tr>
            <td colspan="2" class="section-header">IMPACT CARDS</td>
        </tr>
        <tr>
            <td>Impact Card Preference <span class="required">*</span></td>
            <td class="fill-in">[Delete all except the ONE option you want]<br/><br/>"""

    # Add customizable impact card options
    impact_options = st.session_state.form_customizations.get('impact_card_options', '')
    for line in impact_options.split('\n'):
        if line.strip():
            html_form += f"""
                {line.strip()}<br/>"""

    html_form += """
            </td>
        </tr>
    </table>

    <table>
        <tr>
            <td colspan="2" class="section-header">PAYMENT</td>
        </tr>
        <tr>
            <td>Payment Preference <span class="required">*</span></td>
            <td class="fill-in">[Delete all except the ONE option you want]<br/><br/>"""

    # Add customizable payment options
    payment_options = st.session_state.form_customizations.get('payment_options', '')
    for line in payment_options.split('\n'):
        if line.strip():
            html_form += f"""
                {line.strip()}<br/>"""

    html_form += """
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

    st.info("""
    **What's Next?**

    1. Download and send the client order form to your client
    2. When your client returns the completed form, move to **Tab 3: Order & Client Info** to process the order
    3. You can import the completed HTML form directly in Tab 3
    """)

    # Navigation button at bottom of Tab 2
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Continue to Tab 3: Order & Client Info", type="primary", use_container_width=True, key="tab2_to_tab3"):
            st.session_state.show_tab3_prompt = True
            st.rerun()

    # Show navigation prompt if button was clicked
    if st.session_state.get('show_tab3_prompt', False):
        st.info("Click on the **'Order & Client Info'** tab above to continue.")
        st.session_state.show_tab3_prompt = False

# ============================================================
# TAB 3: ORDER & CLIENT INFO
# ============================================================
with tab3:
    st.header("Order & Client Info - Input Order & Client Details")

    # Show unsaved changes indicator and save status
    col1_status, col2_status = st.columns([1, 1])
    with col1_status:
        if has_unsaved_order_changes():
            st.warning("You have unsaved changes in your order")
    with col2_status:
        save_status = format_time_since_save('order')
        if save_status:
            st.caption(f"{save_status}")

    # Quick Save Section at top
    has_order = len(st.session_state.order_items) > 0
    if has_order:
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                quick_order_name = st.text_input(
                    "Quick save order:",
                    key="quick_save_order_name",
                    placeholder="e.g., Client ABC Q1 2025",
                    label_visibility="collapsed"
                )
            with col2:
                quick_creator = st.text_input(
                    "Your name:",
                    key="quick_save_creator",
                    placeholder="Your name (optional)",
                    label_visibility="collapsed"
                )
            with col3:
                if st.button("Save", type="primary", use_container_width=True, key="quick_save_order_btn"):
                    if not quick_order_name or not quick_order_name.strip():
                        st.error("Please enter an order name")
                    else:
                        # Prepare order data
                        order_data = {
                            'order_items': st.session_state.order_items,
                            'order_shipping': st.session_state.order_shipping,
                            'partner_shipping': st.session_state.partner_shipping,
                            'sales_tax': st.session_state.sales_tax,
                            'kitting_pbp_cost': st.session_state.kitting_pbp_cost,
                            'kitting_client_price': st.session_state.kitting_client_price,
                            'order_discount_type': st.session_state.order_discount_type,
                            'order_discount_preset': st.session_state.order_discount_preset,
                            'order_discount_custom_desc': st.session_state.order_discount_custom_desc,
                            'order_discount_custom_value': st.session_state.order_discount_custom_value,
                            'order_use_marketing_rounding': st.session_state.order_use_marketing_rounding,
                            'apply_cc_fee': st.session_state.apply_cc_fee,
                            'cc_fee_percent': st.session_state.cc_fee_percent,
                            'client_info': st.session_state.client_info,
                            'order_notes': st.session_state.order_notes,
                            'order_confirmed': st.session_state.order_confirmed
                        }

                        success, message, result = save_order(
                            name=quick_order_name.strip(),
                            created_by=quick_creator.strip() if quick_creator else "",
                            order_data=order_data,
                            dataset=st.session_state.selected_dataset
                        )

                        if success:
                            update_last_save_time('order')
                            clear_saved_data_cache()  # Clear cache to show new order
                            st.success(f"{message} - Available in sidebar under 'Saved Orders'")
                            time.sleep(1)
                            st.rerun()
                        else:
                            if result:
                                st.error(f"{message} Try: {result}")
                            else:
                                st.error(message)

    st.divider()

    # ============================================================
    # WORKFLOW GUIDANCE
    # ============================================================
    st.subheader("Getting Started - Choose Your Workflow")

    # Determine which options are available
    has_proposal = len(st.session_state.proposal_products) > 0

    if has_proposal:
        st.markdown("""
        There are **3 ways** to build an order in this tab. Choose the option that matches your situation:

        **RECOMMENDED:** If you sent a client order form (from Tab 2) and received it back completed → Use **Option A** below

        **Alternative:** If you have a proposal (from Tab 1) but no completed client form → Use **Option B** below

        **Fallback:** If starting fresh without a proposal or form → Use **Option C** below
        """)
    else:
        st.markdown("""
        There are **2 ways** to build an order in this tab. Choose the option that matches your situation:

        **RECOMMENDED:** If you sent a client order form (from Tab 2) and received it back completed → Use **Option A** below

        **Alternative:** If starting fresh without a proposal or form → Use **Option B** below

        **Tip:** If you want to create a proposal first, go back to Tab 1 to build a proposal, then return here to import it.
        """)
    st.divider()

    # ============================================================
    # SAVED ORDERS SECTION (Always visible)
    # ============================================================
    with st.expander("Saved Orders", expanded=False):
        st.caption("Save your current order or load a previously saved one")

        # Load all saved orders
        refresh_counter = st.session_state.get('saved_data_refresh_counter', 0)
        saved_orders = cached_load_all_orders(refresh_counter)  # Use cached version to reduce API calls

        # Two columns: Load/Delete on left, Save on right
        load_col, save_col = st.columns(2)

        with load_col:
            st.markdown("**Load Order**")

            if len(saved_orders) == 0:
                st.info("No saved orders yet")
            else:
                # Create dropdown options
                order_options = {
                    f"{o['name']} ({o['created_date'][:10]})": o['order_id']
                    for o in saved_orders
                }

                selected_order_label = st.selectbox(
                    "Select order to load:",
                    options=list(order_options.keys()),
                    key="load_order_select"
                )

                if selected_order_label:
                    selected_order_id = order_options[selected_order_label]

                    # Find full order data
                    selected_order = next(o for o in saved_orders if o['order_id'] == selected_order_id)

                    # Show preview
                    st.caption(f"**Created by:** {selected_order['created_by'] or 'Unknown'}")
                    st.caption(f"**Dataset:** {selected_order['dataset']}")

                    # Load and Delete buttons
                    load_btn_col, delete_btn_col = st.columns(2)

                    with load_btn_col:
                        if st.button("Load", key="load_order_btn", type="primary", use_container_width=True):
                            success, order_data, dataset = load_order_data(selected_order_id)

                            if success:
                                # Check if dataset matches
                                if dataset != st.session_state.selected_dataset:
                                    st.warning(f"WARNING: This order was created with {dataset} dataset, but you're currently using {st.session_state.selected_dataset} dataset. Loading anyway...")

                                # Load order data into session state
                                st.session_state.order_items = order_data.get('order_items', [])
                                st.session_state.order_shipping = order_data.get('order_shipping', 0.0)
                                st.session_state.partner_shipping = order_data.get('partner_shipping', 0.0)
                                st.session_state.sales_tax = order_data.get('sales_tax', 0.0)
                                st.session_state.kitting_pbp_cost = order_data.get('kitting_pbp_cost', 0.0)
                                st.session_state.kitting_client_price = order_data.get('kitting_client_price', 0.0)
                                st.session_state.order_discount_type = order_data.get('order_discount_type', 'none')
                                st.session_state.order_discount_preset = order_data.get('order_discount_preset', 'NGO Discount (5%)')
                                st.session_state.order_discount_custom_desc = order_data.get('order_discount_custom_desc', '')
                                st.session_state.order_discount_custom_value = order_data.get('order_discount_custom_value', 0.0)
                                st.session_state.order_use_marketing_rounding = order_data.get('order_use_marketing_rounding', False)
                                st.session_state.apply_cc_fee = order_data.get('apply_cc_fee', False)
                                st.session_state.cc_fee_percent = order_data.get('cc_fee_percent', 3.0)
                                st.session_state.client_info = order_data.get('client_info', st.session_state.client_info)
                                # Handle both old and new order_notes structures
                                loaded_notes = order_data.get('order_notes', {})
                                if 'kitting_specs' in loaded_notes:
                                    # New 5-category structure
                                    st.session_state.order_notes = loaded_notes
                                else:
                                    # Old 2-category structure - migrate to new
                                    st.session_state.order_notes = {
                                        'kitting_specs': '',
                                        'client_requests': loaded_notes.get('accounting_notes', ''),
                                        'addon_samples': '',
                                        'artwork_attachments': '',
                                        'general_notes': loaded_notes.get('notes_to_partner', '')
                                    }
                                st.session_state.order_confirmed = order_data.get('order_confirmed', False)

                                st.success(f"Loaded order: {selected_order['name']}")
                                st.rerun()
                            else:
                                st.error("Failed to load order data")

                    with delete_btn_col:
                        if st.button("Delete", key="delete_order_btn", use_container_width=True):
                            # Confirmation dialog using session state
                            if 'confirm_delete_order_id' not in st.session_state:
                                st.session_state.confirm_delete_order_id = selected_order_id
                                st.warning(f"WARNING: Are you sure you want to delete '{selected_order['name']}'?")

                                confirm_col1, confirm_col2 = st.columns(2)
                                with confirm_col1:
                                    if st.button("Yes, Delete", key="confirm_delete_order_yes", type="primary"):
                                        success, message = delete_order(st.session_state.confirm_delete_order_id)
                                        if success:
                                            clear_saved_data_cache()  # Clear cache after deletion
                                            st.success(message)
                                            del st.session_state.confirm_delete_order_id
                                            st.rerun()
                                        else:
                                            st.error(message)
                                with confirm_col2:
                                    if st.button("Cancel", key="confirm_delete_order_no"):
                                        del st.session_state.confirm_delete_order_id
                                        st.rerun()

        with save_col:
            st.markdown("**Save Current Order**")

            # Check if there are products to save
            has_products = len(st.session_state.order_items) > 0

            if not has_products:
                st.info("Add products to enable saving")

            order_name = st.text_input(
                "Order name:",
                key="save_order_name",
                placeholder="e.g., Client ABC Q1 2025 Order",
                disabled=not has_products
            )

            created_by = st.text_input(
                "Your name (optional):",
                key="save_order_creator",
                placeholder="e.g., John Smith",
                disabled=not has_products
            )

            if st.button("Save Order", key="save_order_btn", type="primary", use_container_width=True, disabled=not has_products):
                if not order_name or not order_name.strip():
                    st.error("Please enter an order name")
                else:
                    # Prepare order data
                    order_data = {
                        'order_items': st.session_state.order_items,
                        'order_shipping': st.session_state.order_shipping,
                        'partner_shipping': st.session_state.partner_shipping,
                        'sales_tax': st.session_state.sales_tax,
                        'kitting_pbp_cost': st.session_state.kitting_pbp_cost,
                        'kitting_client_price': st.session_state.kitting_client_price,
                        'order_discount_type': st.session_state.order_discount_type,
                        'order_discount_preset': st.session_state.order_discount_preset,
                        'order_discount_custom_desc': st.session_state.order_discount_custom_desc,
                        'order_discount_custom_value': st.session_state.order_discount_custom_value,
                        'order_use_marketing_rounding': st.session_state.order_use_marketing_rounding,
                        'apply_cc_fee': st.session_state.apply_cc_fee,
                        'cc_fee_percent': st.session_state.cc_fee_percent,
                        'client_info': st.session_state.client_info,
                        'order_notes': st.session_state.order_notes,
                        'order_confirmed': st.session_state.order_confirmed
                    }

                    success, message, result = save_order(
                        name=order_name.strip(),
                        created_by=created_by.strip() if created_by else "",
                        order_data=order_data,
                        dataset=st.session_state.selected_dataset
                    )

                    if success:
                        update_last_save_time('order')
                        clear_saved_data_cache()  # Clear cache to show new order
                        st.success(message)
                        st.rerun()  # Rerun to clear form
                    else:
                        # Check if it's a naming conflict
                        if result:  # result contains suggested name
                            st.error(message)
                            # Offer to save with suggested name
                            if st.button(f"Save as '{result}'", key="save_order_with_new_name"):
                                success2, message2, _ = save_order(
                                    name=result,
                                    created_by=created_by.strip() if created_by else "",
                                    order_data=order_data,
                                    dataset=st.session_state.selected_dataset
                                )
                                if success2:
                                    update_last_save_time('order')
                                    clear_saved_data_cache()  # Clear cache to show new order
                                    st.success(message2)
                                    st.rerun()
                        else:
                            st.error(message)

    st.divider()

    # ============================================================
    # OPTION A: HTML CLIENT ORDER FORM IMPORT (RECOMMENDED)
    # ============================================================
    st.header("Option A: Import Completed Client Order Form (RECOMMENDED)")
    st.markdown("**Use this if:** You sent a client order form from Tab 2 and received it back completed")

    with st.expander("Upload Completed Client Order Form", expanded=False):
        st.caption("Upload an HTML order form completed by your client to auto-populate client information.")
        st.info("This will import client info, shipping, payment details, and order products from the form.")

        uploaded_file = st.file_uploader(
            "Upload Client Order Form (HTML)",
            type=['html', 'htm'],
            key="import_client_form_top",
            help="Upload the HTML form that your client filled out and returned to you"
        )

        if uploaded_file is not None:
            # Read and parse the HTML content
            content = uploaded_file.read().decode('utf-8')
            parsed_data = parse_client_order_form_html(content)

            # Show parsing errors if any
            if parsed_data['parse_errors']:
                st.warning("Parsing warnings:")
                for error in parsed_data['parse_errors']:
                    st.caption(f"- {error}")

            # Show preview of extracted data
            st.markdown("**Preview of Extracted Data:**")

            preview_data = {
                "Client Type": parsed_data['client_type'] or "[Not filled]",
                "Company Name": parsed_data['company_name'] or "[Not filled]",
                "Contact Name": parsed_data['contact_name'] or "[Not filled]",
                "Contact Email": parsed_data['contact_email'] or "[Not filled]",
                "Drop Shipping": parsed_data['drop_shipping'] or "[Not filled]",
                "Shipping Address": parsed_data['shipping_address'] or "[Not filled]",
                "Dropshipping Info": parsed_data['dropshipping_info'] or "[Not filled]",
                "Billing Address": parsed_data['billing_address'] or "[Not filled]",
                "Client In-Hands Date": parsed_data['client_in_hands_date'] or "[Not filled]",
                "Impact Card Preference": parsed_data['impact_card_preference'] or "[Not filled]",
                "Payment Preference": parsed_data['payment_preference'] or "[Not filled]"
            }

            # Display as table
            df_preview = pd.DataFrame(list(preview_data.items()), columns=["Field", "Value"])
            st.dataframe(df_preview, use_container_width=True, hide_index=True)

            # Show extracted products
            if parsed_data['products']:
                st.markdown(f"**Products Found:** {len(parsed_data['products'])} product(s)")
                products_df = pd.DataFrame(parsed_data['products'], columns=["Product Name"])
                st.dataframe(products_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No products found in order form")

            # Import button
            st.divider()
            if st.button("Import Client Information", type="primary", use_container_width=True, key="import_client_data_btn_top"):
                # Apply to session state
                st.session_state.client_info['is_new_client'] = (parsed_data['client_type'] == 'New')
                st.session_state.client_info['company_name'] = parsed_data['company_name']
                st.session_state.client_info['contact_name'] = parsed_data['contact_name']
                st.session_state.client_info['contact_email'] = parsed_data['contact_email']
                st.session_state.client_info['shipping_address'] = parsed_data['shipping_address']
                st.session_state.client_info['billing_address'] = parsed_data['billing_address']

                # Set shipping type based on drop shipping answer
                # Default to 'One Location' (show shipping address) unless clearly "Yes" for drop shipping
                if parsed_data['drop_shipping'] == 'Yes':
                    st.session_state.client_info['shipping_type'] = 'Drop Shipping'
                else:
                    # For "No", empty, or any unclear answer, default to One Location
                    st.session_state.client_info['shipping_type'] = 'One Location'

                # Parse and apply date
                if parsed_data['client_in_hands_date']:
                    try:
                        from datetime import datetime
                        # Try to parse MM/DD/YYYY format
                        date_obj = datetime.strptime(parsed_data['client_in_hands_date'], '%m/%d/%Y')
                        st.session_state.client_info['client_in_hands_date'] = date_obj.date()
                    except:
                        # If parsing fails, leave empty and let user enter manually
                        st.session_state.client_info['client_in_hands_date'] = None

                # Map payment preference to our dropdown values
                payment_map = {
                    'ACH': 'ACH',
                    'Check': 'Check',
                    'Credit Card': 'Credit Card (3% processing fee applies)'
                }
                if parsed_data['payment_preference'] in payment_map:
                    st.session_state.client_info['payment_preference'] = payment_map[parsed_data['payment_preference']]

                st.success("Client information imported successfully! Review and edit the fields below as needed.")
                st.rerun()

            # ============================================================
            # PRODUCT SELECTION FROM ORDER FORM
            # ============================================================
            if parsed_data['products']:
                st.divider()
                st.markdown("**Select Products from Order Form:**")
                st.caption("Products will be matched against the catalog and added with default settings (quantity 1, 100% markup).")

                # Match products against catalog
                matched_products = []
                unmatched_products = []

                for product_name in parsed_data['products']:
                    # Try exact match first
                    exact_match = st.session_state.df_template[
                        st.session_state.df_template['Product/Service'].str.lower() == product_name.lower()
                    ]

                    if len(exact_match) > 0:
                        # Exact match found
                        product_row = exact_match.iloc[0].to_dict()
                        matched_products.append({
                            'name': product_name,
                            'match_type': 'Exact',
                            'product_data': product_row
                        })
                    else:
                        # Try partial match
                        partial_match = st.session_state.df_template[
                            st.session_state.df_template['Product/Service'].str.contains(product_name, case=False, na=False)
                        ]

                        if len(partial_match) > 0:
                            # Partial match found - use first match
                            product_row = partial_match.iloc[0].to_dict()
                            matched_products.append({
                                'name': product_name,
                                'match_type': 'Partial',
                                'catalog_name': product_row['Product/Service'],
                                'product_data': product_row
                            })
                        else:
                            # No match found
                            unmatched_products.append(product_name)

                # Show matched products with checkboxes
                if matched_products:
                    st.markdown(f"**Matched Products ({len(matched_products)}):**")

                    selected_product_indices = []

                    for idx, match in enumerate(matched_products):
                        col1, col2 = st.columns([4, 1])

                        with col1:
                            is_selected = st.checkbox(
                                f"{match['name']} ({match['match_type']} match)",
                                key=f"select_form_product_{idx}",
                                value=True  # Default to checked
                            )

                            # Show catalog name if different (partial match)
                            if match['match_type'] == 'Partial':
                                st.caption(f"Catalog: {match['catalog_name']}")

                            # Show partner
                            st.caption(f"Partner: {match['product_data'].get('Partner', 'N/A')}")

                        with col2:
                            if is_selected:
                                selected_product_indices.append(idx)

                    # Add selected button
                    if len(selected_product_indices) > 0:
                        if st.button(f"Add {len(selected_product_indices)} Selected Product(s) to Order", type="primary", use_container_width=True, key="add_form_products_btn"):
                            # Add products to order
                            max_pbp_shipping = 0.0
                            for idx in selected_product_indices:
                                match = matched_products[idx]
                                product_data = match['product_data']

                                # Create order item with default settings (quantity 1, 100% markup)
                                # Get base price for quantity 1
                                base_price_per_unit, tier_info, tier_num = get_unit_price_new_system(product_data, 1)

                                # Calculate costs
                                product_cost_subtotal = base_price_per_unit * 1
                                markup_amount = product_cost_subtotal * 1.0  # 100% markup
                                product_total = product_cost_subtotal + markup_amount

                                # Parse tariff
                                tariff_rate_percent = parse_tariff_rate(product_data.get('Tariff Rate', ''))
                                tariff_base = product_cost_subtotal
                                tariff_amount = calculate_product_tariff(tariff_base, tariff_rate_percent)

                                # Build order item
                                order_item = {
                                    'product_name': product_data.get('Product/Service', 'Unknown Product'),
                                    'product_ref': product_data.get('Purchase Description', ''),
                                    'partner': product_data.get('Partner', 'Unknown Partner'),
                                    'product_data': product_data,
                                    'product_data_row': product_data,
                                    'is_custom': False,
                                    'quantity': 1,
                                    'base_price': base_price_per_unit,
                                    'tier_range': tier_info if tier_info else '',
                                    'tier_column': f'T{tier_num}' if tier_num else '',
                                    'markup_percent': 100.0,
                                    'markup_amount': markup_amount,
                                    'include_customization': False,
                                    'customization_description': product_data.get('Customization Info', ''),
                                    'customization_setup_fee': float(clean_price(product_data.get('Customization Setup Fee', '')) or 0.0),
                                    'customization_per_unit': float(clean_price(product_data.get('Customization Cost per Unit', '')) or 0.0),
                                    'customization_setup_total': 0.0,
                                    'customization_unit_total': 0.0,
                                    'apply_custom_minimum': False,
                                    'customization_minimum_qty': 0,
                                    'product_subtotal': product_cost_subtotal,
                                    'subtotal_before_markup': product_cost_subtotal,
                                    'product_total': product_total,
                                    'total_per_unit': product_total,
                                    'quoted_price_per_unit': (product_cost_subtotal + markup_amount),
                                    'tariff_info': f"{product_data.get('Country', 'N/A')} - {tariff_rate_percent}%" if tariff_rate_percent > 0 else '',
                                    'tariff_rate_percent': tariff_rate_percent,
                                    'tariff_base': tariff_base,
                                    'tariff_amount': tariff_amount
                                }

                                st.session_state.order_items.append(order_item)

                                # Track maximum PBP shipping cost
                                pbp_shipping, _ = get_shipping_costs(product_data)
                                max_pbp_shipping = max(max_pbp_shipping, pbp_shipping)

                            # Auto-populate partner shipping with the maximum cost found
                            if max_pbp_shipping > 0 and st.session_state.partner_shipping == 0:
                                st.session_state.partner_shipping = max_pbp_shipping

                            st.toast(f"Added {len(selected_product_indices)} product(s) from order form!")
                            st.rerun()
                    else:
                        st.caption("Select at least one product above to add to order.")

                # Show unmatched products
                if unmatched_products:
                    st.divider()
                    st.warning(f"**Not Found in Catalog ({len(unmatched_products)}):**")
                    for product_name in unmatched_products:
                        st.caption(f"- {product_name}")
                    st.caption("These products will not be added. You can add them manually using Option C below.")

    st.divider()

    # ============================================================
    # OPTION B: PROPOSAL PRODUCTS SELECTION (if available)
    # ============================================================
    if len(st.session_state.proposal_products) > 0:
        st.header("Option B: Import Products from Proposal (Tab 1)")
        st.markdown("**Use this if:** You created a proposal in Tab 1 but don't have a completed client order form")
        st.info(f"{len(st.session_state.proposal_products)} product(s) available from Proposal (Tab 1). Select below to add to order.")
        st.session_state.using_proposal_data = True

        # Import All button at top level
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Import All Products from Proposal", type="primary", use_container_width=True, key="import_all_proposal"):
                # Import all proposal products to order
                imported_count = 0
                max_pbp_shipping = 0.0  # Track maximum shipping cost among all products

                for prop_item in st.session_state.proposal_products:
                    order_item = convert_proposal_to_order(
                        prop_item,
                        get_unit_price_new_system,
                        calculate_product_tariff
                    )
                    st.session_state.order_items.append(order_item)
                    imported_count += 1

                    # Track maximum PBP shipping cost
                    pbp_shipping, _ = get_shipping_costs(prop_item.get('product_data', {}))
                    max_pbp_shipping = max(max_pbp_shipping, pbp_shipping)

                # Auto-populate partner shipping with the maximum cost found
                if max_pbp_shipping > 0 and st.session_state.partner_shipping == 0:
                    st.session_state.partner_shipping = max_pbp_shipping

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
                    max_pbp_shipping = 0.0
                    for idx in selected_proposal_indices:
                        prop_item = st.session_state.proposal_products[idx]
                        order_item = convert_proposal_to_order(
                            prop_item,
                            get_unit_price_new_system,
                            calculate_product_tariff
                        )
                        st.session_state.order_items.append(order_item)

                        # Track maximum PBP shipping cost
                        pbp_shipping, _ = get_shipping_costs(prop_item.get('product_data', {}))
                        max_pbp_shipping = max(max_pbp_shipping, pbp_shipping)

                    # Auto-populate partner shipping with the maximum cost found
                    if max_pbp_shipping > 0 and st.session_state.partner_shipping == 0:
                        st.session_state.partner_shipping = max_pbp_shipping

                    st.toast(f"Added {len(selected_proposal_indices)} product(s) to order!")
                    st.rerun()
            else:
                st.caption("Select at least one product above to add to order.")

        st.divider()
    else:
        st.session_state.using_proposal_data = False


    # ============================================================
    # OPTION C (or B): MANUAL PRODUCT SELECTION
    # ============================================================
    # Adjust option label based on whether proposal exists
    option_label = "Option C" if has_proposal else "Option B"
    st.header(f"{option_label}: Manual Product Selection")
    st.markdown("**Use this if:** You're starting from scratch without a proposal or completed form")
    st.caption("Add products to your order, then configure settings for each product below")

    # Create dropdowns for filtering
    col1, col2, col3 = st.columns([2, 1, 1])

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
        st.session_state.order_use_msrp = st.checkbox(
            "Use MSRP pricing",
            value=st.session_state.order_use_msrp,
            key="order_use_msrp_checkbox",
            help="When enabled, products with MSRP will have markup auto-calculated to match MSRP. Products without MSRP will use 100% markup."
        )

    with col3:
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

            # Determine markup: use MSRP if enabled, otherwise 100%
            if st.session_state.order_use_msrp:
                markup = calculate_msrp_markup(product_data.to_dict())
            else:
                markup = 100.0

            # Add product with defaults
            new_item = {
                'product_name': product_data.get('Product/Service', 'Unknown Product'),
                'partner': product_data.get('Partner', 'Unknown Partner'),
                'product_data': product_data.to_dict(),
                'quantity': 1,
                'markup_percent': markup,
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
                    'markup_amount': (base_price * 1) * (markup / 100),
                    'product_total': (base_price * 1) + ((base_price * 1) * (markup / 100)),
                    'total_per_unit': ((base_price * 1) + ((base_price * 1) * (markup / 100))) / 1,
                    'tariff_rate_percent': 0.0,
                    'tariff_amount': 0.0
                })

                st.session_state.order_items.append(new_item)

                # Auto-populate partner shipping if this product has shipping data
                pbp_shipping_cost, _ = get_shipping_costs(product_data.to_dict())
                if pbp_shipping_cost > 0 and st.session_state.partner_shipping == 0:
                    st.session_state.partner_shipping = pbp_shipping_cost

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

                    # Show quoted price warning if this came from a proposal and price changed
                    quoted_price = item.get('quoted_price_per_unit', 0.0)
                    if quoted_price > 0:
                        # Product came from proposal - show comparison
                        if abs(client_price_per_unit - quoted_price) > 0.01:  # Allow for rounding errors
                            # Determine WHY the price changed
                            reasons = []

                            # Check if tier changed
                            proposal_tier = item.get('proposal_tier_column', '')
                            current_tier = item.get('tier_column', '')
                            proposal_tier_range = item.get('proposal_tier_range', '')
                            current_tier_range = tier_range

                            if proposal_tier and current_tier and proposal_tier != current_tier:
                                reasons.append(f"Tier change: {proposal_tier} ({proposal_tier_range}) → {current_tier} ({current_tier_range})")

                            # Check if markup changed
                            proposal_markup = item.get('proposal_markup_percent', 0)
                            current_markup = new_markup

                            if abs(proposal_markup - current_markup) > 0.01:
                                reasons.append(f"Markup change: {proposal_markup:.0f}% → {current_markup:.0f}%")

                            # Display warning with reasons
                            if reasons:
                                reason_text = " | ".join(reasons)
                                st.warning(f"WARNING: Price changed from proposal (${quoted_price:.2f}/unit → ${client_price_per_unit:.2f}/unit)\n\nReason: {reason_text}")
                            else:
                                st.warning(f"WARNING: Price changed from proposal: Quoted price was ${quoted_price:.2f}/unit, current is ${client_price_per_unit:.2f}/unit")
                        else:
                            st.info(f"Matches quoted price: ${quoted_price:.2f}/unit")
                    else:
                        # Product added manually (not from proposal)
                        st.caption("Quoted price: Unknown (product added manually)")

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
                        st.markdown("**Client Pricing:**")
                        # Always read default from product_data, use item value if user has edited it
                        default_setup = clean_price(product_data.get('Customization Setup Fee', '')) or 0.0
                        stored_setup = item.get('customization_setup_fee', 0.0)
                        # Use stored value if it's non-zero OR if no default exists, otherwise use default
                        display_setup = stored_setup if (stored_setup > 0 or default_setup == 0) else default_setup

                        new_setup_fee = st.number_input(
                            "Setup Fee (to Client)",
                            min_value=0.0,
                            value=float(display_setup),
                            step=1.0,
                            key=f"prod_setup_{idx}"
                        )

                        st.markdown("**Partner Cost:**")
                        # Load partner cost from spreadsheet
                        default_partner_setup = clean_price(product_data.get('PBP Price: Customization Setup Fee', '')) or 0.0
                        stored_partner_setup = item.get('partner_customization_setup_fee', 0.0)
                        display_partner_setup = stored_partner_setup if (stored_partner_setup > 0 or default_partner_setup == 0) else default_partner_setup

                        new_partner_setup_fee = st.number_input(
                            "Setup Fee (from Partner)",
                            min_value=0.0,
                            value=float(display_partner_setup),
                            step=1.0,
                            key=f"prod_partner_setup_{idx}",
                            help="Cost PBP pays to partner for setup"
                        )

                    with col_perunit:
                        st.markdown("**Client Pricing:**")
                        # Always read default from product_data, use item value if user has edited it
                        default_perunit = clean_price(product_data.get('Customization Cost per Unit', '')) or 0.0
                        stored_perunit = item.get('customization_per_unit', 0.0)
                        # Use stored value if it's non-zero OR if no default exists, otherwise use default
                        display_perunit = stored_perunit if (stored_perunit > 0 or default_perunit == 0) else default_perunit

                        new_perunit_cost = st.number_input(
                            "Per-Unit Cost (to Client)",
                            min_value=0.0,
                            value=float(display_perunit),
                            step=0.1,
                            key=f"prod_perunit_{idx}"
                        )

                        st.markdown("**Partner Cost:**")
                        # Load partner cost from spreadsheet
                        default_partner_perunit = clean_price(product_data.get('PBP Price: Customization Cost per Unit', '')) or 0.0
                        stored_partner_perunit = item.get('partner_customization_per_unit', 0.0)
                        display_partner_perunit = stored_partner_perunit if (stored_partner_perunit > 0 or default_partner_perunit == 0) else default_partner_perunit

                        new_partner_perunit_cost = st.number_input(
                            "Per-Unit Cost (from Partner)",
                            min_value=0.0,
                            value=float(display_partner_perunit),
                            step=0.1,
                            key=f"prod_partner_perunit_{idx}",
                            help="Cost PBP pays to partner per unit"
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
                new_partner_setup_fee = 0.0
                new_partner_perunit_cost = 0.0
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

                # Calculate partner customization costs (for accounting)
                if new_include_custom:
                    effective_custom_qty = new_custom_min_qty if (new_apply_minimum and new_custom_min_qty > new_quantity) else new_quantity
                    partner_customization_setup_total = new_partner_setup_fee
                    partner_customization_unit_total = new_partner_perunit_cost * effective_custom_qty
                else:
                    partner_customization_setup_total = 0.0
                    partner_customization_unit_total = 0.0

                # Update item in session state
                st.session_state.order_items[idx].update({
                    'quantity': new_quantity,
                    'markup_percent': new_markup,
                    'include_customization': new_include_custom,
                    'customization_setup_fee': new_setup_fee,
                    'customization_per_unit': new_perunit_cost,
                    'partner_customization_setup_fee': new_partner_setup_fee,
                    'partner_customization_per_unit': new_partner_perunit_cost,
                    'partner_customization_setup_total': partner_customization_setup_total,
                    'partner_customization_unit_total': partner_customization_unit_total,
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
                    'total_per_unit': total_per_unit,
                    'tariff_base': product_subtotal  # Base for tariff calculation (product cost only, excludes markup and customization)
                })

                # Recalculate tariff if rate is set
                if item.get('tariff_rate_percent', 0) > 0:
                    item['tariff_amount'] = calculate_product_tariff(
                        product_subtotal,
                        item['tariff_rate_percent']
                    )

                # PRICING BREAKDOWN DISPLAY
                st.markdown("##### Pricing Breakdown")
                st.caption(f"**Product: {item['product_name']}**")

                # Import helper function for formatting rows
                from src.helpers import format_pricing_breakdown_row

                breakdown_data = []

                # Base product row - include product name in description
                product_pbp_cost = product_subtotal
                product_client_price = product_subtotal + markup_amount
                client_per_unit = (product_subtotal + markup_amount) / new_quantity if new_quantity > 0 else 0

                breakdown_data.append(
                    format_pricing_breakdown_row(
                        f"Base Product: {item['product_name']}",
                        new_quantity,
                        base_price,  # PBP per unit
                        product_pbp_cost,  # PBP total
                        client_per_unit,  # Client per unit
                        product_client_price  # Client total
                    )
                )

                # Customization setup fee (if applicable)
                if customization_setup_total > 0:
                    breakdown_data.append(
                        format_pricing_breakdown_row(
                            "Customization Setup",
                            "one-time",
                            partner_customization_setup_total,  # PBP per unit (same as total for one-time)
                            partner_customization_setup_total,  # PBP total
                            customization_setup_total,  # Client per unit (same as total for one-time)
                            customization_setup_total  # Client total
                        )
                    )

                # Customization per-unit (if applicable)
                if customization_unit_total > 0:
                    effective_custom_qty = new_custom_min_qty if (new_apply_minimum and new_custom_min_qty > new_quantity) else new_quantity
                    breakdown_data.append(
                        format_pricing_breakdown_row(
                            "Customization Per-Unit",
                            effective_custom_qty,
                            new_partner_perunit_cost,  # PBP per unit cost
                            partner_customization_unit_total,  # PBP total
                            new_perunit_cost,  # Client per unit price
                            customization_unit_total  # Client total
                        )
                    )

                # Create DataFrame with new column structure
                breakdown_df = pd.DataFrame(
                    breakdown_data,
                    columns=["Description", "Units", "PBP Cost (Per Unit)", "PBP Cost", "Client Price (Per Unit)", "Client Price"]
                )
                st.table(breakdown_df)

                # Show totals summary
                total_pbp_cost = product_pbp_cost + partner_customization_setup_total + partner_customization_unit_total
                total_client_price = product_total

                st.caption(f"**Totals:** PBP Cost: ${total_pbp_cost:.2f} | Client Price: ${total_client_price:.2f} | Margin: ${total_client_price - total_pbp_cost:.2f}")

                # Store additional cost fields for order summary
                st.session_state.order_items[idx].update({
                    'customization_setup_cost': partner_customization_setup_total,  # What PBP pays for setup
                    'customization_unit_cost': partner_customization_unit_total,    # What PBP pays per unit
                })

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
            st.markdown("**Client Shipping:**")
            st.session_state.order_shipping = st.number_input(
                "Shipping Price to Client ($)",
                min_value=0.0,
                value=st.session_state.order_shipping,
                step=10.0,
                key="shipping_input",
                help="Shipping cost charged to client"
            )

            st.markdown("**Partner Shipping:**")
            st.session_state.partner_shipping = st.number_input(
                "Shipping Cost from Partner ($)",
                min_value=0.0,
                value=st.session_state.partner_shipping,
                step=10.0,
                key="partner_shipping_input",
                help="Shipping cost PBP pays to partner (for Purchase Orders)"
            )

            st.markdown("**Sales Tax:**")
            st.session_state.sales_tax = st.number_input(
                "Estimated Sales Tax ($)",
                min_value=0.0,
                value=st.session_state.sales_tax,
                step=5.0,
                key="sales_tax_input",
                help="Estimated sales tax amount to be charged to client"
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

            # Show what discount was quoted in proposal (if any)
            proposal_discount_type = st.session_state.get('proposal_discount_type')
            proposal_discount_percent = st.session_state.get('proposal_discount_percent', 0.0)

            if proposal_discount_type == 'NGO':
                st.caption("Discount Quoted to Client: NGO Discount (5%)")
            elif proposal_discount_type == 'Custom' and proposal_discount_percent > 0:
                st.caption(f"Discount Quoted to Client: Custom ({proposal_discount_percent}%)")
            else:
                st.caption("Discount Quoted to Client: None")

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
            st.session_state.order_fifty_cent_rounding = st.checkbox(
                "Round prices to nearest $0.50",
                value=st.session_state.order_fifty_cent_rounding,
                key="order_fifty_cent_rounding_checkbox",
                help="Rounds all prices to nearest 50 cents (e.g., $24.37 → $24.50)"
            )

            st.session_state.order_use_marketing_rounding = st.checkbox(
                "Apply marketing rounding (e.g., $60 → $59)",
                value=st.session_state.order_use_marketing_rounding,
                key="marketing_rounding_checkbox",
                help="Apply charm pricing to prices ending in 0. Applied after $0.50 rounding."
            )

        with col3:
            st.session_state.apply_cc_fee = st.checkbox(
                "Credit card fee",
                value=st.session_state.apply_cc_fee,
                key="cc_fee_checkbox",
                help="Add credit card processing fee to total (default 3%)"
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

        # Kitting & Gift Set Pricing
        st.divider()
        st.subheader("Kitting & Gift Set Pricing")
        st.caption("Add costs for gift boxes, custom packaging, or product assembly")

        col1_kitting, col2_kitting = st.columns(2)

        with col1_kitting:
            st.session_state.kitting_pbp_cost = st.number_input(
                "Kitting Cost (PBP) ($)",
                min_value=0.0,
                value=st.session_state.kitting_pbp_cost,
                step=10.0,
                key="kitting_pbp_input",
                help="What PBP pays for gift set assembly and packaging"
            )

        with col2_kitting:
            st.session_state.kitting_client_price = st.number_input(
                "Kitting Price (Client) ($)",
                min_value=0.0,
                value=st.session_state.kitting_client_price,
                step=10.0,
                key="kitting_client_input",
                help="What client pays for gift sets and custom packaging"
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
                        st.toast(f"Added custom item: {custom_name}")
                        st.rerun()

        with col_notes:
            st.write(f"**Order Notes** ({filled_notes_count} filled)")
            st.caption("Add important details about this order")

    # Order Notes Section - Always visible text areas in 2-column layout
    st.divider()
    st.subheader("Order Notes")
    st.caption("Capture all important details about this order. These notes will appear in purchase orders and invoices.")

    # First row - 3 fields
    notes_col1, notes_col2, notes_col3 = st.columns(3)

    with notes_col1:
        kitting_value = st.session_state.order_notes.get('kitting_specs', '')
        st.session_state.order_notes['kitting_specs'] = st.text_area(
            "Kitting Specifications",
            value=kitting_value,
            placeholder="Box size, packaging requirements, assembly instructions...",
            height=100,
            key="kitting_specs_input",
            help="Details about gift sets, packaging, and assembly"
        )
        if kitting_value:
            word_count = len(kitting_value.split())
            st.caption(f"{word_count} words")

    with notes_col2:
        client_value = st.session_state.order_notes.get('client_requests', '')
        st.session_state.order_notes['client_requests'] = st.text_area(
            "Client Requests",
            value=client_value,
            placeholder="Rush delivery, special handling, specific requirements...",
            height=100,
            key="client_requests_input",
            help="Special requests or requirements from the client"
        )
        if client_value:
            word_count = len(client_value.split())
            st.caption(f"{word_count} words")

    with notes_col3:
        samples_value = st.session_state.order_notes.get('addon_samples', '')
        st.session_state.order_notes['addon_samples'] = st.text_area(
            "Samples Required",
            value=samples_value,
            placeholder="Executive samples, approval samples, extra units...",
            height=100,
            key="addon_samples_input",
            help="Sample products needed for this order"
        )
        if samples_value:
            word_count = len(samples_value.split())
            st.caption(f"{word_count} words")

    # Second row - 2 fields
    notes_col4, notes_col5 = st.columns(2)

    with notes_col4:
        artwork_value = st.session_state.order_notes.get('artwork_attachments', '')
        st.session_state.order_notes['artwork_attachments'] = st.text_area(
            "Artwork Details",
            value=artwork_value,
            placeholder="Logo files, design specifications, brand guidelines, file names...",
            height=100,
            key="artwork_attachments_input",
            help="Logo placement, design requirements, branding information"
        )
        if artwork_value:
            word_count = len(artwork_value.split())
            st.caption(f"{word_count} words")

    with notes_col5:
        general_value = st.session_state.order_notes.get('general_notes', '')
        st.session_state.order_notes['general_notes'] = st.text_area(
            "General Notes",
            value=general_value,
            placeholder="Any other important information about this order...",
            height=100,
            key="general_notes_input",
            help="Catch-all for any other notes or details"
        )
        if general_value:
            word_count = len(general_value.split())
            st.caption(f"{word_count} words")

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
        # Import helper functions
        from src.helpers import calculate_split_totals

        # Calculate split totals
        split_totals = calculate_split_totals(st.session_state.order_items)

        # Apply discount ONLY to products client price (not customization)
        discount_amount = split_totals['products_only_client_price'] * (discount_percent / 100)
        products_after_discount = split_totals['products_only_client_price'] - discount_amount

        # Build subtotal: products after discount + customization (no discount on customization)
        subtotal_after_discount = products_after_discount + split_totals['customization_client_price']

        # Get sales tax amount
        sales_tax = st.session_state.sales_tax

        # Get kitting costs
        kitting_pbp = st.session_state.kitting_pbp_cost
        kitting_client = st.session_state.kitting_client_price

        # Calculate base total before CC fee
        total_before_cc = subtotal_after_discount + shipping + sales_tax + kitting_client + tariff

        # Calculate credit card fee (applied to total before CC fee)
        cc_fee_amount = calculate_credit_card_fee(total_before_cc, st.session_state.apply_cc_fee, st.session_state.cc_fee_percent)

        # Final total
        total_quote = total_before_cc + cc_fee_amount

        # Apply $0.50 rounding if enabled
        total_quote = round_to_nearest_fifty_cents(total_quote, st.session_state.order_fifty_cent_rounding)

        # Apply marketing rounding if enabled (after $0.50 rounding)
        total_quote = apply_marketing_rounding(total_quote, st.session_state.order_use_marketing_rounding)

        total_units = sum(item['quantity'] for item in st.session_state.order_items)

        summary_items = []

        # SECTION 1: Products with product names as headers
        st.markdown("##### Products")
        for item in st.session_state.order_items:
            # Skip custom line items for now
            if item.get('is_custom', False):
                summary_items.append([
                    item['product_name'],
                    item['quantity'],
                    f"${item['total_per_unit']:.2f}",
                    f"${item['product_total']:.2f}",
                    f"${item['total_per_unit']:.2f}",
                    f"${item['product_total']:.2f}"  # Custom items have same cost and price
                ])
                continue

            # Product header
            st.caption(f"**{item['product_name']}**")

            # Regular product: show base product with product name
            product_pbp_cost = item.get('product_subtotal', 0)
            product_client_price = product_pbp_cost + item.get('markup_amount', 0)
            product_pbp_per_unit = product_pbp_cost / item['quantity'] if item['quantity'] > 0 else 0
            product_client_per_unit = product_client_price / item['quantity'] if item['quantity'] > 0 else 0

            summary_items.append([
                f"Base Product: {item['product_name']}",
                item['quantity'],
                f"${product_pbp_per_unit:.2f}",
                f"${product_pbp_cost:.2f}",
                f"${product_client_per_unit:.2f}",
                f"${product_client_price:.2f}"
            ])

        # Products subtotal row
        summary_items.append([
            "**Products Subtotal**",
            "",
            "",
            f"**${split_totals['products_pbp_cost']:.2f}**",
            "",
            f"**${split_totals['products_client_price']:.2f}**"
        ])

        # SECTION 2: Customization (if any)
        if split_totals['customization_client_price'] > 0:
            summary_items.append(["", "", "", "", "", ""])  # Empty row for spacing
            st.markdown("##### Customization")

            for item in st.session_state.order_items:
                if item.get('is_custom', False):
                    continue

                # Show customization if present
                setup_pbp = item.get('customization_setup_cost', 0)
                setup_client = item.get('customization_setup_total', 0)
                unit_pbp = item.get('customization_unit_cost', 0)
                unit_client = item.get('customization_unit_total', 0)
                partner_per_unit = item.get('partner_customization_per_unit', 0)

                if setup_client > 0:
                    summary_items.append([
                        f"{item['product_name']} - Setup",
                        "one-time",
                        f"${setup_pbp:.2f}",  # Per unit same as total for one-time
                        f"${setup_pbp:.2f}",
                        f"${setup_client:.2f}",  # Per unit same as total for one-time
                        f"${setup_client:.2f}"
                    ])

                if unit_client > 0:
                    effective_custom_qty = item.get('customization_minimum_qty', item['quantity']) if item.get('apply_custom_minimum', False) else item['quantity']
                    custom_per_unit = item.get('customization_per_unit', 0)
                    pbp_custom_per_unit = unit_pbp / effective_custom_qty if effective_custom_qty > 0 else 0

                    summary_items.append([
                        f"{item['product_name']} - Per Unit",
                        effective_custom_qty,
                        f"${partner_per_unit:.2f}",
                        f"${unit_pbp:.2f}",
                        f"${custom_per_unit:.2f}",
                        f"${unit_client:.2f}"
                    ])

            # Customization subtotal row
            summary_items.append([
                "**Customization Subtotal**",
                "",
                "",
                f"**${split_totals['customization_pbp_cost']:.2f}**",
                "",
                f"**${split_totals['customization_client_price']:.2f}**"
            ])

        # SECTION 3: Discounts, Shipping, Tariffs, Fees
        summary_items.append(["", "", "", "", "", ""])  # Empty row for spacing

        # Add discount line if applicable (applies to products only, not customization)
        if discount_percent > 0:
            summary_items.append([
                f"Discount ({discount_description})",
                "",
                "",
                "",
                f"-${discount_amount:.2f}",
                ""
            ])

        # Shipping (same for PBP and client)
        summary_items.append(["Shipping", "", "", f"${shipping:.2f}", "", f"${shipping:.2f}"])

        # Sales Tax (only affects client price)
        if sales_tax > 0:
            summary_items.append(["Sales Tax (Estimated)", "", "", "", "", f"${sales_tax:.2f}"])

        # Kitting/Gift Set Assembly (show if either cost > 0)
        if kitting_pbp > 0 or kitting_client > 0:
            summary_items.append(["Kitting/Gift Set Assembly", "", "", f"${kitting_pbp:.2f}", "", f"${kitting_client:.2f}"])

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
                    f"${tariff_amount:.2f}",
                    "",
                    f"${tariff_amount:.2f}"
                ])

        # Add credit card fee if applicable (client pays)
        if st.session_state.apply_cc_fee and cc_fee_amount > 0:
            summary_items.append([
                f"Credit Card Fee ({st.session_state.cc_fee_percent}%)",
                "",
                "",
                "",
                "",
                f"${cc_fee_amount:.2f}"
            ])

        # Calculate total PBP cost (sales tax only affects client, not PBP)
        total_pbp_cost = split_totals['total_pbp_cost'] + shipping + kitting_pbp + tariff

        # Final total row
        summary_items.append([
            "**TOTAL**",
            f"**{total_units} units**",
            "",
            f"**${total_pbp_cost:.2f}**",
            "",
            f"**${total_quote:.2f}**"
        ])

        # Create and display table with new column structure
        summary_df = pd.DataFrame(summary_items, columns=["Item", "Qty", "PBP Cost (Per Unit)", "PBP Cost", "Client Price (Per Unit)", "Client Price"])
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

        # Contacts Management Section
        st.markdown("---")
        st.markdown("**Contacts Information**")

        # Display all contacts
        contacts = st.session_state.client_info.get('contacts', [])
        if not contacts:
            contacts = [{'name': '', 'email': '', 'phone': '', 'role': 'Primary Contact'}]
            st.session_state.client_info['contacts'] = contacts

        # Add/Remove buttons
        col_add, col_spacer = st.columns([1, 3])
        with col_add:
            if st.button("Add Another Contact", key="add_contact_tab3"):
                st.session_state.client_info['contacts'].append({
                    'name': '',
                    'email': '',
                    'phone': '',
                    'role': ''
                })
                st.rerun()

        # Display each contact
        for idx, contact in enumerate(contacts):
            contact_num = idx + 1

            # Contact header with remove button
            if len(contacts) > 1:
                col_header, col_remove = st.columns([3, 1])
                with col_header:
                    st.markdown(f"**Contact {contact_num}**")
                with col_remove:
                    if st.button(f"Remove", key=f"remove_contact_{idx}_tab3"):
                        st.session_state.client_info['contacts'].pop(idx)
                        st.rerun()
            else:
                st.markdown(f"**Contact {contact_num}**")

            # Contact fields in 2 columns
            col_contact1, col_contact2 = st.columns(2)

            with col_contact1:
                contact['name'] = st.text_input(
                    "Name",
                    value=contact.get('name', ''),
                    key=f"contact_name_{idx}_tab3",
                    placeholder="e.g., John Smith"
                )

                contact['email'] = st.text_input(
                    "Email",
                    value=contact.get('email', ''),
                    key=f"contact_email_{idx}_tab3",
                    placeholder="e.g., john@company.com"
                )

            with col_contact2:
                contact['phone'] = st.text_input(
                    "Phone",
                    value=contact.get('phone', ''),
                    key=f"contact_phone_{idx}_tab3",
                    placeholder="e.g., (555) 123-4567"
                )

                role_options = ['Primary Contact', 'Billing Contact', 'Technical Contact', 'Shipping Contact', 'Other']
                current_role = contact.get('role', 'Primary Contact')
                if current_role not in role_options and current_role:
                    role_options.append(current_role)

                contact['role'] = st.selectbox(
                    "Role",
                    options=role_options,
                    index=role_options.index(current_role) if current_role in role_options else 0,
                    key=f"contact_role_{idx}_tab3"
                )

            if idx < len(contacts) - 1:
                st.markdown("")  # Add spacing between contacts

        st.markdown("---")
        st.markdown("**Payment & Delivery Terms**")

        col3, col4 = st.columns(2)

        with col3:
            # Updated to dropdown with Net 15 and Custom option
            payment_terms_options = ['Net 30', 'Net 15', 'Net 60', 'Due on Receipt', '50% Deposit', 'Custom']
            current_timeline = st.session_state.client_info.get('payment_timeline', 'Net 30')

            # If current value is custom (not in standard options), select Custom
            if current_timeline not in payment_terms_options[:-1]:  # Exclude 'Custom' from check
                if current_timeline and current_timeline != 'Custom':
                    st.session_state.custom_payment_terms = current_timeline
                selected_index = payment_terms_options.index('Custom')
            else:
                selected_index = payment_terms_options.index(current_timeline)

            selected_payment = st.selectbox(
                "Payment Terms",
                options=payment_terms_options,
                index=selected_index
            )

            # If Custom is selected, show text input
            if selected_payment == "Custom":
                custom_terms = st.text_input(
                    "Enter Custom Payment Terms",
                    value=st.session_state.custom_payment_terms,
                    placeholder="e.g., Net 45, 2/10 Net 30, etc.",
                    key="custom_payment_input_tab3"
                )
                st.session_state.custom_payment_terms = custom_terms
                st.session_state.client_info['payment_timeline'] = custom_terms if custom_terms else "Custom"
            else:
                st.session_state.client_info['payment_timeline'] = selected_payment

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

    if not st.session_state.order_confirmed:
        st.markdown("### Ready to finalize your order?")
        st.caption("Review the order summary above and client information, then confirm to proceed to Tab 3.")

        if st.button("Confirm Order", type="primary", use_container_width=True):
            st.session_state.order_confirmed = True
            st.rerun()
    else:
        st.success("Order complete! Your order summary is ready.")
        st.info("Go to **Tab 4: Execution & Accounting** to generate Invoice & Purchase Order for this order.")

        # Optional: Add button to go back and edit
        if st.button("Edit Order", type="secondary"):
            st.session_state.order_confirmed = False
            st.rerun()

    # Save Your Work section at bottom of Tab 3
    st.divider()
    st.markdown("### Save Your Work")

    # Show unsaved changes indicator and save status
    if has_unsaved_order_changes():
        st.warning("You have unsaved changes in your order")

    save_status_bottom = format_time_since_save('order')
    if save_status_bottom:
        st.caption(f"{save_status_bottom}")

    # Check if there are products to save
    has_order_items = len(st.session_state.order_items) > 0

    if has_order_items:
        col1, col2 = st.columns(2)
        with col1:
            order_name = st.text_input(
                "Order name:",
                key="save_order_name_bottom",
                placeholder="e.g., Client ABC Q1 2025 Order"
            )
        with col2:
            created_by = st.text_input(
                "Your name (optional):",
                key="save_order_creator_bottom",
                placeholder="e.g., John Smith"
            )

        if st.button("Save Order", type="primary", use_container_width=True, key="save_order_btn_bottom"):
            if not order_name or not order_name.strip():
                st.error("Please enter an order name")
            else:
                # Prepare order data
                order_data = {
                    'order_items': st.session_state.order_items,
                    'order_shipping': st.session_state.order_shipping,
                    'partner_shipping': st.session_state.partner_shipping,
                    'sales_tax': st.session_state.sales_tax,
                    'kitting_pbp_cost': st.session_state.kitting_pbp_cost,
                    'kitting_client_price': st.session_state.kitting_client_price,
                    'order_discount_type': st.session_state.order_discount_type,
                    'order_discount_preset': st.session_state.order_discount_preset,
                    'order_discount_custom_desc': st.session_state.order_discount_custom_desc,
                    'order_discount_custom_value': st.session_state.order_discount_custom_value,
                    'order_use_marketing_rounding': st.session_state.order_use_marketing_rounding,
                    'apply_cc_fee': st.session_state.apply_cc_fee,
                    'cc_fee_percent': st.session_state.cc_fee_percent,
                    'client_info': st.session_state.client_info,
                    'order_notes': st.session_state.order_notes,
                    'order_confirmed': st.session_state.order_confirmed
                }

                success, message, result = save_order(
                    name=order_name.strip(),
                    created_by=created_by.strip() if created_by else "",
                    order_data=order_data,
                    dataset=st.session_state.selected_dataset
                )

                if success:
                    update_last_save_time('order')
                    clear_saved_data_cache()  # Clear cache to show new order
                    st.success(f"{message} - You can find it in the sidebar under 'Saved Orders'")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    # Check if it's a naming conflict
                    if result:  # result contains suggested name
                        st.error(message)
                        if st.button(f"Save as '{result}'", key="save_with_new_name_order_bottom"):
                            success2, message2, _ = save_order(
                                name=result,
                                created_by=created_by.strip() if created_by else "",
                                order_data=order_data,
                                dataset=st.session_state.selected_dataset
                            )
                            if success2:
                                update_last_save_time('order')
                                clear_saved_data_cache()  # Clear cache to show new order
                                st.success(f"{message2} - You can find it in the sidebar")
                                time.sleep(1.5)
                                st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("Add products to your order to enable saving")

    # Navigation button at bottom of Tab 3
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Continue to Tab 4: Execution & Accounting", type="primary", use_container_width=True, key="tab3_to_tab4"):
            st.session_state.show_tab4_prompt = True
            st.rerun()

    # Show navigation prompt if button was clicked
    if st.session_state.get('show_tab4_prompt', False):
        st.info("Click on the **'Execution & Accounting'** tab above to continue.")
        st.session_state.show_tab4_prompt = False

# ============================================================
# TAB 4: EXECUTION & ACCOUNTING
# ============================================================
with tab4:
    st.header("Execution & Accounting - Invoice & Purchase Order Management")
    st.caption("Generate invoices and purchase orders for confirmed orders")
    st.divider()

    # Check if order exists in Tab 3
    if len(st.session_state.order_items) == 0:
        st.info("No order found. Please build an order in Tab 3 first.")
        st.markdown("### To create an invoice/PO:")
        st.markdown("1. Go to **Tab 3: Order & Client Info**")
        st.markdown("2. Complete Sections 1-8 (client info, products, settings, summary)")
        st.markdown("3. Return to this tab to generate Invoice/PO")
    else:
        # ============================================================
        # SECTION 1: REVIEW & EDIT ORDER INFORMATION
        # ============================================================
        st.subheader("1. Review & Edit Order Information")
        st.caption("Review and complete any missing information before generating the invoice/PO")

        client_info = st.session_state.client_info
        validation_warnings = validate_invoice_completeness(client_info, st.session_state.order_items)

        if validation_warnings:
            st.warning(f"{len(validation_warnings)} field(s) need attention. Complete the missing information below:")
        else:
            st.success("All required fields complete - ready to generate Invoice/PO")

        # Editable fields for missing information
        with st.expander("Edit Order Information", expanded=bool(validation_warnings)):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Client Information**")
                # Use callback to update client_info to ensure persistence
                def update_company_name():
                    st.session_state.client_info['company_name'] = st.session_state.tab3_company_name

                st.text_input(
                    "Company Name",
                    value=st.session_state.client_info.get('company_name', ''),
                    key="tab3_company_name",
                    on_change=update_company_name
                )


                def update_billing_address():
                    st.session_state.client_info['billing_address'] = st.session_state.tab3_billing_address

                st.text_area(
                    "Billing Address",
                    value=st.session_state.client_info.get('billing_address', ''),
                    key="tab3_billing_address",
                    height=80,
                    on_change=update_billing_address
                )

                def update_shipping_address():
                    st.session_state.client_info['shipping_address'] = st.session_state.tab3_shipping_address

                st.text_area(
                    "Shipping Address",
                    value=st.session_state.client_info.get('shipping_address', ''),
                    key="tab3_shipping_address",
                    height=80,
                    on_change=update_shipping_address
                )

            # Contacts Management Section
            st.markdown("---")
            st.markdown("**Contacts Management**")

            # Display all contacts
            contacts = st.session_state.client_info.get('contacts', [])
            if not contacts:
                contacts = [{'name': '', 'email': '', 'phone': '', 'role': 'Primary Contact'}]
                st.session_state.client_info['contacts'] = contacts

            # Add button
            if st.button("Add Contact", key="add_contact_tab4"):
                st.session_state.client_info['contacts'].append({
                    'name': '',
                    'email': '',
                    'phone': '',
                    'role': ''
                })
                st.rerun()

            # Display each contact
            for idx, contact in enumerate(contacts):
                with st.expander(f"Contact {idx + 1}", expanded=True):
                    contact_col1, contact_col2 = st.columns(2)

                    with contact_col1:
                        # Create callback functions for each field
                        def update_contact_name(idx=idx):
                            st.session_state.client_info['contacts'][idx]['name'] = st.session_state[f"tab4_contact_name_{idx}"]

                        def update_contact_email(idx=idx):
                            st.session_state.client_info['contacts'][idx]['email'] = st.session_state[f"tab4_contact_email_{idx}"]

                        contact['name'] = st.text_input(
                            "Name",
                            value=contact.get('name', ''),
                            key=f"tab4_contact_name_{idx}",
                            on_change=lambda idx=idx: st.session_state.client_info['contacts'][idx].update(
                                {'name': st.session_state[f"tab4_contact_name_{idx}"]}
                            )
                        )

                        contact['email'] = st.text_input(
                            "Email",
                            value=contact.get('email', ''),
                            key=f"tab4_contact_email_{idx}",
                            on_change=lambda idx=idx: st.session_state.client_info['contacts'][idx].update(
                                {'email': st.session_state[f"tab4_contact_email_{idx}"]}
                            )
                        )

                    with contact_col2:
                        contact['phone'] = st.text_input(
                            "Phone",
                            value=contact.get('phone', ''),
                            key=f"tab4_contact_phone_{idx}",
                            on_change=lambda idx=idx: st.session_state.client_info['contacts'][idx].update(
                                {'phone': st.session_state[f"tab4_contact_phone_{idx}"]}
                            )
                        )

                        role_options = ['Primary Contact', 'Billing Contact', 'Technical Contact', 'Shipping Contact', 'Other']
                        current_role = contact.get('role', 'Primary Contact')
                        if current_role not in role_options and current_role:
                            role_options.append(current_role)

                        contact['role'] = st.selectbox(
                            "Role",
                            options=role_options,
                            index=role_options.index(current_role) if current_role in role_options else 0,
                            key=f"tab4_contact_role_{idx}",
                            on_change=lambda idx=idx: st.session_state.client_info['contacts'][idx].update(
                                {'role': st.session_state[f"tab4_contact_role_{idx}"]}
                            )
                        )

                    # Remove button if more than one contact
                    if len(contacts) > 1:
                        if st.button(f"Remove Contact {idx + 1}", key=f"remove_contact_{idx}_tab4"):
                            st.session_state.client_info['contacts'].pop(idx)
                            st.rerun()

            with col2:
                st.markdown("**Order Details**")

                def update_in_hands_date():
                    st.session_state.client_info['client_in_hands_date'] = st.session_state.tab3_in_hands_date

                st.date_input(
                    "Client In-Hands Date",
                    value=st.session_state.client_info.get('client_in_hands_date'),
                    key="tab3_in_hands_date",
                    on_change=update_in_hands_date
                )

                def update_ship_method():
                    st.session_state.client_info['shipping_type'] = st.session_state.tab3_ship_method

                ship_method_options = ['Ground', 'Air', 'Freight', 'Other']
                current_ship = st.session_state.client_info.get('shipping_type', 'Ground')
                st.selectbox(
                    "Ship Method",
                    options=ship_method_options,
                    index=ship_method_options.index(current_ship) if current_ship in ship_method_options else 0,
                    key="tab3_ship_method",
                    on_change=update_ship_method
                )

                def update_payment_terms():
                    selected = st.session_state.tab3_payment_terms
                    if selected == "Custom":
                        # Use the custom terms if available
                        if st.session_state.custom_payment_terms:
                            st.session_state.client_info['payment_timeline'] = st.session_state.custom_payment_terms
                    else:
                        st.session_state.client_info['payment_timeline'] = selected

                payment_terms_options = ['Net 30', 'Net 15', 'Net 60', 'Due on Receipt', '50% Deposit', 'Custom']
                current_terms = st.session_state.client_info.get('payment_timeline', 'Net 30')

                # Handle custom terms display
                if current_terms not in payment_terms_options[:-1]:  # Exclude 'Custom' from check
                    if current_terms and current_terms != 'Custom':
                        st.session_state.custom_payment_terms = current_terms
                    display_index = payment_terms_options.index("Custom")
                else:
                    display_index = payment_terms_options.index(current_terms)

                selected_payment = st.selectbox(
                    "Payment Terms",
                    options=payment_terms_options,
                    index=display_index,
                    key="tab3_payment_terms",
                    on_change=update_payment_terms
                )

                # If Custom is selected, show text input
                if selected_payment == "Custom":
                    def update_custom_terms():
                        st.session_state.custom_payment_terms = st.session_state.custom_terms_edit_input
                        st.session_state.client_info['payment_timeline'] = st.session_state.custom_terms_edit_input

                    st.text_input(
                        "Custom Payment Terms",
                        value=st.session_state.custom_payment_terms,
                        placeholder="e.g., Net 45, 2/10 Net 30, etc.",
                        key="custom_terms_edit_input",
                        on_change=update_custom_terms
                    )

                def update_payment_method():
                    st.session_state.client_info['payment_preference'] = st.session_state.tab3_payment_method

                payment_method_options = ['Check', 'ACH', 'Credit Card', 'Wire Transfer']
                current_method = st.session_state.client_info.get('payment_preference', 'Check')
                st.selectbox(
                    "Payment Method",
                    options=payment_method_options,
                    index=payment_method_options.index(current_method) if current_method in payment_method_options else 0,
                    key="tab3_payment_method",
                    on_change=update_payment_method
                )

                def update_order_submitted_by():
                    st.session_state.client_info['order_submitted_by'] = st.session_state.tab3_order_submitted_by

                st.text_input(
                    "Order Submitted By",
                    value=st.session_state.client_info.get('order_submitted_by', ''),
                    key="tab3_order_submitted_by",
                    on_change=update_order_submitted_by
                )

                def update_cost_submitted_by():
                    st.session_state.client_info['cost_submitted_by'] = st.session_state.tab3_cost_submitted_by

                st.text_input(
                    "Cost Submitted By",
                    value=st.session_state.client_info.get('cost_submitted_by', ''),
                    key="tab3_cost_submitted_by",
                    on_change=update_cost_submitted_by
                )

                def update_cost_submitted_date():
                    st.session_state.client_info['cost_submitted_date'] = st.session_state.tab3_cost_submitted_date

                st.date_input(
                    "Cost Submitted Date",
                    value=st.session_state.client_info.get('cost_submitted_date'),
                    key="tab3_cost_submitted_date",
                    on_change=update_cost_submitted_date
                )

        st.divider()

        # ============================================================
        # EDITABLE ORDER SETTINGS
        # ============================================================
        with st.expander("Edit Order Settings", expanded=False):
            st.caption("Make adjustments to order settings here. Changes sync to Tab 2.")

            # Shipping & Tariffs - Side by Side
            st.subheader("Shipping & Tariffs")

            col_shipping, col_tariff = st.columns(2)

            with col_shipping:
                st.markdown("**Client Shipping:**")
                st.session_state.order_shipping = st.number_input(
                    "Shipping Price to Client ($)",
                    min_value=0.0,
                    value=st.session_state.order_shipping,
                    step=10.0,
                    key="tab3_shipping_input",
                    help="Shipping cost charged to client"
                )

                st.markdown("**Partner Shipping:**")
                st.session_state.partner_shipping = st.number_input(
                    "Shipping Cost from Partner ($)",
                    min_value=0.0,
                    value=st.session_state.partner_shipping,
                    step=10.0,
                    key="tab3_partner_shipping_input",
                    help="Shipping cost PBP pays to partner (for Purchase Orders)"
                )

                st.markdown("**Sales Tax:**")
                st.session_state.sales_tax = st.number_input(
                    "Estimated Sales Tax ($)",
                    min_value=0.0,
                    value=st.session_state.sales_tax,
                    step=5.0,
                    key="tab3_sales_tax_input",
                    help="Estimated sales tax amount to be charged to client"
                )

            with col_tariff:
                # Calculate total tariff for display
                total_tariff = sum(item.get('tariff_amount', 0.0) for item in st.session_state.order_items)

                st.write(f"**Tariff Total:** ${total_tariff:.2f}")

                show_tariff_details = st.checkbox(
                    "Customize Tariff Rates",
                    key="tab3_show_tariff_details",
                    help="Default rates applied based on country of origin. Check to customize per product."
                )

                if show_tariff_details:
                    st.caption("Tariffs are import duties based on product country of origin. Rates default to current estimates but can be adjusted as needed.")

                    # Build editable tariff table with detailed breakdown
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
                                key=f"tab3_tariff_rate_{idx}",
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
                # Discount as dropdown
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
                    key="tab3_order_discount_select"
                )

                # Update session state based on selection
                if discount_selection == "NGO (5%)":
                    st.session_state.order_discount_type = "preset"
                    st.session_state.order_discount_preset = "NGO Discount (5%)"
                    st.session_state.order_discount_custom_value = 0.0
                    st.session_state.order_discount_custom_desc = ""
                elif discount_selection == "Custom":
                    st.session_state.order_discount_type = "custom"
                else:
                    st.session_state.order_discount_type = "none"
                    st.session_state.order_discount_custom_value = 0.0
                    st.session_state.order_discount_custom_desc = ""

            with col2:
                st.session_state.order_fifty_cent_rounding = st.checkbox(
                    "Round prices to nearest $0.50",
                    value=st.session_state.order_fifty_cent_rounding,
                    key="tab4_fifty_cent_rounding_checkbox",
                    help="Rounds all prices to nearest 50 cents (e.g., $24.37 → $24.50)"
                )

                st.session_state.order_use_marketing_rounding = st.checkbox(
                    "Apply marketing rounding (e.g., $60 → $59)",
                    value=st.session_state.order_use_marketing_rounding,
                    key="tab3_marketing_rounding_checkbox",
                    help="Apply charm pricing to prices ending in 0. Applied after $0.50 rounding."
                )

            with col3:
                st.session_state.apply_cc_fee = st.checkbox(
                    "Credit card fee",
                    value=st.session_state.apply_cc_fee,
                    key="tab3_cc_fee_checkbox",
                    help="Add credit card processing fee to total (default 3%)"
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
                            key="tab3_order_custom_discount_input"
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
                            key="tab3_cc_fee_percent_input",
                            help="Percentage fee charged for credit card payments"
                        )

            # Kitting & Gift Set Pricing
            st.divider()
            st.subheader("Kitting & Gift Set Pricing")

            col1_kitting, col2_kitting = st.columns(2)

            with col1_kitting:
                st.session_state.kitting_pbp_cost = st.number_input(
                    "Kitting Cost (PBP) ($)",
                    min_value=0.0,
                    value=st.session_state.kitting_pbp_cost,
                    step=10.0,
                    key="tab4_kitting_pbp_input",
                    help="What PBP pays for gift set assembly and packaging"
                )

            with col2_kitting:
                st.session_state.kitting_client_price = st.number_input(
                    "Kitting Price (Client) ($)",
                    min_value=0.0,
                    value=st.session_state.kitting_client_price,
                    step=10.0,
                    key="tab4_kitting_client_input",
                    help="What client pays for gift sets and custom packaging"
                )

            # Custom Line Items & Order Notes - Side by Side
            st.divider()

            # Count custom items and filled notes
            custom_item_count = sum(1 for item in st.session_state.order_items if item.get('is_custom', False))
            filled_notes_count = sum(1 for note in st.session_state.order_notes.values() if note and note.strip())

            col_custom, col_notes = st.columns(2)

            with col_custom:
                st.write(f"**Custom Line Items** ({custom_item_count} added)")

                show_custom_item_form = st.checkbox(
                    "Add Custom Line Item",
                    key="tab3_show_custom_item_form",
                    help="Add unique services or customizations not in the catalog"
                )

                if show_custom_item_form:
                    st.caption("Add unique services or customizations not in the catalog")

                    custom_name = st.text_input(
                        "Product/Service Name*",
                        key="tab3_custom_name_input",
                        placeholder="e.g., Custom Engraving Service"
                    )
                    custom_quantity = st.number_input(
                        "Quantity*",
                        min_value=1,
                        value=1,
                        step=1,
                        key="tab3_custom_quantity_input"
                    )
                    custom_description = st.text_input(
                        "Description",
                        key="tab3_custom_description_input",
                        placeholder="e.g., Laser engraving on wooden items"
                    )
                    custom_price = st.number_input(
                        "Total Price ($)*",
                        min_value=0.0,
                        value=0.0,
                        step=10.0,
                        key="tab3_custom_price_input",
                        help="Total price for this line item (quantity × unit price)"
                    )

                    if st.button("Add Custom Item to Order", type="secondary", use_container_width=True, key="tab3_add_custom_item_btn"):
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
                            st.toast(f"Added custom item: {custom_name}")
                            st.rerun()

            with col_notes:
                st.write(f"**Order Notes** ({filled_notes_count} filled)")

                show_notes_form = st.checkbox(
                    "Add Order Notes",
                    key="tab3_show_notes_form",
                    help="Add specific details for this order"
                )

                if show_notes_form:
                    st.caption("Add specific details for this order")

                    st.session_state.order_notes['kitting_specs'] = st.text_area(
                        "Kitting Specifications",
                        value=st.session_state.order_notes.get('kitting_specs', ''),
                        placeholder="Box size, packaging requirements...",
                        height=70,
                        key="tab3_kitting_specs",
                        help="Details about how products should be kitted/packaged"
                    )

                    st.session_state.order_notes['client_requests'] = st.text_area(
                        "Client Requests",
                        value=st.session_state.order_notes.get('client_requests', ''),
                        placeholder="Rush delivery, special handling...",
                        height=70,
                        key="tab3_client_requests",
                        help="Special requests from the client"
                    )

                    st.session_state.order_notes['addon_samples'] = st.text_area(
                        "Add-on Samples",
                        value=st.session_state.order_notes.get('addon_samples', ''),
                        placeholder="Extra units, samples for approval...",
                        height=70,
                        key="tab3_addon_samples",
                        help="Additional samples to include with order"
                    )

                    st.session_state.order_notes['artwork_attachments'] = st.text_area(
                        "Artwork Attachments",
                        value=st.session_state.order_notes.get('artwork_attachments', ''),
                        placeholder="logo_final.ai, label_design_v3.pdf...",
                        height=70,
                        key="tab3_artwork_attachments",
                        help="List of artwork files attached to this order"
                    )

                    st.session_state.order_notes['general_notes'] = st.text_area(
                        "General Notes",
                        value=st.session_state.order_notes.get('general_notes', ''),
                        placeholder="Any other important details...",
                        height=70,
                        key="tab3_general_notes",
                        help="Catch-all for any other notes or details"
                    )

        st.divider()

        # ============================================================
        # SECTION 3: INVOICE & PURCHASE ORDER GENERATION
        # ============================================================
        st.subheader("2. Generate Invoice & Purchase Order")

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

                    # Client-facing prices
                    customization_setup = item.get('customization_setup_total', 0)
                    customization_unit_total = item.get('customization_unit_total', 0)
                    customization_per_unit = item.get('customization_per_unit', 0)

                    # Partner costs
                    partner_customization_setup = item.get('partner_customization_setup_total', 0)
                    partner_customization_unit_total = item.get('partner_customization_unit_total', 0)
                    partner_customization_per_unit = item.get('partner_customization_per_unit', 0)

                    # Setup fee line item (show partner cost vs. client price)
                    if customization_setup > 0 or partner_customization_setup > 0:
                        invoice_line_items.append({
                            'PARTNER': partner,
                            'ITEMS + SPECS': f"  └ Setup Fee: {customization_desc}",
                            'QTY': 1,
                            'IN-HANDS from Partner': partner_in_hands,
                            'COST/UNIT': f"${partner_customization_setup:.2f}",
                            'TOTAL COST': f"${partner_customization_setup:.2f}",
                            'COST VERIFIED?': cost_verified,
                            'SELL PRICE/UNIT': f"${customization_setup:.2f}",
                            'TOTAL SELL PRICE': f"${customization_setup:.2f}"
                        })

                    # Per-unit customization line item (show partner cost vs. client price)
                    if customization_unit_total > 0 or partner_customization_unit_total > 0:
                        invoice_line_items.append({
                            'PARTNER': partner,
                            'ITEMS + SPECS': f"  └ Customization: {customization_desc}",
                            'QTY': qty,
                            'IN-HANDS from Partner': partner_in_hands,
                            'COST/UNIT': f"${partner_customization_per_unit:.2f}",
                            'TOTAL COST': f"${partner_customization_unit_total:.2f}",
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

        # Add shipping line item (show partner cost vs. client price)
        partner_shipping_cost = st.session_state.partner_shipping
        client_shipping_price = shipping
        if partner_shipping_cost > 0 or client_shipping_price > 0:
            invoice_line_items.append({
                'PARTNER': 'Shipping',
                'ITEMS + SPECS': 'Shipping',
                'QTY': 1,
                'IN-HANDS from Partner': 'N/A',
                'COST/UNIT': f"${partner_shipping_cost:.2f}",
                'TOTAL COST': f"${partner_shipping_cost:.2f}",
                'COST VERIFIED?': 'Yes',
                'SELL PRICE/UNIT': f"${client_shipping_price:.2f}",
                'TOTAL SELL PRICE': f"${client_shipping_price:.2f}"
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
            ["Subtotal (Products + Customization)", f"${products_subtotal:.2f}"]
        ]

        # Add discount line if applicable (discount applies to products only, not customization)
        if discount_percent > 0:
            totals_data.append([f"Discount ({discount_description}) - on products only", f"-${discount_amount:.2f}"])

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
            notes_content.append(f"**Kitting Specifications:**\n{order_notes['kitting_specs']}")
        if order_notes.get('client_requests'):
            notes_content.append(f"**Client Requests:**\n{order_notes['client_requests']}")
        if order_notes.get('addon_samples'):
            notes_content.append(f"**Samples Required:**\n{order_notes['addon_samples']}")
        if order_notes.get('artwork_attachments'):
            notes_content.append(f"**Artwork Details:**\n{order_notes['artwork_attachments']}")
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

        # Generate HTML Invoice/PO Form
        html_invoice = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; background-color: #ffffff; }}
        h2 {{ color: #2c3e50; background-color: #ffffff; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h3 {{ color: #34495e; margin-top: 25px; margin-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background-color: #ffffff; }}
        th {{ background-color: #3498db !important; color: #ffffff !important; padding: 12px; text-align: left; font-weight: bold; border: 1px solid #2980b9; }}
        td {{ border: 1px solid #ddd; padding: 10px; background-color: #ffffff; color: #000000; }}
        td:first-child {{ background-color: #f8f9fa !important; color: #000000 !important; font-weight: 500; width: 30%; }}
        .section-header {{ background-color: #2c3e50 !important; color: #ffffff !important; font-weight: bold; padding: 12px; text-align: center; }}
        .notes-section {{ background-color: #e8f4f8; border: 1px solid #3498db; padding: 15px; margin: 15px 0; }}
        .notes-header {{ font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .company-header {{ background-color: #34495e; color: #ffffff; padding: 15px; text-align: center; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h2>INVOICE AND PURCHASE ORDER REQUEST FORM</h2>

    <h3>1. Client/Company Information</h3>
    <table>
        <tr>
            <td>Company/Client Name</td>
            <td>{client_info.get('company_name', 'Not specified')} ({'New' if client_info.get('is_new_client', False) else 'Existing'})</td>
        </tr>
        <tr>
            <td>Contact + Email</td>
            <td>{client_info.get('contact_name', 'Not specified')} &lt;{client_info.get('contact_email', 'Not specified')}&gt;</td>
        </tr>
        <tr>
            <td>Company Billing Address + Email</td>
            <td>{client_info.get('billing_address', 'Not specified').replace(chr(10), ', ')} | {client_info.get('contact_email', 'Not specified')}</td>
        </tr>
        <tr>
            <td>Company Shipping Address</td>
            <td>{client_info.get('shipping_address', 'Not specified').replace(chr(10), ', ')} ({client_info.get('shipping_type', 'Not specified')})</td>
        </tr>
        <tr>
            <td>Client PO #</td>
            <td>{client_info.get('client_po', 'N/A')}</td>
        </tr>
    </table>

    <h3>2. Partners + Point of Contacts</h3>
    <table>
        <tr>
            <th>Partner</th>
            <th>Point of Contact (POC)</th>
        </tr>"""

        # Add partner rows
        if partners_in_order and hasattr(st.session_state, 'partner_contacts'):
            for partner_name in partners_in_order:
                partner_contact = st.session_state.partner_contacts.get(partner_name, {})
                poc_name = partner_contact.get('poc_name', 'Not specified')
                poc_email = partner_contact.get('poc_email', 'Not specified')
                html_invoice += f"""
        <tr>
            <td style="width: 40%;">{partner_name}</td>
            <td>{poc_name} &lt;{poc_email}&gt;</td>
        </tr>"""
        else:
            html_invoice += """
        <tr>
            <td colspan="2" style="text-align: center; color: #7f8c8d;">No partners in order</td>
        </tr>"""

        html_invoice += f"""
    </table>

    <h3>3. Order Details</h3>
    <table>
        <tr>
            <td>Client In-Hands Date</td>
            <td>{client_in_hands}</td>
        </tr>
        <tr>
            <td>Ship Method</td>
            <td>{ship_method}</td>
        </tr>
        <tr>
            <td>Payment Terms</td>
            <td>{payment_terms}</td>
        </tr>
        <tr>
            <td>Payment Method</td>
            <td>{payment_method}</td>
        </tr>
        <tr>
            <td>Order Submitted By</td>
            <td>{order_submitted_by} (Date: {order_submitted_date})</td>
        </tr>
        <tr>
            <td>Cost Submitted By</td>
            <td>{cost_submitted_by} (Date: {cost_submitted_date if cost_submitted_date else 'Not specified'})</td>
        </tr>
    </table>

    <h3>4. Invoice and Purchase Order Item Details</h3>
    <p style="color: #7f8c8d; font-size: 0.9em; margin: 10px 0;">
        This cost-to-sell segment outlines our partners' cost, our sell price to client,
        and our partners' requested in-hands date.
    </p>
    <table>
        <tr>
            <th>Partner</th>
            <th>Items + Specs</th>
            <th>Qty</th>
            <th>In-Hands from Partner</th>
            <th>Cost/Unit</th>
            <th>Total Cost</th>
            <th>Cost Verified?</th>
            <th>Sell Price/Unit</th>
            <th>Total Sell Price</th>
        </tr>"""

        # Add all line items
        for line_item in invoice_line_items:
            html_invoice += f"""
        <tr>
            <td>{line_item['PARTNER']}</td>
            <td>{line_item['ITEMS + SPECS'].replace(chr(10), '<br>')}</td>
            <td style="text-align: center;">{line_item['QTY']}</td>
            <td>{line_item['IN-HANDS from Partner']}</td>
            <td style="text-align: right;">{line_item['COST/UNIT']}</td>
            <td style="text-align: right;">{line_item['TOTAL COST']}</td>
            <td style="text-align: center;">{line_item['COST VERIFIED?']}</td>
            <td style="text-align: right;">{line_item['SELL PRICE/UNIT']}</td>
            <td style="text-align: right;">{line_item['TOTAL SELL PRICE']}</td>
        </tr>"""

        html_invoice += """
    </table>

    <h3>Summary Totals</h3>
    <table>"""

        # Add totals
        for total_item in totals_data:
            is_total_row = total_item[0].startswith('**')
            style = ' style="background-color: #f8f9fa; font-weight: bold;"' if is_total_row else ''
            html_invoice += f"""
        <tr{style}>
            <td>{total_item[0].replace('**', '')}</td>
            <td style="text-align: right;">{total_item[1].replace('**', '')}</td>
        </tr>"""

        html_invoice += """
    </table>"""

        # Add dropshipping notes section (appears in Invoice only, not PO)
        if st.session_state.dropshipping_notes:
            html_invoice += f"""
    <div class="notes-section">
        <div class="notes-header">DROPSHIPPING INSTRUCTIONS</div>
        <p>{st.session_state.dropshipping_notes.replace(chr(10), '<br/>')}</p>
    </div>"""

        # Add notes if any
        if notes_content:
            html_invoice += """
    <div class="notes-section">
        <div class="notes-header">NOTES</div>"""
            for note in notes_content:
                html_invoice += f"""
        <p><strong>{note.split(':')[0] if ':' in note else 'Note'}:</strong> {note.split(':', 1)[1] if ':' in note else note}</p>"""
            html_invoice += """
    </div>"""

        html_invoice += """
</body>
</html>"""

        # Download buttons side by side
        col1, col2 = st.columns(2)

        with col1:
            invoice_csv = invoice_complete.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=invoice_csv,
                file_name=f"invoice_po_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_invoice_po_csv",
                use_container_width=True
            )

        with col2:
            st.download_button(
                label="Download as HTML",
                data=html_invoice,
                file_name=f"invoice_po_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                key="download_invoice_po_html",
                use_container_width=True
            )

        st.caption("CSV for spreadsheet import | HTML for email-ready professional format")

        st.divider()

        # ============================================================
        # SECTION 4: ACCOUNTING EXPORT (FUTURE)
        # ============================================================
        st.subheader("3. Export for Accounting")
        st.caption("Future: QuickBooks export, accounting reports, etc.")
        st.info("Accounting export features will be added in Phase 4")
