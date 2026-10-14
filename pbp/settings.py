"""
Environment-driven settings shared by the pbp package and the web app.

Everything has a default that matches production, so a plain `uvicorn` run
behaves like the live app. Override with environment variables to point a
local run at a copy of a spreadsheet instead of the production one.
"""

import hashlib
import json
import os
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Spreadsheets the client order form reads and writes
SAVED_PROPOSALS_SHEET_ID = os.getenv("PBP_SAVED_PROPOSALS_SHEET_ID", "1njImhHbLM6WwmdwobgJ0UQLj-4GdOgPYnjP7nDCFTb4")
SAVED_ORDERS_SHEET_ID = os.getenv("PBP_SAVED_ORDERS_SHEET_ID", "1pXqBAQOeSvQi1ob8GLc70UhQsM0gwmczYfVWFRPjbao")
FORM_RESPONSES_SHEET_ID = os.getenv("PBP_FORM_RESPONSES_SHEET_ID", "1MYpwnb9L0EC0XnsaLSEuaaJrsjGydcQbpuF1-3vlDSA")
FORM_RESPONSES_SHEET_NAME = os.getenv("PBP_FORM_RESPONSES_SHEET_NAME", "Form Responses 1")
SAVED_MATCHES_SHEET_ID = os.getenv("PBP_SAVED_MATCHES_SHEET_ID", "1cU5CW0ydE1BXDjy3TNkbm4TohZ9CA8jR6h4zQPY_9Io")
IMPACT_SLIDE_MAPPING_SHEET_ID = os.getenv("PBP_IMPACT_SLIDE_MAPPING_SHEET_ID", "1MB5Loc4LcxOHF4vHTOFpW_XuwvErGHP7wNGD-nn4OVg")

# Google Drive folder holding the "All Slides" PowerPoint templates (same variable the Streamlit app reads)
TEMPLATE_FOLDER_ID = os.getenv("TEMPLATE_FOLDER_ID", "1NRGfKlBZNHLmWdD39ppcWbdY8HHXIYv6")
INTRO_OUTRO_TEMPLATE = REPO_ROOT / "templates" / "Intro_Outro_Slides_PbP_Proposals.pptx"
# Where downloaded templates are kept for the life of the process
TEMPLATE_CACHE_DIR = pathlib.Path(os.getenv("PBP_TEMPLATE_CACHE_DIR", "/tmp/pbp-templates"))

# Where Tab 2 of the Streamlit app points client form links (phase 1 cutover switch)
CLIENT_FORM_BASE_URL = os.getenv("CLIENT_FORM_BASE_URL", "https://pbp-order-management-system.onrender.com/")

# How often the web app re-tries copying received orders into Form Responses (0 disables the loop)
SYNC_LOOP_SECONDS = int(os.getenv("PBP_SYNC_LOOP_SECONDS", "60"))

# Staff login (same shared password as the Streamlit app; "pbp2026" is the legacy local fallback, flagged for removal)
APP_PASSWORD = os.getenv("APP_PASSWORD") or "pbp2026"
# Signs the staff session cookie; defaults to a value derived from the password so no new secret is needed
SECRET_KEY = os.getenv("PBP_SECRET_KEY") or hashlib.sha256(("pbp-web:" + APP_PASSWORD).encode()).hexdigest()
SESSION_DAYS = 30

# PBP_DEMO=1 runs the whole app against in-memory sample data (no Google Sheets or Drive); see pbp/demo.py
DEMO = os.getenv("PBP_DEMO", "").strip().lower() in ("1", "true", "yes")


def _secrets_toml():
    """The local .streamlit/secrets.toml as a dict ({} when there is none)."""
    for secrets_path in (REPO_ROOT / ".streamlit" / "secrets.toml", pathlib.Path.home() / ".streamlit" / "secrets.toml"):
        if secrets_path.exists():
            import tomllib
            return tomllib.loads(secrets_path.read_text())
    return {}


def setting(name, default=""):
    """A setting from an environment variable (Render), falling back to .streamlit/secrets.toml."""
    value = os.getenv(name)
    if value is None:
        value = _secrets_toml().get(name)
    value = str(value).strip() if value is not None else ""
    return value or default


_GCP_KEYS = [
    "type", "project_id", "private_key_id", "private_key", "client_email", "client_id",
    "auth_uri", "token_uri", "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain",
]


def service_account_info():
    """
    Google service-account credentials as a dict, from the first source found:
    1. GCP_* environment variables (how Render is configured)
    2. GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    3. .streamlit/secrets.toml, [gcp_service_account] table (local development)
    """
    if os.getenv("GCP_PROJECT_ID"):
        info = {key: os.getenv("GCP_" + key.upper()) for key in _GCP_KEYS}
        # Environment variables lose real newlines in the private key
        info["private_key"] = (info["private_key"] or "").replace("\\n", "\n")
        return info

    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if json_path:
        with open(json_path) as handle:
            return json.load(handle)

    secrets = _secrets_toml()
    if "gcp_service_account" in secrets:
        return secrets["gcp_service_account"]

    raise RuntimeError(
        "No Google Cloud credentials found. Set the GCP_* environment variables, "
        "GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json, or create .streamlit/secrets.toml"
    )
