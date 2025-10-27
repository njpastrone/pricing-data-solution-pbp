# Codebase Reorganization Plan

**Date Created:** 2025-10-27
**Status:** APPROVED - Ready for Implementation
**Estimated Effort:** 9-11 hours total
**Risk Level:** Low-Medium (incremental approach with git safety)

---

## Executive Summary

This plan addresses critical organizational issues in the Peace by Piece International Pricing App:
- **2,339-line monolithic app.py** that violates beginner-friendliness principles
- **Outdated documentation** referencing deprecated jaggery_demo system
- **13 documentation files** with overlapping/contradictory information
- **13+ scattered Python scripts** across multiple directories

**Approach:** Hybrid reorganization prioritizing simplicity and maintainability while respecting the "beginner-friendly, vibe-coder friendly" project philosophy from CLAUDE.md.

---

## Current State Analysis

### Codebase Statistics
- **Main Application:** app.py (2,339 lines)
- **Documentation Files:** 17 markdown files (13 in docs/, 4 root level)
- **Python Scripts:** 14 total (1 production, 13 utility/backup)
- **Data Source:** master_pricing_template_10_14 (3 sheets: Template, Metadata, Partner-Specific Info)
- **Architecture:** Monolithic Streamlit app with Google Sheets backend

### Critical Issues Identified

#### Issue #1: Documentation Out of Sync with Reality

**The Problem:**
Multiple docs reference OLD data source (jaggery_demo) but app actually uses NEW system (master_pricing_template_10_14):

| File | Claims | Reality | Risk Level |
|------|--------|---------|------------|
| DATA_STRUCTURE.md | Documents jaggery_demo with 7 tiers | Not in use | HIGH - Wrong column names |
| README.md | "Active Sheet: jaggery_demo" | Uses master_pricing_template_10_14 | HIGH - Setup broken |
| METHODOLOGY_LOGIC.md | References old column names | App uses different structure | MEDIUM - Confusion |
| APP_UPDATE_PLAN.md | 800-line migration plan TO jaggery | Already past this | LOW - Just clutter |

**Impact:**
- New developers following docs would look for wrong columns
- Current docs say "PBP Cost w/o shipping (1-25)" but app uses "PBP Cost: Tier 1"
- Could cause data loading failures or incorrect calculations

#### Issue #2: Monolithic 2,339-Line app.py

**File Breakdown:**
```
app.py (2,339 lines)
├── Helper Functions (~200 lines)
│   ├── Marketing rounding, MOQ calculation
│   ├── Partner contact extraction
│   ├── Tariff parsing
│   └── Invoice validation
├── Data Loading Functions (~150 lines)
│   ├── Google Sheets connection
│   ├── 3-sheet loading (Template, Metadata, Partner Info)
│   └── Data caching
├── Pricing Calculation Logic (~400 lines)
│   ├── Tier selection (tiered vs flat)
│   ├── Price calculation with markup
│   ├── Customization costs (setup fees, labels)
│   └── Tariff calculations
└── UI Components (~1,589 lines)
    ├── Product selection dropdowns
    ├── Customization inputs (quantity, markup, shipping, tariff)
    ├── Multi-product cart management
    ├── Client information form (30+ fields)
    ├── Proposal generation (4-column MOQ format)
    ├── Invoice/PO generation (bookkeeper template)
    ├── Order notes (5 categories)
    └── CSV/JSON export
```

**Problems:**
- Violates CLAUDE.md Rule #3: "Write beginner-friendly code"
- Hard to navigate and find specific features
- High risk of breaking changes affecting multiple features
- Difficult to test individual components

#### Issue #3: Documentation Sprawl (17 Files)

**Redundancy Analysis:**

| File | Lines | Status | Issue |
|------|-------|--------|-------|
| PLANNING.md | 146 | ✅ Core | Keep - project requirements |
| RESTRUCTURE_CONTEXT.md | 213 | ✅ Current | Keep - actual data structure |
| DATA_STRUCTURE.md | 160 | ❌ Outdated | Archive - documents old jaggery_demo |
| METHODOLOGY_LOGIC.md | 503 | ⚠️ Partial | Update - some outdated references |
| INVOICE_REQUIREMENTS.md | 133 | ✅ Current | Keep - invoice specs |
| INVOICE_PO_RESTRUCTURE_PLAN.md | 456 | ⚠️ Redundant | Merge into INVOICE_REQUIREMENTS.md |
| APP_UPDATE_PLAN.md | 824 | ❌ Completed | Archive - historical migration plan |
| MIGRATION_SUMMARY.md | 48 | ❌ Historical | Archive - old migration notes |
| TARIFF_REFINEMENT_PLAN.md | ~200 | ❌ Completed | Archive - feature implemented |
| MARKUP_SECTION_REFINEMENT_PLAN.md | ~150 | ❌ Completed | Archive - feature implemented |
| DATA_COLLECTION_PLAN.md | ~100 | ❌ Completed | Archive - feature implemented |
| PROPOSAL_REQUIREMENTS.md | ~80 | ⚠️ Overlap | Merge into INVOICE_REQUIREMENTS.md |
| CLIENT_QUESTIONS.md | 71 | ✅ Active | Keep - tracking open questions |

