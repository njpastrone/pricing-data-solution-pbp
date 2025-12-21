# Source Code Modules

This directory contains all business logic extracted from app.py for better organization and maintainability.

**Last Updated:** 2024-12-20
**Version:** 7.3.0 (Production Ready)

---

## Overview

The `src/` directory follows clean architecture principles, separating business logic from UI code. All modules are production-ready and actively maintained.

**Benefits:**
- **Maintainability** - Each module has a single responsibility
- **Testability** - Pure functions can be tested in isolation
- **Readability** - app.py focuses on UI, src/ focuses on logic
- **Reusability** - Functions can be imported anywhere

---

## Core Modules

### Data & Processing

#### `data_loader.py` (10KB)
**Purpose:** Google Sheets API integration and data loading

**Functions:**
- `connect_to_sheets()` - Establish Google Sheets connection (cached)
- `load_pricing_data()` - Load 3 sheets with 5-minute cache

**Returns:**
- `df_template` - Product pricing data (header row 6)
- `df_metadata` - Field definitions (header row 2)
- `df_partner_info` - Partner contacts (header row 2)

**Usage:**
```python
from src.data_loader import load_pricing_data

df_template, df_metadata, df_partner_info = load_pricing_data()
```

**Features:**
- Dataset switching (Demo vs Real)
- Environment variable support for Render
- Automatic cache invalidation

---

#### `helpers.py` (34KB)
**Purpose:** General utility functions for data processing

**Key Functions:**
- `clean_price()` - Convert price strings to floats
- `apply_marketing_rounding()` - Charm pricing ($60 → $59)
- `round_to_nearest_five()` - Round to nearest $5
- `calculate_moq()` - Calculate minimum order quantity
- `parse_tier_info()` - Parse tier ranges from string
- `parse_tariff_rate()` - Parse tariff percentage
- `extract_partner_contacts()` - Parse partner info from DataFrame
- `validate_invoice_completeness()` - Check required fields
- `parse_client_order_form_html()` - Extract data from HTML forms

**Usage:**
```python
from src.helpers import clean_price, apply_marketing_rounding

price = clean_price("$48.00")  # Returns 48.0
rounded = apply_marketing_rounding(60.0)  # Returns 59.0
```

---

### Pricing & Calculations

#### `pricing_engine.py` (15KB)
**Purpose:** All pricing calculations and quote generation

**Functions:**
- `determine_tier_number()` - Map quantity to tier (1-6)
- `get_unit_price_new_system()` - Get price based on tier/flat logic
- `calculate_customization_costs()` - Calculate setup + per-unit costs
- `calculate_product_quote()` - Complete quote for single product
- `calculate_order_total()` - Multi-product order total
- `calculate_msrp_markup()` - Calculate markup to match MSRP
- `calculate_proposal_pricing()` - Pricing for proposal tables

**Usage:**
```python
from src.pricing_engine import calculate_product_quote

quote = calculate_product_quote(
    row=product_row,
    quantity=100,
    markup_percent=50,
    include_customization=True,
    customization_minimum=100
)
# Returns: {
#   'unit_price': 10.0,
#   'subtotal': 1000.0,
#   'setup_fee': 50.0,
#   'customization_per_unit': 2.0,
#   'total': 1250.0
# }
```

**Features:**
- Tiered pricing (6 tiers)
- Flat-rate pricing
- MSRP markup calculation (v6.5)
- Units per package normalization (v6.8)
- Bidirectional pricing (v7.3.0)

---

### PowerPoint Automation

#### `slide_matcher.py` (31KB)
**Purpose:** Product-to-slide matching system (Phase 1)

**Functions:**
- `match_products_to_slides()` - Main matching orchestrator
- `calculate_match_scores()` - Multi-scorer fuzzy matching
- `detect_variant_groups()` - Find multi-variant products
- `extract_variant_identifier()` - Smart variant name extraction

**Usage:**
```python
from src.slide_matcher import match_products_to_slides

matches = match_products_to_slides(
    proposal_items=products,
    template_path="templates/November All Slides.pptx"
)
# Returns: {
#   'exact_matches': [...],
#   'fuzzy_matches': [...],
#   'poor_matches': [...]
# }
```

