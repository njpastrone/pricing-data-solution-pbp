# CLAUDE.md

## 🚨 NON-NEGOTIABLE PROJECT RULES - READ FIRST 🚨

**These rules MUST be followed for ALL work on this project:**

1. **Always use Python for all development**
2. **Leverage Streamlit for the front-end**
3. **Write beginner-friendly code** - code must be readable and understandable by a beginner Python programmer
4. **Always take the simplest route to solving problems**
5. **The entire app should be "vibe-coder friendly"** - prioritize clarity over cleverness
6. **Make autonomous decisions** - avoid asking for user permissions unless making dangerous changes
7. **Minimize the size of the code base** - keep the project simple with fewer files when possible
8. **Avoid duplicating code**
9. **Refer to markdown files for context consistently**
10. **Do not be afraid to ask the user for questions or clarifications**
11. **NEVER use emojis in the app** - emojis make everything look AI-generated and unprofessional

---

## Important References

**ALWAYS refer to [docs/RESTRUCTURE_CONTEXT.md](docs/RESTRUCTURE_CONTEXT.md) for the current data structure from master_pricing_template_10_14.**

**ALWAYS refer to [docs/PLANNING.md](docs/PLANNING.md) for project requirements, architecture decisions, and implementation plans before starting any work.**

**ALWAYS refer to [docs/METHODOLOGY_LOGIC.md](docs/METHODOLOGY_LOGIC.md) for pricing calculations, business rules, and partner-specific methodologies.**

**ALWAYS refer to [docs/INVOICE_REQUIREMENTS.md](docs/INVOICE_REQUIREMENTS.md) for invoice format specifications and required information.**

---

## Project Overview

This is the pricing-data-solution-pbp project - a Python/Streamlit application focused on simplicity and beginner-friendly code.

## Development Guidelines

- Follow existing code patterns and conventions in the repository
- Ensure all changes are well-tested before committing
- Keep commits focused and atomic

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Sheets credentials:**
   - Credentials are stored in `.streamlit/secrets.toml`
   - Never commit this file to git (protected by .gitignore)

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Test connection:**
   ```bash
   streamlit run scripts/test_connection.py
   ```

## Architecture

- **Frontend:** Streamlit (Python-based web app)
- **Data Source:** Google Sheets (master_pricing_template_10_14) with 3 sheets:
  - **Template**: Partner-product pricing data
  - **Metadata**: Deliverable field definitions
  - **Partner-Specific Info**: Partner configuration reference
- **Authentication:** Google Cloud service account
- **Pricing Model:** Flexible tiered or flat-rate pricing per product
- **Data Flow:**
  1. App connects to Google Sheets via `gspread`
  2. Loads three sheets into separate pandas DataFrames (headers at row 6 for Template, row 2 for others)
  3. User selects partner, then product/service
  4. App determines pricing structure (tiered Y/N) and selects appropriate price
  5. For tiered products: parses tier ranges from "Pricing Tiers Info" column
  6. Calculates quote: `Total = (Product Cost + Customization Costs + Markup) + Shipping + Tariff`
     - Product Cost = Base Price (from tier or flat) × Quantity
     - Customization = Setup Fee + (Per-Unit Cost × Quantity)
     - Markup = Product Cost × (Markup % / 100) - applies to product only, NOT fees/shipping/tariff
  7. Displays detailed breakdown, proposal, and invoice as copyable tables

## Current Features

- **Multi-Partner Support:** Select from multiple vendors/suppliers
- **Flexible Pricing:** Both tiered and flat-rate products supported
- **Dynamic Tier Parsing:** Tier ranges defined in data (not hardcoded)
- **Customization Options:** Setup fees + per-unit costs for custom branding
- **Smart Calculations:** Markup applies to product price only
- **Detailed Breakdowns:** Per-unit and total cost breakdowns
- **Discount Options:** NGO preset (5%) + custom discounts
- **Marketing Rounding:** Charm pricing ($60 → $59)
- **Custom Line Items:** Add unique services/customizations

## Project Structure

```
pricing-data-solution-pbp/
├── app.py                      # Main application (PRODUCTION)
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # This file - project rules & context
├── README.md                   # Project overview & quick start
│
├── .streamlit/
│   └── secrets.toml           # Google credentials (SECRET - never commit)
│
├── docs/                       # Documentation
│   ├── PLANNING.md            # Project requirements & goals
│   ├── DATA_STRUCTURE.md      # jaggery_demo data structure
│   ├── METHODOLOGY_LOGIC.md   # Pricing calculations & business rules
│   ├── INVOICE_REQUIREMENTS.md # Invoice format specification
│   ├── CLIENT_QUESTIONS.md    # Unanswered client questions
│   ├── APP_UPDATE_PLAN.md     # Implementation plan & details
│   └── MIGRATION_SUMMARY.md   # Migration history
│
├── scripts/                    # Utility scripts
│   ├── test_connection.py     # Test Google Sheets connection
│   ├── check_jaggery_demo.py  # Investigate jaggery_demo (Python)
│   └── investigate_jaggery_demo.py  # Investigate tool (Streamlit)
│
├── backups/                    # Backup files
│   └── app_mvp_backup.py      # Original MVP
│
└── archive/                    # Deprecated files (old scripts & data)
```

## Common Tasks

- **Refresh pricing data:** Click menu → "Rerun" in the Streamlit app
- **Update credentials:** Edit `.streamlit/secrets.toml`
- **Test API connection:** `streamlit run scripts/test_connection.py`
- **Investigate data structure:** `streamlit run scripts/investigate_jaggery_demo.py` or `python scripts/check_jaggery_demo.py`
- **Deploy to cloud:** Follow Streamlit Cloud deployment guide (add secrets in app settings)

---

## Current Status

**Version:** 2.0 - Multi-Partner Restructured System

**Last Updated:** 2025-10-14

**Features Implemented:**
- ✅ Multi-partner support (Partner X and future partners)
- ✅ Flexible pricing: tiered AND flat-rate products
- ✅ Dynamic tier parsing from Google Sheets data
- ✅ 3-sheet data architecture (Template, Metadata, Partner-Specific Info)
- ✅ Customization system (setup fee + per-unit costs)
- ✅ Multi-product ordering with add-to-cart pattern
- ✅ Per-product markup configuration
- ✅ Smart markup calculation (product only)
- ✅ Discount options (NGO preset 5% + custom discounts)
- ✅ Marketing rounding (charm pricing: $60 → $59)
- ✅ Custom line items for unique services/customizations
- ✅ Professional 6-column invoice table format
- ✅ Per-product proposal tables (4-column MOQ format)
- ✅ Download buttons for all major tables

**Testing Status:**
- ✅ Data loads from master_pricing_template_10_14
- ✅ Tier parsing logic verified (T1-T6 ranges)
- ✅ Tier selection working correctly for various quantities
- ✅ New column structure compatible with app
- ✅ Partner filtering functional

**Production Status:** ✅ Ready for testing with real partners

---

## Future Enhancements

- Multi-partner support (different tier structures per partner)
- Partner-specific configuration file
- Auto-detect tier ranges from column headers
- Remove debug expanders (optional)
- Admin UI for managing partner configurations