**Result:** 13 docs → 7 focused docs (46% reduction)

#### Issue #4: Script Sprawl (14 Files)

```
Current Structure:
├── scripts/
│   ├── test_connection.py (useful - keep)
│   ├── investigate_jaggery_demo.py (useful but misnamed)
│   ├── check_jaggery_demo.py (useful but misnamed)
│   ├── test_new_structure.py (unclear purpose)
│   └── test_data_loading.py (possibly redundant)
├── backups/
│   ├── app_mvp_backup.py (old master_pricing_demo version)
│   └── app_before_restructure_20251014_174904.py (Oct 14 backup)
└── archive/
    ├── test_jaggery_sheet.py
    ├── investigate_jaggery_data.py
    ├── quick_data_check.py
    ├── check_sheet_direct.py
    ├── get_more_rows.py
    └── debug_pricing.py
```

**Issues:**
- Scripts named with "jaggery_demo" but app uses master_pricing_template_10_14
- Unclear which scripts are actively used
- Multiple investigation/debugging scripts doing similar things

---

## Reorganization Strategy: Hybrid Approach

**Philosophy:** Extract complex business logic while keeping UI accessible in single file.

**Rationale:**
- Respects CLAUDE.md "beginner-friendly" and "simplest route" principles
- Separates complex logic (easier to test) from UI (easier to modify)
- Reduces app.py from 2,339 → ~1,500 lines (36% reduction)
- Moderate effort with low risk

---

## Implementation Plan

### Phase 1: Documentation Cleanup (2-3 hours)

**Priority:** CRITICAL - Prevents new developers from following wrong instructions

#### Step 1.1: Archive Outdated Documentation (30 min)

**Actions:**
```bash
mkdir -p archive/docs/old_jaggery_demo
mkdir -p archive/docs/completed_plans

# Archive deprecated jaggery_demo docs
mv docs/DATA_STRUCTURE.md archive/docs/old_jaggery_demo/
mv docs/APP_UPDATE_PLAN.md archive/docs/completed_plans/
mv docs/MIGRATION_SUMMARY.md archive/docs/completed_plans/

# Archive completed feature plans
mv docs/TARIFF_REFINEMENT_PLAN.md archive/docs/completed_plans/
mv docs/MARKUP_SECTION_REFINEMENT_PLAN.md archive/docs/completed_plans/
mv docs/DATA_COLLECTION_PLAN.md archive/docs/completed_plans/
```

**Files Archived:** 6 docs moved to archive/

#### Step 1.2: Consolidate Overlapping Documentation (1 hour)

**Action 1: Merge Invoice Documentation**

Create consolidated `docs/INVOICE_AND_PROPOSAL_SPEC.md`:
- Merge INVOICE_REQUIREMENTS.md + INVOICE_PO_RESTRUCTURE_PLAN.md + PROPOSAL_REQUIREMENTS.md
- Remove redundant sections
- Keep only current specs and field definitions
- Result: 3 files → 1 file (~200 lines total)

**Action 2: Update METHODOLOGY_LOGIC.md**

Update to reflect current master_pricing_template_10_14 structure:
- Change "Data Source: jaggery_demo" → "Data Source: master_pricing_template_10_14"
- Update column references:
  - OLD: "PBP Cost w/o shipping (1-25)"
  - NEW: "PBP Cost: Tier 1"
- Update tier parsing examples to match "Pricing Tiers (Y/N)" system
- Verify all formulas match current app.py implementation

#### Step 1.3: Update Core Documentation (1 hour)

**File: README.md**

