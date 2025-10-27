# Application Architecture

**Last Updated:** 2025-10-27
**Version:** 2.1

---

## Overview

The Peace by Piece International Pricing App is a Streamlit-based web application that enables internal users to generate quotes, proposals, invoices, and purchase orders for artisan products from multiple partners.

**Technology Stack:**
- **Frontend:** Streamlit (Python-based web framework)
- **Backend:** Python 3.x
- **Data Source:** Google Sheets (master_pricing_template_10_14)
- **Authentication:** Google Cloud service account credentials
- **Data Processing:** pandas, gspread

---

## Data Flow

```
1. User selects partner + product
   ↓
2. App queries master_pricing_template_10_14 (3 sheets)
   ↓
3. Pricing engine calculates quote based on tier logic
   ↓
4. User customizes (quantity, markup, shipping, tariff)
   ↓
5. App generates proposal/invoice in standardized format
   ↓
6. User exports as CSV for bookkeeper/client
```

---

## Key Components

### Data Layer (Currently in app.py, planned for src/data_loader.py)

**Responsibilities:**
- Google Sheets API connection and authentication
- 3-sheet data loading (Template, Metadata, Partner-Specific Info)
- Data caching with 5-minute TTL
- Column name normalization

**Key Functions:**
- `connect_to_sheets()` - Authenticates with Google Sheets API using service account
- `load_pricing_data()` - Loads all 3 sheets and returns pandas DataFrames
  - Template sheet: Header at row 6, data starts row 7
  - Metadata sheet: Header at row 2, data starts row 3
  - Partner-Specific Info sheet: Header at row 2, data starts row 3

**Data Caching:**
```python
@st.cache_data(ttl=300)  # 5-minute cache
def load_pricing_data():
    # Loads sheets and returns DataFrames
    return df_template, df_metadata, df_partner_info
```

### Business Logic Layer (Currently in app.py, planned for src/pricing_engine.py)

**Responsibilities:**
- Determine pricing structure (tiered vs flat-rate)
- Tier range parsing and quantity-to-tier mapping
- Price lookup based on tier logic
- Customization cost calculations (setup fees, per-unit costs)
- Tariff calculations
- Order-level totals with shipping and discounts

**Key Functions:**
- `determine_tier_number(quantity, tier_info_string, has_tiers)` - Maps quantity to tier number (1-6)
- `get_unit_price_new_system(row, quantity)` - Returns base price for product based on tier or flat pricing
- `calculate_customization_costs(row, quantity, include_customization)` - Calculates setup fees and per-unit customization costs
- `calculate_product_tariff(product_cost_with_markup, tariff_rate_percent)` - Calculates tariff on product cost
- `calculate_product_quote(row, quantity, markup_percent, ...)` - Complete quote for single product
- `calculate_order_total(order_items, shipping, order_tariff, ...)` - Multi-product order total

**Pricing Logic:**
```
Tiered Products (Pricing Tiers (Y/N) = "Y"):
- Parse tier ranges from "Pricing Tiers Info" column
- Example: "T1: 1-25, T2: 26-50, T3: 51-100, T4: 101-250, T5: 251-500, T6: 501+"
- Select appropriate "PBP Cost: Tier X" column based on quantity

Flat-Rate Products (Pricing Tiers (Y/N) = "N"):
- Use "PBP Cost (No Tiers)" column
- Same price regardless of quantity
```

### Helper Functions Layer (Currently in app.py, planned for src/helpers.py)

**Responsibilities:**
- Data type conversions and cleaning
- Price rounding and formatting
- Partner contact extraction
- Validation and data integrity checks
- Utility calculations (MOQ, credit card fees)

**Key Functions:**
- `clean_price(price_string)` - Converts "$48.00" or "50.00%" to float
- `parse_tier_info(tier_string)` - Parses "T1: 1-25, T2: 26-50" into dict of ranges
- `parse_tariff_rate(tariff_string)` - Extracts numeric tariff rate from string
- `apply_marketing_rounding(price, enabled=True)` - Charm pricing ($60 → $59)
- `round_to_nearest_five(price, enabled=True)` - Rounds to nearest $5
- `calculate_moq(unit_price)` - Calculates minimum order quantity based on $1,000 minimum
- `calculate_credit_card_fee(total, apply_fee, fee_percent)` - Calculates CC processing fee
- `extract_partner_contacts(df_partner_info)` - Pulls POC info from Partner-Specific Info sheet
- `validate_invoice_completeness(client_info, order_items)` - Checks required fields before export

