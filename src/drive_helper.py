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
