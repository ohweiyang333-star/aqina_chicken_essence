"""Meta Graph API wrapper for Messenger, comments, and WhatsApp."""
from __future__ import annotations

import hashlib
import hmac
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

    def send_private_reply(self, comment_id: str, message: str) -> dict[str, Any]:
        """Send a private reply from a Facebook comment thread."""
        return self._post(
            f"/{comment_id}/private_replies",
            data={"message": message, "access_token": settings.meta_page_access_token},
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

    def send_whatsapp_template(
        self,
        *,
        to: str,
        template_name: str,
        body_variables: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send a WhatsApp template message for escalation alerts."""
        components = []
        if body_variables:
            components.append(
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
                "language": {"code": "en_US"},
            },
        }
        if components:
            payload["template"]["components"] = components
        return self._post(
            f"/{settings.meta_whatsapp_phone_number_id}/messages",
            json=payload,
            params={"access_token": settings.meta_whatsapp_access_token},
        )

    def _post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        response = requests.post(f"{self._base_url}{path}", timeout=20, **kwargs)
        response.raise_for_status()
        return response.json()


_meta_client: MetaMessagingClient | None = None


def get_meta_client() -> MetaMessagingClient:
    """Get the shared Meta API client."""
    global _meta_client
    if _meta_client is None:
        _meta_client = MetaMessagingClient()
    return _meta_client