Changes:
```diff
- **Active Sheet:** `jaggery_demo` (Google Sheets)
+ **Active Sheet:** `master_pricing_template_10_14` (Google Sheets)

- **Structure:**
- - Row 1: Empty
- - Row 2: Headers
- - Row 3+: Product data
+ **Structure:** 3-sheet workbook
+ - **Template** (header at row 6): Partner-product pricing data
+ - **Metadata**: Deliverable field definitions
+ - **Partner-Specific Info**: Partner configuration reference

- **Key Fields:**
- - Product Ref. No., Gift Name, Artisan Partner
- - 7 pricing tier columns
- - Art Setup Fee, Label costs, Minimum quantities
+ **Key Fields:**
+ - Partner, Product/Service, Purchase Description
+ - Pricing Tiers (Y/N) flag
+ - Flexible tier definitions (PBP Cost: Tier 1-6 OR PBP Cost (No Tiers))
+ - Customization Setup Fee, Customization Cost per Unit
+ - Tariff Estimate, Shipping
```

**File: RESTRUCTURE_CONTEXT.md**

Add status banner at top:
```markdown
# 🧩 Project Data Structure & Integration Context

**STATUS:** ✅ IMPLEMENTED - This is the CURRENT SYSTEM in production

**Data Source:** master_pricing_template_10_14 (Google Sheets)
**Last Updated:** 2025-10-27
**Implementation Date:** October 2025

---
```

#### Step 1.4: Create New Architecture Documentation (30 min)

**File: docs/ARCHITECTURE.md** (NEW)

Content outline:
```markdown
# Application Architecture

## Overview
Streamlit-based pricing application with Google Sheets backend

## Data Flow
1. User selects partner + product
2. App queries master_pricing_template_10_14
3. Pricing engine calculates quote
4. User customizes (markup, shipping, tariff)
5. App generates proposal/invoice in bookkeeper format

## Key Components
### Data Layer (src/data_loader.py after refactor)
- Google Sheets API connection
- 3-sheet loading: Template, Metadata, Partner-Specific Info
- Data caching (5-minute TTL)

### Business Logic Layer (src/pricing_engine.py after refactor)
- Tier vs flat pricing determination
- Price lookup with tier matching
- Customization calculations (setup fees, labels)
- Tariff calculations

### Presentation Layer (app.py)
- Streamlit UI components
- Session state management
- Multi-product cart
- Invoice/PO generation

## Pricing Formula
Total = (Base Price × Qty + Customization) × (1 + Markup%) + Shipping + Tariff

Where:
- Markup applies to product cost only
- Customization = Setup Fee + (Per-Unit Cost × Qty)
- Tariff = (Base Price × Qty × Markup%) × Tariff Rate%

## File Structure
[Current and proposed structure diagrams]
```

**File: docs/CHANGELOG.md** (NEW)

Document version history:
```markdown
# Changelog

## Version 2.1 - Bookkeeper-Aligned Invoice & PO (October 2025)
- Restructured Invoice/PO to match bookkeeper template
- Added comprehensive order notes (5 categories)
- Auto-extract partner contacts from Google Sheets
- Field validation with user warnings
- Standardized payment/shipping dropdowns

## Version 2.0 - Multi-Sheet Data System (October 2025)
- Migrated from jaggery_demo to master_pricing_template_10_14
- Implemented 3-sheet architecture (Template, Metadata, Partner-Specific Info)
- Added flexible tier system with "Pricing Tiers (Y/N)" flag
- Support for both tiered and flat-rate pricing

## Version 1.1 - Multi-Product Ordering (October 2025)
- Add-to-cart pattern for multiple products
- Per-product markup configuration
- Order-level shipping and tariff

## Version 1.0 - MVP (September 2025)
- Single product quoting
- Basic proposal and invoice generation
- Google Sheets integration
```

**Result:** Documentation tree after Phase 1:
```
docs/
├── README.md (index of all docs - NEW)
├── ARCHITECTURE.md (NEW - system overview)
├── CHANGELOG.md (NEW - version history)
├── PLANNING.md (✅ updated - requirements)
├── RESTRUCTURE_CONTEXT.md (✅ updated - current data structure)
├── METHODOLOGY_LOGIC.md (✅ updated - pricing calculations)
├── INVOICE_AND_PROPOSAL_SPEC.md (✅ consolidated from 3 files)
└── CLIENT_QUESTIONS.md (✅ kept - active tracking)
```

**Metrics:**
- Before: 13 docs
- After: 8 docs (includes 1 index)
- Reduction: 38%
- All docs accurate and current

---

### Phase 2: Code Reorganization - Hybrid Approach (6-8 hours)

**Goal:** Extract business logic while keeping UI in app.py

#### Step 2.1: Create New Directory Structure (15 min)

