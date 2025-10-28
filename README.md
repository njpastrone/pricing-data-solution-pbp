# Peace by Piece International - Order Management System

A Python/Streamlit application for creating proposals, managing orders, and generating invoices for artisan products.

**Current Status:** ✅ Production Ready - Complete 3-Tab Workflow
**Version:** 4.0 - UI Restructure Complete with Proposal-to-Order Integration

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
- Credentials stored in `.streamlit/secrets.toml`
- Never commit this file (protected by `.gitignore`)

### 3. Run the App
```bash
streamlit run app.py
```

### 4. Test Connection (Optional)
```bash
streamlit run scripts/test_connection.py
```

---

## 📁 Project Structure

```
pricing-data-solution-pbp/
├── app.py                      # Main application (PRODUCTION)
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Project rules & context
├── README.md                   # This file
│
├── .streamlit/
│   └── secrets.toml           # Google service account credentials (SECRET)
│
├── docs/                       # Documentation
│   ├── PLANNING.md            # Project requirements & goals
│   ├── RESTRUCTURE_CONTEXT.md # Current data structure (master_pricing_template_10_14)
│   ├── METHODOLOGY_LOGIC.md   # Pricing calculations & business rules
│   ├── INVOICE_AND_PROPOSAL_SPEC.md # Invoice & proposal format specification
│   └── CLIENT_QUESTIONS.md    # Unanswered client questions
│
├── scripts/                    # Utility scripts
│   ├── test_connection.py     # Test Google Sheets connection
│   ├── check_jaggery_demo.py  # Investigate jaggery_demo structure
│   └── investigate_jaggery_demo.py  # Streamlit investigation tool
│
├── backups/                    # Backup files
│   └── app_mvp_backup.py      # Original MVP (master_pricing_demo)
│
└── archive/                    # Deprecated files
    ├── debug_pricing.py
    ├── jaggery_sample_6_23.xlsx
    ├── master_pricing_demo_reference.csv
    └── [deprecated scripts]
```

---

## 🎯 Features

### 3-Tab Workflow

#### Tab 1: Proposals (for prospective clients)
- **Product Filtering:** Filter by price range, partner, country of origin
- **Product Catalog:** Browse all products with detailed specifications
- **Proposal Configuration:** Set quantity, markup %, customization options, MSRP comparison
- **MOQ-Based Pricing Tables:** Automatic minimum order quantity calculations
- **CSV Downloads:** Export proposal tables and client order forms
- **Terms & Conditions:** Customizable terms loaded from config file

#### Tab 2: Order & Client Info (main workflow)
- **Proposal-to-Order Connection:** Import products directly from Tab 1 proposals
- **Multi-Product Ordering:** Add multiple products with add-to-cart pattern
- **Client Information Collection:** Company details, contacts, payment terms
- **Per-Product Markup:** Configure individual markup percentages
- **Tiered & Flat-Rate Pricing:** Flexible pricing models per product
- **Customization Options:** Setup fees + per-unit costs for custom branding
- **Order-Level Costs:** Shipping and tariff applied to entire order
- **Discount Options:** NGO preset (5%) or custom discounts
- **Marketing Rounding:** Optional charm pricing (e.g., $60 → $59)
- **Custom Line Items:** Add unique services not in catalog
- **Order Notes:** 5 categories (kitting, client requests, samples, artwork, general)

#### Tab 3: Execution & Accounting
- **Order Validation:** Completeness check with warnings
- **Editable Order Summary:** Quick edits for shipping, discounts, credit card fees
- **Invoice Generation:** Bookkeeper-standardized invoice format
- **Purchase Order Generation:** Partner-specific PO with auto-extracted contacts
- **CSV Export:** Download order data for accounting systems

### Formula

**Single Product:**
```
Product Total = (Base Price × Quantity) + Art Setup + Label Costs + Markup

Where:
- Markup = Base Price × Quantity × (Markup % / 100)
```

**Multi-Product Order:**
```
Total Order = Sum(All Product Totals) - Discount + Shipping + Tariff

Where:
- Discount applies to products subtotal (not shipping/tariff)
- Shipping and Tariff apply once to entire order
- Optional marketing rounding applies to final total
- Each product has independent markup percentage
```

---

## 📊 Data Source

**Active Sheet:** `master_pricing_template_10_14` (Google Sheets)

**Structure:** 3-sheet workbook
- **Template** (header at row 6): Partner-product pricing data
- **Metadata**: Deliverable field definitions
- **Partner-Specific Info**: Partner configuration reference

