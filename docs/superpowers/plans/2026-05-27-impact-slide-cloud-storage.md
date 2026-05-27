# Impact Slide Cloud Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace local JSON + hardcoded partner list for impact slide matching with a human-managed Google Sheet that resolves slide indices dynamically from the current template.

**Architecture:** A new `load_impact_slide_mapping()` function reads partner-to-slide-title pairs from Google Sheets. A new `resolve_impact_slides()` function combines that mapping with `find_all_impact_slides()` (which scans the template) to produce the `{partner: {slide_index, slide_title}}` dict that `pptx_generator.py` already expects. The app.py call site switches from `build_impact_slide_map()` to `resolve_impact_slides()`.

**Tech Stack:** Python, gspread, Streamlit caching, rapidfuzz (for title normalization)

**Spec:** `docs/superpowers/specs/2026-05-27-impact-slide-cloud-storage-design.md`

---

### Task 1: Add Google Sheet config and loader function

**Files:**
- Modify: `src/data_loader.py:24-55` (DATASET_CONFIGS) and append new function

- [ ] **Step 1: Write the failing test**

Create `tests/test_impact_slide_mapping.py`:

```python
"""Tests for impact slide mapping loader."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_load_impact_slide_mapping_returns_dict():
    """load_impact_slide_mapping returns a dict of partner -> slide title."""
    from src.data_loader import load_impact_slide_mapping
    result = load_impact_slide_mapping()
    assert isinstance(result, dict)
    # Should have at least one entry (sheet has 7 partners)
    assert len(result) > 0


def test_load_impact_slide_mapping_has_expected_partners():
    """Mapping includes known partners from the sheet."""
    from src.data_loader import load_impact_slide_mapping
    result = load_impact_slide_mapping()
    # Check a few known partners exist
    assert "GOEX" in result
    assert "Jaggery" in result


def test_load_impact_slide_mapping_values_contain_your_impact():
    """Each slide title should contain 'Your Impact'."""
    from src.data_loader import load_impact_slide_mapping
    result = load_impact_slide_mapping()
    for partner, slide_title in result.items():
        assert "Your Impact" in slide_title or "your impact" in slide_title.lower(), \
            f"Partner '{partner}' has unexpected slide title: '{slide_title}'"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_impact_slide_mapping.py -v`
Expected: FAIL with "cannot import name 'load_impact_slide_mapping'"

- [ ] **Step 3: Add config entry and implement loader**

In `src/data_loader.py`, add to `DATASET_CONFIGS` after the `saved_matches` entry:

```python
    'impact_slide_mapping': {
        'name': 'Impact Slide Mapping',
        'url': 'https://docs.google.com/spreadsheets/d/1MB5Loc4LcxOHF4vHTOFpW_XuwvErGHP7wNGD-nn4OVg',
        'description': 'Partner-to-impact-slide title mapping (human-managed)',
        'spreadsheet_id': '1MB5Loc4LcxOHF4vHTOFpW_XuwvErGHP7wNGD-nn4OVg'
    }
```

Then add the loader function at the end of `data_loader.py`:

```python
@st.cache_data(ttl=300, show_spinner=False)
def load_impact_slide_mapping():
    """
    Load partner-to-impact-slide-title mapping from Google Sheets.

    The sheet has two columns: Partner, Slide Title.
    Header is row 1, data starts row 2.

    Returns:
        dict: {partner_name: slide_title} e.g. {"GOEX": "Apparel -- Your Impact"}
              Returns empty dict on error.
    """
    try:
        client = connect_to_sheets()
        spreadsheet_id = DATASET_CONFIGS['impact_slide_mapping']['spreadsheet_id']
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.worksheet('Sheet1')
        all_values = sheet.get_all_values()

        if not all_values or len(all_values) <= 1:
            return {}

        mapping = {}
        for row in all_values[1:]:  # Skip header
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                partner = row[0].strip()
                slide_title = row[1].strip()
                mapping[partner] = slide_title

        return mapping

    except Exception as e:
        print(f"Error loading impact slide mapping: {e}")
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_impact_slide_mapping.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/data_loader.py tests/test_impact_slide_mapping.py
git commit -m "FEAT: Add Google Sheets loader for impact slide mapping"
```

---

### Task 2: Add resolve_impact_slides function