**Features:**
- 78.9% match accuracy
- Multi-scorer system (3 algorithms)
- Keyword category boosting (+15%)
- Variant name normalization
- Manual match overrides

---

#### `pptx_generator.py` (48KB)
**Purpose:** PowerPoint generation and table updates (Phase 2)

**Functions:**
- `generate_presentation()` - Main generation orchestrator
- `update_pricing_table()` - Update tables (2×3, 2×4, 3×4 formats)
- `remove_unmatched_slides()` - Clean up unused slides
- `add_cover_slide()` - Professional cover with client name
- `customize_impact_slides()` - Partner-specific impact slides

**Usage:**
```python
from src.pptx_generator import generate_presentation

pptx_path = generate_presentation(
    confirmed_matches=matches,
    client_name="Acme Corp",
    discount_percent=5.0,
    marketing_rounding=True
)
# Returns: "/tmp/Acme_Corp_Proposal.pptx"
```

**Features:**
- Automated slide selection
- Dynamic pricing tables
- Multi-variant consolidation (v6.13)
- Font formatting preservation (15pt)
- Impact slides per partner
- Progress indicators

---

#### `template_loader.py` (11KB)
**Purpose:** Cloud-based PowerPoint template management

**Functions:**
- `load_template()` - Download from Google Drive (43MB)
- `get_template_path()` - Get cached or download template

**Usage:**
```python
from src.template_loader import get_template_path

template_path = get_template_path()
# Downloads once per session, then caches
```

**Features:**
- Session-based caching
- Memory optimization support
- Garbage collection
- Render deployment compatible

---

### Data Persistence

#### `match_manager.py` (8.5KB)
**Purpose:** Manual product-to-slide match storage (JSON-based)

**Functions:**
- `save_manual_matches()` - Save user-defined mappings
- `load_manual_matches()` - Load manual overrides
- `normalize_for_storage()` - Product name normalization

**Storage:** `data/manual_matches.json` (local file)

---

#### `match_memory.py` (13.8KB)
**Purpose:** Confirmed match storage (Google Sheets)

**Functions:**
- `save_confirmed_match()` - Save user-confirmed fuzzy match
- `load_confirmed_matches()` - Load all confirmed matches
- `delete_confirmed_match()` - Remove saved match

**Storage:** Google Sheets (cloud-persistent, dataset-specific)

**Features:**
- Remembers across sessions
- Dataset validation (demo ≠ real)
- Priority: Confirmed > Manual > Fuzzy

---

#### `proposal_manager.py` (7.9KB)
**Purpose:** Save/load/delete proposal functionality

**Functions:**
- `save_proposal()` - Save proposal to Google Sheets
- `load_proposal()` - Load saved proposal
- `delete_proposal()` - Delete saved proposal
- `list_saved_proposals()` - Get all saved proposals

**Storage:** Google Sheets (cloud-persistent)

**Features:**
- Custom naming with auto-versioning (v2, v3)
- Optional creator tracking
- Dataset mismatch warnings
- Full settings preservation

---

#### `order_manager.py` (9.6KB)
**Purpose:** Save/load/delete order functionality

**Functions:**
- `save_order()` - Save order to Google Sheets
- `load_order()` - Load saved order
- `delete_order()` - Delete saved order
- `list_saved_orders()` - Get all saved orders

**Storage:** Google Sheets (cloud-persistent)

**Features:**
- Saves products, settings, client info
- Date serialization handling
- Dataset validation
- Auto-versioning on duplicates

---

## Module Dependencies

### External Packages
```
streamlit==1.40.1        # UI framework
gspread==6.1.3           # Google Sheets API
pandas==2.2.3            # Data processing
python-pptx==1.0.2       # PowerPoint generation
rapidfuzz==3.10.1        # Fuzzy string matching
```

### Internal Dependencies
- `data_loader.py` → No internal deps (core)
- `helpers.py` → No internal deps (utilities)
- `pricing_engine.py` → `helpers.py`
- `slide_matcher.py` → `match_manager.py`, `match_memory.py`
- `pptx_generator.py` → `pricing_engine.py`, `template_loader.py`
- `proposal_manager.py` → `data_loader.py`
- `order_manager.py` → `data_loader.py`

