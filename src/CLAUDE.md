# CLAUDE.md - AI Assistant Context

Last Updated: 2024-12-20
Folder: /src
Purpose: Core business logic modules extracted from app.py for maintainability

---

## Quick Context
- **Primary responsibility**: Business logic, data processing, and utility functions
- **Key dependencies**: Google Sheets API (gspread), pandas, python-pptx, rapidfuzz
- **Used by**: app.py (main Streamlit application)
- **Technology stack**: Python 3.x, pure functions with minimal state

---

## Detailed Overview

The `src/` directory contains all modular business logic extracted from the main Streamlit application. This separation follows clean architecture principles, making the codebase:

1. **More maintainable** - Each module has a single responsibility
2. **More testable** - Pure functions can be tested in isolation
3. **More readable** - app.py focuses on UI, src/ focuses on logic
4. **More reusable** - Functions can be imported anywhere

The modularization happened in **v6.18 (November 2024)** during the codebase simplification phase, reducing total lines by 49% while improving code quality.

All modules follow these principles:
- Pure functions where possible (no side effects)
- Comprehensive docstrings with examples
- Type hints for clarity
- Beginner-friendly naming conventions

---

## Important Files

### Core Data & Processing
- **`data_loader.py` (10KB)**: Google Sheets API integration
  - Handles authentication via service account
  - Caches data for 5 minutes to reduce API calls
  - Loads 3 sheets: Data, Metadata, Partner-Specific Info
  - Supports both demo and real datasets
  - Environment variable support for Render deployment

- **`helpers.py` (34KB)**: General utility functions
  - Price parsing and cleaning (`clean_price()`)
  - Marketing rounding logic (`apply_marketing_rounding()`)
  - Tier parsing from spreadsheet format
  - Tariff calculations
  - Contact extraction from DataFrames
  - HTML parsing for client order forms
  - Validation functions

### Pricing & Calculation
- **`pricing_engine.py` (15KB)**: All pricing calculations
  - Tiered pricing logic (6 tiers: T1-T6)
  - Flat-rate pricing for non-tiered products
  - Customization cost calculations (setup + per-unit)
  - Product quote generation
  - Multi-product order totals
  - Discount application
  - MSRP markup calculations

### PowerPoint Automation
- **`slide_matcher.py` (31KB)**: Product-to-slide matching (Phase 1)
  - Fuzzy matching with 78.9% accuracy
  - Multi-scorer system (token_sort, token_set, partial_ratio)
  - Keyword category boosting (+15% confidence)
  - Variant name normalization
  - Manual match overrides

- **`pptx_generator.py` (48KB)**: PowerPoint generation (Phase 2)
  - Automated slide selection and removal
  - Dynamic pricing table updates (2x3, 2x4, 3x4 formats)
  - Multi-variant product consolidation
  - Font formatting preservation
  - Impact slide customization
  - Cover slide generation

- **`template_loader.py` (11KB)**: Cloud-based template management
  - Downloads 43MB PowerPoint template from Google Drive
  - Session-based caching (downloads once per session)
  - Memory optimization support
  - Garbage collection after heavy operations

### Data Persistence
- **`match_manager.py` (8.5KB)**: Manual match storage (JSON-based)
  - Stores user-defined product-to-slide mappings
  - Local file system persistence (data/manual_matches.json)
  - Product name normalization for consistent matching

- **`match_memory.py` (13.8KB)**: Confirmed match storage (Google Sheets)
  - Remembers user-confirmed fuzzy matches
  - Cloud-persistent (survives sessions)
  - Dataset-specific storage (demo ≠ real)
  - Priority: Confirmed > Manual > Fuzzy

- **`proposal_manager.py` (7.9KB)**: Save/load/delete proposals
  - Cloud-persistent storage in Google Sheets
  - Custom naming with auto-versioning (v2, v3, etc.)
  - Creator tracking (optional)
  - Dataset mismatch warnings

- **`order_manager.py` (9.6KB)**: Save/load/delete orders
  - Cloud-persistent storage in Google Sheets
  - Saves products, settings, and client info
  - Date serialization handling
  - Dataset validation

---

## Code Patterns & Conventions

### Import Pattern
```python
# In app.py
from src.data_loader import load_pricing_data
from src.helpers import clean_price, apply_marketing_rounding
from src.pricing_engine import calculate_product_quote
from src.slide_matcher import match_products_to_slides
from src.pptx_generator import generate_presentation
```

### Error Handling
All functions return `None` or default values on error, with optional error messages:
```python
# Good pattern - no exceptions raised to Streamlit
price = clean_price("invalid")  # Returns 0.0
tier = determine_tier_number(50, tier_data)  # Returns None if invalid
```

### Caching Strategy
- **Data loading**: 5-minute TTL cache via `@st.cache_data`
- **Google Sheets connection**: Resource cache via `@st.cache_resource`
- **PowerPoint template**: Session-based cache (manual clear on dataset switch)

