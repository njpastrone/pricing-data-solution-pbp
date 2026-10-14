# pbp/ - shared core package

Phase 0 of the Streamlit migration moved the pricing engine, helpers, PowerPoint
generator, slide matcher, forms helper/config, manual-match storage (`pbp/core/`)
and photo storage (`pbp/sheets/`) here so the Streamlit app and the future
FastAPI app can both import them. Phase 0 only moved files and changed imports.

## Layout

- `pbp/settings.py`: environment-driven configuration (spreadsheet IDs with env overrides, `CLIENT_FORM_BASE_URL`, credentials lookup).
- `pbp/sheets/gateway.py`: the one Google Sheets connection, cached worksheet handles, quota back-off. Both apps use it.
- `pbp/sheets/client_form.py`: client order form logic (drafts, submit, backup-then-sync). Framework-free since phase 1.
- `pbp/web/`: the FastAPI + HTMX app. Phase 1 serves the client order form; later phases add staff screens.

## Known remaining Streamlit coupling

- `pbp/core/slide_matcher.py` imports `get_confirmed_match` from
  `src.match_memory` (which imports streamlit) inside `find_match`. If that
  lookup fails it logs a warning and falls back to manual/automatic matching.
  Phase 3 moves confirmed-match storage into `pbp/sheets/`.
