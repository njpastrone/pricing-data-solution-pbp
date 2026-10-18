# pbp/ - shared core package

Phase 0 of the Streamlit migration moved the pricing engine, helpers, PowerPoint
generator, slide matcher, forms helper/config, manual-match storage (`pbp/core/`)
and photo storage (`pbp/sheets/`) here so the Streamlit app and the future
FastAPI app can both import them. Phase 0 only moved files and changed imports.

## Known phase-1 work (still Streamlit-coupled)

- `pbp/sheets/drive_helper.py` imports `connect_to_sheets` and `DATASET_CONFIGS`
  from `src.data_loader`, which uses `st.cache_resource` / `st.secrets`.
  Phase 1 moves the Sheets connection into `pbp/sheets/`.
- `pbp/core/slide_matcher.py` imports `get_confirmed_match` from
  `src.match_memory` (which imports streamlit) inside `find_match`. If that
  lookup fails it logs a warning and falls back to manual/automatic matching.
  Phase 1 moves confirmed-match storage into `pbp/sheets/`.
- `pbp/core/forms_helper.py` imports `STATUS_PENDING` from `src.client_form`
  (which imports streamlit). Phase 1 moves `client_form` into `pbp/sheets/`.

Until these are done, importing these three modules pulls in Streamlit.
