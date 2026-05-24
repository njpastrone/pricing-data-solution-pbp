# Per-Product Photo Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist per-product photos across sessions using Google Drive, with upload UI in Tab 3 and download UI in Tab 4.

**Architecture:** New `src/drive_helper.py` module handles Google Drive upload/download/delete. Photos are stored in a single Drive folder. File IDs are saved inside each order's existing JSON data in Google Sheets. The existing `template_loader.py` provides the credential pattern to follow.

**Tech Stack:** Python, Streamlit, Google Drive API (`googleapiclient`), `gspread` (existing)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/drive_helper.py` | Create | Google Drive upload/download/delete for photos |
| `src/order_manager.py` | Modify | Add photo upload on save, photo metadata in JSON, photo delete on order delete |
| `app.py` (~line 7516-7546) | Modify | Replace Section 5 per-order photo bucket with per-product photo UI |
| `app.py` (~line 9455-9472) | Modify | Update Tab 4 HTML export to use per-product photo structure |
| `app.py` (~line 61-66) | Modify | Add `drive_helper` imports |

---

### Task 1: Create `src/drive_helper.py` — Google Drive photo operations

**Files:**
- Create: `src/drive_helper.py`

This module handles all Google Drive interactions for photos. It reuses the credential pattern from `src/template_loader.py:27-70` (`get_drive_credentials()`).

- [ ] **Step 1: Create `src/drive_helper.py` with all functions**

```python
"""
Drive Helper Module for PBP Pricing App

Handles uploading, downloading, and deleting product photos in Google Drive.
Photos are stored in a single shared folder. File IDs are stored in order JSON.
"""

import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


# Google Drive folder ID for storing product photos.
# To set up: Create a folder in Drive, share it with the service account email,
# and paste the folder ID here (the long string in the folder's URL).
PHOTO_FOLDER_ID = ""  # User must fill this in after setup


def _get_drive_service():
    """
    Build and return a Google Drive API service using existing credentials.
    Reuses the same credential pattern as template_loader.py.

    Returns:
        googleapiclient.discovery.Resource: Drive API service
    """
    from src.template_loader import get_drive_credentials
    creds = get_drive_credentials()
    return build('drive', 'v3', credentials=creds)


def upload_photo(file_bytes, filename, folder_id=None):
    """
    Upload a photo to Google Drive.

    Args:
        file_bytes (bytes): Raw photo bytes
        filename (str): Name for the file in Drive (e.g., "ORDER_123_Jam_1.png")
        folder_id (str, optional): Drive folder ID. Uses PHOTO_FOLDER_ID if not provided.

    Returns:
        str or None: File ID if successful, None if failed
    """
    folder = folder_id or PHOTO_FOLDER_ID
    if not folder:
        print("Error: PHOTO_FOLDER_ID not configured in drive_helper.py")
        return None

    try:
        service = _get_drive_service()

        # Determine mime type from filename
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
        mime_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        mime_type = mime_map.get(ext, 'image/png')

        file_metadata = {
            'name': filename,
            'parents': [folder]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype=mime_type,
            resumable=False
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    except Exception as e:
        print(f"Error uploading photo '{filename}': {e}")
        return None


def download_photo(file_id):
    """
    Download a photo from Google Drive by file ID.

    Args:
        file_id (str): Google Drive file ID

    Returns:
        bytes or None: Photo bytes if successful, None if failed
    """
    try:
        service = _get_drive_service()

        request = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        return buffer.read()

    except Exception as e:
        print(f"Error downloading photo (file_id={file_id}): {e}")
        return None


def delete_photos(file_ids):
    """
    Delete multiple photos from Google Drive. Best-effort: logs failures
    but does not raise exceptions.

    Args:
        file_ids (list): List of Google Drive file IDs to delete

    Returns:
        int: Number of files successfully deleted
    """
    if not file_ids:
        return 0

    deleted = 0
    try:
        service = _get_drive_service()

        for file_id in file_ids:
            try:
                service.files().delete(fileId=file_id).execute()
                deleted += 1
            except Exception as e:
                print(f"Warning: Could not delete Drive file {file_id}: {e}")

    except Exception as e:
        print(f"Error connecting to Drive for deletion: {e}")

    return deleted
```

- [ ] **Step 2: Verify the module imports correctly**

Run: `cd "/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp" && python -c "from src.drive_helper import upload_photo, download_photo, delete_photos; print('drive_helper imports OK')"`

Expected: `drive_helper imports OK`

- [ ] **Step 3: Commit**

```bash
git add src/drive_helper.py
git commit -m "FEAT: Add drive_helper module for photo upload/download/delete"
```

---

### Task 2: Update `src/order_manager.py` — photo upload on save, delete on order delete

**Files:**
- Modify: `src/order_manager.py:136-195` (save_order function)
- Modify: `src/order_manager.py:274-300` (delete_order function)

The save function needs to upload photos to Drive before serializing order JSON. The delete function needs to clean up Drive photos. Photo data comes in as a dict keyed by product name: `{"Jam": [{"bytes": b"...", "filename": "mockup.png"}, ...]}`. After upload, it's stored in the JSON as: `{"Jam": [{"file_id": "abc123", "filename": "mockup.png"}, ...]}`.

- [ ] **Step 1: Add photo upload helper function to `order_manager.py`**

Add this function after the `generate_order_id()` function (after line 133) in `src/order_manager.py`:

```python
def upload_order_photos(order_id, photos_by_product):
    """
    Upload photos to Google Drive and return file ID metadata.

    Args:
        order_id (str): Order ID for naming files
        photos_by_product (dict): {product_name: [{"bytes": b"...", "filename": "photo.png"}, ...]}

    Returns:
        dict: {product_name: [{"file_id": "abc123", "filename": "photo.png"}, ...]}
    """
    from src.drive_helper import upload_photo

    photo_metadata = {}

    for product_name, photos in photos_by_product.items():
        product_files = []
        # Clean product name for use in filename (remove special characters)
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in product_name).strip()

        for i, photo in enumerate(photos):
            ext = photo['filename'].rsplit('.', 1)[-1].lower() if '.' in photo['filename'] else 'png'
            drive_filename = f"{order_id}_{safe_name}_{i+1}.{ext}"

            file_id = upload_photo(photo['bytes'], drive_filename)
            if file_id:
                product_files.append({
                    'file_id': file_id,
                    'filename': photo['filename']  # Keep original filename for display
                })

        if product_files:
            photo_metadata[product_name] = product_files

    return photo_metadata
