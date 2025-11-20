"""
Template Loader Module for PBP Pricing App

Handles downloading PowerPoint templates from Google Drive on-demand.
Templates are cached in session state to avoid repeated downloads.
"""

import streamlit as st
import io
from pathlib import Path


# PowerPoint template configuration
TEMPLATE_CONFIG = {
    'all_slides': {
        'name': 'November All Slides.pptx',
        'drive_path': 'data/all_slides/latest/November All Slides.pptx',
        'description': 'Main product slides template',
        'folder_id': None,  # Will search by path
        'cache_key': 'pptx_template_all_slides'
    },
    'intro_outro': {
        'name': 'Intro_Outro_Slides_PbP_Proposals.pptx',
        'local_path': 'templates/Intro_Outro_Slides_PbP_Proposals.pptx',  # Keep local (2.5MB, not a problem)
        'description': 'Intro and outro slides',
        'cache_key': 'pptx_template_intro_outro'
    }
}


def get_drive_credentials():
    """
    Get Google Drive credentials from Streamlit secrets or environment variables.
    Returns credentials object ready for Drive API.
    """
    import os
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Try Streamlit secrets first (local development)
    if "gcp_service_account" in st.secrets:
        creds_info = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return creds

    # Fall back to environment variables (Render deployment)
    elif os.getenv("GCP_PROJECT_ID"):
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


def get_template_path(template_key='all_slides', show_loading=True):
    """
    Get PowerPoint template for use in presentation generation.
    Downloads from cloud if needed, or uses cached version.

    Args:
        template_key: Which template to load ('all_slides' or 'intro_outro')
        show_loading: Whether to show loading spinner

    Returns:
        BytesIO object ready for Presentation() or Path for local files
    """
    config = TEMPLATE_CONFIG.get(template_key)
    if not config:
        return None

    # For intro_outro, use local path if available
    if template_key == 'intro_outro' and 'local_path' in config:
        local_path = Path(config['local_path'])
        if local_path.exists():
            return local_path

    # Check if already in cache
    cache_key = config['cache_key']
    if cache_key in st.session_state:
        # Return cached BytesIO object (reset position to beginning)
        cached_template = st.session_state[cache_key]
        cached_template.seek(0)
        return cached_template

    # Download from cloud
    if show_loading:
        with st.spinner(f"Downloading template: {config['name']}..."):
            template_data, template_name = download_template_from_drive(template_key)
    else:
        template_data, template_name = download_template_from_drive(template_key)

    if template_data:
        # Reset to beginning before returning
        template_data.seek(0)
        return template_data

    return None


def get_template_name(template_key='all_slides'):
    """Get the display name of the template."""
    config = TEMPLATE_CONFIG.get(template_key)
    return config['name'] if config else "Unknown Template"


def clear_template_cache():
    """Clear cached templates from session state (useful for forcing re-download)."""
    for key in ['pptx_template_all_slides', 'pptx_template_intro_outro']:
        if key in st.session_state:
            del st.session_state[key]