---

## Development Guidelines

### Adding New Functions

1. **Choose the right module:**
   - Data fetching → `data_loader.py`
   - Utilities/helpers → `helpers.py`
   - Pricing logic → `pricing_engine.py`
   - PowerPoint → `slide_matcher.py` or `pptx_generator.py`
   - Persistence → `*_manager.py`

2. **Follow conventions:**
   - Pure functions (no session state inside src/)
   - Comprehensive docstrings with examples
   - Type hints for clarity
   - Beginner-friendly naming

3. **Update documentation:**
   - Add to this README
   - Update CLAUDE.md with context
   - Add test script if complex

### Module Responsibilities

- **`helpers.py`** - Pure utility functions, no business logic
- **`data_loader.py`** - Data fetching and DataFrame processing only
- **`pricing_engine.py`** - All pricing calculations and business rules
- **`*_manager.py`** - Data persistence (JSON or Google Sheets)
- **`slide_matcher.py`** - Product matching logic only
- **`pptx_generator.py`** - PowerPoint generation only
- **`app.py`** - UI components and Streamlit interactions only

---

## Common Patterns

### Error Handling
Return `None` or default values on error (no exceptions):
```python
price = clean_price("invalid")  # Returns 0.0, not error
tier = determine_tier_number(50, None)  # Returns None
```

### Caching
Use Streamlit caching decorators:
```python
@st.cache_data(ttl=300)  # 5-minute cache
def load_pricing_data():
    # ... expensive operation
    return df_template, df_metadata, df_partner_info
```

### Dataset Awareness
Check dataset from session state in app.py, pass to functions:
```python
# In app.py
dataset = st.session_state.selected_dataset
df_template, _, _ = load_pricing_data(dataset)

# In src/ modules - receive as parameter
def calculate_quote(row, quantity, dataset="demo"):
    # ... use dataset to determine behavior
```

---

## Testing

### Test Scripts Location
- **Core tests:** `scripts/core/`
- **Feature tests:** `scripts/features/`
- **Investigation:** `scripts/investigations/`

### Key Test Scripts
- `test_connection.py` - Google Sheets API
- `test_bidirectional_pricing.py` - Markup ↔ price calculations
- `test_units_per_package.py` - Package normalization
- `test_match_memory.py` - Confirmed match persistence
- `test_saved_proposals.py` - Proposal save/load/delete
- `test_saved_orders.py` - Order save/load/delete

### Running Tests
```bash
# Core functionality
streamlit run scripts/core/test_connection.py

# Feature tests (Python scripts)
python scripts/features/test_bidirectional_pricing.py

# Main app
streamlit run app.py
```

---

## Recent Changes

### v7.3.0 (December 2024)
- Bidirectional pricing (edit markup OR client price)
- Non-profit terminology (changed from NGO)
- Directory reorganization

### v6.18 (November 2024)
- Codebase simplification (49% reduction)
- Code clarity improvements
- Function renaming for beginners

### v6.13-6.17 (November 2024)
- Multi-variant PowerPoint support
- Cloud-based template loading
- Render deployment optimizations
- Match memory system

---

## Performance Notes

### API Rate Limits
- Google Sheets: 100 requests/100 seconds/user
- Mitigated by 5-minute caching
- Always use `@st.cache_data`

### Memory Usage
- PowerPoint template: 43MB (downloads once)
- Pandas DataFrames: ~1-2MB (real dataset)
- Total app: ~500-800MB (well under 2GB)

### Load Times
- First load: ~3-5 seconds (data + template)
- Cached load: ~0.5-1 second
- PowerPoint gen: ~5-10 seconds

---

## Links

- **Main README:** [../README.md](../README.md)
- **CLAUDE.md:** [CLAUDE.md](CLAUDE.md) (AI-friendly context)
- **Documentation:** [../docs/README.md](../docs/README.md)
- **Methodology:** [../docs/planning/METHODOLOGY_LOGIC.md](../docs/planning/METHODOLOGY_LOGIC.md)
- **Production:** https://pricing-data-solution-pbp.onrender.com