```bash
mkdir -p src
touch src/__init__.py
touch src/data_loader.py
touch src/pricing_engine.py
touch src/helpers.py
```

#### Step 2.2: Extract Helper Functions (1.5 hours)

**File: src/helpers.py** (~200 lines)

Extract from app.py lines 13-200:
```python
"""
Utility helper functions for pricing calculations and data processing.
"""

def apply_marketing_rounding(price, enabled=True):
    """Apply charm pricing: round whole dollar amounts down by $1"""

def round_to_nearest_five(price, enabled=True):
    """Round price to the nearest multiple of 5"""

def calculate_moq(unit_price):
    """Calculate Minimum Order Quantity based on $1,000 minimum"""

def calculate_credit_card_fee(total, apply_fee=False, fee_percent=2.9):
    """Calculate credit card processing fee"""

def extract_partner_contacts(df_partner_info):
    """Extract partner contact information from Partner-Specific Info sheet"""

def validate_invoice_completeness(client_info, order_items):
    """Check if all required fields are filled before invoice/PO generation"""

def parse_tier_info(tier_string):
    """Parse 'T1: 1-25, T2: 26-50' into dict of tier ranges"""

def parse_tariff_rate(tariff_string):
    """Parse tariff percentage from spreadsheet strings"""

def clean_price(price_string):
    """Convert '$48.00' or '50.00%' to float"""
```

**Testing After Extraction:**
```python
# In app.py, replace definitions with:
from src.helpers import (
    apply_marketing_rounding,
    round_to_nearest_five,
    calculate_moq,
    calculate_credit_card_fee,
    extract_partner_contacts,
    validate_invoice_completeness,
    parse_tier_info,
    parse_tariff_rate,
    clean_price
)

# Run app: streamlit run app.py
# Verify all features still work
```

#### Step 2.3: Extract Data Loading Functions (2 hours)

**File: src/data_loader.py** (~150 lines)

Extract from app.py lines 570-680:
```python
"""
Google Sheets data loading and connection management.
Loads master_pricing_template_10_14 with 3 sheets.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

def connect_to_sheets():
    """
    Connect to Google Sheets using service account credentials.
    Returns authenticated gspread client.
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(credentials)

@st.cache_data(ttl=300)
def load_pricing_data():
    """
    Load pricing data from master_pricing_template_10_14.
    Returns: (df_template, df_metadata, df_partner_info)
    """
    gc = connect_to_sheets()
    spreadsheet = gc.open("master_pricing_template_10_14")

    # Load Template sheet (header at row 6)
    template_sheet = spreadsheet.worksheet("Template")
    template_values = template_sheet.get_all_values()
    template_headers = [col.strip() for col in template_values[5]]  # Row 6
    template_rows = template_values[6:]  # Data starts row 7
    df_template = pd.DataFrame(template_rows, columns=template_headers)

    # Load Metadata sheet (header at row 2)
    metadata_sheet = spreadsheet.worksheet("Metadata")
    metadata_values = metadata_sheet.get_all_values()
    metadata_headers = [col.strip() for col in metadata_values[1]]  # Row 2
    metadata_rows = metadata_values[2:]  # Data starts row 3
    df_metadata = pd.DataFrame(metadata_rows, columns=metadata_headers)

    # Load Partner-Specific Info sheet (header at row 2)
    partner_sheet = spreadsheet.worksheet("Partner-Specific Info")
    partner_values = partner_sheet.get_all_values()
    partner_headers = [col.strip() for col in partner_values[1]]  # Row 2
    partner_rows = partner_values[2:]  # Data starts row 3
    df_partner_info = pd.DataFrame(partner_rows, columns=partner_headers)

    return df_template, df_metadata, df_partner_info
```

**Testing After Extraction:**
```python
# In app.py, replace definitions with:
from src.data_loader import load_pricing_data

# Run app: streamlit run app.py
# Verify data loads correctly
# Check product dropdowns populate
```

#### Step 2.4: Extract Pricing Engine (2.5 hours)

**File: src/pricing_engine.py** (~400 lines)