```

- [ ] **Step 2: Modify `save_order()` to accept and store photo metadata**

In `src/order_manager.py`, modify the `save_order` function signature (line 136) to accept an optional `photos_by_product` parameter, and add the upload logic before JSON serialization.

Change the function signature from:
```python
def save_order(name, created_by, order_data, dataset):
```
to:
```python
def save_order(name, created_by, order_data, dataset, photos_by_product=None):
```

Then add this block after line 170 (after the `order_id = generate_order_id()` line), before `order_data_serializable = convert_dates_to_strings(order_data)`:

```python
        # Upload photos to Google Drive if any were provided
        if photos_by_product:
            photo_metadata = upload_order_photos(order_id, photos_by_product)
            if photo_metadata:
                order_data['product_photos'] = photo_metadata
```

- [ ] **Step 3: Add photo cleanup helper function**

Add this function after `upload_order_photos()`:

```python
def get_photo_file_ids_from_order(order_data):
    """
    Extract all Drive file IDs from an order's photo metadata.

    Args:
        order_data (dict): Deserialized order data

    Returns:
        list: List of Drive file IDs
    """
    file_ids = []
    product_photos = order_data.get('product_photos', {})
    for product_name, photos in product_photos.items():
        for photo in photos:
            if 'file_id' in photo:
                file_ids.append(photo['file_id'])
    return file_ids
