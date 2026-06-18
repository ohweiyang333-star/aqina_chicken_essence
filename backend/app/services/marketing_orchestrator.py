"""Orchestration logic for webhook ingestion and internal marketing tasks."""
from __future__ import annotations

from copy import deepcopy
import logging
import re
from typing import Any
import requests

from app.core.config import settings
from app.models.chatbot import SalesConversationTurn
from app.models.marketing import NormalizedMarketingEvent
from app.services.meta_media_assets import MetaMediaAssetService
from app.services.chatbot_settings import ChatbotSettingsService, DEFAULT_FACEBOOK_COMMENT_KEYWORDS
from app.services.chatbot_skill_router import is_cart_hot_checkout_intent, should_send_paynow_qr_for_checkout_intent
from app.services.follow_up import FollowUpEngine
from app.services.gift_choices import normalize_gift_choice
from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_utils import ensure_datetime, excerpt, payload_hash, stable_id, utcnow
from app.services.storage_uploads import upload_public_file_to_firebase
from app.services.whatsapp_console import WhatsAppConsoleService, is_marketing_opt_out_text


FACEBOOK_PRIVATE_REPLY_QUICK_REPLIES = [
    {"content_type": "text", "title": "自己喝", "payload": "AQINA_SELF_CARE"},
    {"content_type": "text", "title": "孕期/月子", "payload": "AQINA_MATERNITY"},
    {"content_type": "text", "title": "送长辈", "payload": "AQINA_GIFT_ELDER"},
]

logger = logging.getLogger(__name__)

FINAL_COMMENT_EVENT_STATUSES = {
    "processed",
    "processed_with_errors",
    "reply_failed",
    "skipped_disabled",
    "skipped_no_keyword",
    "skipped_self_comment",
    "skipped_replies_disabled",
}
MIN_PAYMENT_REFERENCE_LENGTH = 6
DUPLICATE_PAYMENT_REFERENCE_FLAG = "duplicate_payment_reference"
INITIAL_PROMOTION_SUPPRESSION_TERMS = (
    "退款",
    "投诉",
    "退货",
    "换货",
    "取消订单",
    "转人工",
    "真人",
    "人工",
    "客服",
    "负责人",
    "订单状态",
    "付款状态",
    "物流",
    "追踪",
    "没收到",
    "还没收到",
    "破损",
    "refund",
    "complaint",
    "complain",
    "cancel order",
    "order status",
    "payment status",
    "tracking",
    "where is my order",
    "already paid",
    "paid already",
    "person in charge",
    "human",
    "staff",
    "agent",
)
DELIVERY_FEE_QUESTION_TERMS = (
    "delivery fee",
    "delivery fees",
    "shipping fee",
    "shipping fees",
    "postage",
    "delivery charge",
    "shipping charge",
    "delivery cost",
    "shipping cost",
    "运费",
    "邮费",
    "配送费",
    "送货费",
)
DELIVERY_FEE_ANSWER_TERMS = (
    "include singapore delivery fee",
    "includes singapore delivery fee",
    "included singapore delivery fee",
    "no separate delivery fee",
    "no extra delivery fee",
    "delivery fee is included",
    "delivery fees are included",
    "已包含新加坡配送费",
    "包含新加坡配送费",
    "不需要另加邮费",
    "无需另加邮费",
    "没有额外配送费",
    "不另收配送费",
)