Extract from app.py lines 162-560:
```python
"""
Core pricing calculation engine.
Handles tier selection, price lookup, customization costs, and tariff calculations.
"""

import pandas as pd
from src.helpers import parse_tier_info, parse_tariff_rate, clean_price

def determine_tier_number(quantity, tier_info_string, has_tiers):
    """Returns tier number (1-6) based on quantity"""

def get_unit_price_new_system(row, quantity):
    """
    Get correct unit price based on tier logic from master_pricing_template_10_14.
    Handles both tiered and non-tiered pricing.
    """

def calculate_product_tariff(product_cost_with_markup, tariff_rate_percent):
    """Calculate tariff on product cost"""

def calculate_customization_costs(row, quantity, include_customization):
    """
    Calculate customization costs (setup fee + per-unit costs).
    Returns dict with breakdown.
    """

def calculate_product_quote(row, quantity, markup_percent,
                           include_customization, customization_minimum):
    """
    Calculate complete quote for a single product.
    Returns detailed breakdown dict.
    """

def calculate_order_total(order_items, shipping, order_tariff,
                         discount_percent=0, apply_rounding=False):
    """
    Calculate total for multi-product order.
    Returns order summary dict.
    """
```

**Testing After Extraction:**
```python
# In app.py, replace definitions with:
from src.pricing_engine import (
    determine_tier_number,
    get_unit_price_new_system,
    calculate_product_tariff,
    calculate_customization_costs,
    calculate_product_quote,
    calculate_order_total
)

# Run app: streamlit run app.py
# Test pricing calculations for:
# - Tiered products (quantity 50, 150, 600)
# - Flat-rate products
# - Products with customization
# - Products with tariffs
# - Multi-product orders
# Verify all calculations match previous results
```

#### Step 2.5: Update app.py Structure (1 hour)

**New app.py structure** (~1,500 lines):
```python
"""
Peace by Piece International - Pricing & Quoting App
Main Streamlit UI application.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import extracted modules
from src.data_loader import load_pricing_data
from src.pricing_engine import (
    get_unit_price_new_system,
    calculate_product_quote,
    calculate_order_total,
    determine_tier_number
)
from src.helpers import (
    apply_marketing_rounding,
    calculate_moq,
    validate_invoice_completeness,
    extract_partner_contacts,
    parse_tariff_rate
)

# ============================================================
# SECTION 1: PAGE CONFIGURATION & SESSION STATE
# ============================================================

st.set_page_config(...)

# Initialize session state
if 'order_items' not in st.session_state:
    st.session_state.order_items = []
# ... rest of session state

# ============================================================
# SECTION 2: DATA LOADING
# ============================================================

df_template, df_metadata, df_partner_info = load_pricing_data()
partner_contacts = extract_partner_contacts(df_partner_info)

# ============================================================
# SECTION 3: PRODUCT SELECTION UI
# ============================================================

st.header("Product Selection")
# ... all product selection UI code

# ============================================================
# SECTION 4: CUSTOMIZATION INPUTS
# ============================================================

st.header("Customization Options")
# ... all customization input UI code

# ============================================================
# SECTION 5: ORDER MANAGEMENT
# ============================================================

st.header("Current Order")
# ... multi-product cart UI code

# ============================================================
# SECTION 6: CLIENT INFORMATION
# ============================================================

st.header("Client Information")
# ... all client info form UI code

# ============================================================
# SECTION 7: PROPOSAL GENERATION
# ============================================================

st.header("Proposal")
# ... proposal display and export code

# ============================================================
# SECTION 8: INVOICE & PURCHASE ORDER
# ============================================================

st.header("Invoice & Purchase Order")
# ... invoice/PO display and export code

# ============================================================
# SECTION 9: ORDER NOTES & EXPORT
# ============================================================

st.header("Order Notes")
# ... notes input and export code
```

**Benefits of New Structure:**
- Clear section markers make navigation easy
- Each section ~150-250 lines (scannable)
- Business logic separated from UI
- Maintains single-file simplicity for UI
- Total app.py reduction: 2,339 → ~1,500 lines (36% reduction)

#### Step 2.6: Add Module Documentation (30 min)

**File: src/README.md** (NEW)

```markdown
# Source Code Modules

This directory contains the core business logic extracted from app.py.

## Module Overview

### data_loader.py
Handles Google Sheets connection and data loading.

**Functions:**
- `connect_to_sheets()` - Authenticate with Google Sheets API
- `load_pricing_data()` - Load 3 sheets from master_pricing_template_10_14

**Data Sources:**
- Template sheet: Partner-product pricing data (header row 6)
- Metadata sheet: Deliverable field definitions (header row 2)
- Partner-Specific Info: Partner configuration (header row 2)

### pricing_engine.py
Core pricing calculation logic.

**Functions:**
- `get_unit_price_new_system(row, quantity)` - Get price based on tier/flat system
- `calculate_customization_costs(row, qty, include)` - Setup fees + per-unit costs
- `calculate_product_tariff(cost, rate)` - Tariff calculation
- `calculate_product_quote(row, qty, markup, ...)` - Complete product quote
- `calculate_order_total(items, shipping, tariff, ...)` - Multi-product order total

**Pricing Formula:**
Total = (Base × Qty + Customization) × (1 + Markup%) + Shipping + Tariff

### helpers.py
Utility functions for data processing and validation.

**Functions:**
- `clean_price(str)` - Convert "$48.00" to float
- `parse_tier_info(str)` - Parse "T1: 1-25, T2: 26-50" into ranges
- `parse_tariff_rate(str)` - Convert "50.00%" to float
- `calculate_moq(price)` - Calculate minimum order quantity
- `validate_invoice_completeness(client, items)` - Pre-export validation
- `extract_partner_contacts(df)` - Get partner contact info from sheets

## Usage Example

```python
from src.data_loader import load_pricing_data
from src.pricing_engine import calculate_product_quote
from src.helpers import parse_tariff_rate

