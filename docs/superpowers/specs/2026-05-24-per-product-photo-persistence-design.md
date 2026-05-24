# Per-Product Photo Persistence via Google Drive

**Date:** 2026-05-24
**Status:** Approved
**Version:** 1.0

## Problem

Users upload product photos in Tab 3 but they only persist for the current session. Photos need to survive across sessions (saved/loaded with orders) so users can download specific photos in Tab 4 to attach to POs or invoices.

## Design

### Storage: Google Drive

- All photos stored in a single shared Google Drive folder
- File naming: `{order_id}_{product_name}_{index}.{ext}`
- File IDs stored in the order's JSON data (inside the existing `Order_Data_JSON` cell in Google Sheets)
- No new Sheets columns needed
- Uses the same service account credentials (Drive scope already authorized in `data_loader.py`)

### New Module: `src/drive_helper.py`

Functions:
- `ensure_folder_exists()` — creates the shared folder on first use, returns folder ID
- `upload_photo(file_bytes, filename, folder_id)` — uploads a photo, returns file ID
- `download_photo(file_id)` — downloads photo bytes by file ID
- `delete_photos(file_ids)` — deletes multiple photos (best-effort, logs failures)

Folder ID stored as a constant after first creation.

### Order Manager Changes (`src/order_manager.py`)

- **Save:** Before serializing order JSON, upload any session photos to Drive. Store file IDs in product data under `"photos": [{"file_id": "abc123", "filename": "mockup.png"}, ...]`
- **Load:** Return photo metadata (file IDs + filenames) with order data. Actual photo bytes downloaded on-demand in UI.
- **Delete:** Delete associated Drive photos when an order is deleted. If Drive deletion fails, log but don't block order deletion.

### Tab 3 UI (Upload)

- Replace current "Section 5: Product Photos" (per-order bucket) with per-product photo section
- Dropdown to select which product to upload photos for
- `st.file_uploader` with `accept_multiple_files=True`, image types only (png, jpg, jpeg, webp)
- Thumbnails shown in grid (up to 4 columns) with product name label
- Summary below showing all products with photos (e.g., "Jam: 2 photos, Tote Bag: 1 photo")
- Photos stored in `st.session_state` keyed by product name until order is saved
- Cap: 5 photos per product

### Tab 4 UI (Download)

- Each product with photos shows thumbnails below product details
- Individual `st.download_button` per photo with original filename
- Photos downloaded from Drive on-demand (not all at once on page load)
- Existing HTML export continues embedding photos inline (current behavior)
- No changes to CSV export

### Edge Cases

- **Order deletion:** Drive photos deleted too (best-effort)
- **Re-saving as new version:** New order gets its own photo copies. Old order keeps its photos.
- **No photos:** Zero changes to existing flow. Feature is purely additive.
- **Session-only:** If user uploads but never saves, photos stay in session state only (no Drive upload)
- **Manual setup required:** Google Drive API must be enabled in Google Cloud Console. A shared folder must be created and its ID configured.

## Manual Setup Steps (User)

1. Go to Google Cloud Console > APIs & Services > Enable APIs
2. Enable "Google Drive API" (same project as Google Sheets)
3. Create a folder in Google Drive
4. Share the folder with the service account email (editor access)
5. Copy the folder ID (from the URL) into `src/drive_helper.py`

## Files Changed

| File | Change |
|------|--------|
| `src/drive_helper.py` | New module — Drive upload/download/delete |
| `src/order_manager.py` | Photo upload on save, metadata in JSON, delete on order delete |
| `app.py` (Tab 3) | Replace Section 5 with per-product photo UI |
| `app.py` (Tab 4) | Add per-product photo thumbnails + download buttons |
| `requirements.txt` | No changes (google-api-python-client already included) |
