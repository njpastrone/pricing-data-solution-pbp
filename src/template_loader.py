"""
Template Loader Module for PBP Pricing App

Handles downloading PowerPoint templates from Google Drive on-demand.
Supports dynamic template discovery (multiple product slide templates).
Templates are cached in session state to avoid repeated downloads.
"""

import streamlit as st
import io
import tempfile
import os
from pathlib import Path


# PowerPoint template configuration (intro/outro only - product templates are discovered dynamically)
TEMPLATE_CONFIG = {
    'intro_outro': {
        'name': 'Intro_Outro_Slides_PbP_Proposals.pptx',
        'local_path': 'templates/Intro_Outro_Slides_PbP_Proposals.pptx',  # Keep local (2.5MB, not a problem)
        'description': 'Intro and outro slides',
        'cache_key': 'pptx_template_intro_outro'
    }
}


def get_drive_credentials():
    """
    Get Google Drive credentials from environment variables or Streamlit secrets.
    Returns credentials object ready for Drive API.
    """
    import os
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Try environment variables first (Render deployment)
    if os.getenv("GCP_PROJECT_ID"):
        # Fix private key newlines
        private_key = os.getenv("GCP_PRIVATE_KEY", "").replace("\\n", "\n")

        creds_info = {
            "type": os.getenv("GCP_TYPE"),
            "project_id": os.getenv("GCP_PROJECT_ID"),
            "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("GCP_CLIENT_EMAIL"),
            "client_id": os.getenv("GCP_CLIENT_ID"),
            "auth_uri": os.getenv("GCP_AUTH_URI"),
            "token_uri": os.getenv("GCP_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN")
        }
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return creds

    # Fall back to Streamlit secrets (local development)
    try:
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
            return creds
    except Exception:
        pass

    raise Exception("No Google Cloud credentials found")


def find_file_in_drive(filename):
    """
    Find a file in Google Drive by name using Drive API.

    Args:
        filename: Name of file to find (e.g., "November All Slides.pptx")

    Returns:
        File ID if found, None otherwise
    """
    try:
        from googleapiclient.discovery import build

        # Get credentials
        creds = get_drive_credentials()

        # Build Drive service
        drive_service = build('drive', 'v3', credentials=creds)

        # Search for file by name
        query = f"name='{filename}' and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        files = results.get('files', [])

        if files:
            return files[0]['id']  # Return first match

        return None

    except Exception as e:
        st.error(f"Error finding file in Drive: {e}")
        return None


def list_available_templates():
    """
    Query Google Drive for all available product slide templates.
    Searches for files matching '*All Slides*.pptx'.

    Returns:
        list: List of dicts sorted newest-first:
              [{'name': 'February All Slides.pptx', 'file_id': '...', 'modified_time': '...'}]
              Returns empty list on error.
    """
    try:
        from googleapiclient.discovery import build

        creds = get_drive_credentials()
        drive_service = build('drive', 'v3', credentials=creds)

        # Search for files matching the pattern
        query = "name contains 'All Slides' and mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation' and trashed=false"
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()

        files = results.get('files', [])

        return [
            {
                'name': f['name'],
                'file_id': f['id'],
                'modified_time': f.get('modifiedTime', '')
            }
            for f in files
        ]

    except Exception as e:
        print(f"Error listing templates from Drive: {e}")
        return []


