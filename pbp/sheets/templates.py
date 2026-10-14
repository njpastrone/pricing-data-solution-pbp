"""
PowerPoint templates from Google Drive, downloaded once per process.

The Streamlit app downloads the 43 MB "All Slides" deck into every browser
session. Here a template is fetched once into TEMPLATE_CACHE_DIR and reused
by every request until the file changes in Drive (the modified time is part
of the cached file name).
"""

import io
import re
import threading
import time

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials

from pbp import settings
from pbp.sheets import gateway

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
LIST_CACHE_SECONDS = 300

_lock = threading.Lock()
_list_cache = {"loaded_at": 0.0, "templates": []}
_mapping_cache = {"loaded_at": 0.0, "mapping": None}


def _drive():
    creds = Credentials.from_service_account_info(settings.service_account_info(), scopes=gateway.SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_templates(force=False):
    """[{'name', 'file_id', 'modified_time'}] of the decks in the templates folder, newest first."""
    with _lock:
        if _list_cache["templates"] and not force and time.time() - _list_cache["loaded_at"] < LIST_CACHE_SECONDS:
            return _list_cache["templates"]
    query = f"'{settings.TEMPLATE_FOLDER_ID}' in parents and mimeType='{PPTX_MIME}' and trashed=false"
    result = _drive().files().list(q=query, includeItemsFromAllDrives=True, supportsAllDrives=True,
                                   fields="files(id, name, modifiedTime)", orderBy="modifiedTime desc").execute()
    templates = [{"name": f["name"], "file_id": f["id"], "modified_time": f.get("modifiedTime", "")} for f in result.get("files", [])]
    with _lock:
        _list_cache.update(loaded_at=time.time(), templates=templates)
    return templates


def template_path(template):
    """Local path of a template dict from list_templates(), downloading it on first use."""
    settings.TEMPLATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = re.sub(r"[^0-9A-Za-z]", "", template.get("modified_time", ""))
    path = settings.TEMPLATE_CACHE_DIR / f"{template['file_id']}_{stamp}.pptx"
    if path.exists() and path.stat().st_size > 0:
        return path
    request = _drive().files().get_media(fileId=template["file_id"])
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    if not buffer.getvalue():
        raise RuntimeError(f"Downloaded template '{template['name']}' is empty")
    tmp = path.with_suffix(".part")
    tmp.write_bytes(buffer.getvalue())
    tmp.replace(path)
    return path


def intro_outro_path():
    """The intro/outro deck, committed in the repo."""
    return settings.INTRO_OUTRO_TEMPLATE


def impact_slide_mapping(force=False):
    """{partner: impact slide title} from the human-managed mapping sheet, cached five minutes."""
    with _lock:
        if _mapping_cache["mapping"] is not None and not force and time.time() - _mapping_cache["loaded_at"] < LIST_CACHE_SECONDS:
            return _mapping_cache["mapping"]
    mapping = {}
    try:
        sheet = gateway.open_worksheet(settings.IMPACT_SLIDE_MAPPING_SHEET_ID, "Sheet1")
        for row in gateway.retry_on_quota(sheet.get_all_values)[1:]:
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                mapping[row[0].strip()] = row[1].strip()
    except Exception as e:
        print(f"Error loading impact slide mapping: {e}")
    with _lock:
        _mapping_cache.update(loaded_at=time.time(), mapping=mapping)
    return mapping
