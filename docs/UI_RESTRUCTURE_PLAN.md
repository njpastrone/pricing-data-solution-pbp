# UI Restructure Plan: 3-Tab System
## Peace by Piece Order Management System

**Date:** October 28, 2025
**Version:** 1.0
**Status:** Ready for Implementation

---

## Table of Contents
1. [Overview](#overview)
2. [Phase 1: Backup & Preparation](#phase-1-backup--preparation)
3. [Phase 2: Core Restructure](#phase-2-core-restructure)
4. [Phase 3: Tab 1 - Proposals](#phase-3-tab-1---proposals)
5. [Phase 4: Tab 2 - Order & Client Info](#phase-4-tab-2---order--client-info)
6. [Phase 5: Tab 3 - Execution & Accounting](#phase-5-tab-3---execution--accounting)
7. [Phase 6: Sidebar Updates](#phase-6-sidebar-updates)
8. [Phase 7: Code Organization](#phase-7-code-organization)
9. [Phase 8: Testing](#phase-8-testing)
10. [Future Enhancements](#future-enhancements)
11. [Timeline Estimate](#timeline-estimate)

---

## Overview

### Goal
Restructure the Peace by Piece Pricing & Quoting App from a single-page workflow into a 3-tab system that mirrors the actual business process.

### New Structure
- **Tab 1: Proposals** - Generate proposals for prospective clients
- **Tab 2: Order & Client Info** - Collect order details and client information
- **Tab 3: Execution & Accounting** - Generate invoices and purchase orders

### Key Principles
- Follow all non-negotiables from CLAUDE.md
- Keep code in single file (app.py) for beginner-friendliness
- Preserve all existing functionality
- Allow free navigation between tabs
- Maintain session state across tab switches
- Show clear validation warnings but don't block progress

---

## Phase 1: Backup & Preparation

### 1.1 Create Backup
**Action:** Copy current working app to backups folder
```bash
cp app.py backups/app_2025_10_28_1pm_backup.py
```

### 1.2 Create Git Commit
**Action:** Commit current state before making changes
```bash
git add .
git commit -m "Backup before UI restructure to 3-tab system - Oct 28 2025"
```

### 1.3 Create Config File Structure
**Action:** Create config directory and terms & conditions file
```bash
mkdir -p config
touch config/terms_conditions.txt
```

**Content for `config/terms_conditions.txt`:**
```
[PLACEHOLDER - Terms & Conditions]

Payment terms, delivery expectations, liability clauses, etc. to be added.
```

**Note:** Add `config/` to `.gitignore` if it contains sensitive information

---

## Phase 2: Core Restructure

### 2.1 Update App Header
**Current:**
```python
st.title("Peace by Piece Pricing & Quoting App")
```

**New:**
```python
st.title("Peace by Piece Order Management System")
```

**Update purpose statement:**
```python
st.markdown("""
**Welcome to the PBP Order Management System** — This tool helps you manage the complete
order lifecycle from proposal generation to client invoicing and partner purchase orders.

**Workflow:** Proposals → Order & Client Info → Execution & Accounting
""")
```

### 2.2 Session State Initialization
**Add new state variables:**

```python
# Tab 1: Proposals
if 'proposal_products' not in st.session_state:
    st.session_state.proposal_products = []

if 'proposal_marketing_rounding' not in st.session_state:
    st.session_state.proposal_marketing_rounding = False

if 'proposal_filters' not in st.session_state:
    st.session_state.proposal_filters = {
        'min_price': None,
        'max_price': None,
        'partners': [],
        'countries': []
    }

if 'proposal_terms' not in st.session_state:
    # Load from config file
    try:
        with open('config/terms_conditions.txt', 'r') as f:
            st.session_state.proposal_terms = f.read()
    except:
        st.session_state.proposal_terms = "[PLACEHOLDER - Terms & Conditions]"

# Tab 2: Order & Client Info
if 'using_proposal_data' not in st.session_state:
    st.session_state.using_proposal_data = False

# Disable order history temporarily
if 'order_history_disabled' not in st.session_state:
    st.session_state.order_history_disabled = True
```

**Keep existing state variables:**
- `order_items`
- `edit_index`
- `order_shipping`
- `order_discount_type`, `order_discount_preset`, etc.
- `order_use_marketing_rounding`
- `client_info`
- `order_notes`
- `apply_cc_fee`, `cc_fee_percent`

### 2.3 Create Tab Structure
**Add after data loading section:**

```python
# ============================================================
# TAB STRUCTURE
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "📋 Proposals",
    "📦 Order & Client Info",
    "💼 Execution & Accounting"
])
```

---

## Phase 3: Tab 1 - Proposals

### 3.1 Filtering Section
**Location:** Top of Tab 1

**Code Structure:**
```python
with tab1:
    st.header("1. Proposal Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Price Range")
        min_price = st.number_input(
            "Min price per unit ($) - Optional",
            min_value=0.0,
            value=st.session_state.proposal_filters.get('min_price', None),
            step=1.0,
            key="filter_min_price"
        )
        max_price = st.number_input(
            "Max price per unit ($)",
            min_value=0.0,
            value=st.session_state.proposal_filters.get('max_price', None),
            step=1.0,
            key="filter_max_price"
        )

    with col2:
        st.subheader("Partner/Maker")
        all_partners = sorted(df_template["Partner"].unique().tolist())
        selected_partners = st.multiselect(
            "Select partners",
            options=all_partners,
            default=all_partners,
            key="filter_partners"
        )

    with col3:
        st.subheader("Country of Origin")
        all_countries = sorted(df_template["Country of Origin"].dropna().unique().tolist())
        selected_countries = st.multiselect(
            "Select countries",
            options=all_countries,
            default=all_countries,
            key="filter_countries"
        )

    # Save to session state
    st.session_state.proposal_filters['min_price'] = min_price
    st.session_state.proposal_filters['max_price'] = max_price
    st.session_state.proposal_filters['partners'] = selected_partners
    st.session_state.proposal_filters['countries'] = selected_countries
```

**Filtering Logic:**
```python
# Filter products based on selections
filtered_df = df_template.copy()

# Apply partner filter
if selected_partners:
    filtered_df = filtered_df[filtered_df["Partner"].isin(selected_partners)]

# Apply country filter
if selected_countries:
    filtered_df = filtered_df[filtered_df["Country of Origin"].isin(selected_countries)]

# Apply price filter (calculate base price for filtering)
if max_price and max_price > 0:
    # Filter logic: calculate MOQ price for each product and filter
    # This requires calculating price for each row - implement as helper function
    filtered_df = filter_products_by_price(filtered_df, min_price, max_price)

st.info(f"Showing {len(filtered_df)} products matching filters")
```

### 3.2 Product Catalog
**Location:** Below filtering section

**Display:**
```python
st.divider()
st.header("2. Product Catalog")

# Display as interactive table
for idx, row in filtered_df.iterrows():
    product_data = row

    with st.expander(f"{product_data['Product/Service']} - {product_data['Partner']}"):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Partner:** {product_data['Partner']}")
            st.markdown(f"**Country:** {product_data.get('Country of Origin', 'N/A')}")
            st.markdown(f"**Tiered Pricing:** {product_data.get('Pricing Tiers (Y/N)', 'N/A')}")

            # Calculate and show base price at MOQ
            preliminary_price, _, _ = get_unit_price_new_system(product_data, 100)  # Use 100 as estimate
            if preliminary_price:
                estimated_moq = calculate_moq(preliminary_price)
                moq_price, _, _ = get_unit_price_new_system(product_data, estimated_moq)
                st.markdown(f"**Price at MOQ ({estimated_moq} units):** ${moq_price:.2f}/unit")

            # Show description if available
            desc = product_data.get("Marketing Description", "")
            if desc and desc.strip():
                st.caption(desc)

        with col2:
            if st.button("Add to Proposal", key=f"add_proposal_{idx}"):
                # Set flag to open configuration for this product
                st.session_state.configuring_product = product_data.to_dict()
                st.rerun()

# Configuration UI (opens when product selected)
if 'configuring_product' in st.session_state and st.session_state.configuring_product:
    st.divider()
    st.subheader("Configure Product for Proposal")

    product_config = st.session_state.configuring_product

    # Quantity
    quantity = st.number_input("Quantity", min_value=1, value=100, step=1)

    # Markup
    markup = st.number_input("Markup %", min_value=0.0, value=100.0, step=5.0)

    # MSRP (optional)
    show_msrp = st.checkbox("Include MSRP comparison")
    msrp_value = 0.0
    if show_msrp:
        msrp_value = st.number_input("Partner MSRP", min_value=0.0, value=0.0, step=1.0)

    # Customization
    include_custom = st.checkbox("Include customization")
    custom_setup = 0.0
    custom_per_unit = 0.0
    if include_custom:
        custom_setup = st.number_input("Setup Fee", min_value=0.0, value=0.0, step=1.0)
        custom_per_unit = st.number_input("Per Unit Cost", min_value=0.0, value=0.0, step=0.1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add to Proposal", type="primary"):
            # Create proposal item with default values
            proposal_item = {
                'product_data': product_config,
                'quantity': quantity,
                'markup_percent': markup,
                'msrp_value': msrp_value,
                'show_msrp': show_msrp,
                'include_customization': include_custom,
                'customization_setup_fee': custom_setup,
                'customization_per_unit': custom_per_unit
            }
            st.session_state.proposal_products.append(proposal_item)
            del st.session_state.configuring_product
            st.success("Added to proposal!")
            st.rerun()

    with col2:
        if st.button("Cancel"):
            del st.session_state.configuring_product
            st.rerun()
```

### 3.3 Proposal Preview Section
**Location:** Below product catalog

```python
st.divider()
st.header("3. Proposal Preview")

if len(st.session_state.proposal_products) == 0:
    st.info("No products added to proposal yet. Add products from the catalog above.")
else:
    st.success(f"{len(st.session_state.proposal_products)} product(s) in proposal")

    # Global marketing rounding
    st.session_state.proposal_marketing_rounding = st.checkbox(
        "Apply marketing rounding (e.g., $60 → $59)",
        value=st.session_state.proposal_marketing_rounding,
        key="proposal_marketing_rounding_checkbox"
    )

    st.divider()

    # Display each product
    for idx, item in enumerate(st.session_state.proposal_products):
        product_data = item['product_data']

        with st.expander(f"{product_data['Product/Service']} - {item['quantity']} units"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**Partner:** {product_data['Partner']}")
                st.write(f"**Quantity:** {item['quantity']}")
                st.write(f"**Markup:** {item['markup_percent']:.1f}%")
                if item['include_customization']:
                    st.write(f"**Customization:** Yes (${item['customization_setup_fee']:.2f} setup + ${item['customization_per_unit']:.2f}/unit)")

            with col2:
                if st.button("✏️ Edit", key=f"edit_proposal_{idx}"):
                    # Load product into configuration UI
                    st.session_state.configuring_product = item
                    st.session_state.editing_proposal_index = idx
                    st.rerun()

            with col3:
                if st.button("Remove", key=f"remove_proposal_{idx}"):
                    st.session_state.proposal_products.pop(idx)
                    st.rerun()

            # Show proposal table (collapsed by default)
            with st.expander("View Proposal Table", expanded=False):
                # Generate proposal table (same logic as current Section 9)
                # Calculate MOQ, pricing tiers, customization fees
                # Display in 4-column format
                pass  # Implementation details same as current proposal section
```

### 3.4 Terms & Conditions
**Location:** Below proposal preview

```python
st.divider()
st.header("4. Terms & Conditions")

st.session_state.proposal_terms = st.text_area(
    "Edit terms & conditions if needed",
    value=st.session_state.proposal_terms,
    height=200,
    key="proposal_terms_input"
)
```

### 3.5 Client Order Form Output
**Location:** Below terms & conditions

```python
st.divider()
st.header("5. Client Order Form")

st.markdown("""
Copy the form below and send to your client to collect order details:
""")

client_form_text = """
CLIENT ORDER FORM

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

st.text_area("Client Order Form", value=client_form_text, height=400, key="client_form_display")
```

### 3.6 Downloads Section
**Location:** Bottom of Tab 1

```python
st.divider()
st.header("6. Downloads")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Download Proposal Tables (CSV)"):
        # Generate CSV with all proposal tables
        # Implementation: compile all proposal data
        pass

with col2:
    if st.button("Download Client Order Form (CSV)"):
        # Generate CSV format of order form
        pass

with col3:
    if st.button("Download Client Order Form (Text)"):
        # Download as .txt file
        st.download_button(
            label="Download Form (TXT)",
            data=client_form_text,
            file_name="client_order_form.txt",
            mime="text/plain"
        )
```

---

## Phase 4: Tab 2 - Order & Client Info

### 4.1 Proposal Status Message
**Location:** Top of Tab 2

```python
with tab2:
    st.header("Order & Client Information")

    # Check if proposal data exists
    if len(st.session_state.proposal_products) > 0:
        st.info(f"✓ Using products from Proposal ({len(st.session_state.proposal_products)} products available to select)")
        st.session_state.using_proposal_data = True
    else:
        st.info("No proposal linked - you can select from full product catalog")
        st.session_state.using_proposal_data = False
```

### 4.2 Part A: Client Information
**Location:** First section in Tab 2

```python
st.divider()
st.header("Part A: Client Information")

with st.expander("Client Details", expanded=False):
    # Use exact same structure as current Section 1
    # Copy all client_info fields from current app
    # No changes needed to this section
    pass
```

### 4.3 Part B: Order Details
**Location:** Second section in Tab 2

#### Sub-section B1: Product Selection from Proposal

```python
st.divider()
st.header("Part B: Order Details")

if st.session_state.using_proposal_data:
    st.subheader("Select Products from Proposal")

    # Build checklist of proposal products
    selected_indices = []

    for idx, item in enumerate(st.session_state.proposal_products):
        product_data = item['product_data']
        col1, col2 = st.columns([3, 1])

        with col1:
            is_selected = st.checkbox(
                f"{product_data['Product/Service']} - {product_data['Partner']}",
                key=f"select_proposal_product_{idx}"
            )
            st.caption(f"Proposal qty: {item['quantity']} | Markup: {item['markup_percent']}%")

        with col2:
            if is_selected:
                selected_indices.append(idx)

    if st.button("Add Selected to Order", type="primary"):
        # Add selected products to order_items
        for idx in selected_indices:
            item = st.session_state.proposal_products[idx]
            # Convert proposal item to order item format
            # Carry over all settings but make editable
            order_item = convert_proposal_to_order(item)
            st.session_state.order_items.append(order_item)

        st.success(f"Added {len(selected_indices)} product(s) to order!")
        st.rerun()

    st.divider()
```

#### Sub-section B2: Add Product Not in Proposal

```python
st.subheader("Add Product Not in Proposal")

with st.expander("➕ Add Product Not in Proposal", expanded=False):
    # Use exact same product selection UI as current Section 2
    # Partner dropdown, product dropdown, configuration
    # "Add to Order" button
    pass
```

#### Sub-section B3: Current Order

```python
st.divider()
st.subheader("Current Order")

if len(st.session_state.order_items) == 0:
    st.info("No products in order yet. Select products above to add to order.")
else:
    # Use exact same display as current Section 6
    # Show order items with edit/remove buttons
    # Show line item breakdowns
    pass
```

### 4.4 Part C: Order Settings
**Location:** Third section in Tab 2

```python
st.divider()
st.header("Part C: Order Settings")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order first, then configure order settings here.")
else:
    # Use exact same structure as current Section 7
    # Shipping
    # Tariff configuration (full detailed section)
    # Discount options
    # Additional options (marketing rounding, CC fee)
    # Custom line items
    # Order notes
    pass
```

### 4.5 Part D: Order Summary
**Location:** Fourth section in Tab 2

```python
st.divider()
st.header("Part D: Order Summary")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to see the total quote calculation.")
else:
    # Use exact same structure as current Section 8
    # Calculate totals
    # Display summary table
    # Download order summary CSV

    # Modify "Save Quote to History" button
    if st.button("Save Quote to History", type="secondary", disabled=True):
        st.info("Order history temporarily unavailable during restructure")
```

---

## Phase 5: Tab 3 - Execution & Accounting

### 5.1 Missing Data Validation
**Location:** Top of Tab 3

```python
with tab3:
    st.header("Execution & Accounting")

    # Validate required data
    missing_fields = []

    # Check client info
    if not st.session_state.client_info.get('company_name'):
        missing_fields.append("Company Name")
    if not st.session_state.client_info.get('contact_name'):
        missing_fields.append("Contact Name")
    if not st.session_state.client_info.get('contact_email'):
        missing_fields.append("Contact Email")
    if not st.session_state.client_info.get('billing_address'):
        missing_fields.append("Billing Address")

    # Check order items
    if len(st.session_state.order_items) == 0:
        missing_fields.append("Order Items (at least 1 product required)")

    # Display warning if missing data
    if missing_fields:
        st.warning(f"⚠️ Missing required data: {', '.join(missing_fields)}. Complete in Tab 2 to generate accurate invoice/PO.")
    else:
        st.success("✓ All required data complete - ready to generate documents")
```

### 5.2 Order Summary Dropdown
**Location:** Below validation banner

```python
st.divider()

with st.expander("View/Edit Order Summary", expanded=False):
    st.markdown("### Order Summary (Editable)")

    # Display same content as Tab 2 Part D
    # Allow editing of:
    # - Shipping
    # - Tariff rates
    # - Discounts
    # - CC fee

    # All changes sync to session_state automatically
    # Rerun to update Tab 2 as well

    # Copy logic from current Section 8
    pass
```

### 5.3 Client Invoice Section
**Location:** Main content area

```python
st.divider()

# ============================================================
# CLIENT INVOICE (FOR CLIENT)
# ============================================================
st.markdown("## 📄 INVOICE FOR CLIENT")
st.markdown("**This document goes to your client**")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate an invoice.")
else:
    # Use exact same structure as current Section 10
    # Header information
    # Partner POC info
    # Delivery & payment details
    # Itemized table (SELL PRICE column)
    # Summary totals
    # Notes section

    # Download button
    st.download_button(
        label="Download Invoice (CSV)",
        data=invoice_csv,
        file_name=f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
```

### 5.4 Partner Purchase Orders Section
**Location:** Below invoice section

```python
st.divider()

# ============================================================
# PURCHASE ORDERS (FOR PARTNERS)
# ============================================================
st.markdown("## 📦 PURCHASE ORDERS FOR PARTNERS")
st.markdown("**These documents go to your partners/suppliers**")

if len(st.session_state.order_items) == 0:
    st.caption("Add products to your order to generate purchase orders.")
else:
    # Get unique partners from order items
    partners_in_order = list(set(
        item['partner'] for item in st.session_state.order_items
        if not item.get('is_custom', False)
    ))

    if not partners_in_order:
        st.info("No partner products in order (only custom items)")
    else:
        st.info(f"Generating {len(partners_in_order)} purchase order(s) - one per partner")

        # Generate PO for each partner
        for partner_name in partners_in_order:
            st.markdown(f"### Purchase Order: {partner_name}")

            # Get partner contact info
            partner_contact = st.session_state.partner_contacts.get(partner_name, {})
            poc_name = partner_contact.get('poc_name', 'Not specified')
            poc_email = partner_contact.get('poc_email', 'Not specified')

            st.write(f"**Partner Contact:** {poc_name} ({poc_email})")

            # Filter order items for this partner
            partner_items = [
                item for item in st.session_state.order_items
                if item.get('partner') == partner_name
            ]

            # Build PO table
            po_line_items = []

            for item in partner_items:
                # Base product line
                partner_cost = item.get('partner_cost_per_unit', item.get('base_price', 0))

                po_line_items.append({
                    'PARTNER': partner_name,
                    'ITEMS + SPECS': f"{item['product_name']}\n{item.get('product_specs', '')}",
                    'QTY': item['quantity'],
                    'IN-HANDS from Partner': item.get('partner_in_hands_date', 'TBD'),
                    'COST': f"${partner_cost:.2f}",
                    'COST VERIFIED?': item.get('cost_verified', 'Pending'),
                    'SELL PRICE': f"${item.get('product_total', 0):.2f}"
                })

                # Add customization lines if applicable
                if item.get('include_customization', False):
                    # Setup fee line
                    if item.get('customization_setup_total', 0) > 0:
                        po_line_items.append({
                            'PARTNER': partner_name,
                            'ITEMS + SPECS': f"Setup Fee: {item.get('customization_description', 'Custom work')}",
                            'QTY': 1,
                            'IN-HANDS from Partner': item.get('partner_in_hands_date', 'TBD'),
                            'COST': f"${item.get('customization_setup_total', 0):.2f}",
                            'COST VERIFIED?': item.get('cost_verified', 'Pending'),
                            'SELL PRICE': f"${item.get('customization_setup_total', 0):.2f}"
                        })

                    # Per-unit customization line
                    if item.get('customization_unit_total', 0) > 0:
                        po_line_items.append({
                            'PARTNER': partner_name,
                            'ITEMS + SPECS': f"Customization: {item.get('customization_description', 'Custom work')}",
                            'QTY': item['quantity'],
                            'IN-HANDS from Partner': item.get('partner_in_hands_date', 'TBD'),
                            'COST': f"${item.get('customization_per_unit', 0):.2f}",
                            'COST VERIFIED?': item.get('cost_verified', 'Pending'),
                            'SELL PRICE': f"${item.get('customization_unit_total', 0):.2f}"
                        })

                # Add tariff line if applicable
                if item.get('tariff_amount', 0) > 0:
                    po_line_items.append({
                        'PARTNER': partner_name,
                        'ITEMS + SPECS': f"Tariff ({item.get('tariff_rate_percent', 0)}%)",
                        'QTY': 1,
                        'IN-HANDS from Partner': "N/A",
                        'COST': f"${item.get('tariff_amount', 0):.2f}",
                        'COST VERIFIED?': "Yes",
                        'SELL PRICE': f"${item.get('tariff_amount', 0):.2f}"
                    })

            # Display PO table
            po_df = pd.DataFrame(po_line_items)
            st.table(po_df)

            # Calculate partner-specific totals
            partner_subtotal = sum(
                item.get('product_total', 0) for item in partner_items
            )
            st.markdown(f"**Partner Subtotal:** ${partner_subtotal:.2f}")

            # Show partner-specific notes if available
            if st.session_state.order_notes:
                with st.expander("Notes for this Partner", expanded=False):
                    for note_key, note_value in st.session_state.order_notes.items():
                        if note_value and note_value.strip():
                            st.markdown(f"**{note_key.replace('_', ' ').title()}:** {note_value}")

            # Download button for this PO
            po_csv = po_df.to_csv(index=False)
            st.download_button(
                label=f"Download PO: {partner_name} (CSV)",
                data=po_csv,
                file_name=f"po_{partner_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"download_po_{partner_name}"
            )

            st.divider()
```

### 5.5 Downloads Section
**Location:** Bottom of Tab 3

```python
st.divider()
st.header("Download All Documents")

if len(st.session_state.order_items) > 0:
    col1, col2 = st.columns(2)

    with col1:
        # Invoice download (duplicate from above for easy access)
        st.download_button(
            label="Download Invoice (CSV)",
            data=invoice_csv,
            file_name=f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_invoice_bottom"
        )

    with col2:
        # Download all button (optional, for future implementation)
        st.button("Download All Documents (ZIP)", disabled=True)
        st.caption("Coming soon: Download invoice + all POs in one ZIP file")
```

---

## Phase 6: Sidebar Updates

### 6.1 Update Recent Orders Section
**Location:** Sidebar

```python
with st.sidebar:
    st.markdown("## Instructions & Tools")

    # Keep existing instructions expander (update text for new workflow)
    with st.expander("How to Use This App", expanded=False):
        st.markdown("""
        **Step-by-step guide:**

        **Tab 1: Proposals**
        1. Filter products by price range, partner, or country
        2. Add products to proposal with default settings
        3. Edit proposal products as needed
        4. Download proposal tables and client order form

        **Tab 2: Order & Client Info**
        1. Enter client information
        2. Select products from proposal (or add new products)
        3. Configure order settings (shipping, tariff, discounts)
        4. Review order summary

        **Tab 3: Execution & Accounting**
        1. Review missing data warnings (if any)
        2. Generate client invoice
        3. Generate partner purchase orders (one per partner)
        4. Download all documents
        """)

    st.markdown("---")

    # Replace Recent Orders with temporary message
    st.markdown("### Order Management")
    st.caption("**Order History:** Temporarily unavailable during restructure")
    st.caption("**Saved Proposals:** Coming soon")
```

### 6.2 Add Progress Indicator
**Location:** Top of sidebar

```python
with st.sidebar:
    st.markdown("### Progress")

    # Check Tab 1 status
    tab1_status = "✓" if len(st.session_state.proposal_products) > 0 else "○"
    tab1_count = f"({len(st.session_state.proposal_products)} products)" if len(st.session_state.proposal_products) > 0 else ""

    # Check Tab 2 status
    has_client_info = bool(st.session_state.client_info.get('company_name'))
    has_order_items = len(st.session_state.order_items) > 0

    if has_client_info and has_order_items:
        tab2_status = "✓"
        tab2_msg = f"({len(st.session_state.order_items)} products)"
    elif has_client_info or has_order_items:
        tab2_status = "⚠️"
        tab2_msg = "(incomplete)"
    else:
        tab2_status = "○"
        tab2_msg = ""

    # Check Tab 3 status
    missing_fields = []
    if not st.session_state.client_info.get('company_name'):
        missing_fields.append("company")
    if not st.session_state.client_info.get('contact_email'):
        missing_fields.append("email")
    if len(st.session_state.order_items) == 0:
        missing_fields.append("products")

    if not missing_fields:
        tab3_status = "✓"
        tab3_msg = "(ready)"
    elif len(missing_fields) < 3:
        tab3_status = "⚠️"
        tab3_msg = f"(missing {len(missing_fields)})"
    else:
        tab3_status = "○"
        tab3_msg = "(not ready)"

    st.markdown(f"""
    {tab1_status} **Tab 1: Proposals** {tab1_count}
    {tab2_status} **Tab 2: Order Info** {tab2_msg}
    {tab3_status} **Tab 3: Execution** {tab3_msg}
    """)

    st.markdown("---")
```

### 6.3 Add Clear All Data Button
**Location:** Middle of sidebar (after progress indicator)

```python
with st.sidebar:
    st.markdown("### Actions")

    if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
        # Show confirmation dialog
        st.session_state.confirm_clear = True

    # Confirmation dialog
    if st.session_state.get('confirm_clear', False):
        st.warning("⚠️ Are you sure? This will clear all data from all tabs (Proposals, Order Info, and Execution). This cannot be undone.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Clear All", type="primary", use_container_width=True):
                # Clear all session state
                st.session_state.proposal_products = []
                st.session_state.proposal_marketing_rounding = False
                st.session_state.proposal_filters = {
                    'min_price': None,
                    'max_price': None,
                    'partners': [],
                    'countries': []
                }
                st.session_state.order_items = []
                st.session_state.edit_index = None
                st.session_state.order_shipping = 0.0
                st.session_state.order_discount_type = "none"
                st.session_state.client_info = {
                    'is_new_client': True,
                    'company_name': '',
                    # ... reset all fields
                }
                st.session_state.order_notes = {
                    'kitting_specs': '',
                    'client_requests': '',
                    'addon_samples': '',
                    'artwork_attachments': '',
                    'general_notes': ''
                }
                st.session_state.confirm_clear = False
                st.success("All data cleared. Starting fresh.")
                st.rerun()

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()

    st.markdown("---")
```

### 6.4 Keep Existing Sidebar Elements
- Data Status section (keep as-is)
- Download Options section (keep as-is, update context)

---

## Phase 7: Code Organization

### 7.1 File Structure
**No changes to file structure - keep everything in app.py**

### 7.2 Code Section Organization

```python
"""
Peace by Piece International - Order Management System
3-tab workflow: Proposals → Order & Client Info → Execution & Accounting
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
    calculate_product_tariff
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
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="auto"
)

# ============================================================
# HELPER FUNCTIONS (NEW)
# ============================================================

def filter_products_by_price(df, min_price, max_price):
    """Filter products by price range"""
    # Implementation: calculate MOQ price for each product and filter
    pass

def convert_proposal_to_order(proposal_item):
    """Convert proposal item format to order item format"""
    # Implementation: transform data structure
    pass

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
# [All session state initialization code here]

# ============================================================
# DATA LOADING
# ============================================================
# [Data loading code here]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    # [All sidebar code here]
    pass

# ============================================================
# HEADER
# ============================================================
st.title("Peace by Piece Order Management System")
st.markdown("""
**Welcome to the PBP Order Management System** — Manage the complete order lifecycle
from proposal generation to client invoicing and partner purchase orders.

**Workflow:** Proposals → Order & Client Info → Execution & Accounting
""")
st.divider()

# ============================================================
# TAB STRUCTURE
# ============================================================
tab1, tab2, tab3 = st.tabs([
    "📋 Proposals",
    "📦 Order & Client Info",
    "💼 Execution & Accounting"
])

# ============================================================
# TAB 1: PROPOSALS
# ============================================================
with tab1:
    # 1.1 Filtering Section
    # 1.2 Product Catalog
    # 1.3 Proposal Preview
    # 1.4 Terms & Conditions
    # 1.5 Client Order Form
    # 1.6 Downloads
    pass

# ============================================================
# TAB 2: ORDER & CLIENT INFO
# ============================================================
with tab2:
    # 2.1 Proposal Status Message
    # 2.2 Part A: Client Information
    # 2.3 Part B: Order Details
    # 2.4 Part C: Order Settings
    # 2.5 Part D: Order Summary
    pass

# ============================================================
# TAB 3: EXECUTION & ACCOUNTING
# ============================================================
with tab3:
    # 3.1 Missing Data Validation
    # 3.2 Order Summary Dropdown
    # 3.3 Client Invoice
    # 3.4 Partner Purchase Orders
    # 3.5 Downloads Section
    pass

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(f"Last data refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Use 'Refresh Data' button in sidebar to update pricing from Google Sheets")
```

### 7.3 Move Previews to Expanders

**Current sections with detailed breakdowns → Move to collapsed expanders:**

1. **Product detail breakdowns** (Tab 1, Tab 2)
   - Pricing tier information
   - Marketing description
   - Product specifications

2. **Cost breakdowns** (Tab 2)
   - Detailed per-unit calculations
   - Customization cost breakdown
   - Tariff calculation details

3. **Order notes** (Tab 2)
   - All 5 categories in collapsed expander

4. **Proposal tables** (Tab 1)
   - Each product's proposal table in collapsed expander

**Implementation pattern:**
```python
# Instead of:
st.markdown("**Detailed Breakdown:**")
st.table(breakdown_df)

# Use:
with st.expander("View Detailed Breakdown", expanded=False):
    st.table(breakdown_df)
```

---

## Phase 8: Testing

### 8.1 Tab 1: Proposals Testing

**Filtering Functionality:**
- [ ] Price range filter works (min optional, max required)
- [ ] Partner multi-select filter works
- [ ] Country multi-select filter works
- [ ] Products display correctly with all filters
- [ ] Product count updates when filters change
- [ ] Show all products by default (no filters)

**Product Catalog:**
- [ ] Product list displays correctly
- [ ] Product details show (partner, country, tiered Y/N, price at MOQ)
- [ ] "Add to Proposal" button opens configuration UI
- [ ] Configuration UI has all fields (qty, markup, MSRP, customization)
- [ ] Default values populate correctly
- [ ] Cancel button works
- [ ] Add button adds product to proposal

**Proposal Preview:**
- [ ] Products display in preview section
- [ ] Global marketing rounding checkbox works
- [ ] Edit button reopens configuration
- [ ] Remove button removes from proposal
- [ ] Proposal tables generate correctly (collapsed expanders)
- [ ] Customization fees show as separate items
- [ ] Tariff info displays if applicable

**Terms & Conditions:**
- [ ] Loads from config file
- [ ] Text area is editable
- [ ] Changes persist in session state

**Client Order Form:**
- [ ] Displays formatted text correctly
- [ ] All questions included
- [ ] Text area is copyable

**Downloads:**
- [ ] Download Proposal Tables (CSV) works
- [ ] Download Client Order Form (CSV) works
- [ ] Download Client Order Form (Text) works

### 8.2 Tab 2: Order & Client Info Testing

**Proposal Status:**
- [ ] Shows "Using products from Proposal" when proposal exists
- [ ] Shows "No proposal linked" when no proposal
- [ ] Product count is correct

**Client Information:**
- [ ] All fields display correctly
- [ ] All fields save to session state
- [ ] Conditional fields work (shipping address)
- [ ] Dropdowns have correct options
- [ ] Date pickers work
- [ ] Auto-filled dates work

**Product Selection from Proposal:**
- [ ] Checklist displays all proposal products
- [ ] Shows correct product details
- [ ] Multi-select works
- [ ] "Add Selected to Order" adds products correctly
- [ ] Settings carry over from proposal
- [ ] Settings are editable after adding

**Add Product Not in Proposal:**
- [ ] Button opens full product selector
- [ ] Partner/product dropdowns work
- [ ] Configuration UI same as Tab 1
- [ ] Add to Order button works
- [ ] Product adds to order_items correctly

**Current Order:**
- [ ] Displays all order items
- [ ] Each item shows correct details
- [ ] Edit button works
- [ ] Remove button works
- [ ] Line item breakdowns display correctly
- [ ] Nested expanders work (collapsed by default)

**Order Settings:**
- [ ] Shipping input works
- [ ] Tariff configuration works (per-product editing)
- [ ] Discount options work (none/preset/custom)
- [ ] Marketing rounding checkbox works
- [ ] CC fee checkbox and input work
- [ ] Custom line items add correctly
- [ ] Order notes save correctly (5 categories)

**Order Summary:**
- [ ] Calculates correctly (products + shipping + tariff + discount + CC fee)
- [ ] Table displays all line items
- [ ] Total quote is correct
- [ ] Download CSV works
- [ ] Save to History button shows disabled message

### 8.3 Tab 3: Execution & Accounting Testing

**Missing Data Validation:**
- [ ] Detects missing company name
- [ ] Detects missing contact email
- [ ] Detects missing billing address
- [ ] Detects missing order items
- [ ] Warning banner displays clearly
- [ ] Lists all missing fields
- [ ] Allows proceeding even with missing data

**Order Summary Dropdown:**
- [ ] Expander opens/closes correctly
- [ ] Shows same data as Tab 2 summary
- [ ] Editable fields work (shipping, tariff, discount, CC fee)
- [ ] Changes sync back to Tab 2
- [ ] Rerun updates both tabs

**Client Invoice:**
- [ ] Header shows "INVOICE FOR CLIENT" clearly
- [ ] Header information displays correctly
- [ ] Partner POC info displays
- [ ] Delivery & payment details show
- [ ] Itemized table has correct columns (SELL PRICE)
- [ ] All products listed
- [ ] Customization line items show
- [ ] Tariff line items show
- [ ] Summary totals calculate correctly
- [ ] Notes section displays all notes
- [ ] Download Invoice (CSV) works

**Partner Purchase Orders:**
- [ ] Header shows "PURCHASE ORDERS FOR PARTNERS" clearly
- [ ] Detects all unique partners in order
- [ ] Generates correct number of POs
- [ ] Each PO shows only that partner's products
- [ ] Partner contact info displays correctly
- [ ] Itemized table has correct columns (COST, IN-HANDS, etc.)
- [ ] Customization line items included
- [ ] Tariff line items included
- [ ] Partner-specific totals calculate correctly
- [ ] Partner-specific notes display
- [ ] Download PO (CSV) works for each partner

**Downloads Section:**
- [ ] Individual download buttons work
- [ ] "Download All (ZIP)" shows as coming soon

### 8.4 Integration Testing (Cross-Tab)

**Full Workflow Test:**
1. [ ] Create proposal in Tab 1
   - Add 3 products from different partners
   - Configure with different markups
   - Enable customization on 1 product
   - Apply marketing rounding
   - Download proposal tables
   - Download client order form

2. [ ] Switch to Tab 2
   - Verify proposal status message shows "Using products from Proposal"
   - Fill out all client info fields
   - Select 2 products from proposal checklist
   - Click "Add Selected to Order"
   - Verify settings carried over correctly
   - Edit one product (change quantity)
   - Add 1 product not in proposal
   - Configure shipping ($100)
   - Configure tariff (verify per-product calculations)
   - Apply 5% NGO discount
   - Add custom line item
   - Add order notes (kitting specs + general notes)
   - Verify order summary is correct
   - Download order summary CSV

3. [ ] Switch to Tab 3
   - Verify no missing data warnings (or correct warnings if intentional)
   - Open order summary dropdown
   - Edit shipping to $150
   - Verify change reflected immediately
   - Verify invoice generates correctly
   - Count number of POs (should be 3 for 3 partners)
   - Verify each PO contains only that partner's products
   - Download invoice CSV
   - Download all 3 PO CSVs

4. [ ] Switch back to Tab 2
   - Verify shipping is $150 (synced from Tab 3)
   - Verify order summary matches Tab 3

5. [ ] Click "Clear All Data" in sidebar
   - Confirm in dialog
   - Verify all tabs reset to empty
   - Verify filters reset
   - Verify all session state cleared

**Session State Persistence:**
- [ ] Switch Tab 1 → Tab 2 → Tab 1: proposal data persists
- [ ] Switch Tab 2 → Tab 3 → Tab 2: order data persists
- [ ] Switch Tab 1 → Tab 3 → Tab 1: proposal data persists
- [ ] Make change in Tab 2 → switch to Tab 1 → switch back to Tab 2: change persists

**Edge Cases:**

1. [ ] **Empty states:**
   - Tab 1 with no products in proposal
   - Tab 2 with no order items
   - Tab 3 with no order items
   - All tabs with empty client info

2. [ ] **Single-partner order:**
   - Create order with products from only 1 partner
   - Verify only 1 PO generated in Tab 3

3. [ ] **Multi-partner order (3+ partners):**
   - Create order with products from 4 different partners
   - Verify 4 separate POs generated
   - Verify each PO is correctly filtered

4. [ ] **Custom line items only:**
   - Create order with only custom items (no partner products)
   - Verify invoice generates correctly
   - Verify PO section shows "No partner products" message

5. [ ] **Proposal with all products filtered out:**
   - Set price filter to exclude all products
   - Verify message shows "Showing 0 products"

6. [ ] **Marketing rounding edge cases:**
   - Test with $60.00 → should become $59.00
   - Test with $59.50 → should stay $59.50 (not a whole number)
   - Test with $100.00 → should become $99.00

7. [ ] **Tariff calculations:**
   - Order with products from multiple countries
   - Verify each tariff calculated separately
   - Verify total tariff is sum of all

8. [ ] **Discount applications:**
   - Test NGO discount (5%)
   - Test custom discount (10%)
   - Verify discount applies to products subtotal only (not shipping/tariff)

9. [ ] **CC fee calculations:**
   - Enable CC fee (2.9%)
   - Verify fee calculated on total before fee
   - Verify fee adds to final total correctly

### 8.5 Data Validation Testing

**Test with real Google Sheets data:**
- [ ] Load master_pricing_template_10_14
- [ ] Verify all sheets load (Template, Metadata, Partner-Specific Info)
- [ ] Test with tiered pricing products (verify tier ranges parse correctly)
- [ ] Test with flat pricing products (verify "No Tiers" displays)
- [ ] Test with products requiring customization (verify default costs load)
- [ ] Test with products from multiple countries (verify tariff rates)
- [ ] Test with missing data (blank fields in spreadsheet)
- [ ] Test partner contact extraction (verify POC info populates)

**Price calculation verification:**
- [ ] Manually calculate total for sample order
- [ ] Verify app calculation matches manual calculation
- [ ] Verify markup applies only to product cost (not customization/shipping/tariff)
- [ ] Verify customization setup fee is one-time (not multiplied by quantity)
- [ ] Verify customization per-unit cost multiplies by quantity
- [ ] Verify tariff base excludes customization costs

### 8.6 UI/UX Testing

**Layout & Visual:**
- [ ] All tabs display correctly
- [ ] Tab labels are clear and intuitive
- [ ] Column layouts work (no overlap or misalignment)
- [ ] Expanders expand/collapse smoothly
- [ ] Tables display correctly (no cut-off columns)
- [ ] Buttons are clearly labeled
- [ ] Warning messages are visually distinct
- [ ] Success messages display correctly
- [ ] Progress indicator in sidebar is clear

**Interactions:**
- [ ] All buttons respond correctly (no double-clicks needed)
- [ ] All inputs save correctly (no lost data)
- [ ] All dropdowns work (options display, selection saves)
- [ ] All checkboxes work (state toggles correctly)
- [ ] All text inputs work (accept and save text)
- [ ] All number inputs work (accept valid ranges only)
- [ ] All date pickers work (select and save dates)
- [ ] All download buttons work (file downloads with correct name)

**Confirmation Dialogs:**
- [ ] Clear All Data shows confirmation
- [ ] Confirmation has clear Yes/No options
- [ ] Cancel works correctly
- [ ] Confirm executes action correctly

**Messages & Feedback:**
- [ ] Progress indicator updates correctly
- [ ] Status messages are clear (proposal linked, using proposal, etc.)
- [ ] Validation warnings are specific (list missing fields)
- [ ] Success messages confirm actions
- [ ] Error messages are helpful

**Performance:**
- [ ] App loads quickly
- [ ] Tab switches are instant (no lag)
- [ ] Data calculations are fast
- [ ] Large orders (10+ products) perform well
- [ ] Filters apply quickly
- [ ] No freezing or unresponsiveness

---

## Future Enhancements
*(Outside scope of current restructure - implement later)*

### Proposal Management
- **Save proposals:** Store proposals with unique IDs, load later
- **Proposal versioning:** Track v1, v2, v3 of same proposal
- **Proposal history:** Sidebar section showing all saved proposals
- **Proposal templates:** Pre-configured product sets for common scenarios
- **Proposal expiration dates:** Auto-archive old proposals
- **Proposal status tracking:** Draft, Sent, Accepted, Declined

### Order Management
- **Save orders:** Store orders in database/persistent storage
- **Re-enable order history:** Show recent orders in sidebar with new structure
- **Order status tracking:** Draft → Sent → Confirmed → In Production → Fulfilled
- **Order search/filter:** Find orders by client name, date, status, etc.
- **Order archiving:** Move completed orders to archive
- **Order cloning:** Duplicate existing order for similar new order

### Client Management
- **Client database:** Store client info for reuse across orders
- **Client auto-fill:** Select existing client, auto-populate fields
- **Client history:** View all orders for a specific client
- **Client notes:** Add general notes about client preferences
- **Client pricing tiers:** Preferred/negotiated pricing for repeat clients
- **Client contacts:** Multiple contacts per client (primary, secondary, etc.)

### Import/Export
- **CSV upload for client order form:** Parse CSV, auto-populate Tab 2
- **Bulk product import:** Upload CSV list of products to add to proposal
- **Excel export:** Formatted invoice/PO templates in Excel format
- **PDF generation:** Professional PDF invoices and POs with branding
- **Email integration:** Send proposals/invoices directly from app

### Advanced Filtering & Search
- **Product category filter:** Filter by product type (bags, accessories, etc.)
- **Product material filter:** Filter by material (fabric, wood, metal, etc.)
- **Full-text search:** Search product descriptions and names
- **Save filter presets:** Save commonly-used filter combinations
- **Recently used products:** Quick-add frequently ordered products
- **Favorites:** Mark products as favorites for easy access

### Analytics & Reporting
- **Proposal conversion rate:** % of proposals that become orders
- **Most popular products:** Products appearing in most proposals/orders
- **Revenue by partner:** Total revenue generated per partner
- **Average order value:** Mean order total across all orders
- **Client lifetime value:** Total revenue per client over time
- **Profit margin analysis:** Markup % trends and profitability
- **Monthly/quarterly reports:** Revenue, orders, products sold

### Customization & Branding
- **Custom proposal templates:** Multiple template styles (formal, casual, etc.)
- **Company logo upload:** Add logo to invoices and POs
- **Custom terms per client type:** Different T&Cs for new vs repeat clients
- **Color scheme customization:** Match company branding
- **Custom email templates:** Branded email text for sending proposals

### Collaboration Features
- **Multi-user support:** Multiple team members using same app
- **User roles:** Admin, Sales, Finance roles with different permissions
- **Comments/notes on proposals:** Team discussion on specific proposals
- **Approval workflows:** Require approval before sending large proposals
- **Activity log:** Track who changed what and when
- **Notifications:** Alert users of status changes or pending approvals

### Advanced Pricing
- **Dynamic pricing rules:** Automatic pricing based on volume, client tier, etc.
- **Volume discount automation:** Auto-apply discounts at certain quantities
- **Seasonal pricing:** Price changes based on time of year
- **Partner-specific markups:** Different default markups per partner
- **Currency support:** Multi-currency pricing for international clients
- **Real-time exchange rates:** Auto-update currency conversions

### Integration
- **QuickBooks/Xero integration:** Auto-sync invoices to accounting software
- **ShipStation integration:** Auto-create shipments for orders
- **CRM integration:** Sync with Salesforce, HubSpot, etc.
- **Email automation:** SendGrid, Mailchimp for automated emails
- **Payment processing:** Stripe, PayPal integration for online payments
- **Inventory management:** Track partner stock levels, low stock alerts

### Mobile Optimization
- **Responsive design:** Optimize layout for tablet/mobile viewing
- **Mobile-friendly inputs:** Touch-optimized controls
- **Offline mode:** Work without internet, sync when connected
- **Mobile app:** Native iOS/Android app version

### Advanced Features
- **Version control for orders:** Track changes to orders over time
- **Comparison tool:** Compare multiple proposals side-by-side
- **Scenario modeling:** "What if" pricing scenarios
- **Automated reminders:** Follow-up on proposals, payment reminders
- **Document templates:** Custom invoice/PO layouts
- **Batch operations:** Apply changes to multiple products/orders at once
- **Import from previous system:** Migrate data from old tools
- **Export to accounting:** Batch export for monthly bookkeeping

---

## Timeline Estimate

### Phase 1-2: Backup & Setup
**Time:** 30 minutes
- Create backup file
- Create git commit
- Create config file structure
- Test data loading

### Phase 3: Tab 1 - Proposals
**Time:** 2-3 hours
- Filtering section (1 hour)
- Product catalog with "Add to Proposal" (1 hour)
- Proposal preview section (30 min)
- Terms & conditions (15 min)
- Client order form (15 min)
- Downloads section (30 min)

### Phase 4: Tab 2 - Order & Client Info
**Time:** 2-3 hours
- Proposal status message (15 min)
- Client information (30 min - mostly copy from current app)
- Product selection from proposal (1 hour)
- Add product not in proposal (30 min)
- Current order display (30 min - copy from current app)
- Order settings (30 min - copy from current app)
- Order summary (15 min - copy from current app)

### Phase 5: Tab 3 - Execution & Accounting
**Time:** 2-3 hours
- Missing data validation (30 min)
- Order summary dropdown (15 min)
- Client invoice (1 hour - mostly copy from current Section 10)
- Partner purchase orders (1-1.5 hours - new logic to split by partner)
- Downloads section (15 min)

### Phase 6: Sidebar Updates
**Time:** 1 hour
- Progress indicator (30 min)
- Clear All Data button (15 min)
- Update existing sections (15 min)

### Phase 7: Code Organization
**Time:** 1 hour
- Add section comments (15 min)
- Organize helper functions (30 min)
- Move previews to expanders (15 min)

### Phase 8: Testing
**Time:** 2-3 hours
- Unit testing per tab (1 hour)
- Integration testing (1 hour)
- Edge case testing (30 min)
- Data validation testing (30 min)

### Total Estimated Time
**12-15 hours of development + testing**

### Recommended Approach
1. **Day 1 (4-5 hours):** Phases 1-3 (Backup, setup, Tab 1)
2. **Day 2 (4-5 hours):** Phases 4-5 (Tab 2, Tab 3)
3. **Day 3 (3-4 hours):** Phases 6-8 (Sidebar, organization, testing)

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review and approve this plan
- [ ] Ensure current app is working and tested
- [ ] Commit any pending changes to git
- [ ] Inform team of upcoming restructure (if applicable)

### Phase 1: Backup
- [ ] Copy app.py to backups/app_2025_10_28_1pm_backup.py
- [ ] Create git commit with message
- [ ] Verify backup file is identical to original

### Phase 2: Setup
- [ ] Create config directory
- [ ] Create terms_conditions.txt
- [ ] Update app title and header
- [ ] Add new session state variables
- [ ] Create tab structure
- [ ] Test: App still loads with tab structure

### Phase 3: Tab 1
- [ ] Implement filtering section
- [ ] Implement product catalog
- [ ] Implement "Add to Proposal" workflow
- [ ] Implement proposal preview
- [ ] Implement terms & conditions
- [ ] Implement client order form
- [ ] Implement downloads
- [ ] Test: Run Tab 1 checklist from Phase 8.1

### Phase 4: Tab 2
- [ ] Implement proposal status message
- [ ] Copy client information section
- [ ] Implement product selection from proposal
- [ ] Implement "Add product not in proposal"
- [ ] Copy current order display
- [ ] Copy order settings
- [ ] Copy order summary
- [ ] Test: Run Tab 2 checklist from Phase 8.2

### Phase 5: Tab 3
- [ ] Implement missing data validation
- [ ] Implement order summary dropdown
- [ ] Copy and adapt invoice section
- [ ] Implement multi-partner PO generation
- [ ] Implement downloads section
- [ ] Test: Run Tab 3 checklist from Phase 8.3

### Phase 6: Sidebar
- [ ] Implement progress indicator
- [ ] Implement Clear All Data button
- [ ] Update recent orders section
- [ ] Update instructions
- [ ] Test: Sidebar elements work from all tabs

### Phase 7: Organization
- [ ] Add section comments
- [ ] Organize helper functions
- [ ] Move previews to expanders
- [ ] Review code readability
- [ ] Test: App still functions identically

### Phase 8: Testing
- [ ] Run unit testing checklists (8.1, 8.2, 8.3)
- [ ] Run integration testing (8.4)
- [ ] Run data validation testing (8.5)
- [ ] Run UI/UX testing (8.6)
- [ ] Fix any bugs found
- [ ] Re-test after fixes

### Post-Implementation
- [ ] Final end-to-end test with real data
- [ ] User acceptance testing (if applicable)
- [ ] Create git commit with message "Complete UI restructure to 3-tab system"
- [ ] Update documentation (README, PLANNING.md if needed)
- [ ] Deploy to production (if applicable)
- [ ] Monitor for issues in first few days

---

## Success Criteria

The restructure is considered successful when:

1. **All functionality preserved:** Everything that worked in the old app works in the new app
2. **All tests pass:** Complete testing checklist with no failures
3. **Data integrity:** Calculations match old app exactly
4. **No regressions:** No new bugs introduced
5. **Performance maintained:** App loads and runs as fast as before
6. **Code organized:** Clear sections with comments, easy to navigate
7. **User-friendly:** Workflow is intuitive, messages are clear
8. **Backup available:** Old app safely stored in backups folder
9. **Documentation updated:** Plan document and git history reflect changes
10. **Ready for future enhancements:** Structure supports features in Future Enhancements section

---

## Contact & Support

**For questions during implementation:**
- Refer to CLAUDE.md for project rules and context
- Refer to PLANNING.md for requirements and goals
- Refer to METHODOLOGY_LOGIC.md for pricing calculations
- Refer to INVOICE_REQUIREMENTS.md for invoice/PO format

**Troubleshooting:**
- If app breaks during restructure, restore from `backups/app_2025_10_28_1pm_backup.py`
- If data loading fails, check Google Sheets credentials in `.streamlit/secrets.toml`
- If calculations are wrong, compare with backup app output side-by-side

---

## Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-10-28 | 1.0 | Claude + User | Initial comprehensive plan created |

---

**END OF PLAN**

Ready to proceed with implementation when approved.