**Files:**
- Modify: `src/slide_matcher.py` (add new function, keep existing `find_all_impact_slides` unchanged)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_impact_slide_mapping.py`:

```python
def test_resolve_impact_slides_with_matching_titles():
    """resolve_impact_slides matches sheet titles against template slides."""
    from src.slide_matcher import resolve_impact_slides

    # Simulate: sheet says GOEX -> "Apparel -- Your Impact"
    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}

    # Simulate: template has that slide at index 50
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel \u2013 Your Impact"},
        {"slide_index": 100, "slide_title": "Honey Products \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" in result
    assert result["GOEX"]["slide_index"] == 50
    assert result["GOEX"]["slide_title"] == "Apparel \u2013 Your Impact"


def test_resolve_impact_slides_fuzzy_dash_match():
    """resolve_impact_slides handles dash vs em-dash differences."""
    from src.slide_matcher import resolve_impact_slides

    # Sheet uses em dash, template uses regular dash
    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel - Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" in result
    assert result["GOEX"]["slide_index"] == 50


def test_resolve_impact_slides_partner_not_in_sheet():
    """Partners not in the sheet mapping are skipped."""
    from src.slide_matcher import resolve_impact_slides

    sheet_mapping = {"GOEX": "Apparel \u2013 Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["Unknown Partner"], sheet_mapping, template_slides)
    assert "Unknown Partner" not in result


def test_resolve_impact_slides_title_not_in_template():
    """If sheet title doesn't match any template slide, partner is skipped."""
    from src.slide_matcher import resolve_impact_slides

    sheet_mapping = {"GOEX": "Deleted Slide -- Your Impact"}
    template_slides = [
        {"slide_index": 50, "slide_title": "Apparel \u2013 Your Impact"},
    ]

    result = resolve_impact_slides(["GOEX"], sheet_mapping, template_slides)
    assert "GOEX" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_impact_slide_mapping.py::test_resolve_impact_slides_with_matching_titles -v`
Expected: FAIL with "cannot import name 'resolve_impact_slides'"

- [ ] **Step 3: Implement resolve_impact_slides**

Add this function to `src/slide_matcher.py` (after `find_all_impact_slides`, around line 778):

```python
def resolve_impact_slides(
    partners: List[str],
    sheet_mapping: Dict[str, str],
    template_slides: List[Dict]
) -> Dict[str, Dict]:
    """
    Resolve impact slides by matching Google Sheet titles against current template slides.

    Args:
        partners: List of partner names in the proposal
        sheet_mapping: Dict from load_impact_slide_mapping(), e.g. {"GOEX": "Apparel -- Your Impact"}
        template_slides: List from find_all_impact_slides(), e.g. [{"slide_index": 50, "slide_title": "..."}]

    Returns:
        Dict mapping partner to resolved slide info:
        {
            "GOEX": {"slide_index": 50, "slide_title": "Apparel -- Your Impact"}
        }
        Partners with no match are omitted.
    """
    result = {}

    for partner in partners:
        # Look up the expected slide title from the sheet
        expected_title = sheet_mapping.get(partner)
        if not expected_title:
            continue

        # Normalize dashes for comparison (em dash, en dash, regular dash)
        def normalize_dashes(text):
            return text.replace("\u2014", "-").replace("\u2013", "-").replace("\u2012", "-")

        normalized_expected = normalize_dashes(expected_title).lower().strip()

        # Try exact match first (after dash normalization)
        matched_slide = None
        for slide in template_slides:
            normalized_slide = normalize_dashes(slide['slide_title']).lower().strip()
            if normalized_slide == normalized_expected:
                matched_slide = slide
                break

        # Fall back to fuzzy match on title text (handles minor wording changes)
        if not matched_slide:
            best_score = 0
            for slide in template_slides:
                normalized_slide = normalize_dashes(slide['slide_title']).lower().strip()
                score = fuzz.ratio(normalized_expected, normalized_slide)
                if score > best_score:
                    best_score = score
                    matched_slide = slide if score >= 80 else None

        if matched_slide:
            result[partner] = {
                'slide_title': matched_slide['slide_title'],
                'slide_index': matched_slide['slide_index']
            }

    return result
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `python -m pytest tests/test_impact_slide_mapping.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/slide_matcher.py tests/test_impact_slide_mapping.py
git commit -m "FEAT: Add resolve_impact_slides using sheet mapping + template scan"
```

---

### Task 3: Wire up app.py and clean up old code

**Files:**
- Modify: `app.py:2362-2382` (impact slide selection section)
- Modify: `src/slide_matcher.py` (remove `build_impact_slide_map`)
- Modify: `src/match_manager.py` (remove `partner_impact_matches`)

- [ ] **Step 1: Update app.py to use the new function**

Replace the import and map-building block at `app.py:2362-2382`. Change:

```python
        from src.slide_matcher import extract_unique_partners, build_impact_slide_map, find_all_impact_slides
```

to:

```python
        from src.slide_matcher import extract_unique_partners, resolve_impact_slides, find_all_impact_slides
        from src.data_loader import load_impact_slide_mapping
```

Replace the map-building block (lines ~2372-2382):

```python
            # Build dynamic impact slide map from selected template
            pptx_template_for_impacts = get_template_path('all_slides', show_loading=False)
            if pptx_template_for_impacts:
                # Cache map in session state keyed by template name
                selected_template_name = st.session_state.get('selected_pptx_template', {}).get('name', '')
                map_cache_key = f"impact_slide_map_{selected_template_name}"
                if map_cache_key not in st.session_state:
                    st.session_state[map_cache_key] = build_impact_slide_map(pptx_template_for_impacts)
                dynamic_impact_map = st.session_state[map_cache_key]
            else:
                dynamic_impact_map = {}
```

with:

```python
            # Resolve impact slides from Google Sheet mapping + current template
            pptx_template_for_impacts = get_template_path('all_slides', show_loading=False)
            if pptx_template_for_impacts:
                selected_template_name = st.session_state.get('selected_pptx_template', {}).get('name', '')
                map_cache_key = f"impact_slide_map_{selected_template_name}"
                if map_cache_key not in st.session_state:
                    sheet_mapping = load_impact_slide_mapping()
                    template_slides = find_all_impact_slides(pptx_template_for_impacts)
                    st.session_state[map_cache_key] = resolve_impact_slides(unique_partners, sheet_mapping, template_slides)
                dynamic_impact_map = st.session_state[map_cache_key]
            else:
                dynamic_impact_map = {}
```

Also update the generation section (~line 2561-2562) where `gen_impact_map` is built. Change:

```python
                    gen_impact_map_key = f"impact_slide_map_{gen_template_name}"
                    gen_impact_map = st.session_state.get(gen_impact_map_key, {})
```

to:

```python
                    gen_impact_map_key = f"impact_slide_map_{gen_template_name}"
                    if gen_impact_map_key not in st.session_state:
                        sheet_mapping = load_impact_slide_mapping()
                        template_slides = find_all_impact_slides(str(product_template_path))
                        gen_partners = extract_unique_partners(st.session_state.proposal_products)
                        st.session_state[gen_impact_map_key] = resolve_impact_slides(gen_partners, sheet_mapping, template_slides)
                    gen_impact_map = st.session_state.get(gen_impact_map_key, {})
```

Add the missing import at the top of this generation block if not already imported:

```python
                    from src.data_loader import load_impact_slide_mapping
```

- [ ] **Step 2: Remove build_impact_slide_map from slide_matcher.py**

Delete the `build_impact_slide_map` function (lines 441-505) and the associated comment block. Keep `find_all_impact_slides` and `resolve_impact_slides`.

Also delete `match_impact_slides` (lines 587-696) and `match_impact_slides_by_partner` (lines 781-end of that function) -- these are the old fuzzy partner matching functions that are no longer used.

Keep:
- `find_all_impact_slides()` (still needed for template scanning)
- `resolve_impact_slides()` (new function from Task 2)
- `extract_unique_partners()` (still used in app.py)

- [ ] **Step 3: Clean up match_manager.py**

In `src/match_manager.py`, remove all references to `partner_impact_matches`:

- In `load_manual_matches()`: Remove `"partner_impact_matches": {}` from the empty structure and the existence check
- In `save_manual_match()`: Remove the `elif match_category == "partner_impact"` branch
- In `delete_manual_match()`: Remove the `elif match_category == "partner_impact"` branch
- In `get_manual_match()`: Remove the `elif match_category == "partner_impact"` branch
- In `get_all_manual_matches()`: Remove the `elif match_category == "partner_impact"` branch

Since `match_category` is now always `"product"`, simplify all functions to remove the `match_category` parameter entirely. Update function signatures and remove the branching logic.

- [ ] **Step 4: Verify no remaining references to removed functions**

Run:
```bash
grep -rn "build_impact_slide_map\|match_impact_slides_by_partner\|match_impact_slides\b\|partner_impact_matches" --include="*.py" .
```

Expected: No matches (or only in test files / comments that should also be cleaned up).

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add app.py src/slide_matcher.py src/match_manager.py
git commit -m "FEAT: Switch impact slides to Google Sheets mapping, remove old fuzzy matching"
```

---

### Task 4: Manual verification

- [ ] **Step 1: Run the app locally and verify impact slide selection**

Run: `streamlit run app.py`

1. Go to Tab 1 (Proposal Generator)
2. Add products from at least 2 different partners (e.g., GOEX and Jaggery)
3. Scroll to Step 2: Impact Slides
4. Verify: Both partners show "Impact slides found for: GOEX, Jaggery"
5. Expand "Customize Impact Slides" -- verify correct slides are pre-selected
6. Generate a PowerPoint and confirm impact slides appear after each partner's products

- [ ] **Step 2: Commit any fixes if needed**

```bash
git add -u
git commit -m "FIX: Address issues found during impact slide verification"
```
