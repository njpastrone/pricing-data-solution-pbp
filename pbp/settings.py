"""
Environment-driven settings shared by the pbp package and the web app.

Everything has a default that matches production, so a plain `uvicorn` run
behaves like the live app. Override with environment variables to point a
local run at a copy of a spreadsheet instead of the production one.
"""

import json
import os
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Spreadsheets the client order form reads and writes
SAVED_PROPOSALS_SHEET_ID = os.getenv("PBP_SAVED_PROPOSALS_SHEET_ID", "1njImhHbLM6WwmdwobgJ0UQLj-4GdOgPYnjP7nDCFTb4")
SAVED_ORDERS_SHEET_ID = os.getenv("PBP_SAVED_ORDERS_SHEET_ID", "1pXqBAQOeSvQi1ob8GLc70UhQsM0gwmczYfVWFRPjbao")
FORM_RESPONSES_SHEET_ID = os.getenv("PBP_FORM_RESPONSES_SHEET_ID", "1MYpwnb9L0EC0XnsaLSEuaaJrsjGydcQbpuF1-3vlDSA")
FORM_RESPONSES_SHEET_NAME = os.getenv("PBP_FORM_RESPONSES_SHEET_NAME", "Form Responses 1")

# Where Tab 2 of the Streamlit app points client form links (phase 1 cutover switch)
CLIENT_FORM_BASE_URL = os.getenv("CLIENT_FORM_BASE_URL", "https://pbp-order-management-system.onrender.com/")

# How often the web app re-tries copying received orders into Form Responses (0 disables the loop)
SYNC_LOOP_SECONDS = int(os.getenv("PBP_SYNC_LOOP_SECONDS", "60"))

# Largest drop-shipping file the client form accepts (bytes)
MAX_UPLOAD_BYTES = int(os.getenv("PBP_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

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

    for secrets_path in (REPO_ROOT / ".streamlit" / "secrets.toml", pathlib.Path.home() / ".streamlit" / "secrets.toml"):
        if secrets_path.exists():
            import tomllib
            return tomllib.loads(secrets_path.read_text())["gcp_service_account"]

    raise RuntimeError(
        "No Google Cloud credentials found. Set the GCP_* environment variables, "
        "GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json, or create .streamlit/secrets.toml"
    )
