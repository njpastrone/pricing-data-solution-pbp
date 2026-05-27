# Impact Slide Cloud Storage

**Date:** 2026-05-27
**Status:** Approved
**Version:** 8.5.0

## Problem

Impact slide matching for PowerPoint generation relies on:
1. A hardcoded partner list in `build_impact_slide_map()` (slide_matcher.py:464)
2. Fuzzy matching between partner names and slide title text (unreliable -- partner names often don't match slide titles)
3. Local-only JSON storage for manual overrides (`data/manual_matches.json`) that resets on deploy

This means impact slides can be wrong or missing with no easy way to fix them persistently.

## Solution

Store the partner-to-impact-slide mapping in a dedicated Google Sheet that humans manage directly. At PowerPoint generation time, the app reads the mapping and resolves slide indices dynamically from the current template.

## Data Storage

**Spreadsheet:** `impact_slide_matches` (ID: `1MB5Loc4LcxOHF4vHTOFpW_XuwvErGHP7wNGD-nn4OVg`)

Two columns, manually maintained:

| Partner | Slide Title |
|---------|-------------|
| GOEX | Apparel -- Your Impact |
| Gronn | Upcycled Glasses -- Your Impact |
| Homeless Garden Project | Spa & Food Gifts -- Your Impact |
| Hon's Honey | Honey Products -- Your Impact |
| Itza Wood | Wood Gifts -- Your Impact |
| Jaggery | Good Felt, ReDenim, and Upcycled Bags -- Your Impact |
| Work + Shelter | Sewn Goods -- Your Impact |

No Slide Index or Template Name columns -- indices change monthly with new templates and are resolved dynamically at generation time.

## Resolution Flow (at PowerPoint generation time)

1. Load the mapping from Google Sheets (cached like other data)
2. Scan the current template with existing `find_all_impact_slides()` to get all "Your Impact" slides + their current indices
3. For each partner in the proposal, look up their Slide Title from the sheet
4. Find that title in the scanned template slides to get the current index
5. Exact string match first, fall back to fuzzy match on title text (handles minor dash formatting differences like -- vs --)
6. If no match found, skip the impact slide for that partner

## Code Changes

### `src/data_loader.py`
- Add `impact_slide_mapping` to `DATASET_CONFIGS` with spreadsheet ID
- Add `load_impact_slide_mapping()` function to read Sheet1 and return a dict of `{partner: slide_title}`
- Cache with `@st.cache_data(ttl=300)` (5 minutes, same as other data)

### `src/slide_matcher.py`
- Replace `build_impact_slide_map()` with `resolve_impact_slides(partners, template_path)` that:
  1. Calls `load_impact_slide_mapping()` to get partner -> slide title from Google Sheets
  2. Calls `find_all_impact_slides(template_path)` to get current template slides + indices
  3. Matches by title text to resolve indices
- Remove the hardcoded `known_partners` list
- Remove or simplify `match_impact_slides_by_partner()` (no longer needed for fuzzy partner matching)

### `src/match_manager.py`
- Remove `partner_impact_matches` from JSON structure (no longer used)

### `src/pptx_generator.py`
- No changes -- still receives `{partner: {slide_index, slide_title}}` dict

### `find_all_impact_slides()`
- No changes -- still scans template for "Your Impact" text

## What This Enables

- Colleague can edit the Google Sheet directly to add/fix mappings as templates evolve
- No code changes needed when partners or slide titles change
- Reliable matching every time (no fuzzy guessing between partner names and slide categories)
- Survives deploys (cloud storage)
- Partners are no longer hardcoded