### Presentation Layer (app.py)

**Responsibilities:**
- Streamlit UI components and layout
- Session state management
- User input handling and validation
- Multi-product cart management
- Invoice/PO generation and formatting
- CSV export functionality

**UI Sections:**
1. **Page Configuration & Session State** - App setup and state initialization
2. **Data Loading** - Loads Google Sheets data and partner contacts
3. **Product Selection UI** - Partner and product dropdowns
4. **Customization Inputs** - Quantity, markup, customization options
5. **Order Management** - Add-to-cart, edit, remove products
6. **Client Information** - Client details form
7. **Proposal Generation** - Per-product pricing tables with MOQ format
8. **Invoice & Purchase Order** - Bookkeeper-aligned combined form
9. **Order Notes & Export** - Notes input and CSV download

---

## Pricing Formula

### Single Product Calculation

```
Product Cost = Base Price × Quantity
Customization Cost = Setup Fee + (Per-Unit Cost × Quantity)
Markup = Product Cost × (Markup % / 100)

Product Total = Product Cost + Customization Cost + Markup
```

### Multi-Product Order Total

```
Order Subtotal = Sum of all Product Totals
Discount Amount = Order Subtotal × (Discount % / 100)

Subtotal After Discount = Order Subtotal - Discount Amount

Order Total = Subtotal After Discount + Shipping + Tariff
```

**Key Principles:**
- Markup applies to **product cost only** (not setup fees, shipping, or tariff)
- Tariff is calculated on **product cost with markup** (not on fees/shipping)
- Shipping and tariff are **order-level** costs (apply once per order)
- Discounts apply to **product subtotal** (not shipping/tariff)

---

## Session State Management

Streamlit session state is used to persist data across user interactions:

```python
st.session_state.order_items = []  # List of products in current order
st.session_state.client_info = {}  # Client contact and billing information
st.session_state.order_notes = {}  # Kitting specs, client requests, etc.
st.session_state.editing_index = None  # Track which product is being edited
```

**Session State Benefits:**
- Preserves order across product additions
- Enables edit/remove functionality
- Maintains client info while user navigates sections
- Supports multi-step workflow without losing data

---

## File Structure (Current)

```
pricing-data-solution-pbp/
├── app.py (2,339 lines - MONOLITHIC)
├── requirements.txt
├── CLAUDE.md
├── README.md
│
├── .streamlit/
│   └── secrets.toml (Google credentials)
│
├── docs/
│   ├── ARCHITECTURE.md (this file)
│   ├── CHANGELOG.md
│   ├── PLANNING.md
│   ├── RESTRUCTURE_CONTEXT.md
│   ├── METHODOLOGY_LOGIC.md
│   ├── INVOICE_AND_PROPOSAL_SPEC.md
│   └── CLIENT_QUESTIONS.md
│
├── scripts/
│   └── test_connection.py
│
├── backups/
│   └── [timestamped backups]
│
└── archive/
    ├── docs/ (outdated documentation)
    └── scripts/ (deprecated utilities)
```

---

## File Structure (Planned After Reorganization)

```
pricing-data-solution-pbp/
├── app.py (1,500 lines - UI ONLY)
│
├── src/ (NEW - BUSINESS LOGIC)
│   ├── __init__.py
│   ├── README.md
│   ├── data_loader.py (150 lines) - Google Sheets integration
│   ├── pricing_engine.py (400 lines) - Pricing calculations
│   └── helpers.py (200 lines) - Utility functions
│
├── docs/
│   ├── ARCHITECTURE.md (this file)
│   ├── CHANGELOG.md
│   ├── PLANNING.md
│   ├── RESTRUCTURE_CONTEXT.md
│   ├── METHODOLOGY_LOGIC.md
│   ├── INVOICE_AND_PROPOSAL_SPEC.md
│   └── CLIENT_QUESTIONS.md
│
├── scripts/
│   ├── test_connection.py
│   └── investigate_data.py (consolidated investigation tool)
│
└── archive/
    ├── docs/ (outdated documentation)
    ├── backups/ (old versions)
    └── scripts/ (deprecated utilities)
```