### Dataset Handling
Two datasets supported:
1. **Demo**: `master_pricing_template_10_14` (19 products, 4 partners)
2. **Real**: `master_pricing` (133 products, 4 partners)

Functions check `st.session_state.selected_dataset` for context.

---

## Common Tasks

### To add a new pricing calculation:
1. Add function to `pricing_engine.py`
2. Follow existing naming: `calculate_*()` for computations
3. Add comprehensive docstring with example
4. Import in app.py where needed
5. Test with both demo and real datasets

### To add a new utility function:
1. Determine if it's data (data_loader), pricing (pricing_engine), or general (helpers)
2. Add to appropriate module
3. Keep it pure (no session state access inside src/)
4. Update module docstring if it's a major addition

### To modify PowerPoint matching:
1. **Matching logic**: Edit `slide_matcher.py`
2. **Table generation**: Edit `pptx_generator.py`
3. **Manual overrides**: Users edit via UI (stored in `match_manager.py`)
4. **Confirmed matches**: Auto-saved to Google Sheets via `match_memory.py`

### To debug pricing issues:
1. Check `pricing_engine.py` for calculation logic
2. Verify tier parsing in `helpers.py::parse_tier_info()`
3. Test with known quantities using test scripts in `scripts/features/`
4. Use `scripts/core/investigate_data.py` to examine raw spreadsheet data

---

## Important Notes

### Bidirectional Pricing (v7.3.0)
New in Week 2 Sprint - users can edit either markup % OR client price directly:
```python
# When user edits client price:
new_markup = ((client_price / pbp_cost) - 1) * 100

# When user edits markup:
client_price = pbp_cost * (1 + markup / 100)
```
Implemented in Tab 1 and Tab 3.

### Units Per Package (v6.8)
Products can have "Units per Package" column in spreadsheet:
- Normalizes package costs to per-unit costs
- Example: $48 for 6-pack → $8/unit
- Default: 1 (no change for most products)
- Handled in `pricing_engine.py::get_unit_price_new_system()`

### MSRP Pricing (v6.5)
When "Use MSRP pricing" checkbox is enabled:
- Calculates markup to match MSRP: `markup = ((MSRP / cost) - 1) * 100`
- Products without MSRP use 100% markup
- Edge case: MSRP below cost → 0% markup (break-even)
- Applied at add-time (not retroactive)

### Tiered vs Flat Pricing
Products can have either:
1. **Tiered pricing**: 6 tiers (T1-T6) with quantity ranges
2. **Flat pricing**: Single price regardless of quantity

Detection logic in `pricing_engine.py`:
```python
def is_tiered(row):
    return str(row.get('Pricing Tiers (Y/N)', 'N')).strip().upper() == 'Y'
```

### PowerPoint Variant Detection (v6.13)
Multi-variant products (e.g., "Jam - 4oz" and "Jam - 8oz") can consolidate to one slide:
- Automatic variant detection via `detect_variant_groups()`
- Smart variant identifier extraction (size, flavor, numeric units, parentheses)
- Pricing consistency check (all variants same MOQ/price?)
- User confirmation UI with conditional options
- Multi-row table population when needed

### Google Sheets Structure
Expected sheets in spreadsheet:
1. **Data** (header row 6): Product pricing data
   - Required columns: Partner, Product/Service, Pricing Tiers (Y/N), PBP Cost columns, MSRP
   - Optional: Units per Package, Country of Origin, Description
2. **Metadata** (header row 2): Field definitions for customization
3. **Partner-Specific Info** (header row 2): Partner contact information

Header row detection is critical - hardcoded in `data_loader.py`.

### Memory Optimization (v6.16-6.17)
For Render deployment (2GB RAM):
- PowerPoint template downloads on-demand from Google Drive (43MB)
- Session caching prevents duplicate downloads
- Garbage collection after heavy operations
- `USE_MEMORY_OPTIMIZATION` toggle in app.py (currently disabled)

### Non-Profit Terminology (v7.3.0)
Changed from "NGO" to "Non-profit" throughout:
- Default discount still 5%
- Applied in UI labels, variable names, comments
- Backward compatible with saved proposals/orders

---

## Gotchas & Notes

### Session State Boundaries
- **src/ modules should NEVER access `st.session_state` directly**
- All state access happens in app.py
- Functions receive data as parameters, return calculated values
- This keeps modules pure and testable

### Caching Invalidation
When dataset changes (demo ↔ real):
- Clear all caches: `st.cache_data.clear()`
- Clear proposals: `st.session_state.proposal_items = []`
- Clear orders: `st.session_state.order_items = []`
- Prevents data mismatches

### Float Precision
Marketing rounding and calculations use Python's `round()`:
- Can have floating-point precision issues
- Always format currency for display: `f"${value:,.2f}"`
- Epsilon comparisons for price equality: `abs(a - b) < 0.01`

### Spreadsheet Column Names
Case-sensitive and space-sensitive:
- "Units per Package" (lowercase "per")
- "Pricing Tiers (Y/N)" (exact parentheses)
- "PBP Cost (No Tiers)" vs "PBP Cost: Tier 1" (colon matters)

