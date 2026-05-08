"""Admin inbox operations for Messenger and WhatsApp conversations."""
from __future__ import annotations

from typing import Any

from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_utils import ensure_datetime, stable_id, utcnow
from app.services.meta_client import get_meta_client
from app.services.meta_media_assets import MetaMediaAssetService


SUPPORTED_INBOX_CHANNELS = {"messenger", "whatsapp"}
VALID_MARKETING_TAGS = {"lead_cold", "qualified_warm", "cart_hot", "handoff_pending"}


class MarketingConversationConsoleService:
    """Business logic for the unified admin conversation inbox."""

    def __init__(
        self,
        *,
        db: Any,
        meta_client: Any | None = None,
        contact_service: MarketingContactService | None = None,
    ) -> None:
        self.db = db
        self.meta_client = meta_client or get_meta_client()
        self.contact_service = contact_service or MarketingContactService(db)

    def list_conversations(self, *, channel: str = "all", limit: int = 50) -> dict[str, Any]:
        self._validate_channel_filter(channel)
        query = self.db.collection("marketing_conversations")
        if channel != "all":
            query = query.where("channel", "==", channel)
        docs = query.order_by("last_message_at", direction="DESCENDING").limit(
            limit * 3 if channel == "all" else limit
        ).stream()
        items = []
        for doc in docs:
            conversation = doc.to_dict()
            conversation_channel = conversation.get("channel")
            if conversation_channel not in SUPPORTED_INBOX_CHANNELS:
                continue
            items.append(self._conversation_summary(doc.id, conversation))
            if len(items) >= limit:
                break
        return {"items": items}

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        contact["contact_id"] = conversation["contact_id"]
        return {
            "conversation": self._conversation_summary(conversation_id, conversation, contact=contact),
            "contact": contact,
            "messages": self._messages_for(conversation_id, limit=100),
            "orders": self._orders_for_contact(contact),
            "window": self._window_payload(contact),
        }

    def send_manual_text(self, conversation_id: str, text: str, admin: dict[str, Any]) -> dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            raise ValueError("Message text cannot be empty.")
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        if not self._customer_window_open(contact):
            raise ValueError("Customer service window is closed. Free-form replies are disabled.")

        channel = conversation["channel"]
        identifiers = contact.get("identifiers") or {}
        if channel == "messenger":
            result = self.meta_client.send_messenger_text(
                recipient_psid=identifiers.get("psid", ""),
                text=stripped,
            )
        elif channel == "whatsapp":
            result = self.meta_client.send_whatsapp_text(
                to=identifiers.get("wa_id") or identifiers.get("phone_e164") or "",
                text=stripped,
            )
        else:
            raise ValueError(f"Unsupported inbox channel: {channel}")

        provider_message_id = self._extract_provider_message_id(result)
        _, message_id = self.contact_service.append_message(
            contact_id=conversation["contact_id"],
            channel=channel,
            direction="outbound",
            role="admin",
            text=stripped,
            source=f"admin_{channel}_console",
            provider_message_id=provider_message_id,
            delivery_status="sent",
            created_at=utcnow(),
        )
        return {
            "status": "sent",
            "provider_message_id": provider_message_id,
            "message_id": message_id,
            "sent_by": admin.get("email") or admin.get("uid"),
        }

    def ensure_manual_reply_window_open(self, conversation_id: str) -> None:
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        if not self._customer_window_open(contact):
            raise ValueError("Customer service window is closed. Free-form replies are disabled.")

    def send_manual_image(
        self,
        conversation_id: str,
        *,
        media_url: str,
        media_content_type: str,
        media_filename: str,
        caption: str | None,
        admin: dict[str, Any],
    ) -> dict[str, Any]:
        source_url = media_url.strip()
        if not source_url:
            raise ValueError("Image URL cannot be empty.")
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        if not self._customer_window_open(contact):
            raise ValueError("Customer service window is closed. Free-form replies are disabled.")

        channel = conversation["channel"]
        contact_for_send = self._contact_with_send_identifier(contact, channel)
        stripped_caption = (caption or "").strip()
        media_service = MetaMediaAssetService(db=self.db, meta_client=self.meta_client)
        result = media_service.send_chatbot_image(
            channel=channel,
            contact=contact_for_send,
            source_url=source_url,
            cache_key=stable_id("manual_image", conversation_id, source_url),
            caption=stripped_caption or None,
        )

        provider_message_id = self._extract_provider_message_id(result)
        _, message_id = self.contact_service.append_message(
            contact_id=conversation["contact_id"],
            channel=channel,
            direction="outbound",
            role="admin",
            text=stripped_caption or "Manual image sent",
            source=f"admin_{channel}_console",
            provider_message_id=provider_message_id,
            delivery_status="sent",
            message_type="image",
            created_at=utcnow(),
            media_url=source_url,
            media_content_type=media_content_type,
            media_filename=media_filename,
        )
        return {
            "status": "sent",
            "provider_message_id": provider_message_id,
            "message_id": message_id,
            "media_url": source_url,
            "sent_by": admin.get("email") or admin.get("uid"),
        }

    def update_automation(self, conversation_id: str, *, paused: bool, reason: str | None) -> dict[str, Any]:
        conversation = self._get_conversation(conversation_id)
        if paused:
            self.contact_service.pause_automation(
                conversation["contact_id"],
                reason=reason or "admin_unified_inbox",
            )
            return {"status": "paused"}
        self.contact_service.resume_automation(conversation["contact_id"])
        return {"status": "resumed"}

    def update_contact_tag(self, contact_id: str, current_tag: str) -> dict[str, Any]:
        if current_tag not in VALID_MARKETING_TAGS:
            raise ValueError(f"Unsupported marketing tag: {current_tag}")
        self.contact_service.update_contact_tag(
            contact_id,
            current_tag,
            source="admin_unified_inbox",
        )
        return {"status": "updated", "contact_id": contact_id, "current_tag": current_tag}

    def _conversation_summary(
        self,
        conversation_id: str,
        conversation: dict[str, Any],
        *,
        contact: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        contact_payload = contact or self.contact_service.get_contact(conversation["contact_id"])
        contact_payload["contact_id"] = conversation["contact_id"]
        latest_messages = self._messages_for(conversation_id, limit=1, descending=True)
        latest = latest_messages[0] if latest_messages else None
        platform_id = self._platform_id(contact_payload, conversation.get("channel", ""))
        return {
            "conversation_id": conversation_id,
            "contact_id": conversation["contact_id"],
            "channel": conversation.get("channel", ""),
            "customer_name": self._contact_name(contact_payload) or self._masked_platform_id(platform_id),
            "platform_id": platform_id,
            "current_tag": contact_payload.get("current_tag", ""),
            "marketing_status": contact_payload.get("marketing_status", "unknown"),
            "automation_paused": bool(contact_payload.get("automation_paused")),
            "acquisition": self._acquisition_payload(contact_payload),
            "last_message_at": conversation.get("last_message_at"),
            "latest_message": latest,
            "window": self._window_payload(contact_payload),
            "orders": self._orders_for_contact(contact_payload)[:3],
        }

    def _get_conversation(self, conversation_id: str) -> dict[str, Any]:
        snapshot = self.db.collection("marketing_conversations").document(conversation_id).get()
        if not snapshot.exists:
            raise KeyError(f"Conversation not found: {conversation_id}")
        conversation = snapshot.to_dict()
        if conversation.get("channel") not in SUPPORTED_INBOX_CHANNELS:
            raise ValueError("Only Messenger and WhatsApp conversations are supported by this inbox.")
        return conversation

    def _messages_for(self, conversation_id: str, limit: int, descending: bool = False) -> list[dict[str, Any]]:
        docs = (
            self.db.collection("marketing_conversations")
            .document(conversation_id)
            .collection("messages")
            .order_by("created_at", direction="DESCENDING" if descending else "ASCENDING")
            .limit(limit)
            .stream()
        )
        messages = []
        for doc in docs:
            message = doc.to_dict()
            message["message_id"] = doc.id
            messages.append(message)
        return messages

    def _orders_for_contact(self, contact: dict[str, Any]) -> list[dict[str, Any]]:
        contact_id = contact.get("contact_id")
        identifiers = contact.get("identifiers") or {}
        wa_id = identifiers.get("wa_id") or identifiers.get("phone_e164")
        orders = []
        for doc in self.db.collection("orders").stream():
            order = doc.to_dict()
            customer = order.get("customer", {})
            if order.get("marketing_contact_id") == contact_id or (wa_id and customer.get("whatsapp") == wa_id):
                order["order_id"] = doc.id
                orders.append(order)
        orders.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        return orders

    def _window_payload(self, contact: dict[str, Any]) -> dict[str, Any]:
        expires_at = ensure_datetime(contact.get("window_expires_at"))
        return {
            "is_open": self._customer_window_open(contact),
            "expires_at": expires_at,
        }

    @staticmethod
    def _customer_window_open(contact: dict[str, Any]) -> bool:
        expires_at = ensure_datetime(contact.get("window_expires_at"))
        return expires_at is not None and utcnow() <= expires_at

    @staticmethod
    def _contact_name(contact: dict[str, Any]) -> str:
        order_fields = contact.get("order_fields") or {}
        profile = contact.get("profile") or {}
        return str(order_fields.get("name") or profile.get("name") or contact.get("name") or "")

    @staticmethod
    def _platform_id(contact: dict[str, Any], channel: str) -> str:
        identifiers = contact.get("identifiers") or {}
        if channel == "messenger":
            return str(identifiers.get("psid") or "")
        if channel == "whatsapp":
            return str(identifiers.get("wa_id") or identifiers.get("phone_e164") or "")
        return ""

    @staticmethod
    def _contact_with_send_identifier(contact: dict[str, Any], channel: str) -> dict[str, Any]:
        identifiers = dict(contact.get("identifiers") or {})
        if channel == "messenger":
            if not identifiers.get("psid"):
                raise ValueError("Messenger PSID is missing for this contact.")
        elif channel == "whatsapp":
            if not identifiers.get("wa_id") and identifiers.get("phone_e164"):
                identifiers["wa_id"] = identifiers["phone_e164"]
            if not identifiers.get("wa_id"):
                raise ValueError("WhatsApp recipient ID is missing for this contact.")
        else:
            raise ValueError(f"Unsupported inbox channel: {channel}")
        return {**contact, "identifiers": identifiers}

    @staticmethod
    def _masked_platform_id(platform_id: str) -> str:
        if not platform_id:
            return "Unknown contact"
        if len(platform_id) <= 8:
            return platform_id
        return f"{platform_id[:4]}...{platform_id[-4:]}"

    @staticmethod
    def _acquisition_payload(contact: dict[str, Any]) -> dict[str, Any]:
        acquisition = contact.get("acquisition")
        if not isinstance(acquisition, dict):
            acquisition = {}
        return {
            "source": acquisition.get("source") or "unknown/direct",
            "ref": acquisition.get("ref"),
            "ad_id": acquisition.get("ad_id"),
            "post_id": acquisition.get("post_id"),
            "raw_referral": acquisition.get("raw_referral"),
        }

    @staticmethod
    def _extract_provider_message_id(payload: dict[str, Any]) -> str | None:
        if payload.get("message_id"):
            return payload.get("message_id")
        messages = payload.get("messages") or []
        if messages:
            return messages[0].get("id")
        return None

    @staticmethod
    def _validate_channel_filter(channel: str) -> None:
        if channel != "all" and channel not in SUPPORTED_INBOX_CHANNELS:
            raise ValueError(f"Unsupported inbox channel: {channel}")