**Benefits of Modular Structure:**
- **Separation of Concerns:** UI, business logic, and data access are separated
- **Easier Testing:** Can unit test pricing engine and helpers independently
- **Better Navigation:** Smaller files are easier to read and maintain
- **Reusability:** Business logic can be imported by other tools/scripts
- **Beginner-Friendly:** Clear module boundaries help new developers understand codebase

---

## Data Integration

### Google Sheets Connection

**Authentication:**
- Service account credentials stored in `.streamlit/secrets.toml`
- Scopes: `spreadsheets` and `drive`
- Connection established via `gspread` library

**Data Source:**
- Spreadsheet name: `master_pricing_template_10_14`
- 3 sheets: Template, Metadata, Partner-Specific Info
- Headers at different rows depending on sheet

### Data Refresh Strategy

- **Caching:** 5-minute TTL to balance freshness and performance
- **Manual Refresh:** Users can force refresh via Streamlit menu → "Rerun"
- **Automatic Refresh:** Cache expires automatically after 5 minutes

---

## Export Formats

### CSV Export (Current)

Generated for both proposals and invoices:
- Header section with client/order metadata
- Itemized table with product details
- Totals section (subtotal, shipping, tariff, grand total)
- Notes section (kitting specs, client requests, artwork, etc.)

### Future Enhancements

- **JSON Export:** Structured data format for API integration
- **PDF Generation:** Professional PDF invoices/proposals
- **Email Integration:** Direct submission to bookkeeper via email
- **Excel Export:** Multi-sheet workbook with formatting

---

## Security Considerations

### Credentials Management
- Google service account credentials never committed to git
- `.streamlit/secrets.toml` protected by `.gitignore`
- Credentials should be added manually or via deployment platform secrets

### Data Access
- Read-only access to Google Sheets (no write operations)
- Service account has minimal required permissions
- No client data stored locally (session state only)

### Deployment
- Deploy via Streamlit Cloud or similar platform
- Add secrets through platform UI (never in code)
- Use HTTPS for all production deployments

---

## Performance Considerations

### Data Loading
- **Caching:** 5-minute cache reduces API calls
- **Lazy Loading:** Data loaded only when needed
- **Parallel Requests:** Could load 3 sheets in parallel (future optimization)

### Session State
- Lightweight data structures minimize memory usage
- Order items list grows with order size but typically < 100 products
- No large file uploads or image processing

### UI Rendering
- Streamlit auto-reruns on user input
- Use `st.cache_data` for expensive operations
- Minimize recomputation by caching pricing calculations

---

## Testing Strategy

### Manual Testing
- Product selection and pricing calculations
- Multi-product order management (add, edit, remove)
- Proposal and invoice generation
- CSV export functionality
- Data validation and error handling

### Regression Testing
- Compare quotes before/after code changes
- Verify calculations match spreadsheet formulas
- Test edge cases (empty fields, invalid inputs, boundary quantities)

### Future: Automated Testing
- Unit tests for pricing engine functions
- Integration tests for data loading
- End-to-end tests for complete quote generation workflow

---

## Development Workflow

### Making Changes
1. Read relevant documentation (CLAUDE.md, RESTRUCTURE_CONTEXT.md, METHODOLOGY_LOGIC.md)
2. Create git backup commit before major changes
3. Make incremental changes with testing after each step
4. Update documentation to reflect changes
5. Test thoroughly before deployment

### Adding New Partners
1. Add partner data to master_pricing_template_10_14 (Template sheet)
2. Add partner contact info to Partner-Specific Info sheet
3. Define pricing structure (tiered or flat-rate)
4. Test with sample quotes
5. Document partner-specific rules in METHODOLOGY_LOGIC.md

### Modifying Calculations
1. Identify function in pricing engine
2. Update formula according to business rules
3. Test with known examples
4. Update METHODOLOGY_LOGIC.md with new formula
5. Create before/after comparison for validation

---

## Future Roadmap

### Short-Term (1-3 months)
- Complete code reorganization (extract modules)
- Add unit tests for pricing engine
- Implement investigation tool consolidation
- Improve error handling and validation

### Medium-Term (3-6 months)
- PDF generation for proposals/invoices
- Email integration for bookkeeper submission
- Multi-partner configuration system
- Enhanced data validation and user warnings

### Long-Term (6-12 months)
- API for external integrations
- Automated quote history tracking
- Client portal for quote viewing
- Advanced reporting and analytics

---

**End of Architecture Documentation**