class MarketingAutomationOrchestrator:
    """Coordinate webhook intake, event storage, chat replies, checkout, and escalation."""

    def __init__(
        self,
        *,
        db: Any,
        task_queue: Any,
        contact_service: MarketingContactService,
        follow_up_engine: FollowUpEngine,
        meta_client: Any,
        gemini_service: Any,
    ) -> None:
        self.db = db
        self.task_queue = task_queue
        self.contact_service = contact_service
        self.follow_up_engine = follow_up_engine
        self.meta_client = meta_client
        self.gemini_service = gemini_service
        self.settings_service = ChatbotSettingsService(db)

    def ingest_facebook_webhook(self, payload: dict[str, Any]) -> int:
        accepted = 0
        for entry in payload.get("entry", []):
            for message_event in entry.get("messaging", []):
                messenger_event = self._normalize_messenger_event(message_event)
                if messenger_event is None:
                    referral_event = self._normalize_messenger_referral_event(message_event)
                    if referral_event is None:
                        continue

                    occurred_at = referral_event["occurred_at"]
                    identifiers = {"psid": referral_event["sender_psid"]}
                    contact_id, conversation_id = self.contact_service.upsert_contact_from_event(
                        channel="messenger",
                        identifiers=identifiers,
                        current_tag="lead_cold",
                        status="active",
                        interaction_time=occurred_at,
                        acquisition=referral_event["acquisition"],
                    )
                    self._backfill_messenger_profile_for_webhook(contact_id, identifiers)
                    normalized = NormalizedMarketingEvent(
                        provider="meta",
                        channel="messenger",
                        event_type="messenger_referral_received",
                        dedupe_key=referral_event["dedupe_key"],
                        occurred_at=occurred_at,
                        contact_id=contact_id,
                        conversation_id=conversation_id,
                        identifiers=identifiers,
                        payload={
                            "channel": "messenger",
                            "acquisition": referral_event["acquisition"],
                            "sender_psid": identifiers["psid"],
                        },
                    )
                    if self._record_event(normalized):
                        event_id = stable_id("event", normalized.dedupe_key)
                        self.db.collection("marketing_events").document(event_id).set(
                            {
                                "status": "processed_referral",
                                "processed_at": utcnow(),
                                "updated_at": utcnow(),
                            },
                            merge=True,
                        )
                        accepted += 1
                    continue

                occurred_at = messenger_event["occurred_at"]
                identifiers = {"psid": messenger_event["sender_psid"]}
                contact_id, conversation_id = self.contact_service.upsert_contact_from_event(
                    channel="messenger",
                    identifiers=identifiers,
                    current_tag="lead_cold",
                    status="active",
                    interaction_time=occurred_at,
                    acquisition=messenger_event["acquisition"],
                )
                self._backfill_messenger_profile_for_webhook(contact_id, identifiers)
                self.contact_service.append_message(
                    contact_id=contact_id,
                    channel="messenger",
                    direction="inbound",
                    role="user",
                    text=messenger_event["text"],
                    source=messenger_event["source"],
                    provider_message_id=messenger_event["provider_message_id"],
                    message_type=messenger_event["message_type"],
                    created_at=occurred_at,
                )
                is_opt_out = messenger_event["message_type"] == "text" and is_marketing_opt_out_text(messenger_event["text"])
                if is_opt_out:
                    self.contact_service.mark_marketing_opt_out(
                        contact_id,
                        source="messenger_inbound_keyword",
                    )
                normalized = NormalizedMarketingEvent(
                    provider="meta",
                    channel="messenger",
                    event_type=(
                        "messenger_opt_out_received"
                        if is_opt_out
                        else messenger_event["event_type"]
                    ),
                    dedupe_key=messenger_event["dedupe_key"],
                    occurred_at=occurred_at,
                    contact_id=contact_id,
                    conversation_id=conversation_id,
                    identifiers=identifiers,
                    payload={
                        "channel": "messenger",
                        "text": messenger_event["text"],
                        "message_type": messenger_event["message_type"],
                        "attachment_url": messenger_event.get("attachment_url"),
                        "mime_type": messenger_event.get("mime_type"),
                        "provider_message_id": messenger_event["provider_message_id"],
                        "postback_payload": messenger_event.get("postback_payload"),
                        "quick_reply_payload": messenger_event.get("quick_reply_payload"),
                        "acquisition": messenger_event["acquisition"],
                        "sender_psid": identifiers["psid"],
                    },
                )
                created = self._record_event(normalized)
                if created:
                    event_id = stable_id("event", normalized.dedupe_key)
                    if is_opt_out:
                        self.db.collection("marketing_events").document(event_id).set(
                            {
                                "status": "processed_opt_out",
                                "processed_at": utcnow(),
                                "updated_at": utcnow(),
                            },
                            merge=True,
                        )
                        accepted += 1
                        continue
                    self.task_queue.enqueue_marketing_event(event_id, "process-inbound-message")
                    self.follow_up_engine.schedule_follow_up_jobs(
                        contact_id=contact_id,
                        conversation_id=conversation_id,
                        anchor_interaction_time=occurred_at,
                        current_tag="lead_cold",
                    )
                    accepted += 1

            for change in entry.get("changes", []):
                value = change.get("value", {})
                if change.get("field") != "feed" or value.get("item") != "comment":
                    logger.info(
                        "facebook_webhook_change_skipped reason=unsupported_change field=%s item=%s verb=%s",
                        change.get("field"),
                        value.get("item"),
                        value.get("verb"),
                    )
                    continue
                if value.get("verb") and value.get("verb") != "add":
                    logger.info(
                        "facebook_webhook_change_skipped reason=unsupported_verb item=%s verb=%s has_comment_id=%s",
                        value.get("item"),
                        value.get("verb"),
                        bool(value.get("comment_id")),
                    )
                    continue

                runtime_settings = self.settings_service.get_settings(persist_migration=False)
                automation = self._facebook_comment_automation_settings(runtime_settings)
                if not automation["enabled"]:
                    logger.info("facebook_webhook_change_skipped reason=automation_disabled")
                    continue
                if self._is_page_self_comment(value=value, entry=entry, automation=automation):
                    logger.info(
                        "facebook_webhook_change_skipped reason=page_self_comment has_comment_id=%s has_message=%s",
                        bool(value.get("comment_id")),
                        bool(value.get("message")),
                    )
                    continue

                comment_text = str(value.get("message", ""))
                matched_keyword = self._matched_comment_keyword(comment_text, automation["keywords"])
                if not matched_keyword:
                    logger.info(
                        "facebook_webhook_change_skipped reason=no_keyword has_comment_id=%s message_chars=%s",
                        bool(value.get("comment_id")),
                        len(comment_text),
                    )
                    continue

                comment_id = str(value.get("comment_id") or "")
                if not comment_id:
                    logger.info(
                        "facebook_webhook_change_skipped reason=missing_comment_id matched_keyword=%s message_chars=%s",
                        matched_keyword,
                        len(comment_text),
                    )
                    continue

                occurred_at = ensure_datetime(value.get("created_time")) or utcnow()
                page_id = str(entry.get("id") or value.get("page_id") or settings.meta_page_id or "")
                normalized = NormalizedMarketingEvent(
                    provider="meta",
                    channel="facebook",
                    event_type="facebook_comment_created",
                    dedupe_key=f"facebook-comment:{comment_id}",
                    occurred_at=occurred_at,
                    identifiers={"commenter_id": str(value.get("from", {}).get("id", ""))},
                    payload={
                        "comment_id": comment_id,
                        "post_id": value.get("post_id"),
                        "comment_text": comment_text,
                        "from_id": value.get("from", {}).get("id"),
                        "from_name": value.get("from", {}).get("name"),
                        "page_id": page_id,
                        "matched_keyword": matched_keyword,
                        "public_reply_enabled": automation["public_reply_enabled"],
                        "private_reply_enabled": automation["private_reply_enabled"],
                    },
                )
                if self._record_event(normalized):
                    event_id = stable_id("event", normalized.dedupe_key)
                    self.task_queue.enqueue_marketing_event(event_id, "process-comment-event")
                    logger.info(
                        "facebook_webhook_comment_recorded matched_keyword=%s public_reply_enabled=%s private_reply_enabled=%s",
                        matched_keyword,
                        automation["public_reply_enabled"],
                        automation["private_reply_enabled"],
                    )
                    accepted += 1
                else:
                    logger.info(
                        "facebook_webhook_change_skipped reason=duplicate_comment_event matched_keyword=%s",
                        matched_keyword,
                    )

        return accepted

    def _backfill_messenger_profile_for_webhook(self, contact_id: str, identifiers: dict[str, str]) -> None:
        psid = identifiers.get("psid")
        if not psid:
            return
        try:
            contact = self.contact_service.get_contact(contact_id)
            order_fields = contact.get("order_fields") or {}
            profile = contact.get("profile") or {}
            existing_name = order_fields.get("name") or profile.get("name") or contact.get("name")
            if existing_name:
                return

            profile_data = self.meta_client.get_messenger_profile(psid)
            name = str(
                profile_data.get("name")
                or " ".join(
                    part
                    for part in [profile_data.get("first_name"), profile_data.get("last_name")]
                    if part
                )
            ).strip()
            if name:
                self.contact_service.update_contact_profile(
                    contact_id,
                    {"profile": {"name": name}}
                )
                logger.info("messenger_profile_backfilled_in_webhook psid=%s name=%s", psid, name)
        except Exception as exc:
            logger.info("messenger_profile_backfill_failed_in_webhook psid=%s error=%s", psid, exc)

    def _normalize_messenger_event(self, message_event: dict[str, Any]) -> dict[str, Any] | None:
        sender_psid = str(message_event.get("sender", {}).get("id") or "")
        if not sender_psid:
            return None

        message = message_event.get("message") or {}
        postback = message_event.get("postback") or {}
        occurred_at = ensure_datetime(message_event.get("timestamp")) or utcnow()

        attachments = message.get("attachments") or []
        image_attachment = next((item for item in attachments if item.get("type") == "image"), None)
        audio_attachment = next((item for item in attachments if item.get("type") == "audio"), None)
        attachment = image_attachment or audio_attachment

        provider_message_id = message.get("mid")
        postback_payload = None
        quick_reply_payload = (message.get("quick_reply") or {}).get("payload")
        source = "messenger_webhook"
        event_type = "messenger_message_received"

        if postback:
            message_type = "postback"
            postback_payload = postback.get("payload")
            message_text = str(postback.get("title") or postback_payload or "[postback]")
            source = "messenger_postback"
            event_type = "messenger_postback_received"
        elif audio_attachment:
            message_type = "audio"
            message_text = "[audio]"
        elif image_attachment:
            message_type = "image"
            message_text = "[image]"
        elif "text" in message:
            message_type = "text"
            message_text = str(message.get("text") or "")
        else:
            return None

        dedupe_seed = (
            provider_message_id
            or f"{sender_psid}:{occurred_at.isoformat()}:{postback_payload or quick_reply_payload or message_text}"
        )
        return {
            "sender_psid": sender_psid,
            "occurred_at": occurred_at,
            "text": message_text,
            "source": source,
            "event_type": event_type,
            "dedupe_key": f"messenger:{message_type}:{dedupe_seed}",
            "message_type": message_type,
            "provider_message_id": provider_message_id,
            "postback_payload": postback_payload,
            "quick_reply_payload": quick_reply_payload,
            "attachment_url": (attachment or {}).get("payload", {}).get("url"),
            "mime_type": (attachment or {}).get("payload", {}).get("mime_type"),
            "acquisition": self._messenger_acquisition(message_event),
        }

    def _normalize_messenger_referral_event(self, message_event: dict[str, Any]) -> dict[str, Any] | None:
        sender_psid = str(message_event.get("sender", {}).get("id") or "")
        referral = message_event.get("referral")
        if not sender_psid or not isinstance(referral, dict) or not referral:
            return None

        occurred_at = ensure_datetime(message_event.get("timestamp")) or utcnow()
        return {
            "sender_psid": sender_psid,
            "occurred_at": occurred_at,
            "dedupe_key": f"messenger:referral:{sender_psid}:{occurred_at.isoformat()}:{payload_hash(referral)}",
            "acquisition": self._messenger_acquisition(message_event),
        }

    @staticmethod
    def _messenger_acquisition(message_event: dict[str, Any]) -> dict[str, Any]:
        postback = message_event.get("postback") or {}
        message = message_event.get("message") or {}
        referral = (
            postback.get("referral")
            or message.get("referral")
            or message_event.get("referral")
            or {}
        )
        if not isinstance(referral, dict):
            referral = {}
        source = referral.get("source") or "unknown/direct"
        return {
            "source": source,
            "ref": referral.get("ref"),
            "ad_id": referral.get("ad_id"),
            "post_id": referral.get("post_id"),
            "raw_referral": deepcopy(referral) if referral else None,
        }

    def ingest_whatsapp_webhook(self, payload: dict[str, Any]) -> int:
        accepted = 0
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                statuses = value.get("statuses", [])
                logger.info(
                    "whatsapp_webhook_change_received field=%s message_count=%s status_count=%s",
                    change.get("field"),
                    len(messages),
                    len(statuses),
                )
                for message in messages:
                    message_type = message.get("type")
                    if message_type not in {"text", "image", "audio"}:
                        logger.info(
                            "whatsapp_webhook_message_skipped reason=unsupported_type type=%s",
                            message_type,
                        )
                        continue

                    occurred_at = ensure_datetime(message.get("timestamp")) or utcnow()
                    wa_id = str(message.get("from", ""))
                    identifiers = {"wa_id": wa_id, "phone_e164": wa_id}
                    message_text = (
                        message.get("text", {}).get("body", "")
                        if message_type == "text"
                        else message.get("image", {}).get("caption") or ("[audio]" if message_type == "audio" else "[image]")
                    )
                    contact_id, conversation_id = self.contact_service.upsert_contact_from_event(
                        channel="whatsapp",
                        identifiers=identifiers,
                        current_tag="lead_cold",
                        status="active",
                        interaction_time=occurred_at,
                    )
                    self.contact_service.append_message(
                        contact_id=contact_id,
                        channel="whatsapp",
                        direction="inbound",
                        role="user",
                        text=message_text,
                        source="whatsapp_webhook",
                        provider_message_id=message.get("id"),
                        message_type=message_type,
                        created_at=occurred_at,
                    )
                    if is_marketing_opt_out_text(message_text):
                        self.contact_service.mark_marketing_opt_out(
                            contact_id,
                            source="whatsapp_inbound_keyword",
                        )
                    normalized = NormalizedMarketingEvent(
                        provider="meta",
                        channel="whatsapp",
                        event_type="whatsapp_message_received",
                        dedupe_key=f"whatsapp:{message.get('id')}",
                        occurred_at=occurred_at,
                        contact_id=contact_id,
                        conversation_id=conversation_id,
                        identifiers=identifiers,
                        payload={
                            "channel": "whatsapp",
                            "text": message_text,
                            "message_type": message_type,
                            "media_id": (message.get("image") or message.get("audio") or {}).get("id"),
                            "mime_type": (message.get("image") or message.get("audio") or {}).get("mime_type"),
                            "sha256": (message.get("image") or message.get("audio") or {}).get("sha256"),
                            "provider_message_id": message.get("id"),
                            "wa_id": wa_id,
                        },
                    )
                    if self._record_event(normalized):
                        event_id = stable_id("event", normalized.dedupe_key)
                        self.task_queue.enqueue_marketing_event(event_id, "process-inbound-message")
                        self.follow_up_engine.schedule_follow_up_jobs(
                            contact_id=contact_id,
                            conversation_id=conversation_id,
                            anchor_interaction_time=occurred_at,
                            current_tag="lead_cold",
                        )
                        accepted += 1
                        logger.info(
                            "whatsapp_webhook_message_recorded message_type=%s queued=true",
                            message_type,
                        )
                    else:
                        logger.info("whatsapp_webhook_message_skipped reason=duplicate")

                for status in statuses:
                    delivery_update = WhatsAppConsoleService(
                        db=self.db,
                        meta_client=self.meta_client,
                        task_queue=self.task_queue,
                        contact_service=self.contact_service,
                    ).update_delivery_status(status)
                    normalized = NormalizedMarketingEvent(
                        provider="meta",
                        channel="whatsapp",
                        event_type="whatsapp_status_updated",
                        dedupe_key=f"whatsapp-status:{status.get('id')}:{status.get('status')}",
                        occurred_at=utcnow(),
                        identifiers={"wa_id": str(status.get("recipient_id", ""))},
                        payload=status,
                    )
                    self._record_event(normalized)
                    logger.info(
                        "whatsapp_webhook_status_recorded status=%s delivery_updated=%s",
                        status.get("status"),
                        delivery_update.get("updated"),
                    )
        return accepted

    def process_comment_event(self, event_id: str) -> dict[str, Any]:
        ref = self.db.collection("marketing_events").document(event_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise KeyError(f"Marketing event not found: {event_id}")

        event = snapshot.to_dict()
        existing_status = event.get("status")
        if existing_status in FINAL_COMMENT_EVENT_STATUSES:
            return {"status": existing_status, "contact_id": event.get("contact_id")}

        payload = event.get("payload", {})
        runtime_settings = self.settings_service.get_settings()
        automation = self._facebook_comment_automation_settings(runtime_settings)
        if not automation["enabled"]:
            return self._mark_comment_event(
                ref,
                status="skipped_disabled",
                payload={"skip_reason": "facebook_comment_automation_disabled"},
            )
        if self._is_page_self_comment_from_payload(payload=payload, automation=automation):
            return self._mark_comment_event(
                ref,
                status="skipped_self_comment",
                payload={"skip_reason": "page_self_comment"},
            )
        matched_keyword = payload.get("matched_keyword") or self._matched_comment_keyword(
            str(payload.get("comment_text", "")),
            automation["keywords"],
        )
        if not matched_keyword:
            return self._mark_comment_event(
                ref,
                status="skipped_no_keyword",
                payload={"skip_reason": "no_purchase_intent_keyword"},
            )

        occurred_at = ensure_datetime(event.get("received_at")) or utcnow()
        contact_id, conversation_id = self.contact_service.upsert_contact_from_event(
            channel="facebook",
            identifiers={"commenter_id": str(payload.get("from_id", ""))},
            current_tag="lead_cold",
            status="provisional",
            comment_time=occurred_at,
        )
        self.contact_service.append_message(
            contact_id=contact_id,
            channel="facebook",
            direction="inbound",
            role="user",
            text=payload.get("comment_text", ""),
            source="facebook_comment",
            provider_comment_id=payload.get("comment_id"),
            message_type="comment",
            created_at=occurred_at,
        )
        public_reply_template = (
            runtime_settings.get("crm_follow_up_rules", {})
            .get("comment_hook", {})
            .get("public_reply", {})
            .get("instruction")
            or settings.meta_comment_reply_template
        )
        private_reply_template = (
            runtime_settings.get("crm_follow_up_rules", {})
            .get("comment_hook", {})
            .get("private_opening", {})
            .get("instruction")
            or settings.meta_private_reply_template
        )
        public_reply = self._render_comment_template(public_reply_template, payload)
        private_reply = self._render_comment_template(private_reply_template, payload)
        comment_id = str(payload.get("comment_id") or "")

        public_reply_status = "disabled"
        private_reply_status = "disabled"
        provider_responses: dict[str, Any] = {}
        errors: dict[str, str] = {}

        if automation["public_reply_enabled"] and public_reply:
            try:
                provider_responses["public_reply"] = self.meta_client.reply_to_comment(
                    comment_id=comment_id,
                    message=public_reply,
                )
                public_reply_status = "sent"
            except Exception as exc:  # noqa: BLE001 - persist provider errors instead of retrying duplicate DMs.
                public_reply_status = "failed"
                errors["public_reply"] = str(exc)[:500]

        if automation["private_reply_enabled"] and private_reply:
            try:
                provider_responses["private_reply"] = self.meta_client.send_private_reply(
                    comment_id=comment_id,
                    message=private_reply,
                    quick_replies=FACEBOOK_PRIVATE_REPLY_QUICK_REPLIES,
                )
                private_reply_status = "sent"
                self.contact_service.append_message(
                    contact_id=contact_id,
                    channel="facebook",
                    direction="outbound",
                    role="assistant",
                    text=private_reply,
                    source="facebook_private_reply",
                    provider_comment_id=comment_id,
                    message_type="private_reply",
                    delivery_status="sent",
                )
            except Exception as exc:  # noqa: BLE001 - record failure and avoid task retry loops.
                private_reply_status = "failed"
                errors["private_reply"] = str(exc)[:500]

        if public_reply_status == "disabled" and private_reply_status == "disabled":
            status_value = "skipped_replies_disabled"
        elif errors and (public_reply_status == "sent" or private_reply_status == "sent"):
            status_value = "processed_with_errors"
        elif errors:
            status_value = "reply_failed"
        else:
            status_value = "processed"

        ref.set(
            {
                "status": status_value,
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "matched_keyword": matched_keyword,
                "public_reply_status": public_reply_status,
                "private_reply_status": private_reply_status,
                "provider_responses": provider_responses,
                "reply_errors": errors,
                "processed_at": utcnow(),
                "updated_at": utcnow(),
            },
            merge=True,
        )
        return {
            "status": status_value,
            "contact_id": contact_id,
            "public_reply_status": public_reply_status,
            "private_reply_status": private_reply_status,
        }

    def process_inbound_message(self, event_id: str) -> dict[str, Any]:
        ref = self.db.collection("marketing_events").document(event_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise KeyError(f"Marketing event not found: {event_id}")

        event = snapshot.to_dict()
        payload = event.get("payload", {})
        if payload.get("message_type") == "image":
            return self._process_payment_receipt_event(ref=ref, event=event)

        contact_id = event["contact_id"]
        contact = self.contact_service.get_contact(contact_id)
        contact, prompt_phone_defaulted = self._contact_with_channel_order_defaults(
            channel=event["channel"],
            contact=contact,
        )
        incoming_text = str(payload.get("text", ""))
        if payload.get("message_type") == "audio":
            if not self.gemini_service.is_ready():
                ref.set({"status": "blocked_configuration", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
                logger.info("inbound_message_processing_blocked reason=gemini_not_ready_audio channel=%s", event["channel"])
                return {"status": "blocked_configuration"}
            try:
                incoming_text = self._transcribe_audio_event(ref=ref, event=event)
            except Exception as exc:  # noqa: BLE001 - customers should receive a readable fallback.
                logger.warning("audio_transcription_failed channel=%s error=%s", event["channel"], exc)
                return self._process_audio_transcription_failure(ref=ref, event=event, contact=contact)

        if is_marketing_opt_out_text(incoming_text) or contact.get("marketing_status") == "opted_out":
            if is_marketing_opt_out_text(incoming_text):
                self.contact_service.mark_marketing_opt_out(contact_id, source=f"{event['channel']}_inbound_keyword")
            ref.set({"status": "skipped_opt_out", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
            logger.info("inbound_message_processing_skipped reason=opt_out channel=%s", event["channel"])
            return {"status": "skipped_opt_out"}

        if self._is_payment_confirmation_text(incoming_text) and self._find_active_checkout_session(contact_id):
            return self._process_payment_confirmation_text(
                ref=ref,
                event=event,
                contact=contact,
                incoming_text=incoming_text,
            )

        if not self.gemini_service.is_ready():
            ref.set({"status": "blocked_configuration", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
            logger.info("inbound_message_processing_blocked reason=gemini_not_ready channel=%s", event["channel"])
            return {"status": "blocked_configuration"}

        runtime_settings = self.settings_service.get_settings()
        conversation_id = event["conversation_id"]
        messages = self.contact_service.get_recent_messages(conversation_id)
        hot_checkout_intent = is_cart_hot_checkout_intent(
            incoming_text,
            current_tag=contact.get("current_tag"),
        )
        customer_locale = _detect_customer_locale(incoming_text, contact)
        if not self._should_skip_initial_promotion(incoming_text, contact):
            self._send_initial_promotion_image(
                channel=event["channel"],
                contact_id=contact_id,
                conversation_id=conversation_id,
                runtime_settings=runtime_settings,
                customer_locale=customer_locale,
            )
        turn = self._normalize_turn(
            self.gemini_service.generate_chat_reply(
                contact=contact,
                messages=messages,
                incoming_text=incoming_text,
                channel=event["channel"],
                runtime_settings=runtime_settings,
            )
        )
        turn.reply_text = _ensure_delivery_fee_answer(
            incoming_text=incoming_text,
            reply_text=turn.reply_text,
            customer_locale=customer_locale,
        )

        turn_order_fields = turn.order_fields.model_dump()
        precheckout_qr_selected_package_code = turn.selected_package_code or contact.get("selected_package_code")
        merged_order_fields = self._merge_order_fields(contact.get("order_fields", {}), turn_order_fields)
        merged_order_fields, runtime_phone_defaulted = self._apply_whatsapp_phone_default(
            channel=event["channel"],
            contact=contact,
            order_fields=merged_order_fields,
        )
        selected_package_code = turn.selected_package_code or contact.get("selected_package_code")
        detected_gift_choice = self._resolve_gift_choice(
            selected_package_code=selected_package_code,
            incoming_text=incoming_text,
            turn=turn,
            contact=contact,
            order_fields=merged_order_fields,
        )
        if detected_gift_choice:
            merged_order_fields["gift_choice"] = detected_gift_choice
        incoming_customer_request_remark = self._normalize_customer_request_remark(
            getattr(turn, "customer_request_remark", None)
        )
        customer_request_remark = self._merge_customer_request_remarks(
            contact.get("customer_request_remark"),
            incoming_customer_request_remark,
        )
        missing_order_fields = self._effective_missing_order_fields(
            turn.missing_order_fields,
            order_fields=merged_order_fields,
            require_all_fields=bool(turn.checkout_ready or turn.selected_package_code),
        )
        checkout_ready = self._checkout_ready_after_channel_defaults(
            channel=event["channel"],
            turn=turn,
            order_fields=merged_order_fields,
            missing_order_fields=missing_order_fields,
            phone_defaulted=prompt_phone_defaulted or runtime_phone_defaulted,
        )
        effective_next_tag = "cart_hot" if checkout_ready or hot_checkout_intent else turn.next_tag
        update_fields = {
            "lead_goal": turn.lead_goal,
            "recommended_package_code": turn.recommended_package_code,
            "upgrade_package_code": turn.upgrade_package_code,
            "selected_package_code": turn.selected_package_code,
            "order_fields": merged_order_fields,
            "missing_order_fields": missing_order_fields,
            "future_contact_opt_in": bool(turn.opt_in_granted),
            "chatbot_locale": customer_locale,
        }
        if customer_request_remark:
            update_fields["customer_request_remark"] = customer_request_remark
            update_fields["customer_request_remark_updated_at"] = utcnow()
        if detected_gift_choice:
            update_fields["gift_choice"] = detected_gift_choice
        if hot_checkout_intent or checkout_ready:
            update_fields["handoff_recommended"] = True
            update_fields["handoff_reason"] = "high_intent_checkout"
        self.contact_service.update_contact_profile(contact_id, update_fields)
        if turn.opt_in_granted:
            self.contact_service.grant_marketing_opt_in(contact_id, source="chatbot_opt_in")

        if turn.escalate or turn.next_tag == "handoff_pending":
            escalation_reply = turn.reply_text.strip()
            if escalation_reply:
                send_result = self._send_channel_reply(
                    channel=event["channel"],
                    contact=self.contact_service.get_contact(contact_id),
                    text=escalation_reply,
                )
                self.contact_service.append_message(
                    contact_id=contact_id,
                    channel=event["channel"],
                    direction="outbound",
                    role="assistant",
                    text=escalation_reply,
                    source="gemini_chatbot",
                    provider_message_id=self._extract_provider_message_id(event["channel"], send_result),
                    created_at=utcnow(),
                    delivery_status="sent",
                )
            escalation_id = self._escalate_contact(
                contact=contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message=incoming_text,
                reason=turn.escalation_reason or "manual_handoff_requested",
                runtime_settings=runtime_settings,
                send_customer_message=False,
            )
            ref.set({"status": "escalated", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
            logger.info("inbound_message_processing_escalated channel=%s", event["channel"])
            return {"status": "escalated", "escalation_id": escalation_id}

        checkout_session = None
        reply_text = turn.reply_text.strip()
        if checkout_ready and turn.selected_package_code:
            checkout_session = self._create_checkout_session(
                contact_id=contact_id,
                conversation_id=conversation_id,
                selected_package_code=turn.selected_package_code,
                order_fields=merged_order_fields,
                runtime_settings=runtime_settings,
                customer_request_remark=customer_request_remark,
                incoming_customer_request_remark=incoming_customer_request_remark,
                latest_customer_message=incoming_text,
            )
            if self._reply_requests_phone(reply_text) and (prompt_phone_defaulted or runtime_phone_defaulted):
                reply_text = self._checkout_ready_reply(customer_locale)
            reply_text = self._append_paynow_summary(
                reply_text,
                order_id=checkout_session["order_id"],
                total_amount=checkout_session["total_amount"],
                paynow_settings=runtime_settings.get("payment", {}).get("paynow", {}),
            )

        if effective_next_tag != contact.get("current_tag"):
            self.contact_service.update_contact_tag(
                contact_id,
                effective_next_tag,
                source="gemini_chat_turn",
                metadata={"event_id": event_id},
            )

        send_result = self._send_channel_reply(
            channel=event["channel"],
            contact=self.contact_service.get_contact(contact_id),
            text=reply_text,
        )
        provider_message_id = self._extract_provider_message_id(event["channel"], send_result)
        self.contact_service.append_message(
            contact_id=contact_id,
            channel=event["channel"],
            direction="outbound",
            role="assistant",
            text=reply_text,
            source="gemini_chatbot",
            provider_message_id=provider_message_id,
            created_at=utcnow(),
            delivery_status="sent",
        )
        self._send_chatbot_media_assets(
            channel=event["channel"],
            contact_id=contact_id,
            conversation_id=conversation_id,
            turn=turn,
            runtime_settings=runtime_settings,
            customer_locale=customer_locale,
        )
        if self._should_send_precheckout_paynow_qr(
            contact=self.contact_service.get_contact(contact_id),
            incoming_text=incoming_text,
            selected_package_code=precheckout_qr_selected_package_code,
            checkout_session=checkout_session,
        ):
            try:
                qr_result = self._send_precheckout_paynow_qr_image(
                    channel=event["channel"],
                    contact=self.contact_service.get_contact(contact_id),
                    paynow_settings=runtime_settings.get("payment", {}).get("paynow", {}),
                    customer_locale=customer_locale,
                )
                qr_provider_message_id = self._extract_provider_message_id(event["channel"], qr_result)
                self.contact_service.append_message(
                    contact_id=contact_id,
                    channel=event["channel"],
                    direction="outbound",
                    role="assistant",
                    text="Pre-checkout PayNow QR image sent",
                    source="paynow_qr_media",
                    provider_message_id=qr_provider_message_id,
                    message_type="image",
                    created_at=utcnow(),
                    delivery_status="sent",
                )
                self.contact_service.update_contact_profile(
                    contact_id,
                    {
                        "precheckout_paynow_qr_sent": True,
                        "precheckout_paynow_qr_sent_at": utcnow(),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - keep checkout conversation moving if media fails.
                logger.warning("precheckout_paynow_qr_media_failed contact_id=%s error=%s", contact_id, exc)
        latest_contact = self.contact_service.get_contact(contact_id)
        if (
            customer_request_remark
            and not checkout_session
            and self._should_send_customer_request_alert(
                contact=latest_contact,
                incoming_customer_request_remark=incoming_customer_request_remark,
            )
        ):
            alert_id = self._create_customer_request_internal_alert(
                contact=latest_contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message=incoming_text,
                customer_request_remark=customer_request_remark,
                runtime_settings=runtime_settings,
            )
            if alert_id:
                self.contact_service.update_contact_profile(
                    contact_id,
                    {
                        "customer_request_alert_sent": True,
                        "customer_request_alert_id": alert_id,
                        "customer_request_alert_remark": incoming_customer_request_remark,
                    },
                )
        if checkout_session:
            qr_result = self._send_checkout_qr_image(
                channel=event["channel"],
                contact=self.contact_service.get_contact(contact_id),
                checkout_session=checkout_session,
                paynow_settings=runtime_settings.get("payment", {}).get("paynow", {}),
            )
            qr_provider_message_id = self._extract_provider_message_id(event["channel"], qr_result)
            self.contact_service.append_message(
                contact_id=contact_id,
                channel=event["channel"],
                direction="outbound",
                role="assistant",
                text="PayNow QR image sent",
                source="paynow_qr_media",
                provider_message_id=qr_provider_message_id,
                message_type="image",
                created_at=utcnow(),
                delivery_status="sent",
            )
            self.contact_service.update_contact_profile(
                contact_id,
                {
                    "checkout_session_id": checkout_session["session_id"],
                    "checkout_url": checkout_session["checkout_url"],
                },
            )
        ref.set({"status": "processed", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
        logger.info(
            "inbound_message_processed channel=%s checkout_created=%s",
            event["channel"],
            bool(checkout_session),
        )
        return {"status": "processed", "checkout_session_id": checkout_session["session_id"] if checkout_session else None}

    def _create_checkout_session(
        self,
        *,
        contact_id: str,
        conversation_id: str,
        selected_package_code: str,
        order_fields: dict[str, Any],
        runtime_settings: dict[str, Any],
        customer_request_remark: str | None = None,
        incoming_customer_request_remark: str | None = None,
        latest_customer_message: str = "",
    ) -> dict[str, Any]:
        packages = runtime_settings.get("packages", {})
        package = packages.get(selected_package_code)
        if not package:
            raise KeyError(f"Unknown package code: {selected_package_code}")

        now = utcnow()
        gift_choice = normalize_gift_choice(order_fields.get("gift_choice")) if selected_package_code == "pack2" else None
        contact = self.contact_service.get_contact(contact_id)
        existing_id = contact.get("checkout_session_id")
        if existing_id:
            existing = self.db.collection("marketing_checkout_sessions").document(existing_id).get()
            if existing.exists:
                session = existing.to_dict()
                session["session_id"] = existing.id
                session_update: dict[str, Any] = {"updated_at": now}
                if gift_choice:
                    session_update["gift_choice"] = gift_choice
                    session["gift_choice"] = gift_choice
                remark = self._normalize_customer_request_remark(customer_request_remark)
                if remark:
                    session_update["customer_request_remark"] = remark
                    session_update["notes"] = remark
                    session["customer_request_remark"] = remark
                if len(session_update) > 1:
                    self.db.collection("marketing_checkout_sessions").document(existing_id).set(session_update, merge=True)
                    if session.get("order_id"):
                        self.db.collection("orders").document(session["order_id"]).set(session_update, merge=True)
                if remark and self._should_send_customer_request_alert(
                    contact=contact,
                    incoming_customer_request_remark=incoming_customer_request_remark,
                ):
                    alert_id = self._create_customer_request_internal_alert(
                        contact=contact,
                        contact_id=contact_id,
                        conversation_id=conversation_id,
                        latest_customer_message=latest_customer_message,
                        customer_request_remark=remark,
                        runtime_settings=runtime_settings,
                    )
                    if alert_id:
                        self.contact_service.update_contact_profile(
                            contact_id,
                            {
                                "customer_request_alert_sent": True,
                                "customer_request_alert_id": alert_id,
                                "customer_request_alert_remark": self._normalize_customer_request_remark(
                                    incoming_customer_request_remark
                                ),
                            },
                        )
                return session

        order_id = stable_id("order", contact_id, selected_package_code, now.isoformat())
        subtotal_amount = self._money(float(package["price_sgd"]))
        box_count = self._package_box_count(package)
        shipping_fee = self._shipping_fee_for(box_count)
        total_amount = self._money(subtotal_amount + shipping_fee)
        order_payload = {
            "customer": {
                "name": order_fields.get("name"),
                "email": None,
                "whatsapp": order_fields.get("phone"),
                "address": order_fields.get("address"),
            },
            "items": [
                {
                    "product_id": package["code"],
                    "product_name": package["name_zh"],
                    "product_name_zh": package["name_zh"],
                    "quantity": 1,
                    "unit_price": subtotal_amount,
                    "total_price": subtotal_amount,
                }
            ],
            "subtotal_amount": subtotal_amount,
            "shipping_fee": shipping_fee,
            "box_count": box_count,
            "gift_choice": gift_choice,
            "total_amount": total_amount,
            "payment_method": "paynow",
            "payment_status": "pending",
            "order_status": "pending",
            "payment_receipt_url": None,
            "notes": self._normalize_customer_request_remark(customer_request_remark),
            "customer_request_remark": self._normalize_customer_request_remark(customer_request_remark),
            "source": "marketing_chatbot",
            "created_from": "marketing_inbox",
            "source_channel": contact.get("channel"),
            "marketing_contact_id": contact_id,
            "conversation_id": conversation_id,
            "channel": contact.get("channel"),
            "checkout_session_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self.db.collection("orders").document(order_id).set(order_payload)

        token = stable_id("paynow", order_id, now.isoformat())
        session_id = stable_id("checkout", order_id)
        checkout_url = f"{settings.frontend_base_url.rstrip('/')}/paynow/{token}"
        paynow_settings = runtime_settings.get("payment", {}).get("paynow", {})
        session_payload = {
            "order_id": order_id,
            "token": token,
            "package_code": package["code"],
            "checkout_url": checkout_url,
            "conversation_id": conversation_id,
            "contact_id": contact_id,
            "status": "active",
            "payment_reference": f"{paynow_settings.get('payment_reference_prefix', 'AQINA')}-{order_id}",
            "subtotal_amount": subtotal_amount,
            "shipping_fee": shipping_fee,
            "box_count": box_count,
            "gift_choice": gift_choice,
            "total_amount": total_amount,
            "customer_request_remark": self._normalize_customer_request_remark(customer_request_remark),
            "notes": self._normalize_customer_request_remark(customer_request_remark),
            "created_at": now,
            "updated_at": now,
        }
        self.db.collection("marketing_checkout_sessions").document(session_id).set(session_payload)
        self.db.collection("orders").document(order_id).set({"checkout_session_id": session_id, "updated_at": now}, merge=True)
        order_alert_id = self._create_order_internal_alert(
            contact=contact,
            contact_id=contact_id,
            conversation_id=conversation_id,
            order_id=order_id,
            order_payload=order_payload,
            latest_customer_message=latest_customer_message,
            customer_request_remark=customer_request_remark,
            runtime_settings=runtime_settings,
        )
        incoming_remark = self._normalize_customer_request_remark(incoming_customer_request_remark)
        if order_alert_id and incoming_remark:
            self.contact_service.update_contact_profile(
                contact_id,
                {
                    "customer_request_alert_sent": True,
                    "customer_request_alert_id": order_alert_id,
                    "customer_request_alert_remark": incoming_remark,
                },
            )
        return {"session_id": session_id, **session_payload}

    def _create_order_internal_alert(
        self,
        *,
        contact: dict[str, Any],
        contact_id: str,
        conversation_id: str,
        order_id: str,
        order_payload: dict[str, Any],
        latest_customer_message: str,
        customer_request_remark: str | None,
        runtime_settings: dict[str, Any],
    ) -> str | None:
        try:
            return self._create_internal_notification(
                contact=contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message=self._order_alert_message(
                    order_id=order_id,
                    order_payload=order_payload,
                    latest_customer_message=latest_customer_message,
                    customer_request_remark=customer_request_remark,
                ),
                reason="order_created_pending_payment",
                runtime_settings=runtime_settings,
                remark=customer_request_remark,
            )
        except Exception as exc:  # noqa: BLE001 - internal alert must not block checkout.
            logger.warning("order_internal_alert_failed order_id=%s error=%s", order_id, exc)
            return None

    def _create_customer_request_internal_alert(
        self,
        *,
        contact: dict[str, Any],
        contact_id: str,
        conversation_id: str,
        latest_customer_message: str,
        customer_request_remark: str,
        runtime_settings: dict[str, Any],
    ) -> str | None:
        try:
            return self._create_internal_notification(
                contact=contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message=(
                    "Customer special request for staff review. "
                    f"Remark: {customer_request_remark}. Latest: {latest_customer_message}"
                ),
                reason="customer_request_remark",
                runtime_settings=runtime_settings,
                remark=customer_request_remark,
            )
        except Exception as exc:  # noqa: BLE001 - internal alert must not block checkout.
            logger.warning("customer_request_internal_alert_failed contact_id=%s error=%s", contact_id, exc)
            return None

    def _escalate_contact(
        self,
        *,
        contact: dict[str, Any],
        contact_id: str,
        conversation_id: str,
        latest_customer_message: str,
        reason: str,
        runtime_settings: dict[str, Any],
        send_customer_message: bool = True,
    ) -> str:
        handoff_message = self._safe_handoff_message(runtime_settings.get("handoff_message", ""))
        if send_customer_message and handoff_message:
            self._send_channel_reply(channel=contact["channel"], contact=contact, text=handoff_message)
            self.contact_service.append_message(
                contact_id=contact_id,
                channel=contact["channel"],
                direction="outbound",
                role="assistant",
                text=handoff_message,
                source="handoff_message",
                created_at=utcnow(),
                delivery_status="sent",
            )

        self.contact_service.pause_automation(contact_id, reason=reason)
        return self._create_internal_notification(
            contact=contact,
            contact_id=contact_id,
            conversation_id=conversation_id,
            latest_customer_message=latest_customer_message,
            reason=reason,
            runtime_settings=runtime_settings,
        )

    def _create_internal_notification(
        self,
        *,
        contact: dict[str, Any],
        contact_id: str,
        conversation_id: str,
        latest_customer_message: str,
        reason: str,
        runtime_settings: dict[str, Any],
        remark: str | None = None,
    ) -> str:
        escalation_settings = runtime_settings.get("escalation", {}) or {}
        recipients = self._escalation_notification_recipients(escalation_settings)
        template_name = str(escalation_settings.get("whatsapp_template_name") or "").strip()
        escalation_id = stable_id("escalation", contact_id, conversation_id, reason, utcnow().isoformat())
        template_variables = [
            contact.get("identifiers", {}).get("wa_id") or contact.get("identifiers", {}).get("psid") or contact_id,
            reason,
            str(latest_customer_message or "")[:120],
        ]
        if not escalation_settings.get("enabled"):
            notification_status = "disabled"
        elif recipients and template_name:
            notification_status = "pending"
        else:
            notification_status = "not_configured"

        payload = {
            "contact_id": contact_id,
            "conversation_id": conversation_id,
            "reason": reason,
            "latest_customer_message": latest_customer_message,
            "status": "open",
            "private_whatsapp_number": recipients[0] if recipients else "",
            "private_whatsapp_numbers": recipients,
            "template_name": template_name,
            "template_variables": template_variables,
            "notification_status": notification_status,
            "notification_error": None,
            "notification_results": [],
            "remark": self._normalize_customer_request_remark(remark) or "",
            "notified_at": None,
            "resolved_at": None,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        self.db.collection("marketing_escalations").document(escalation_id).set(payload)

        if escalation_settings.get("enabled") and recipients and template_name:
            self._send_internal_notification_templates(
                escalation_id=escalation_id,
                recipients=recipients,
                template_name=template_name,
                template_variables=template_variables,
            )
        return escalation_id

    def _send_internal_notification_templates(
        self,
        *,
        escalation_id: str,
        recipients: list[str],
        template_name: str,
        template_variables: list[str],
    ) -> None:
        results = []
        sent_count = 0
        for recipient in recipients:
            try:
                result = self.meta_client.send_whatsapp_template(
                    to=recipient,
                    template_name=template_name,
                    body_variables=template_variables,
                )
                sent_count += 1
                results.append(
                    {
                        "to": recipient,
                        "status": "sent",
                        "provider_message_id": self._extract_provider_message_id("whatsapp", result),
                    }
                )
            except Exception as exc:  # pragma: no cover - provider failures are integration-only
                logger.warning("internal_notification_failed escalation_id=%s recipient=%s error=%s", escalation_id, recipient, exc)
                results.append({"to": recipient, "status": "failed", "error": str(exc)})

        if sent_count == len(recipients):
            notification_status = "sent"
        elif sent_count:
            notification_status = "partial_failed"
        else:
            notification_status = "failed"

        update = {
            "notification_status": notification_status,
            "notification_results": results,
            "updated_at": utcnow(),
        }
        if sent_count:
            update["notified_at"] = utcnow()
        if sent_count < len(recipients):
            update["notification_error"] = "One or more internal WhatsApp notifications failed"
        self.db.collection("marketing_escalations").document(escalation_id).set(update, merge=True)

    @staticmethod
    def _escalation_notification_recipients(escalation_settings: dict[str, Any]) -> list[str]:
        values = [escalation_settings.get("private_whatsapp_number")]
        additional = escalation_settings.get("additional_private_whatsapp_numbers")
        if isinstance(additional, list):
            values.extend(additional)
        recipients: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in recipients:
                recipients.append(text)
        return recipients

    @classmethod
    def _merge_customer_request_remarks(cls, existing: Any, incoming: Any) -> str | None:
        parts: list[str] = []
        for value in (existing, incoming):
            remark = cls._normalize_customer_request_remark(value)
            if remark and remark not in parts:
                parts.append(remark)
        merged = " | ".join(parts)
        return merged[:1000] or None

    @staticmethod
    def _normalize_customer_request_remark(value: Any) -> str | None:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:1000] or None

    @classmethod
    def _should_send_customer_request_alert(
        cls,
        *,
        contact: dict[str, Any],
        incoming_customer_request_remark: str | None,
    ) -> bool:
        incoming = cls._normalize_customer_request_remark(incoming_customer_request_remark)
        if not incoming:
            return False
        return incoming != cls._normalize_customer_request_remark(contact.get("customer_request_alert_remark"))

    @staticmethod
    def _order_alert_message(
        *,
        order_id: str,
        order_payload: dict[str, Any],
        latest_customer_message: str,
        customer_request_remark: str | None,
    ) -> str:
        customer = order_payload.get("customer") if isinstance(order_payload.get("customer"), dict) else {}
        item = (order_payload.get("items") or [{}])[0]
        product_name = item.get("product_name_zh") or item.get("product_name") or item.get("product_id") or "Order"
        parts = [
            "New chatbot order pending PayNow receipt",
            f"Order #{order_id[-8:]}",
            f"Channel: {order_payload.get('source_channel') or order_payload.get('channel') or '-'}",
            f"Customer: {customer.get('name') or '-'} / {customer.get('whatsapp') or '-'}",
            f"Item: {product_name}",
            f"Total: SGD {float(order_payload.get('total_amount') or 0):.2f}",
        ]
        remark = MarketingAutomationOrchestrator._normalize_customer_request_remark(customer_request_remark)
        if remark:
            parts.append(f"Remark: {remark}")
        message = MarketingAutomationOrchestrator._normalize_customer_request_remark(latest_customer_message)
        if message:
            parts.append(f"Latest: {message}")
        return " | ".join(parts)

    def _send_channel_reply(self, *, channel: str, contact: dict[str, Any], text: str) -> dict[str, Any]:
        identifiers = contact.get("identifiers", {})
        if channel == "messenger":
            return self.meta_client.send_messenger_text(recipient_psid=identifiers["psid"], text=text)
        if channel == "whatsapp":
            return self.meta_client.send_whatsapp_text(to=identifiers["wa_id"], text=text)
        raise ValueError(f"Unsupported outbound channel: {channel}")

    def _send_checkout_qr_image(
        self,
        *,
        channel: str,
        contact: dict[str, Any],
        checkout_session: dict[str, Any],
        paynow_settings: dict[str, Any],
    ) -> dict[str, Any]:
        reference = checkout_session.get("payment_reference") or (
            f"{paynow_settings.get('payment_reference_prefix', 'AQINA')}-{checkout_session['order_id']}"
        )
        caption = (
            f"PayNow: {paynow_settings.get('account_name', 'Boong Poultry Pte Ltd')}\n"
            f"Amount: SGD {float(checkout_session.get('total_amount', 0)):.2f}\n"
            f"Reference: {reference}"
        )
        media_service = MetaMediaAssetService(db=self.db, meta_client=self.meta_client)
        return media_service.send_paynow_qr(
            channel=channel,
            contact=contact,
            paynow_settings=paynow_settings,
            caption=caption,
        )

    def _should_send_precheckout_paynow_qr(
        self,
        *,
        contact: dict[str, Any],
        incoming_text: str,
        selected_package_code: str | None,
        checkout_session: dict[str, Any] | None,
    ) -> bool:
        if checkout_session:
            return False
        if contact.get("checkout_session_id") or contact.get("precheckout_paynow_qr_sent"):
            return False
        return should_send_paynow_qr_for_checkout_intent(
            incoming_text,
            current_tag=contact.get("current_tag"),
            selected_package_code=selected_package_code,
        )

    def _send_precheckout_paynow_qr_image(
        self,
        *,
        channel: str,
        contact: dict[str, Any],
        paynow_settings: dict[str, Any],
        customer_locale: str,
    ) -> dict[str, Any]:
        account_name = paynow_settings.get("account_name", "Boong Poultry Pte Ltd")
        if customer_locale == "en":
            caption = (
                f"PayNow: {account_name}\n"
                "Please send the payment screenshot here after payment. Also share the recipient name, phone number, and Singapore address so our team can confirm the order."
            )
        else:
            caption = (
                f"PayNow 收款户名：{account_name}\n"
                "付款后请把截图发回这里。也请留下收件人姓名、联系电话和新加坡地址，客服会帮您确认订单。"
            )
        media_service = MetaMediaAssetService(db=self.db, meta_client=self.meta_client)
        return media_service.send_paynow_qr(
            channel=channel,
            contact=contact,
            paynow_settings=paynow_settings,
            caption=caption,
        )

    def _send_chatbot_media_assets(
        self,
        *,
        channel: str,
        contact_id: str,
        conversation_id: str,
        turn: SalesConversationTurn,
        runtime_settings: dict[str, Any],
        customer_locale: str,
    ) -> None:
        media_assets = runtime_settings.get("media_assets", {}) or {}
        if not media_assets:
            return

        contact = self.contact_service.get_contact(contact_id)
        sent_media = deepcopy(contact.get("sent_media") or {})
        sent_media.setdefault("initial_promotion_languages", {})
        if isinstance(sent_media.get("brand_intro"), bool) and sent_media.get("brand_intro"):
            sent_media.setdefault("brand_intro_languages", {})["zh"] = True
        sent_media.setdefault("brand_intro_languages", {})
        sent_media.setdefault("package_images", {})
        media_service = MetaMediaAssetService(db=self.db, meta_client=self.meta_client)

        brand_intro = _localized_media_value(
            media_assets.get("brand_intro_images") or media_assets.get("brand_intro"),
            customer_locale,
        )
        if brand_intro and not sent_media.get("brand_intro_languages", {}).get(customer_locale):
            try:
                result = media_service.send_chatbot_image(
                    channel=channel,
                    contact=contact,
                    source_url=brand_intro,
                    cache_key=f"brand_intro_{customer_locale}",
                    caption=_localized_media_value(
                        (media_assets.get("captions", {}) or {}).get("brand_intro"),
                        customer_locale,
                    ),
                )
                self._append_outbound_media_message(
                    contact_id=contact_id,
                    conversation_id=conversation_id,
                    channel=channel,
                    text=f"Brand intro image sent: {customer_locale}",
                    source="chatbot_brand_intro_media",
                    provider_message_id=self._extract_provider_message_id(channel, result),
                )
                sent_media["brand_intro"] = True
                sent_media.setdefault("brand_intro_languages", {})[customer_locale] = True
                self.contact_service.update_contact_profile(contact_id, {"sent_media": sent_media})
                contact = self.contact_service.get_contact(contact_id)
            except Exception as exc:  # noqa: BLE001 - media failures should not block chatbot text.
                logger.warning("chatbot_brand_intro_media_failed contact_id=%s error=%s", contact_id, exc)

        package_code = turn.selected_package_code or turn.recommended_package_code
        package_images = media_assets.get("package_images", {}) or {}
        package_image = _localized_media_value(package_images.get(package_code or ""), customer_locale)
        if package_code and package_image and not sent_media.get("package_images", {}).get(package_code):
            try:
                result = media_service.send_chatbot_image(
                    channel=channel,
                    contact=contact,
                    source_url=package_image,
                    cache_key=f"package_{package_code}_{customer_locale}",
                    caption=_localized_media_value(
                        (media_assets.get("captions", {}) or {}).get(package_code),
                        customer_locale,
                    ),
                )
                self._append_outbound_media_message(
                    contact_id=contact_id,
                    conversation_id=conversation_id,
                    channel=channel,
                    text=f"Product image sent: {package_code}",
                    source="chatbot_product_media",
                    provider_message_id=self._extract_provider_message_id(channel, result),
                )
                sent_media.setdefault("package_images", {})[package_code] = True
                self.contact_service.update_contact_profile(contact_id, {"sent_media": sent_media})
            except Exception as exc:  # noqa: BLE001 - media failures should not block chatbot text.
                logger.warning("chatbot_product_media_failed contact_id=%s package_code=%s error=%s", contact_id, package_code, exc)

    def _send_initial_promotion_image(
        self,
        *,
        channel: str,
        contact_id: str,
        conversation_id: str,
        runtime_settings: dict[str, Any],
        customer_locale: str,
    ) -> None:
        media_assets = runtime_settings.get("media_assets", {}) or {}
        promotion_image = _localized_media_value(
            media_assets.get("initial_promotion_images"),
            customer_locale,
        )
        if not promotion_image:
            return

        contact = self.contact_service.get_contact(contact_id)
        sent_media = deepcopy(contact.get("sent_media") or {})
        sent_media.setdefault("initial_promotion_languages", {})
        if sent_media.get("initial_promotion") or sent_media.get("initial_promotion_languages", {}).get(
            customer_locale
        ):
            return

        try:
            media_service = MetaMediaAssetService(db=self.db, meta_client=self.meta_client)
            result = media_service.send_chatbot_image(
                channel=channel,
                contact=contact,
                source_url=promotion_image,
                cache_key=f"initial_promotion_{customer_locale}",
                caption=_localized_media_value(
                    (media_assets.get("captions", {}) or {}).get("initial_promotion"),
                    customer_locale,
                ),
            )
            self._append_outbound_media_message(
                contact_id=contact_id,
                conversation_id=conversation_id,
                channel=channel,
                text=f"Initial promotion image sent: {customer_locale}",
                source="chatbot_initial_promotion_media",
                provider_message_id=self._extract_provider_message_id(channel, result),
            )
            sent_media["initial_promotion"] = True
            sent_media.setdefault("initial_promotion_languages", {})[customer_locale] = True
            self.contact_service.update_contact_profile(contact_id, {"sent_media": sent_media})
        except Exception as exc:  # noqa: BLE001 - media failures should not block chatbot text.
            logger.warning(
                "chatbot_initial_promotion_media_failed contact_id=%s error=%s",
                contact_id,
                exc,
            )

    def _append_outbound_media_message(
        self,
        *,
        contact_id: str,
        conversation_id: str,
        channel: str,
        text: str,
        source: str,
        provider_message_id: str | None,
    ) -> None:
        self.contact_service.append_message(
            contact_id=contact_id,
            channel=channel,
            direction="outbound",
            role="assistant",
            text=text,
            source=source,
            provider_message_id=provider_message_id,
            message_type="image",
            created_at=utcnow(),
            delivery_status="sent",
        )

    def _transcribe_audio_event(self, *, ref: Any, event: dict[str, Any]) -> str:
        payload = event.get("payload", {})
        data, content_type = self._download_audio_payload(event)
        mime_type = str(payload.get("mime_type") or content_type or "audio/ogg").split(";")[0]
        transcript = self.gemini_service.transcribe_audio_bytes(data=data, mime_type=mime_type).strip()
        if not transcript:
            raise ValueError("Gemini audio transcription returned empty text")
        updated_payload = dict(payload)
        updated_payload["transcribed_text"] = transcript
        updated_payload["text"] = transcript
        ref.set({"payload": updated_payload, "updated_at": utcnow()}, merge=True)
        return transcript

    def _download_audio_payload(self, event: dict[str, Any]) -> tuple[bytes, str]:
        payload = event.get("payload", {})
        if event["channel"] == "whatsapp":
            media_id = payload.get("media_id")
            if not media_id:
                raise ValueError("WhatsApp audio is missing media_id")
            return self.meta_client.download_whatsapp_media(media_id)
        if event["channel"] == "messenger":
            attachment_url = payload.get("attachment_url")
            if not attachment_url:
                raise ValueError("Messenger audio is missing attachment_url")
            response = requests.get(attachment_url, timeout=20)
            response.raise_for_status()
            return response.content, response.headers.get("content-type", "audio/ogg").split(";")[0]
        raise ValueError(f"Unsupported audio channel: {event['channel']}")

    def _process_audio_transcription_failure(self, *, ref: Any, event: dict[str, Any], contact: dict[str, Any]) -> dict[str, Any]:
        reply_text = "不好意思，我这边暂时听不清这段语音，方便您打字发给我吗？"
        send_result = self._send_channel_reply(channel=event["channel"], contact=contact, text=reply_text)
        self.contact_service.append_message(
            contact_id=event["contact_id"],
            channel=event["channel"],
            direction="outbound",
            role="assistant",
            text=reply_text,
            source="audio_transcription_failed",
            provider_message_id=self._extract_provider_message_id(event["channel"], send_result),
            created_at=utcnow(),
            delivery_status="sent",
        )
        ref.set({"status": "audio_transcription_failed", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
        return {"status": "audio_transcription_failed"}

    def _process_payment_confirmation_text(
        self,
        *,
        ref: Any,
        event: dict[str, Any],
        contact: dict[str, Any],
        incoming_text: str,
    ) -> dict[str, Any]:
        reply_text = self._payment_ack_text()
        send_result = self._send_channel_reply(channel=event["channel"], contact=contact, text=reply_text)
        self.contact_service.append_message(
            contact_id=event["contact_id"],
            channel=event["channel"],
            direction="outbound",
            role="assistant",
            text=reply_text,
            source="payment_confirmation_ack",
            provider_message_id=self._extract_provider_message_id(event["channel"], send_result),
            created_at=utcnow(),
            delivery_status="sent",
        )
        ref.set(
            {
                "status": "payment_confirmation_processed",
                "latest_customer_message": incoming_text,
                "processed_at": utcnow(),
                "updated_at": utcnow(),
            },
            merge=True,
        )
        return {"status": "payment_confirmation_processed"}

    def _process_payment_receipt_event(self, *, ref: Any, event: dict[str, Any]) -> dict[str, Any]:
        runtime_settings = self.settings_service.get_settings()
        contact_id = event["contact_id"]
        conversation_id = event["conversation_id"]
        contact = self.contact_service.get_contact(contact_id)
        session = self._find_active_checkout_session(contact_id)
        if not session:
            escalation_id = self._escalate_contact(
                contact=contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message="PayNow receipt image received but no active checkout session was found.",
                reason="unmatched_payment_receipt",
                runtime_settings=runtime_settings,
                send_customer_message=False,
            )
            ref.set(
                {
                    "status": "escalated_unmatched_receipt",
                    "escalation_id": escalation_id,
                    "processed_at": utcnow(),
                    "updated_at": utcnow(),
                },
                merge=True,
            )
            return {"status": "escalated_unmatched_receipt", "escalation_id": escalation_id}

        order_id = session["order_id"]
        receipt = self._store_inbound_receipt(event=event, order_id=order_id)
        receipt_url = receipt["url"]
        order_snapshot = self.db.collection("orders").document(order_id).get()
        order = order_snapshot.to_dict() if order_snapshot.exists else {}
        total_amount = float(order.get("total_amount") or session.get("total_amount") or 0)
        payment_id = stable_id("payment", order_id)
        now = utcnow()
        verification = self._build_payment_verification(
            order_id=order_id,
            payment_id=payment_id,
            expected_amount=total_amount,
            receipt_bytes=receipt["data"],
            content_type=receipt["content_type"],
            now=now,
        )
        transaction_id = verification.get("reference_number")
        risk_flags = []
        if verification.get("duplicate_detected"):
            risk_flags = [DUPLICATE_PAYMENT_REFERENCE_FLAG]

        payment_payload = {
            "order_id": order_id,
            "method": "paynow",
            "payment_method": "paynow",
            "amount": total_amount,
            "status": "payment_submitted",
            "transaction_id": transaction_id,
            "screenshot_url": receipt_url,
            "source": "marketing_chatbot",
            "payment_verification": verification,
            "created_at": now,
            "updated_at": now,
        }
        if risk_flags:
            payment_payload["risk_flags"] = risk_flags
        self.db.collection("payments").document(payment_id).set(
            payment_payload,
            merge=True,
        )
        order_payload = {
            "payment_status": "payment_submitted",
            "payment_receipt_url": receipt_url,
            "transaction_id": transaction_id,
            "payment_verification": verification,
            "updated_at": now,
        }
        if risk_flags:
            order_payload["risk_flags"] = self._append_risk_flags(order.get("risk_flags"), risk_flags)
        self.db.collection("orders").document(order_id).set(order_payload, merge=True)
        self.db.collection("marketing_checkout_sessions").document(session["session_id"]).set(
            {
                "status": "receipt_submitted",
                "payment_receipt_url": receipt_url,
                "payment_verification": verification,
                "updated_at": now,
            },
            merge=True,
        )
        duplicate_escalation_id = None
        if verification.get("duplicate_detected"):
            duplicate_escalation_id = self._escalate_contact(
                contact=contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message=(
                    "Duplicate payment reference detected: "
                    f"{verification.get('reference_number') or verification.get('reference_normalized')}"
                ),
                reason=DUPLICATE_PAYMENT_REFERENCE_FLAG,
                runtime_settings=runtime_settings,
                send_customer_message=False,
            )
        reply_text = self._payment_ack_text()
        send_result = self._send_channel_reply(channel=event["channel"], contact=contact, text=reply_text)
        provider_message_id = self._extract_provider_message_id(event["channel"], send_result)
        self.contact_service.append_message(
            contact_id=contact_id,
            channel=event["channel"],
            direction="outbound",
            role="assistant",
            text=reply_text,
            source="payment_receipt_ack",
            provider_message_id=provider_message_id,
            created_at=now,
            delivery_status="sent",
        )
        ref.set(
            {
                "status": "payment_receipt_processed",
                "order_id": order_id,
                "payment_receipt_url": receipt_url,
                "payment_verification": verification,
                "duplicate_escalation_id": duplicate_escalation_id,
                "processed_at": now,
                "updated_at": now,
            },
            merge=True,
        )
        return {"status": "payment_receipt_processed", "order_id": order_id}

    def _build_payment_verification(
        self,
        *,
        order_id: str,
        payment_id: str,
        expected_amount: float,
        receipt_bytes: bytes,
        content_type: str,
        now: Any,
    ) -> dict[str, Any]:
        try:
            analysis = self.gemini_service.analyze_payment_receipt_image(
                data=receipt_bytes,
                mime_type=content_type,
                expected_amount=expected_amount,
            )
        except Exception as exc:  # noqa: BLE001 - receipt analysis must not block order processing.
            logger.warning("payment_receipt_analysis_unavailable order_id=%s error=%s", order_id, exc)
            return self._unavailable_payment_verification(expected_amount=expected_amount, now=now)

        if not isinstance(analysis, dict) or not analysis:
            return self._unavailable_payment_verification(expected_amount=expected_amount, now=now)

        extracted_amount = self._extract_receipt_amount(analysis.get("paid_amount"))
        reference_number = self._clean_receipt_text(analysis.get("bank_transaction_reference"))
        reference_normalized = self._normalize_payment_reference(reference_number)
        warnings = self._normalize_receipt_warnings(analysis.get("warnings"))

        amount_match = extracted_amount is not None and abs(self._money(extracted_amount) - self._money(expected_amount)) <= 0.01
        if extracted_amount is None:
            warnings.append("Could not read paid amount from receipt")
        elif not amount_match:
            warnings.append("Amount does not match expected total")

        if not reference_normalized:
            warnings.append("Could not read bank transaction reference from receipt")

        duplicate_result = self._find_duplicate_payment_references(
            reference_number=reference_number,
            reference_normalized=reference_normalized,
            current_payment_id=payment_id,
        )
        duplicate_detected = bool(duplicate_result["duplicate_payment_ids"])
        if duplicate_detected:
            warnings.append("Duplicate payment reference detected")

        status = "ok" if amount_match and reference_normalized and not duplicate_detected and not warnings else "warning"
        return {
            "status": status,
            "expected_amount": self._money(expected_amount),
            "extracted_amount": self._money(extracted_amount) if extracted_amount is not None else None,
            "amount_match": amount_match,
            "reference_number": reference_number,
            "reference_normalized": reference_normalized,
            "duplicate_detected": duplicate_detected,
            "duplicate_order_ids": duplicate_result["duplicate_order_ids"],
            "duplicate_payment_ids": duplicate_result["duplicate_payment_ids"],
            "warnings": warnings,
            "confidence": self._normalize_confidence(analysis.get("confidence")),
            "currency": self._clean_receipt_text(analysis.get("currency")),
            "recipient_reference": self._clean_receipt_text(analysis.get("recipient_reference")),
            "payment_datetime": self._clean_receipt_text(analysis.get("payment_datetime")),
            "analyzed_at": now,
        }

    def _unavailable_payment_verification(self, *, expected_amount: float, now: Any) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "expected_amount": self._money(expected_amount),
            "extracted_amount": None,
            "amount_match": False,
            "reference_number": None,
            "reference_normalized": None,
            "duplicate_detected": False,
            "duplicate_order_ids": [],
            "duplicate_payment_ids": [],
            "warnings": ["AI receipt analysis unavailable"],
            "confidence": None,
            "currency": None,
            "recipient_reference": None,
            "payment_datetime": None,
            "analyzed_at": now,
        }

    def _find_duplicate_payment_references(
        self,
        *,
        reference_number: str | None,
        reference_normalized: str | None,
        current_payment_id: str,
    ) -> dict[str, list[str]]:
        if not reference_normalized:
            return {"duplicate_order_ids": [], "duplicate_payment_ids": []}

        queries = [
            ("payment_verification.reference_normalized", reference_normalized),
            ("transaction_id", reference_normalized),
        ]
        if reference_number and reference_number != reference_normalized:
            queries.append(("transaction_id", reference_number))

        matched: dict[str, str] = {}
        for field, value in queries:
            try:
                snapshots = self.db.collection("payments").where(field, "==", value).stream()
            except Exception as exc:  # noqa: BLE001 - do not block receipt processing on duplicate scan failures.
                logger.warning("payment_reference_duplicate_scan_failed field=%s error=%s", field, exc)
                continue

            for snapshot in snapshots:
                if snapshot.id == current_payment_id:
                    continue
                data = snapshot.to_dict()
                matched[snapshot.id] = str(data.get("order_id") or "")

        duplicate_payment_ids = sorted(matched)
        duplicate_order_ids = sorted({order_id for order_id in matched.values() if order_id})
        return {
            "duplicate_order_ids": duplicate_order_ids,
            "duplicate_payment_ids": duplicate_payment_ids,
        }

    def _find_active_checkout_session(self, contact_id: str) -> dict[str, Any] | None:
        contact = self.contact_service.get_contact(contact_id)
        existing_id = contact.get("checkout_session_id")
        if existing_id:
            snapshot = self.db.collection("marketing_checkout_sessions").document(existing_id).get()
            if snapshot.exists:
                session = snapshot.to_dict()
                session["session_id"] = snapshot.id
                if session.get("status") in {"active", "receipt_submitted"}:
                    return session

        docs = (
            self.db.collection("marketing_checkout_sessions")
            .where("contact_id", "==", contact_id)
            .where("status", "==", "active")
            .limit(1)
            .stream()
        )
        if docs:
            session = docs[0].to_dict()
            session["session_id"] = docs[0].id
            return session
        return None

    @staticmethod
    def _is_payment_confirmation_text(text: str) -> bool:
        normalized = str(text or "").casefold()
        payment_terms = ["完成付款", "已付款", "已经付款", "付款了", "付了", "paid", "paynow done", "payment done"]
        screenshot_terms = ["截图", "receipt", "screenshot"]
        return any(term in normalized for term in payment_terms) or (
            "付款" in normalized and any(term in normalized for term in screenshot_terms)
        )

    @staticmethod
    def _should_skip_initial_promotion(incoming_text: str, contact: dict[str, Any]) -> bool:
        if contact.get("automation_paused"):
            return True
        if contact.get("current_tag") in {"cart_hot", "handoff_pending"}:
            return True
        if contact.get("checkout_session_id") or contact.get("precheckout_paynow_qr_sent"):
            return True

        normalized = str(incoming_text or "").casefold()
        return any(term in normalized for term in INITIAL_PROMOTION_SUPPRESSION_TERMS)

    @staticmethod
    def _payment_ack_text() -> str:
        return "收到您的 PayNow 付款截图了，我们会尽快核对并安排发货。"

    @staticmethod
    def _safe_handoff_message(value: str) -> str:
        text = str(value or "").strip()
        blocked_terms = ["转接人工", "人工同事", "人工智能", "ai chatbot", "ai chartboard", "chatbot"]
        if any(term in text.casefold() for term in blocked_terms):
            return ""
        return text

    def _store_inbound_receipt(self, *, event: dict[str, Any], order_id: str) -> dict[str, Any]:
        payload = event.get("payload", {})
        channel = event["channel"]
        if channel == "whatsapp":
            media_id = payload.get("media_id")
            if not media_id:
                raise ValueError("WhatsApp receipt image is missing media_id")
            data, content_type = self.meta_client.download_whatsapp_media(media_id)
            receipt_seed = media_id
        elif channel == "messenger":
            attachment_url = payload.get("attachment_url")
            if not attachment_url:
                raise ValueError("Messenger receipt image is missing attachment_url")
            response = requests.get(attachment_url, timeout=20)
            response.raise_for_status()
            data = response.content
            content_type = response.headers.get("content-type", "image/jpeg").split(";")[0]
            receipt_seed = payload.get("provider_message_id") or attachment_url
        else:
            raise ValueError(f"Unsupported receipt channel: {channel}")

        extension = self._extension_for_content_type(content_type)
        receipt_id = stable_id("receipt", order_id, receipt_seed)
        url = upload_public_file_to_firebase(
            data=data,
            destination_path=f"payment_receipts/{order_id}/{receipt_id}.{extension}",
            content_type=content_type,
        )
        return {
            "url": url,
            "data": data,
            "content_type": content_type,
        }

    @staticmethod
    def _extract_receipt_amount(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", str(value))
        if not match:
            return None
        return float(match.group(0).replace(",", ""))

    @staticmethod
    def _clean_receipt_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() in {"null", "none", "n/a", "na"}:
            return None
        return text

    @staticmethod
    def _normalize_payment_reference(value: str | None) -> str | None:
        normalized = re.sub(r"[^A-Za-z0-9]", "", value or "").upper()
        if len(normalized) < MIN_PAYMENT_REFERENCE_LENGTH:
            return None
        return normalized

    @staticmethod
    def _normalize_receipt_warnings(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        warnings = []
        for item in value:
            text = str(item or "").strip()
            if text and text not in warnings:
                warnings.append(text)
        return warnings

    @staticmethod
    def _normalize_confidence(value: Any) -> float | None:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, confidence))

    @staticmethod
    def _append_risk_flags(existing: Any, additions: list[str]) -> list[str]:
        flags = [str(item) for item in existing] if isinstance(existing, list) else []
        for flag in additions:
            if flag not in flags:
                flags.append(flag)
        return flags

    @staticmethod
    def _extract_provider_message_id(channel: str, payload: dict[str, Any]) -> str | None:
        if channel == "messenger":
            return payload.get("message_id")
        messages = payload.get("messages") or []
        return messages[0].get("id") if messages else None

    @staticmethod
    def _append_checkout_url(reply_text: str, checkout_url: str) -> str:
        if checkout_url in reply_text:
            return reply_text
        spacer = "\n\n" if reply_text else ""
        return f"{reply_text}{spacer}{checkout_url}".strip()

    @staticmethod
    def _append_paynow_summary(
        reply_text: str,
        *,
        order_id: str,
        total_amount: float,
        paynow_settings: dict[str, Any],
    ) -> str:
        account_name = paynow_settings.get("account_name", "Boong Poultry Pte Ltd")
        reference = f"{paynow_settings.get('payment_reference_prefix', 'AQINA')}-{order_id}"
        summary = (
            f"PayNow 收款户名：{account_name}\n"
            f"金额：SGD {float(total_amount):.2f}\n"
            f"Reference：{reference}\n"
            "我会直接发送 PayNow QR 图片给您。付款后请把截图发回这里，我们才会安排订单处理。"
        )
        spacer = "\n\n" if reply_text else ""
        return f"{reply_text}{spacer}{summary}".strip()

    @staticmethod
    def _package_box_count(package: dict[str, Any]) -> int:
        if package.get("box_count"):
            return int(package["box_count"])
        code = str(package.get("code", ""))
        if code == "pack1":
            return 1
        if code in {"pack2", "energy_14"}:
            return 2
        if code in {"pack4", "maternal_28"}:
            return 4
        if code in {"pack6", "family_42"}:
            return 6
        return max(1, round(float(package.get("pack_count", 7)) / 7))

    @staticmethod
    def _shipping_fee_for(box_count: int) -> float:
        return 0.0

    @staticmethod
    def _money(value: float) -> float:
        return round(value + 1e-8, 2)

    @staticmethod
    def _extension_for_content_type(content_type: str) -> str:
        normalized = content_type.lower()
        if normalized == "image/png":
            return "png"
        if normalized == "image/webp":
            return "webp"
        return "jpg"

    @staticmethod
    def _normalize_turn(result: Any) -> SalesConversationTurn:
        if isinstance(result, SalesConversationTurn):
            return result
        if isinstance(result, dict):
            return SalesConversationTurn.model_validate(result)
        return SalesConversationTurn(reply_text=str(result or "").strip(), next_tag="lead_cold")

    @staticmethod
    def _merge_order_fields(current_fields: dict[str, Any], incoming_fields: dict[str, Any]) -> dict[str, Any]:
        merged = dict(current_fields or {})
        for key, value in incoming_fields.items():
            if value:
                merged[key] = value
        return merged

    @staticmethod
    def _resolve_gift_choice(
        *,
        selected_package_code: str | None,
        incoming_text: str,
        turn: SalesConversationTurn,
        contact: dict[str, Any],
        order_fields: dict[str, Any],
    ) -> dict[str, str] | None:
        if selected_package_code != "pack2":
            return None

        contact_order_fields = contact.get("order_fields") if isinstance(contact.get("order_fields"), dict) else {}
        candidates = [
            getattr(turn, "gift_choice", None),
            order_fields.get("gift_choice"),
            contact.get("gift_choice"),
            contact_order_fields.get("gift_choice"),
            incoming_text,
        ]
        for candidate in candidates:
            gift_choice = normalize_gift_choice(candidate)
            if gift_choice:
                return gift_choice
        return None

    @classmethod
    def _contact_with_channel_order_defaults(
        cls,
        *,
        channel: str,
        contact: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        if channel != "whatsapp":
            return contact, False

        order_fields = dict(contact.get("order_fields") or {})
        if cls._valid_order_field("phone", order_fields):
            return contact, False

        phone = cls._whatsapp_contact_phone(contact)
        if not phone:
            return contact, False

        enriched = dict(contact)
        enriched["order_fields"] = {**order_fields, "phone": phone}
        return enriched, True

    @classmethod
    def _apply_whatsapp_phone_default(
        cls,
        *,
        channel: str,
        contact: dict[str, Any],
        order_fields: dict[str, Any],
    ) -> tuple[dict[str, Any], bool]:
        fields = dict(order_fields or {})
        current_phone = cls._normalize_chat_phone(fields.get("phone"))
        if current_phone:
            fields["phone"] = current_phone
            return fields, False
        if channel != "whatsapp":
            return fields, False

        phone = cls._whatsapp_contact_phone(contact)
        if not phone:
            return fields, False
        fields["phone"] = phone
        return fields, True

    @classmethod
    def _checkout_ready_after_channel_defaults(
        cls,
        *,
        channel: str,
        turn: SalesConversationTurn,
        order_fields: dict[str, Any],
        missing_order_fields: list[str],
        phone_defaulted: bool,
    ) -> bool:
        if not turn.selected_package_code or missing_order_fields:
            return False
        if not all(cls._valid_order_field(field, order_fields) for field in ("name", "phone", "address")):
            return False
        return bool(turn.checkout_ready or (channel == "whatsapp" and phone_defaulted))

    @classmethod
    def _effective_missing_order_fields(
        cls,
        missing_fields: list[str],
        *,
        order_fields: dict[str, Any],
        require_all_fields: bool,
    ) -> list[str]:
        normalized_missing: list[str] = []
        for field in missing_fields or []:
            normalized = str(field or "").strip()
            if not normalized:
                continue
            if normalized in {"name", "phone", "address"} and cls._valid_order_field(normalized, order_fields):
                continue
            if normalized not in normalized_missing:
                normalized_missing.append(normalized)

        if require_all_fields:
            for field in ("name", "phone", "address"):
                if not cls._valid_order_field(field, order_fields) and field not in normalized_missing:
                    normalized_missing.append(field)
        return normalized_missing

    @staticmethod
    def _whatsapp_contact_phone(contact: dict[str, Any]) -> str | None:
        identifiers = contact.get("identifiers") or {}
        if not isinstance(identifiers, dict):
            return None
        for key in ("wa_id", "phone_e164"):
            phone = MarketingAutomationOrchestrator._normalize_chat_phone(identifiers.get(key))
            if phone:
                return phone
        return None

    @staticmethod
    def _normalize_chat_phone(value: Any) -> str | None:
        digits = "".join(character for character in str(value or "") if character.isdigit())
        if 8 <= len(digits) <= 20:
            return digits
        return None

    @classmethod
    def _valid_order_field(cls, field: str, order_fields: dict[str, Any]) -> bool:
        value = order_fields.get(field)
        if field == "phone":
            return cls._normalize_chat_phone(value) is not None
        return bool(str(value or "").strip())

    @staticmethod
    def _reply_requests_phone(reply_text: str) -> bool:
        normalized = str(reply_text or "").casefold()
        phone_terms = [
            "联系电话",
            "电话号码",
            "电话",
            "手机号码",
            "phone number",
            "contact number",
            "mobile number",
            "whatsapp number",
        ]
        return any(term in normalized for term in phone_terms)

    @staticmethod
    def _checkout_ready_reply(locale: str) -> str:
        if locale == "en":
            return "I have prepared your order details. I will send the PayNow QR image next."
        return "我已经帮您把订单资料整理好了。接下来我会直接发送 PayNow QR 图片给您。"

    @staticmethod
    def _facebook_comment_automation_settings(runtime_settings: dict[str, Any]) -> dict[str, Any]:
        raw = runtime_settings.get("facebook_comment_automation", {}) or {}
        keywords = raw.get("keywords") or DEFAULT_FACEBOOK_COMMENT_KEYWORDS
        return {
            "enabled": bool(raw.get("enabled", True)),
            "keywords": [
                keyword.strip()
                for keyword in (str(item) for item in keywords)
                if keyword.strip()
            ],
            "public_reply_enabled": bool(raw.get("public_reply_enabled", True)),
            "private_reply_enabled": bool(raw.get("private_reply_enabled", True)),
            "ignore_page_self_comments": bool(raw.get("ignore_page_self_comments", True)),
        }

    @staticmethod
    def _matched_comment_keyword(comment_text: str, keywords: list[str]) -> str | None:
        normalized_text = comment_text.casefold()
        for keyword in keywords:
            normalized_keyword = keyword.casefold().strip()
            if normalized_keyword and normalized_keyword in normalized_text:
                return keyword
        return None

    @staticmethod
    def _is_page_self_comment(*, value: dict[str, Any], entry: dict[str, Any], automation: dict[str, Any]) -> bool:
        if not automation.get("ignore_page_self_comments", True):
            return False
        commenter_id = str(value.get("from", {}).get("id") or "")
        page_id = str(entry.get("id") or value.get("page_id") or settings.meta_page_id or "")
        configured_page_id = str(settings.meta_page_id or "")
        return bool(commenter_id and (commenter_id == page_id or commenter_id == configured_page_id))

    @staticmethod
    def _is_page_self_comment_from_payload(*, payload: dict[str, Any], automation: dict[str, Any]) -> bool:
        if not automation.get("ignore_page_self_comments", True):
            return False
        commenter_id = str(payload.get("from_id") or "")
        page_id = str(payload.get("page_id") or settings.meta_page_id or "")
        configured_page_id = str(settings.meta_page_id or "")
        return bool(commenter_id and (commenter_id == page_id or commenter_id == configured_page_id))

    @staticmethod
    def _render_comment_template(template: str, payload: dict[str, Any]) -> str:
        name = str(payload.get("from_name") or "").strip() or "您"
        rendered = str(template or "").replace("[顾客名字]", name)
        rendered = rendered.replace("{{name}}", name).replace("{name}", name)
        return rendered.strip()

    @staticmethod
    def _mark_comment_event(ref: Any, *, status: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        update_payload = {
            "status": status,
            "processed_at": utcnow(),
            "updated_at": utcnow(),
            **(payload or {}),
        }
        ref.set(update_payload, merge=True)
        return {"status": status}

    def _record_event(self, event: NormalizedMarketingEvent) -> bool:
        event_id = stable_id("event", event.dedupe_key)
        ref = self.db.collection("marketing_events").document(event_id)
        if ref.get().exists:
            return False

        ref.set(
            {
                "provider": event.provider,
                "channel": event.channel,
                "event_type": event.event_type,
                "dedupe_key": event.dedupe_key,
                "status": "queued",
                "contact_id": event.contact_id,
                "conversation_id": event.conversation_id,
                "identifiers": event.identifiers,
                "payload": event.payload,
                "payload_hash": payload_hash(event.payload),
                "payload_excerpt": excerpt(event.payload),
                "received_at": event.occurred_at,
                "processed_at": None,
                "updated_at": utcnow(),
            }
        )
        return True


def _detect_customer_locale(incoming_text: str, contact: dict[str, Any]) -> str:
    text = str(incoming_text or "")
    chinese_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    ascii_letter_count = sum(1 for char in text if ("a" <= char.lower() <= "z"))
    if chinese_count:
        return "zh"
    if ascii_letter_count >= 3:
        return "en"
    previous_locale = str(contact.get("chatbot_locale") or "").strip().lower()
    if previous_locale in {"zh", "en"}:
        return previous_locale
    return "zh"


def _ensure_delivery_fee_answer(*, incoming_text: str, reply_text: str, customer_locale: str) -> str:
    if not _asks_delivery_fee(incoming_text):
        return reply_text
    if _answers_delivery_fee(reply_text):
        return reply_text
    prefix = (
        "The listed prices already include Singapore delivery fee, so there is no separate delivery fee."
        if customer_locale == "en"
        else "目前 1盒 SGD47.90、2盒 SGD79.80 已包含新加坡配送费，不需要另外加邮费。"
    )
    text = str(reply_text or "").strip()
    if not text:
        return prefix
    return f"{prefix}\n\n{text}"


def _asks_delivery_fee(text: str) -> bool:
    normalized = str(text or "").strip().lower()
    return any(term in normalized for term in DELIVERY_FEE_QUESTION_TERMS)


def _answers_delivery_fee(text: str) -> bool:
    normalized = str(text or "").strip().lower()
    return any(term in normalized for term in DELIVERY_FEE_ANSWER_TERMS)


def _localized_media_value(value: Any, locale: str) -> str:
    normalized_locale = locale if locale in {"zh", "en"} else "zh"
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        localized = value.get(normalized_locale) or value.get("zh") or value.get("en")
        if localized:
            return str(localized).strip()
        for candidate in value.values():
            if candidate:
                return str(candidate).strip()
    return ""