# Load data
df_template, df_metadata, df_partner_info = load_pricing_data()

# Get product row
product = df_template[df_template['Product/Service'] == 'Product Y'].iloc[0]

# Calculate quote
quote = calculate_product_quote(
    row=product,
    quantity=100,
    markup_percent=50,
    include_customization=True,
    customization_minimum=100
)

print(f"Total: ${quote['total']:.2f}")
```

## Testing

Run tests from project root:
```bash
# Test data loading
python scripts/test_connection.py

# Test full app
streamlit run app.py
```
```

---

### Phase 3: Script Cleanup (1 hour)

#### Step 3.1: Consolidate Investigation Scripts (30 min)

**File: scripts/investigate_data.py** (NEW - consolidates 2 scripts)

Merge:
- `scripts/investigate_jaggery_demo.py`
- `scripts/check_jaggery_demo.py`

Update to query master_pricing_template_10_14:
```python
"""
Data Investigation Tool
Streamlit app to explore master_pricing_template_10_14 structure and content.
"""

import streamlit as st
from src.data_loader import load_pricing_data

st.title("Master Pricing Template Data Inspector")

df_template, df_metadata, df_partner_info = load_pricing_data()

# Sheet selection
sheet_choice = st.selectbox(
    "Select sheet to inspect:",
    ["Template", "Metadata", "Partner-Specific Info"]
)

if sheet_choice == "Template":
    st.subheader("Template Sheet")
    st.write(f"Total products: {len(df_template)}")
    st.write(f"Columns: {len(df_template.columns)}")
    st.dataframe(df_template.head(20))

    # Column explorer
    col = st.selectbox("Inspect column:", df_template.columns)
    st.write(df_template[col].value_counts())

elif sheet_choice == "Metadata":
    # ... similar for metadata

elif sheet_choice == "Partner-Specific Info":
    # ... similar for partner info
```

**Actions:**
```bash
# Delete old scripts
rm scripts/investigate_jaggery_demo.py
rm scripts/check_jaggery_demo.py

# Evaluate test_new_structure.py and test_data_loading.py
# If redundant, delete them as well
```

#### Step 3.2: Organize Backups and Archive (30 min)

```bash
# Create organized archive structure
mkdir -p archive/backups/pre_october_2025
mkdir -p archive/scripts/old_investigation_tools

# Move backups
mv backups/app_mvp_backup.py archive/backups/pre_october_2025/
mv backups/app_before_restructure_20251014_174904.py archive/backups/pre_october_2025/

# Keep only most recent backup in backups/
# Create new backup before Phase 2 refactor:
cp app.py backups/app_before_modular_refactor_$(date +%Y%m%d).py

# Archive old investigation scripts (already in archive/)
# Just add README explaining what they are:
```

**File: archive/scripts/README.md** (NEW)

```markdown
# Archived Scripts

These scripts are from earlier development phases and are kept for historical reference.

## Investigation Tools (jaggery_demo era)
- `investigate_jaggery_data.py` - Explored old jaggery_demo structure
- `test_jaggery_sheet.py` - Connection tests for jaggery_demo
- `quick_data_check.py` - Quick validation of jaggery_demo data
- `check_sheet_direct.py` - Direct sheet access debugging
- `get_more_rows.py` - Row extraction utility

## Debugging Tools
- `debug_pricing.py` - Pricing calculation debugging

**Note:** App now uses master_pricing_template_10_14, not jaggery_demo.
Current investigation tool: `scripts/investigate_data.py`
```

**Final scripts/ structure:**
```
scripts/
├── test_connection.py       # Google Sheets connection test
└── investigate_data.py      # Data exploration tool (NEW - consolidated)
```

