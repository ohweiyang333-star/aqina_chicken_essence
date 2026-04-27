"""Firebase Storage upload helpers."""
from __future__ import annotations

from urllib.parse import quote
from uuid import uuid4

from firebase_admin import storage

from app.core.config import settings


def upload_public_file_to_firebase(
    *,
    data: bytes,
    destination_path: str,
    content_type: str,
) -> str:
    """Upload bytes to Firebase Storage and return a tokenized media URL."""
    token = str(uuid4())
    bucket = storage.bucket(settings.firebase_storage_bucket)
    blob = bucket.blob(destination_path)
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_string(data, content_type=content_type)
    encoded_path = quote(destination_path, safe="")
    return (
        f"https://firebasestorage.googleapis.com/v0/b/"
        f"{settings.firebase_storage_bucket}/o/{encoded_path}?alt=media&token={token}"
    )
