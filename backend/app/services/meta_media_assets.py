"""Meta media asset cache for reusable chatbot images."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
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
        return self.send_chatbot_image(
            channel=channel,
            contact=contact,
            source_url=source,
            cache_key="paynow_qr",
            caption=caption,
        )

    def send_chatbot_image(
        self,
        *,
        channel: str,
        contact: dict[str, Any],
        source_url: str,
        cache_key: str,
        caption: str | None = None,
    ) -> dict[str, Any]:
        source = str(source_url or "").strip()
        if not source:
            raise ValueError("Chatbot image source is not configured")
        identifiers = contact.get("identifiers", {})
        if channel == "whatsapp":
            media_id = self._get_or_upload_whatsapp_media(source, cache_key=cache_key)
            return self.meta_client.send_whatsapp_image(
                to=identifiers["wa_id"],
                media_id=media_id,
                caption=caption,
            )

        if channel == "messenger":
            try:
                attachment_id = self._get_or_upload_messenger_attachment(source, cache_key=cache_key)
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

    def _get_or_upload_whatsapp_media(self, source: str, *, cache_key: str) -> str:
        source_url = _resolve_source_url(source)
        ref = self.db.collection("meta_media_assets").document(_cache_doc_id(cache_key, "whatsapp"))
        snapshot = ref.get()
        current = snapshot.to_dict() if snapshot.exists else {}
        if current.get("source_url") == source_url and current.get("whatsapp_media_id"):
            return current["whatsapp_media_id"]

        media = _ensure_whatsapp_supported_image(self._download_media(source_url))
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

    def _get_or_upload_messenger_attachment(self, source: str, *, cache_key: str) -> str:
        source_url = _resolve_source_url(source)
        ref = self.db.collection("meta_media_assets").document(_cache_doc_id(cache_key, "messenger"))
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


def _cache_doc_id(cache_key: str, channel: str) -> str:
    normalized = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in cache_key)
    return f"{normalized or 'chatbot_image'}_{channel}"


def _ensure_whatsapp_supported_image(media: MediaBytes) -> MediaBytes:
    content_type = (media.content_type or "image/jpeg").lower()
    if content_type == "image/jpg":
        return MediaBytes(
            data=media.data,
            content_type="image/jpeg",
            filename=_replace_extension(media.filename, "jpg"),
            source_url=media.source_url,
        )
    if content_type in {"image/jpeg", "image/png"}:
        return media
    if content_type == "image/webp":
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - dependency is installed in production image.
            raise ValueError("Pillow is required to convert WebP images before WhatsApp upload") from exc

        with Image.open(BytesIO(media.data)) as image:
            rgb = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode in {"RGBA", "LA"}:
                alpha = image.convert("RGBA").getchannel("A")
                rgb.paste(image.convert("RGB"), mask=alpha)
            else:
                rgb = image.convert("RGB")
            output = BytesIO()
            rgb.save(output, format="JPEG", quality=90, optimize=True)
        return MediaBytes(
            data=output.getvalue(),
            content_type="image/jpeg",
            filename=_replace_extension(media.filename, "jpg"),
            source_url=media.source_url,
        )
    return media


def _replace_extension(filename: str, extension: str) -> str:
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return f"{stem}.{extension}"
