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

**ALWAYS refer to [docs/PLANNING.md](docs/PLANNING.md) for project requirements, architecture decisions, and implementation plans before starting any work.**

**ALWAYS refer to [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md) for the exact structure of the jaggery_demo data to avoid coding mistakes.**

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
- **Data Source:** Google Sheets (jaggery_demo)
- **Authentication:** Google Cloud service account
- **Pricing Model:** Tiered pricing with 7 quantity ranges
- **Data Flow:**
  1. App connects to Google Sheets via `gspread`
  2. Loads pricing data into pandas DataFrame (skip row 1, headers at row 2, data from row 3)
  3. User selects products, enters quantity, and custom options
  4. App selects correct pricing tier based on quantity (1-25, 26-50, 51-100, 101-250, 251-500, 501-1000, 1000+)
  5. Calculates quote: `Total = (Product Cost + Additional Costs + Markup) + Shipping + Tariff`
     - Product Cost = Base Price (from tier) × Quantity
     - Additional Costs = Art Setup Fee + Label Costs (if labels selected)
     - Markup = Product Cost × (Markup % / 100) - applies to product only, NOT fees/shipping/tariff
  6. Displays detailed breakdown, proposal, and invoice as copyable tables

## Current Features

- **Tiered Pricing:** Automatic tier selection based on order quantity
- **Optional Labels:** Custom labels with minimum enforcement (100 labels for Jaggery partner)
- **Art Setup Fee:** One-time fee per order (only when labels selected)
- **Smart Calculations:** Markup applies to product price only
- **Detailed Breakdowns:** Per-unit and total cost breakdowns
- **Minimum Quantity Validation:** Warns if order is below product minimum
- **Soft-Coded Design:** Easy to modify tier ranges and partner-specific settings

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

**Version:** 1.4 - Per-Product Proposal Tables with Download Buttons

**Last Updated:** 2025-10-06

**Features Implemented:**
- ✅ Tiered pricing system (7 quantity ranges)
- ✅ Multi-product ordering with add-to-cart pattern
- ✅ Per-product markup configuration
- ✅ Optional custom labels with minimum enforcement
- ✅ Art setup fee (conditional on labels)
- ✅ Smart markup calculation (product only)
- ✅ Discount options (NGO preset 5% + custom discounts)
- ✅ Marketing rounding (charm pricing: $60 → $59)
- ✅ Custom line items for unique services/customizations
- ✅ Detailed cost breakdowns
- ✅ Minimum quantity validation
- ✅ Professional 6-column invoice table format
- ✅ Per-product proposal tables (4-column MOQ format)
- ✅ Download buttons for all major tables (proposals, invoices, order summary)
- ✅ Clean, organized codebase structure

**Testing Status:**
- ✅ Tier selection verified (e.g., quantity 70 → 51-100 tier)
- ✅ Calculations verified across multiple products
- ✅ Label minimum enforcement working
- ✅ All products loading successfully
- ✅ Proposal tables generate correctly with MOQ pricing
- ✅ Download functionality working for all table types

**Production Status:** ✅ Ready

---

## Future Enhancements

- Multi-partner support (different tier structures per partner)
- Partner-specific configuration file
- Auto-detect tier ranges from column headers
- Remove debug expanders (optional)
- Admin UI for managing partner configurations
