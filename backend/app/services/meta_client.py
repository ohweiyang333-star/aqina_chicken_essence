"""Meta Graph API wrapper for Messenger, comments, and WhatsApp."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import requests

from app.core.config import settings


class MetaMessagingClient:
    """Thin wrapper over Meta Graph API endpoints used by the skeleton."""

    def __init__(self) -> None:
        self._base_url = f"https://graph.facebook.com/{settings.meta_graph_api_version}"

    def verify_signature(self, raw_body: bytes, signature_header: str | None) -> bool:
        """Validate Meta webhook HMAC SHA-256 signatures."""
        if not settings.meta_app_secret or not signature_header:
            return False
        if not signature_header.startswith("sha256="):
            return False

        expected = hmac.new(
            settings.meta_app_secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        provided = signature_header.split("=", 1)[1]
        return hmac.compare_digest(expected, provided)

    def reply_to_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        """Post a public reply under a Facebook comment."""
        return self._post(
            f"/{comment_id}/comments",
            data={"message": message, "access_token": settings.meta_page_access_token},
        )

    def send_private_reply(
        self,
        comment_id: str,
        message: str,
        quick_replies: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a private reply from a Facebook comment using the Page Send API."""
        if not settings.meta_page_id:
            raise ValueError("META_PAGE_ID is required to send Facebook private replies")

        message_payload: dict[str, Any] = {"text": message}
        if quick_replies:
            message_payload["quick_replies"] = quick_replies

        payload = {
            "recipient": {"comment_id": comment_id},
            "messaging_type": "RESPONSE",
            "message": message_payload,
        }
        return self._post(
            f"/{settings.meta_page_id}/messages",
            json=payload,
            params={"access_token": settings.meta_page_access_token},
        )

    def send_messenger_text(self, recipient_psid: str, text: str) -> dict[str, Any]:
        """Send a Messenger text message."""
        payload = {
            "recipient": {"id": recipient_psid},
            "messaging_type": "RESPONSE",
            "message": {"text": text},
        }
        return self._post(
            "/me/messages",
            json=payload,
            params={"access_token": settings.meta_page_access_token},
        )

    def send_whatsapp_text(self, to: str, text: str) -> dict[str, Any]:
        """Send a WhatsApp text message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        return self._post(
            f"/{settings.meta_whatsapp_phone_number_id}/messages",
            json=payload,
            params={"access_token": settings.meta_whatsapp_access_token},
        )

    def upload_whatsapp_media(self, *, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        """Upload image bytes to WhatsApp Cloud API and return a media id."""
        return self._post(
            f"/{settings.meta_whatsapp_phone_number_id}/media",
            data={"messaging_product": "whatsapp"},
            files={"file": (filename, data, content_type)},
            params={"access_token": settings.meta_whatsapp_access_token},
        )

    def send_whatsapp_image(self, *, to: str, media_id: str, caption: str | None = None) -> dict[str, Any]:
        """Send a WhatsApp image message by an uploaded media id."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"id": media_id},
        }
        if caption:
            payload["image"]["caption"] = caption
        return self._post(
            f"/{settings.meta_whatsapp_phone_number_id}/messages",
            json=payload,
            params={"access_token": settings.meta_whatsapp_access_token},
        )

    def download_whatsapp_media(self, media_id: str) -> tuple[bytes, str]:
        """Download WhatsApp media bytes by media id."""
        metadata = self._get(
            f"/{media_id}",
            params={"access_token": settings.meta_whatsapp_access_token},
        )
        media_url = metadata.get("url")
        if not media_url:
            raise ValueError("WhatsApp media metadata did not include a download URL")
        response = requests.get(
            media_url,
            timeout=20,
            headers={"Authorization": f"Bearer {settings.meta_whatsapp_access_token}"},
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/jpeg").split(";")[0]
        return response.content, content_type

    def upload_messenger_attachment(self, *, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        """Upload a reusable Messenger image attachment and return an attachment id."""
        message = {
            "attachment": {
                "type": "image",
                "payload": {"is_reusable": True},
            }
        }
        return self._post(
            "/me/message_attachments",
            data={"message": json.dumps(message)},
            files={"filedata": (filename, data, content_type)},
            params={"access_token": settings.meta_page_access_token},
        )

    def send_messenger_image_attachment(self, *, recipient_psid: str, attachment_id: str) -> dict[str, Any]:
        """Send a Messenger image message by reusable attachment id."""
        payload = {
            "recipient": {"id": recipient_psid},
            "messaging_type": "RESPONSE",
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"attachment_id": attachment_id},
                }
            },
        }
        return self._post(
            "/me/messages",
            json=payload,
            params={"access_token": settings.meta_page_access_token},
        )

    def send_messenger_image_url(self, *, recipient_psid: str, image_url: str) -> dict[str, Any]:
        """Send a Messenger image attachment by URL fallback without exposing it as text."""
        payload = {
            "recipient": {"id": recipient_psid},
            "messaging_type": "RESPONSE",
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"url": image_url, "is_reusable": True},
                }
            },
        }
        return self._post(
            "/me/messages",
            json=payload,
            params={"access_token": settings.meta_page_access_token},
        )

    def send_whatsapp_template(
        self,
        *,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        body_variables: list[str] | None = None,
        components: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a WhatsApp template message for escalation alerts."""
        template_components: list[dict[str, Any]] = list(components or [])
        if body_variables:
            template_components.append(
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": value}
                        for value in body_variables
                    ],
                }
            )
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if template_components:
            payload["template"]["components"] = template_components
        return self._post(
            f"/{settings.meta_whatsapp_phone_number_id}/messages",
            json=payload,
            params={"access_token": settings.meta_whatsapp_access_token},
        )

    def list_whatsapp_templates(self) -> dict[str, Any]:
        """Fetch approved and pending templates from the configured WABA."""
        return self._get(
            f"/{settings.meta_whatsapp_business_account_id}/message_templates",
            params={
                "access_token": settings.meta_whatsapp_access_token,
                "fields": "name,language,status,category,components",
                "limit": 100,
            },
        )

    def create_whatsapp_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a WhatsApp template through the Business Management API."""
        return self._post(
            f"/{settings.meta_whatsapp_business_account_id}/message_templates",
            json=payload,
            params={"access_token": settings.meta_whatsapp_access_token},
        )

    def get_whatsapp_phone_number_health(self) -> dict[str, Any]:
        """Read basic phone number status used by the admin health panel."""
        return self._get(
            f"/{settings.meta_whatsapp_phone_number_id}",
            params={
                "access_token": settings.meta_whatsapp_access_token,
                "fields": "display_phone_number,verified_name,quality_rating,status",
            },
        )

    def _post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        response = requests.post(f"{self._base_url}{path}", timeout=20, **kwargs)
        response.raise_for_status()
        return response.json()

    def _get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        response = requests.get(f"{self._base_url}{path}", timeout=20, **kwargs)
        response.raise_for_status()
        return response.json()


_meta_client: MetaMessagingClient | None = None


def get_meta_client() -> MetaMessagingClient:
    """Get the shared Meta API client."""
    global _meta_client
    if _meta_client is None:
        _meta_client = MetaMessagingClient()
    return _meta_client