```

- [ ] **Step 4: Modify `delete_order()` to clean up Drive photos**

In `src/order_manager.py`, modify `delete_order()` (line 274). Before deleting the row from the sheet, load the order data and delete associated photos.

Replace the existing `delete_order` function with:

```python
def delete_order(order_id):
    """
    Delete an order from Google Sheets and clean up associated Drive photos.

    Args:
        order_id (str): Unique order ID to delete

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sheet = initialize_orders_sheet()
        if sheet is None:
            return False, "Failed to connect to orders sheet"

        all_values = sheet.get_all_values()

        # Find row with matching order_id
        for i, row in enumerate(all_values[1:], start=2):  # Start at row 2 (skip header)
            if len(row) >= 1 and row[0] == order_id:
                # Try to delete associated photos from Drive (best-effort)
                if len(row) >= 6 and row[5]:
                    try:
                        order_data = json.loads(row[5])
                        file_ids = get_photo_file_ids_from_order(order_data)
                        if file_ids:
                            from src.drive_helper import delete_photos
                            deleted = delete_photos(file_ids)
                            print(f"Deleted {deleted}/{len(file_ids)} photos from Drive")
                    except Exception as e:
                        print(f"Warning: Could not clean up Drive photos: {e}")

                sheet.delete_rows(i)
                return True, "Order deleted successfully"

        return False, "Order not found"

    except Exception as e:
        return False, f"Error deleting order: {str(e)}"
```

- [ ] **Step 5: Verify imports work**

Run: `cd "/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp" && python -c "from src.order_manager import save_order, delete_order, upload_order_photos, get_photo_file_ids_from_order; print('order_manager imports OK')"`

Expected: `order_manager imports OK`

- [ ] **Step 6: Commit**

```bash
git add src/order_manager.py
git commit -m "FEAT: Add photo upload/delete to order save/delete workflow"
```

---

### Task 3: Update Tab 3 UI — per-product photo upload section

**Files:**
- Modify: `app.py:7516-7546` (Section 5: Product Photos)

Replace the current per-order photo bucket with a per-product photo section. Uses `st.session_state.product_photos` (dict keyed by product name) instead of `st.session_state.order_photos` (flat list).

- [ ] **Step 1: Replace Section 5 in Tab 3**

In `app.py`, replace lines 7516-7546 (the entire Product Photos section, from `# PRODUCT PHOTOS` comment through the `st.caption("Photos are stored...")` line) with:

```python
    # ============================================================
    # PRODUCT PHOTOS
    # ============================================================
    st.divider()
    st.header("5. Product Photos")
    st.caption("Upload photos for specific products (e.g., product images, mockups, artwork). Up to 5 photos per product.")

    if 'product_photos' not in st.session_state:
        st.session_state.product_photos = {}  # {product_name: [UploadedFile, ...]}

    if st.session_state.order_items:
        # Dropdown to select which product to upload photos for
        product_names = [item['product'] for item in st.session_state.order_items]
        selected_product = st.selectbox(
            "Select product to upload photos for",
            options=product_names,
            key="photo_product_selector"
        )

        # Show current photo count for selected product
        current_photos = st.session_state.product_photos.get(selected_product, [])
        remaining = 5 - len(current_photos)

        if remaining > 0:
            uploaded_photos = st.file_uploader(
                f"Upload photos for {selected_product} ({remaining} remaining)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key=f"photo_uploader_{selected_product}"
            )

            if uploaded_photos:
                # Add new photos up to the cap of 5
                existing = st.session_state.product_photos.get(selected_product, [])
                space_left = 5 - len(existing)
                new_photos = uploaded_photos[:space_left]

                if new_photos:
                    st.session_state.product_photos[selected_product] = existing + new_photos
                    if len(uploaded_photos) > space_left:
                        st.warning(f"Only added {space_left} photo(s) - maximum 5 per product reached.")
        else:
            st.info(f"{selected_product} already has 5 photos (maximum).")

        # Display photos for selected product
        current_photos = st.session_state.product_photos.get(selected_product, [])
        if current_photos:
            st.markdown(f"**{selected_product}** - {len(current_photos)} photo(s):")
            cols = st.columns(min(len(current_photos), 4))
            for i, photo in enumerate(current_photos):
                with cols[i % 4]:
                    photo.seek(0)
                    st.image(photo, caption=photo.name, use_column_width=True)

        # Summary of all products with photos
        products_with_photos = {k: v for k, v in st.session_state.product_photos.items() if v}
        if products_with_photos:
            st.divider()
            st.markdown("**Photo Summary:**")
            for prod_name, photos in products_with_photos.items():
                st.caption(f"- {prod_name}: {len(photos)} photo(s)")
        else:
            st.caption("No photos uploaded yet.")

        if st.session_state.product_photos:
            st.caption("Photos will be saved to Google Drive when you save the order.")
        else:
            st.caption("Photos are stored for this session only until the order is saved.")
    else:
        st.info("Add products to your order first, then you can upload photos for each product.")
```

- [ ] **Step 2: Update the save_order calls in Tab 3 to pass photo data**

There are two `save_order()` calls in Tab 3's save section (around lines 7881 and 7899). Both need to pass the photo data.

Before the `save_order()` call near line 7881, add this block to prepare photo bytes:

```python
                # Prepare photos for upload to Drive
                photos_for_upload = {}
                for prod_name, photos in st.session_state.get('product_photos', {}).items():
                    if photos:
                        photo_list = []
                        for photo in photos:
                            photo.seek(0)
                            photo_list.append({
                                'bytes': photo.read(),
                                'filename': photo.name
                            })
                        photos_for_upload[prod_name] = photo_list
```

Then update both `save_order()` calls to include `photos_by_product=photos_for_upload`:

```python
                success, message, result = save_order(
                    name=order_name.strip(),
                    created_by=created_by.strip() if created_by else "",
                    order_data=order_data,
                    dataset=st.session_state.selected_dataset,
                    photos_by_product=photos_for_upload if photos_for_upload else None
                )
```

Do the same for the second `save_order()` call (the versioned name fallback around line 7899).

- [ ] **Step 3: Update the save_order calls in the sidebar quick-save (around line 4494)**

Same pattern — prepare `photos_for_upload` dict and pass to `save_order()`. Add the photo preparation block before the `save_order()` call at line 4494 and update the call to include `photos_by_product=photos_for_upload if photos_for_upload else None`.

- [ ] **Step 4: Load photo metadata when loading an order**

When an order is loaded (around lines 4580-4628 in the Tab 3 load section), the `product_photos` metadata is already inside the loaded `order_data` dict under the key `product_photos`. After the order data is loaded into session state, add:

```python
                                # Load photo metadata from saved order (actual photos downloaded on-demand)
                                saved_photos = order_data.get('product_photos', {})
                                if saved_photos:
                                    st.session_state.product_photos = {}
                                    st.session_state.product_photo_metadata = saved_photos  # {product: [{file_id, filename}]}
                                else:
                                    st.session_state.product_photos = {}
                                    st.session_state.product_photo_metadata = {}
```

Do the same for the sidebar load section (around lines 872-977).

- [ ] **Step 5: Verify the app starts without errors**

Run: `cd "/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp" && python -c "import app; print('app imports OK')" 2>&1 | head -5`

Note: This may show Streamlit-specific warnings, that's OK. The key is no ImportError or SyntaxError.

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "FEAT: Replace per-order photo bucket with per-product photo upload UI in Tab 3"
```

---

### Task 4: Update Tab 4 UI — per-product photo display with download buttons

**Files:**
- Modify: `app.py:9455-9472` (Tab 4 HTML export photo section)
- Modify: `app.py` (Tab 4 order review area — add photo thumbnails + download buttons)

- [ ] **Step 1: Add photo display with download buttons in Tab 4 order review**

Find the Tab 4 area where products are listed for review. After each product's details, add a section to display photos. Look for where order items are iterated in Tab 4 and add this pattern after each product's details:

```python
                    # Show product photos if available
                    product_photos_meta = st.session_state.get('product_photo_metadata', {})
                    product_photos_session = st.session_state.get('product_photos', {})
                    
                    # Check session photos first (current session uploads), then saved metadata
                    if item['product'] in product_photos_session and product_photos_session[item['product']]:
                        photos = product_photos_session[item['product']]
                        photo_cols = st.columns(min(len(photos), 4))
                        for pi, photo in enumerate(photos):
                            with photo_cols[pi % 4]:
                                photo.seek(0)
                                st.image(photo, caption=photo.name, use_column_width=True)
                                photo.seek(0)
                                st.download_button(
                                    label=f"Download",
                                    data=photo.read(),
                                    file_name=photo.name,
                                    key=f"dl_photo_{item['product']}_{pi}"
                                )
                    elif item['product'] in product_photos_meta:
                        # Download from Drive on-demand
                        photos_meta = product_photos_meta[item['product']]
                        if photos_meta:
                            photo_cols = st.columns(min(len(photos_meta), 4))
                            for pi, meta in enumerate(photos_meta):
                                with photo_cols[pi % 4]:
                                    from src.drive_helper import download_photo
                                    photo_bytes = download_photo(meta['file_id'])
                                    if photo_bytes:
                                        st.image(photo_bytes, caption=meta['filename'], use_column_width=True)
                                        st.download_button(
                                            label=f"Download",
                                            data=photo_bytes,
                                            file_name=meta['filename'],
                                            key=f"dl_drive_photo_{item['product']}_{pi}"
                                        )
                                    else:
                                        st.caption(f"Could not load: {meta['filename']}")
```

Note: The exact location depends on the Tab 4 product iteration loop. Search for the area where `item['product']` is displayed in Tab 4 and add the photo display block after each product's information.

- [ ] **Step 2: Update HTML export to use per-product photo structure**

In `app.py`, replace lines 9455-9472 (the current HTML photo embedding code) with:

```python
        # Add product photos if any exist (per-product structure)
        product_photos_meta = st.session_state.get('product_photo_metadata', {})
        product_photos_session = st.session_state.get('product_photos', {})
        
        has_any_photos = bool(product_photos_session) or bool(product_photos_meta)
        
        if has_any_photos:
            import base64
            html_invoice += """
    <h3>Product Photos</h3>"""
            
            # Collect all product names that have photos
            all_photo_products = set(
                list(product_photos_session.keys()) + list(product_photos_meta.keys())
            )
            
            for prod_name in sorted(all_photo_products):
                html_invoice += f"""
    <h4>{prod_name}</h4>"""
                
                # Try session photos first (current session uploads)
                if prod_name in product_photos_session and product_photos_session[prod_name]:
                    for photo in product_photos_session[prod_name]:
                        photo.seek(0)
                        photo_bytes = photo.read()
                        b64 = base64.b64encode(photo_bytes).decode()
                        ext = photo.name.rsplit('.', 1)[-1].lower()
                        mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp'}
                        mime_type = mime_map.get(ext, 'image/png')
                        html_invoice += f"""
    <div style="margin-bottom: 20px;">
        <p style="font-weight: bold; margin-bottom: 5px;">{photo.name}</p>
        <img src="data:{mime_type};base64,{b64}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 4px;" />
    </div>"""
                
                # Fall back to Drive photos (loaded from saved order)
                elif prod_name in product_photos_meta:
                    for meta in product_photos_meta[prod_name]:
                        from src.drive_helper import download_photo
                        photo_bytes = download_photo(meta['file_id'])
                        if photo_bytes:
                            b64 = base64.b64encode(photo_bytes).decode()
                            ext = meta['filename'].rsplit('.', 1)[-1].lower()
                            mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp'}
                            mime_type = mime_map.get(ext, 'image/png')
                            html_invoice += f"""
    <div style="margin-bottom: 20px;">
        <p style="font-weight: bold; margin-bottom: 5px;">{meta['filename']}</p>
        <img src="data:{mime_type};base64,{b64}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 4px;" />
    </div>"""
```

- [ ] **Step 3: Add `drive_helper` import at top of `app.py`**

At `app.py:61-66`, add the import. Change:

```python
from src.order_manager import (
    save_order,
    load_all_orders,
    load_order_data,
    delete_order
)
```

to:

```python
from src.order_manager import (
    save_order,
    load_all_orders,
    load_order_data,
    delete_order
)
# drive_helper is imported inline where needed (download_photo in Tab 4)
```

No top-level import needed for `drive_helper` since it's imported inline only in Tab 4 to avoid loading Drive API unnecessarily.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "FEAT: Add per-product photo display and download buttons in Tab 4"
```

---

### Task 5: Clean up old `order_photos` session state references

**Files:**
- Modify: `app.py` (multiple locations)

The old `order_photos` session state key is no longer used. Clean up any remaining references.

- [ ] **Step 1: Search for and remove old `order_photos` references**

Search for `order_photos` in `app.py`. The Section 5 replacement (Task 3) already removed the main usage. Check for any remaining references:

- Initialization code (e.g., `if 'order_photos' not in st.session_state`)
- Order loading code that might set `order_photos`
- Any other UI code referencing `order_photos`

Remove or replace each occurrence. If there are initialization blocks like:
```python
if 'order_photos' not in st.session_state:
    st.session_state.order_photos = []
```
Replace with:
```python
if 'product_photos' not in st.session_state:
    st.session_state.product_photos = {}
if 'product_photo_metadata' not in st.session_state:
    st.session_state.product_photo_metadata = {}
```

Only add the initialization if it doesn't already exist from Task 3.

- [ ] **Step 2: Verify no `order_photos` references remain**

Run: `grep -n "order_photos" app.py`

Expected: No output (all references removed).

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "FIX: Remove old per-order photo references, use per-product photo state"
```

---

### Task 6: Manual testing and final verification

**Files:** None (testing only)

- [ ] **Step 1: Verify the app starts cleanly**

Run: `cd "/Users/nicolopastrone/Desktop/Development Projects/pricing-data-solution-pbp" && streamlit run app.py`

Open in browser. Check:
- No errors on page load
- Tab 3 Section 5 shows the product dropdown (after adding a product)
- Upload works and shows thumbnails
- Photo summary shows correct counts

- [ ] **Step 2: Test the full save/load cycle (requires PHOTO_FOLDER_ID to be configured)**

1. Add products in Tab 3
2. Upload photos for 2 different products
3. Save the order
4. Refresh the page (new session)
5. Load the saved order
6. Verify photos appear in Tab 4 with download buttons
7. Delete the order
8. Verify photos are cleaned up from Drive

- [ ] **Step 3: Test edge cases**

- Upload 6 photos for one product — verify only 5 are accepted with warning
- Save an order with no photos — verify it works exactly as before
- Load an old order (saved before this feature) — verify no errors (graceful fallback)

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "FIX: Address issues found during manual testing"
```