### PowerPoint Font Preservation
Template uses 15pt font - must be preserved:
```python
# In pptx_generator.py
for paragraph in cell.text_frame.paragraphs:
    for run in paragraph.runs:
        run.font.size = Pt(15)  # Always restore original size
```

### Date Serialization (v6.7)
Orders with date fields need special handling for JSON storage:
```python
# Convert dates to ISO strings before saving
def serialize_dates(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    # ... recursive handling for dicts/lists
```

### Fuzzy Matching Confidence Thresholds
In `slide_matcher.py`:
- **90%+**: Exact match (auto-confirm)
- **70-89%**: Fuzzy match (user confirms)
- **<70%**: Poor match (show alternatives)

Keyword boosting adds +15% for same category (e.g., "Jam" products).

---

## Recent Changes (v7.3.0 - December 2024)

### Bidirectional Pricing
- Users can now edit client price directly, not just markup %
- Added in Tab 1 (Proposal Generator) and Tab 3 (Order & Client Info)
- Calculation: `new_markup = ((client_price / pbp_cost) - 1) * 100`

### Non-Profit Terminology
- Changed "NGO" to "Non-profit" throughout codebase
- Updated UI labels, variable names, comments
- Still defaults to 5% discount

### Critical Bug Fix
- Fixed undefined `new_markup` variable in Tab 3
- Caused app crash when editing products
- Now properly handles both markup and price edits

---

## Testing

### Unit Tests
Individual test scripts in `scripts/features/`:
- `test_bidirectional_pricing.py` - Test markup ↔ price calculations
- `test_units_per_package.py` - Test package normalization
- `test_match_memory.py` - Test confirmed match persistence
- See `scripts/README.md` for full list

### Integration Tests
- `test_tab3_to_tab4_data_flow.py` - Full Tab 3 → Tab 4 workflow
- `test_saved_proposals.py` - Save/load/delete proposals
- `test_saved_orders.py` - Save/load/delete orders

### Core Tests
- `test_connection.py` - Google Sheets API connection
- `investigate_data.py` - Raw data structure inspection

---

## Dependencies

### Python Packages
```
streamlit==1.40.1
gspread==6.1.3
pandas==2.2.3
python-pptx==1.0.2
rapidfuzz==3.10.1
```

### External Services
- **Google Sheets API**: Data storage and retrieval
- **Google Drive API**: PowerPoint template hosting
- **Render**: Production deployment (2GB RAM, $25/month)

### File System
- `data/manual_matches.json` - Manual product-to-slide mappings (local)
- Google Sheets: saved_proposals, saved_orders, saved_matches (cloud)

---

## Performance Considerations

### API Rate Limits
- Google Sheets API: 100 requests/100 seconds/user
- Mitigated by 5-minute caching
- Always use `@st.cache_data` for data loading functions

### Memory Usage
- PowerPoint template: 43MB (downloads once per session)
- Pandas DataFrames: ~1-2MB for real dataset (133 products)
- Total app memory: ~500MB-800MB (well under 2GB limit)

### Page Load Time
- First load: ~3-5 seconds (data fetch + template download)
- Subsequent loads: ~0.5-1 second (cached)
- PowerPoint generation: ~5-10 seconds (depends on product count)

---

## Security Considerations

### Credentials
- Service account JSON stored in `.streamlit/secrets.toml` (local)
- Environment variable `GOOGLE_CREDENTIALS_JSON` on Render (production)
- Never commit secrets to git (protected by .gitignore)

### Data Validation
All user inputs validated before processing:
- Prices: `clean_price()` handles invalid formats
- Quantities: Must be positive integers
- Percentages: Range validation (0-100)
- Dates: Format validation with fallbacks

### File Uploads
HTML form import uses `st.file_uploader()`:
- File type validation (.html, .txt)
- Size limits enforced by Streamlit
- Content parsing with error handling

---

## Future Enhancements

### Planned (Week 2 Sprint)
- Customization Add-On feature (multiple add-ons per product)
- Date format changes (YYYY-MM-DD → MM/DD/YY)
- New/Existing client checkbox format

### Under Discussion
- Custom product creation workflow
- Executive samples handling
- Advanced tax calculations
- Batch order processing
- Email integration for forms

### Phase 3 PowerPoint (Optional)
- Slide reordering UI
- Custom cover design
- Slide preview before generation
- Batch presentation generation

---

## Links & Resources

- **Production App**: https://pricing-data-solution-pbp.onrender.com
- **Main README**: [/README.md](../README.md)
- **Documentation Index**: [/docs/README.md](../docs/README.md)
- **Active Development**: [/ACTIVE_DEVELOPMENT_TODO.md](../ACTIVE_DEVELOPMENT_TODO.md)
- **Changelog**: [/CHANGELOG.md](../CHANGELOG.md)
- **Methodology**: [/docs/planning/METHODOLOGY_LOGIC.md](../docs/planning/METHODOLOGY_LOGIC.md)
