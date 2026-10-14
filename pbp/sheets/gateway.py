"""
One Google Sheets connection per process.

- connect(): authorises once and reuses the client
- open_worksheet(): opens each worksheet once and reuses the handle (an open
  costs two read requests against a 60-per-minute quota)
- retry_on_quota(): waits and retries when Google answers HTTP 429

Nothing here depends on Streamlit, so both the Streamlit app and the web app
can use it.
"""

import threading
import time
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from pbp import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Seconds between attempts when Google says "quota exceeded"
QUOTA_RETRY_WAITS = [2, 4, 8, 16]

_lock = threading.Lock()
_client = None
_worksheets = {}

# Health information for /internal/health
state = {"last_ok_at": None, "last_error": None, "last_error_at": None}


def connect():
    """Authorised gspread client, created on first use."""
    global _client
    with _lock:
        if _client is None:
            creds = Credentials.from_service_account_info(settings.service_account_info(), scopes=SCOPES)
            _client = gspread.authorize(creds)
        return _client


def retry_on_quota(action):
    """
    Run action(); if Google says "quota exceeded" (HTTP 429), wait and retry.

    A 429 means Google rejected the request without applying it, so retrying
    a write (like append_row) cannot create a duplicate row.
    """
    for wait in QUOTA_RETRY_WAITS + [None]:
        try:
            result = action()
            state["last_ok_at"] = datetime.now().isoformat(timespec="seconds")
            return result
        except gspread.exceptions.APIError as e:
            if getattr(e, "code", None) != 429 or wait is None:
                state["last_error"] = str(e)
                state["last_error_at"] = datetime.now().isoformat(timespec="seconds")
                raise
            print(f"Google Sheets quota hit, retrying in {wait}s")
            time.sleep(wait)
        except Exception as e:
            state["last_error"] = str(e)
            state["last_error_at"] = datetime.now().isoformat(timespec="seconds")
            raise


# ponytail: handles are cached until the process restarts; a renamed tab needs a restart
def open_worksheet(spreadsheet_id, sheet_name, create_with_headers=None):
    """
    Open a worksheet once and reuse it.

    If create_with_headers is given and the tab does not exist, it is created
    with that header row.
    """
    key = (spreadsheet_id, sheet_name)
    with _lock:
        if key in _worksheets:
            return _worksheets[key]
    spreadsheet = retry_on_quota(lambda: connect().open_by_key(spreadsheet_id))
    try:
        sheet = retry_on_quota(lambda: spreadsheet.worksheet(sheet_name))
    except gspread.exceptions.WorksheetNotFound:
        if not create_with_headers:
            raise
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=len(create_with_headers))
        last_column = chr(ord("A") + len(create_with_headers) - 1)
        sheet.update(f"A1:{last_column}1", [create_with_headers])
    with _lock:
        _worksheets[key] = sheet
    return sheet


def reset():
    """Forget the cached client and worksheets (used by tests)."""
    global _client
    with _lock:
        _client = None
        _worksheets.clear()
