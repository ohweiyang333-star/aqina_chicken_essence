"""Meta media asset cache for reusable chatbot images."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from app.core.config import settings
from app.services.marketing_utils import utcnow


@dataclass(frozen=True)
class MediaBytes:
    data: bytes
    content_type: str
    filename: str
    source_url: str


class MetaMediaAssetService:
    """Upload image bytes to Meta once, then send by provider media IDs."""

    def __init__(self, *, db: Any, meta_client: Any) -> None:
        self.db = db
        self.meta_client = meta_client

    def send_paynow_qr(
        self,
        *,
        channel: str,
        contact: dict[str, Any],
        paynow_settings: dict[str, Any],
        caption: str | None = None,
    ) -> dict[str, Any]:
        source = str(paynow_settings.get("payment_qr_image") or "").strip()
        if not source:
            raise ValueError("PayNow QR image is not configured")

        identifiers = contact.get("identifiers", {})
        if channel == "whatsapp":
            media_id = self._get_or_upload_whatsapp_media(source)
            return self.meta_client.send_whatsapp_image(
                to=identifiers["wa_id"],
                media_id=media_id,
                caption=caption,
            )

        if channel == "messenger":
            try:
                attachment_id = self._get_or_upload_messenger_attachment(source)
                return self.meta_client.send_messenger_image_attachment(
                    recipient_psid=identifiers["psid"],
                    attachment_id=attachment_id,
                )
            except Exception:
                # Messenger's upload endpoint can be permission-sensitive; still send
                # an image attachment rather than exposing the URL as text.
                media = self._download_media(source)
                return self.meta_client.send_messenger_image_url(
                    recipient_psid=identifiers["psid"],
                    image_url=media.source_url,
                )

        raise ValueError(f"Unsupported outbound channel: {channel}")

    def _get_or_upload_whatsapp_media(self, source: str) -> str:
        source_url = _resolve_source_url(source)
        ref = self.db.collection("meta_media_assets").document("paynow_qr_whatsapp")
        snapshot = ref.get()
        current = snapshot.to_dict() if snapshot.exists else {}
        if current.get("source_url") == source_url and current.get("whatsapp_media_id"):
            return current["whatsapp_media_id"]

        media = self._download_media(source_url)
        response = self.meta_client.upload_whatsapp_media(
            filename=media.filename,
            content_type=media.content_type,
            data=media.data,
        )
        media_id = response.get("id")
        if not media_id:
            raise ValueError("Meta WhatsApp media upload did not return an id")
        ref.set(
            {
                "source_url": media.source_url,
                "content_type": media.content_type,
                "filename": media.filename,
                "whatsapp_media_id": media_id,
                "updated_at": utcnow(),
            },
            merge=True,
        )
        return media_id

    def _get_or_upload_messenger_attachment(self, source: str) -> str:
        source_url = _resolve_source_url(source)
        ref = self.db.collection("meta_media_assets").document("paynow_qr_messenger")
        snapshot = ref.get()
        current = snapshot.to_dict() if snapshot.exists else {}
        if current.get("source_url") == source_url and current.get("messenger_attachment_id"):
            return current["messenger_attachment_id"]

        media = self._download_media(source_url)
        response = self.meta_client.upload_messenger_attachment(
            filename=media.filename,
            content_type=media.content_type,
            data=media.data,
        )
        attachment_id = response.get("attachment_id")
        if not attachment_id:
            raise ValueError("Meta Messenger attachment upload did not return an attachment_id")
        ref.set(
            {
                "source_url": media.source_url,
                "content_type": media.content_type,
                "filename": media.filename,
                "messenger_attachment_id": attachment_id,
                "updated_at": utcnow(),
            },
            merge=True,
        )
        return attachment_id

    @staticmethod
    def _download_media(source: str) -> MediaBytes:
        source_url = _resolve_source_url(source)
        response = requests.get(source_url, timeout=20)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png").split(";")[0]
        filename = _filename_from_url(source_url)
        return MediaBytes(
            data=response.content,
            content_type=content_type,
            filename=filename,
            source_url=source_url,
        )


def _resolve_source_url(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        return source
    if source.startswith("/"):
        return f"{settings.frontend_base_url.rstrip('/')}{source}"
    return source


def _filename_from_url(source_url: str) -> str:
    path = urlparse(source_url).path.rstrip("/")
    filename = path.rsplit("/", 1)[-1] if path else "paynow-qr.png"
    return filename or "paynow-qr.png"