def download_template_by_id(file_id, template_name):
    """
    Download a specific template from Google Drive by file ID.
    Caches in session state keyed by template name.

    Args:
        file_id: Google Drive file ID
        template_name: Display name (used as cache key)

    Returns:
        Path to temporary file, or None on error
    """
    cache_key = f"pptx_template_{template_name}"
    temp_file_key = f"{cache_key}_tempfile"

    # Check session cache first
    if cache_key in st.session_state:
        cached_template = st.session_state[cache_key]
        cached_template.seek(0)
        data = cached_template.read()
        cached_template.seek(0)

        st.info(f"Using cached template: {template_name} ({len(data):,} bytes)")

        # Create or reuse temp file
        if temp_file_key not in st.session_state or not os.path.exists(st.session_state[temp_file_key]):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
            temp_file.write(data)
            temp_file.flush()
            temp_file.close()
            st.session_state[temp_file_key] = temp_file.name

        return Path(st.session_state[temp_file_key])

    # Download from Google Drive
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload

        creds = get_drive_credentials()
        drive_service = build('drive', 'v3', credentials=creds)

        request = drive_service.files().get_media(fileId=file_id)
        template_data = io.BytesIO()
        downloader = MediaIoBaseDownload(template_data, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        template_data.seek(0)
        data_size = len(template_data.getvalue())
        if data_size == 0:
            st.error(f"Downloaded file is empty! File ID: {file_id}")
            return None

        st.success(f"Downloaded {template_name} ({data_size:,} bytes)")

        # Cache in session state
        st.session_state[cache_key] = template_data

        # Write to temp file
        template_data.seek(0)
        data = template_data.read()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
        temp_file.write(data)
        temp_file.flush()
        temp_file.close()
        st.session_state[temp_file_key] = temp_file.name

        return Path(temp_file.name)

    except Exception as e:
        st.error(f"Error downloading template '{template_name}': {e}")
        return None


def download_template_from_drive(template_key='all_slides'):
    """
    Download PowerPoint template from Google Drive.
    Caches result in st.session_state for session reuse.

    Args:
        template_key: Key from TEMPLATE_CONFIG ('all_slides' or 'intro_outro')

    Returns:
        tuple: (BytesIO object with template data, template filename) or (None, None) on error
    """
    config = TEMPLATE_CONFIG.get(template_key)
    if not config:
        st.error(f"Unknown template key: {template_key}")
        return None, None

    # Check if intro_outro template should be loaded from local file
    if template_key == 'intro_outro' and 'local_path' in config:
        local_path = Path(config['local_path'])
        if local_path.exists():
            with open(local_path, 'rb') as f:
                template_data = io.BytesIO(f.read())
            return template_data, config['name']
        else:
            st.error(f"Local template not found: {local_path}")
            return None, None

    # Check session cache first
    cache_key = config['cache_key']
    if cache_key in st.session_state:
        return st.session_state[cache_key], config['name']

    # Download from Google Drive
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload

        # Find file in Drive
        file_id = find_file_in_drive(config['name'])

        if not file_id:
            st.error(f"Template file not found in Google Drive: {config['name']}")
            creds = get_drive_credentials()
            st.info(f"Please ensure '{config['name']}' is shared with the service account: {creds.service_account_email}")
            return None, None

        # Get credentials and build Drive service
        creds = get_drive_credentials()
        drive_service = build('drive', 'v3', credentials=creds)

        # Download file
        request = drive_service.files().get_media(fileId=file_id)
        template_data = io.BytesIO()
        downloader = MediaIoBaseDownload(template_data, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Reset buffer to beginning
        template_data.seek(0)

        # Debug: Check if data was actually downloaded
        data_size = len(template_data.getvalue())
        if data_size == 0:
            st.error(f"Downloaded file is empty! File ID: {file_id}")
            return None, None

        st.success(f"Successfully downloaded {data_size:,} bytes from Google Drive")

        # Cache in session state
        st.session_state[cache_key] = template_data

        return template_data, config['name']

    except Exception as e:
        st.error(f"Error downloading template from Google Drive: {e}")
        st.info("Falling back to local template if available...")

        # Try local fallback
        local_path = Path(f"templates/{config['name']}")
        if local_path.exists():
            with open(local_path, 'rb') as f:
                template_data = io.BytesIO(f.read())
            return template_data, config['name']

        return None, None


def _download_no_cache(template_key, show_loading=True):
    """
    Download template directly to temp file without caching in session state.
    Used for memory optimization during PowerPoint generation.

    Args:
        template_key: Which template to load ('all_slides' or 'intro_outro')
        show_loading: Whether to show loading spinner

    Returns:
        Path to temporary file or None on error
    """
    config = TEMPLATE_CONFIG.get(template_key)
    if not config:
        return None

    # For intro_outro, use local path if available
    if template_key == 'intro_outro' and 'local_path' in config:
        local_path = Path(config['local_path'])
        if local_path.exists():
            return local_path

    # Download directly without caching
    if show_loading:
        with st.spinner(f"Downloading template: {config['name']}..."):
            template_data, template_name = download_template_from_drive(template_key)
    else:
        template_data, template_name = download_template_from_drive(template_key)

    if template_data:
        # Write to temporary file and return path
        template_data.seek(0)
        data = template_data.read()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
        temp_file.write(data)
        temp_file.flush()
        temp_file.close()

        return Path(temp_file.name)

    return None


def get_template_path(template_key='all_slides', show_loading=True, use_cache=True):
    """
    Get PowerPoint template for use in presentation generation.
    Downloads from cloud if needed, or uses cached version.

    For 'all_slides': Uses the user-selected template from session state
    (selected_pptx_template). Falls back to first available template.

    For 'intro_outro': Uses local file (unchanged).

    Args:
        template_key: Which template to load ('all_slides' or 'intro_outro')
        show_loading: Whether to show loading spinner
        use_cache: Whether to use session state caching (set False for memory optimization)

    Returns:
        Path to template file, or None on error
    """
    # Handle intro_outro (unchanged - uses local file or TEMPLATE_CONFIG)
    if template_key == 'intro_outro':
        config = TEMPLATE_CONFIG.get('intro_outro')
        if config and 'local_path' in config:
            local_path = Path(config['local_path'])
            if local_path.exists():
                return local_path

        # Memory optimization path
        if not use_cache:
            return _download_no_cache(template_key, show_loading)

        # Download from cloud as fallback
        if show_loading:
            with st.spinner(f"Downloading template: {config['name']}..."):
                template_data, template_name = download_template_from_drive(template_key)
        else:
            template_data, template_name = download_template_from_drive(template_key)

        if template_data:
            template_data.seek(0)
            data = template_data.read()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
            temp_file.write(data)
            temp_file.flush()
            temp_file.close()
            return Path(temp_file.name)

        return None

    # Handle all_slides: use selected template from session state
    selected = st.session_state.get('selected_pptx_template')

    if selected:
        # Download the selected template by file ID
        if show_loading:
            with st.spinner(f"Loading template: {selected['name']}..."):
                return download_template_by_id(selected['file_id'], selected['name'])
        else:
            return download_template_by_id(selected['file_id'], selected['name'])

    # No template selected yet - try to auto-discover and select
    templates = list_available_templates()
    if templates:
        # Default to most recently modified
        st.session_state['selected_pptx_template'] = templates[0]
        selected = templates[0]

        if show_loading:
            with st.spinner(f"Loading template: {selected['name']}..."):
                return download_template_by_id(selected['file_id'], selected['name'])
        else:
            return download_template_by_id(selected['file_id'], selected['name'])

    st.error("No product slide templates found in Google Drive. Upload a file with 'All Slides' in the name.")
    return None


def get_template_name(template_key='all_slides'):
    """Get the display name of the current template."""
    if template_key == 'all_slides':
        selected = st.session_state.get('selected_pptx_template')
        if selected:
            return selected['name']
        return "No template selected"

    config = TEMPLATE_CONFIG.get(template_key)
    return config['name'] if config else "Unknown Template"


def clear_template_cache():
    """Clear cached templates from session state (useful for forcing re-download)."""
    # Clear any dynamically cached templates
    keys_to_remove = [k for k in st.session_state if k.startswith('pptx_template_')]
    for key in keys_to_remove:
        del st.session_state[key]