**Key Fields:**
- Partner, Product/Service, Purchase Description
- Pricing Tiers (Y/N) flag
- Flexible tier definitions (PBP Cost: Tier 1-6 OR PBP Cost (No Tiers))
- Customization Setup Fee, Customization Cost per Unit
- Tariff Estimate, Shipping

See [docs/RESTRUCTURE_CONTEXT.md](docs/RESTRUCTURE_CONTEXT.md) for complete details.

---

## 🔧 Configuration

### Pricing Tiers (Soft-Coded)
Edit tier ranges in `app.py` → `get_price_for_quantity()` function:

```python
tier_columns = [
    {'min': 1, 'max': 25, 'column': 'PBP Cost w/o shipping (1-25)'},
    {'min': 26, 'max': 50, 'column': 'PBP Cost w/o shipping (26-50)'},
    # ... more tiers
]
```

### Label Costs (Jaggery Partner)
- Label Art Setup: $70 (one-time)
- Label Unit Cost: From product data
- Label Minimum: 100 labels

Edit in `app.py` → `calculate_additional_costs()` function.

---

## 📚 Documentation

**Essential Reading:**
- [CLAUDE.md](CLAUDE.md) - Project rules & development guidelines
- [docs/RESTRUCTURE_CONTEXT.md](docs/RESTRUCTURE_CONTEXT.md) - Current data structure
- [docs/METHODOLOGY_LOGIC.md](docs/METHODOLOGY_LOGIC.md) - Pricing calculations
- [docs/INVOICE_AND_PROPOSAL_SPEC.md](docs/INVOICE_AND_PROPOSAL_SPEC.md) - Invoice & proposal formats

**Planning:**
- [docs/PLANNING.md](docs/PLANNING.md) - Project requirements
- [docs/CLIENT_QUESTIONS.md](docs/CLIENT_QUESTIONS.md) - Tracking open questions

---

## 🧪 Testing

### Manual Testing Checklist

**Product Selection & Customization:**
- [ ] Product selection dropdown works
- [ ] Quantity input validates minimum
- [ ] Tier selection matches quantity (e.g., 70 → 51-100 tier)
- [ ] Label checkbox adds correct costs
- [ ] Label minimum enforced (100 labels)
- [ ] Art setup fee only shows when labels selected
- [ ] Markup applies to product price only
- [ ] Per-product markup can be set independently

**Multi-Product Order Management:**
- [ ] Add to Order button adds product to order
- [ ] Current Order section displays all added products
- [ ] Edit button repopulates form with product details
- [ ] Update button replaces edited product in order
- [ ] Remove button deletes product from order
- [ ] Clear Entire Order button clears all products
- [ ] Order persists across product additions (session state)

**Order-Level Settings:**
- [ ] Shipping input only active when products in order
- [ ] Tariff input only active when products in order
- [ ] Shipping/tariff apply once to entire order

**Calculations & Display:**
- [ ] Product totals calculate correctly
- [ ] Order total sums all products + shipping + tariff
- [ ] Per-product breakdowns show in Current Order
- [ ] Order Summary shows all products with totals
- [ ] Proposal displays multi-product details correctly
- [ ] Invoice displays multi-product line items correctly

### Test Cases
See [docs/METHODOLOGY_LOGIC.md](docs/METHODOLOGY_LOGIC.md) for detailed single-product and multi-product test cases.

---

## 🚢 Deployment

### Streamlit Cloud
1. Push to GitHub repository
2. Connect Streamlit Cloud to repo
3. Add secrets in app settings (paste contents of `.streamlit/secrets.toml`)
4. Deploy!

---

## 🔮 Future Enhancements

### Multi-Partner Support
Currently built for Jaggery partner. Future versions will support multiple partners with:
- Different pricing tier structures
- Different tier ranges
- Different cost components
- Partner-specific configurations

See [docs/APP_UPDATE_PLAN.md](docs/APP_UPDATE_PLAN.md) for multi-partner architecture strategy.

---

## 🛠️ Common Tasks

**Refresh pricing data:** Menu → "Rerun" in the app

**Update credentials:** Edit `.streamlit/secrets.toml`

**Investigate data:** `streamlit run scripts/investigate_jaggery_demo.py`

**Test connection:** `streamlit run scripts/test_connection.py`

---

## 📝 Development Guidelines

See [CLAUDE.md](CLAUDE.md) for complete development rules, including:
- Always use Python & Streamlit
- Write beginner-friendly code
- Take the simplest route
- Soft-code everything for easy editing
- Minimize codebase size
- Avoid code duplication

---

## 📄 License

Peace by Piece International - Internal Tool

---

**Last Updated:** 2025-10-28
**Version:** 4.0 (Complete UI Restructure with Proposal-to-Order Integration)