---

## Testing & Validation Plan

### Phase 1 Testing (Documentation)
**Method:** Manual review
- [ ] Verify no broken links between docs
- [ ] Confirm all references to data source are correct
- [ ] Check that CHANGELOG.md has all major versions
- [ ] Review ARCHITECTURE.md for accuracy

### Phase 2 Testing (Code Refactor)
**Method:** Functional testing

**Test Suite:**
1. **Data Loading**
   - [ ] App starts without errors
   - [ ] All 3 sheets load correctly
   - [ ] Product dropdowns populate
   - [ ] Partner contacts extract correctly

2. **Pricing Calculations**
   - [ ] Tiered product (qty 50) calculates correctly
   - [ ] Tiered product (qty 250) calculates correctly
   - [ ] Flat-rate product calculates correctly
   - [ ] Customization costs add correctly
   - [ ] Tariff calculations match previous results
   - [ ] Multi-product order totals match

3. **UI Functionality**
   - [ ] Add product to cart works
   - [ ] Edit product in cart works
   - [ ] Remove product from cart works
   - [ ] Client info form saves to session state
   - [ ] Proposal generates and displays
   - [ ] Invoice/PO generates and displays
   - [ ] CSV export downloads correctly

4. **Regression Testing**
   - [ ] Compare 5 sample quotes before/after refactor
   - [ ] All calculations must match exactly
   - [ ] All UI features must work identically

### Phase 3 Testing (Script Cleanup)
**Method:** Execution test
- [ ] scripts/test_connection.py runs without errors
- [ ] scripts/investigate_data.py loads all 3 sheets
- [ ] No references to deleted scripts in documentation

---

## Risk Mitigation

### Backup Strategy
```bash
# Before starting ANY phase:
git add .
git commit -m "Backup before reorganization - $(date +%Y-%m-%d)"

# Before Phase 2 (code refactor):
cp app.py backups/app_before_modular_refactor_$(date +%Y%m%d).py
```

### Rollback Plan
If issues arise during Phase 2:
```bash
# Restore from backup
cp backups/app_before_modular_refactor_YYYYMMDD.py app.py

# Or revert git commit
git revert HEAD
```

### Incremental Approach
- Complete Phase 1 fully before starting Phase 2
- Test after each extraction in Phase 2 (helpers → data → pricing)
- Can stop after any phase if needed

---

## Success Criteria

### Phase 1 Success
- [ ] All docs reference correct data source (master_pricing_template_10_14)
- [ ] No contradictory information between docs
- [ ] 7 focused docs remaining (from 13)
- [ ] New developer can follow README → ARCHITECTURE → RESTRUCTURE_CONTEXT

### Phase 2 Success
- [ ] app.py reduced to ~1,500 lines
- [ ] All functionality works identically
- [ ] 5 sample quotes match exactly (before/after)
- [ ] Code is more maintainable (modules < 400 lines each)

### Phase 3 Success
- [ ] Only 2 scripts in scripts/ (from 5+)
- [ ] No orphaned files
- [ ] Clear archive organization

### Overall Success
- [ ] Project easier to navigate
- [ ] Documentation accurate and current
- [ ] Code follows "beginner-friendly" principle
- [ ] No broken functionality
- [ ] Ready for multi-partner expansion

---

## Post-Reorganization: Next Steps

After completing this reorganization, the project will be ready for:

1. **Unit Testing** - Add tests for pricing_engine.py and helpers.py
2. **Multi-Partner Expansion** - Add 2nd partner with different pricing structure
3. **Configuration Management** - Move partner-specific logic to config files
4. **Performance Optimization** - Profile and optimize data loading
5. **Feature Development** - Easier to add new features with modular structure

---

## Appendix: File Structure Comparison

### Before Reorganization
```
pricing-data-solution-pbp/
├── app.py (2,339 lines - MONOLITHIC)
├── docs/ (13 files - FRAGMENTED)
│   ├── PLANNING.md
│   ├── RESTRUCTURE_CONTEXT.md (current)
│   ├── DATA_STRUCTURE.md (OUTDATED)
│   ├── METHODOLOGY_LOGIC.md (partial outdated)
│   ├── INVOICE_REQUIREMENTS.md
│   ├── INVOICE_PO_RESTRUCTURE_PLAN.md (redundant)
│   ├── PROPOSAL_REQUIREMENTS.md (redundant)
│   ├── APP_UPDATE_PLAN.md (completed)
│   ├── MIGRATION_SUMMARY.md (historical)
│   ├── TARIFF_REFINEMENT_PLAN.md (completed)
│   ├── MARKUP_SECTION_REFINEMENT_PLAN.md (completed)
│   ├── DATA_COLLECTION_PLAN.md (completed)
│   └── CLIENT_QUESTIONS.md
├── scripts/ (5+ files - UNCLEAR PURPOSE)
│   ├── test_connection.py
│   ├── investigate_jaggery_demo.py (MISNAMED)
│   ├── check_jaggery_demo.py (MISNAMED)
│   ├── test_new_structure.py (unclear)
│   └── test_data_loading.py (redundant?)
├── backups/ (2 files)
└── archive/ (6+ old scripts)
```

### After Reorganization
```
pricing-data-solution-pbp/
├── app.py (1,500 lines - UI ONLY)
├── src/ (NEW - BUSINESS LOGIC)
│   ├── __init__.py
│   ├── README.md
│   ├── data_loader.py (150 lines)
│   ├── pricing_engine.py (400 lines)
│   └── helpers.py (200 lines)
├── docs/ (8 files - FOCUSED & CURRENT)
│   ├── README.md (index)
│   ├── ARCHITECTURE.md (NEW)
│   ├── CHANGELOG.md (NEW)
│   ├── PLANNING.md (updated)
│   ├── RESTRUCTURE_CONTEXT.md (updated - current system)
│   ├── METHODOLOGY_LOGIC.md (updated)
│   ├── INVOICE_AND_PROPOSAL_SPEC.md (consolidated from 3)
│   └── CLIENT_QUESTIONS.md
├── scripts/ (2 files - CLEAR PURPOSE)
│   ├── test_connection.py
│   └── investigate_data.py (consolidated)
├── backups/ (1 file - most recent)
│   └── app_before_modular_refactor_20251027.py
└── archive/ (ORGANIZED)
    ├── docs/
    │   ├── old_jaggery_demo/
    │   │   └── DATA_STRUCTURE.md
    │   └── completed_plans/
    │       ├── APP_UPDATE_PLAN.md
    │       ├── TARIFF_REFINEMENT_PLAN.md
    │       └── [other completed plans]
    ├── backups/
    │   └── pre_october_2025/
    └── scripts/
        ├── README.md
        └── [old investigation tools]
```

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review this plan thoroughly
- [ ] Create git commit: "Backup before reorganization"
- [ ] Ensure app is currently working (test in browser)
- [ ] Note current app behavior for regression testing

### Phase 1: Documentation (2-3 hours)
- [ ] Step 1.1: Archive 6 outdated docs
- [ ] Step 1.2: Merge invoice docs into INVOICE_AND_PROPOSAL_SPEC.md
- [ ] Step 1.2: Update METHODOLOGY_LOGIC.md column references
- [ ] Step 1.3: Update README.md data source references
- [ ] Step 1.3: Add status banner to RESTRUCTURE_CONTEXT.md
- [ ] Step 1.4: Create ARCHITECTURE.md
- [ ] Step 1.4: Create CHANGELOG.md
- [ ] Step 1.4: Create docs/README.md index
- [ ] Test: Review all docs for accuracy

### Phase 2: Code Refactor (6-8 hours)
- [ ] Step 2.1: Create src/ directory structure
- [ ] Step 2.2: Extract helpers.py
- [ ] Step 2.2: Update app.py imports
- [ ] Step 2.2: Test app runs correctly
- [ ] Step 2.3: Extract data_loader.py
- [ ] Step 2.3: Update app.py imports
- [ ] Step 2.3: Test data loads correctly
- [ ] Step 2.4: Extract pricing_engine.py
- [ ] Step 2.4: Update app.py imports
- [ ] Step 2.4: Test pricing calculations
- [ ] Step 2.5: Add section markers to app.py
- [ ] Step 2.6: Create src/README.md
- [ ] Test: Full regression testing (all features)
- [ ] Test: Compare 5 sample quotes before/after

### Phase 3: Script Cleanup (1 hour)
- [ ] Step 3.1: Create scripts/investigate_data.py
- [ ] Step 3.1: Delete old investigation scripts
- [ ] Step 3.2: Organize backups into archive/
- [ ] Step 3.2: Create archive/scripts/README.md
- [ ] Test: Run remaining scripts to verify functionality

### Post-Implementation
- [ ] Final testing: Full app walkthrough
- [ ] Create git commit: "Complete reorganization - modular structure"
- [ ] Update this plan status to "COMPLETED"
- [ ] Document any deviations or lessons learned

---

**End of Reorganization Plan**
