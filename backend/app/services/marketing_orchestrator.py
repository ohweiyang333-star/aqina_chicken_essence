"""Orchestration logic for webhook ingestion and internal marketing tasks."""
from __future__ import annotations

from typing import Any
import requests

from app.core.config import settings
from app.models.chatbot import SalesConversationTurn
from app.models.marketing import NormalizedMarketingEvent
from app.services.meta_media_assets import MetaMediaAssetService
from app.services.chatbot_settings import ChatbotSettingsService
from app.services.follow_up import FollowUpEngine
from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_utils import ensure_datetime, excerpt, payload_hash, stable_id, utcnow
from app.services.storage_uploads import upload_public_file_to_firebase


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
                message = message_event.get("message", {})
                attachments = message.get("attachments", [])
                image_attachment = next(
                    (item for item in attachments if item.get("type") == "image"),
                    None,
                )
                if "text" not in message and not image_attachment:
                    continue

                occurred_at = ensure_datetime(message_event.get("timestamp")) or utcnow()
                identifiers = {"psid": str(message_event.get("sender", {}).get("id", ""))}
                message_type = "image" if image_attachment else "text"
                message_text = message.get("text", "") if message_type == "text" else "[image]"
                contact_id, conversation_id = self.contact_service.upsert_contact_from_event(
                    channel="messenger",
                    identifiers=identifiers,
                    current_tag="lead_cold",
                    status="active",
                    interaction_time=occurred_at,
                )
                self.contact_service.append_message(
                    contact_id=contact_id,
                    channel="messenger",
                    direction="inbound",
                    role="user",
                    text=message_text,
                    source="messenger_webhook",
                    provider_message_id=message.get("mid"),
                    message_type=message_type,
                    created_at=occurred_at,
                )
                normalized = NormalizedMarketingEvent(
                    provider="meta",
                    channel="messenger",
                    event_type="messenger_message_received",
                    dedupe_key=f"messenger:{message.get('mid')}",
                    occurred_at=occurred_at,
                    contact_id=contact_id,
                    conversation_id=conversation_id,
                    identifiers=identifiers,
                    payload={
                        "channel": "messenger",
                        "text": message_text,
                        "message_type": message_type,
                        "attachment_url": (image_attachment or {}).get("payload", {}).get("url"),
                        "provider_message_id": message.get("mid"),
                        "sender_psid": identifiers["psid"],
                    },
                )
                created = self._record_event(normalized)
                if created:
                    event_id = stable_id("event", normalized.dedupe_key)
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
                    continue
                occurred_at = utcnow()
                normalized = NormalizedMarketingEvent(
                    provider="meta",
                    channel="facebook",
                    event_type="facebook_comment_created",
                    dedupe_key=f"facebook-comment:{value.get('comment_id')}",
                    occurred_at=occurred_at,
                    identifiers={"commenter_id": str(value.get("from", {}).get("id", ""))},
                    payload={
                        "comment_id": value.get("comment_id"),
                        "post_id": value.get("post_id"),
                        "comment_text": value.get("message", ""),
                        "from_id": value.get("from", {}).get("id"),
                        "page_id": entry.get("id"),
                    },
                )
                if self._record_event(normalized):
                    event_id = stable_id("event", normalized.dedupe_key)
                    self.task_queue.enqueue_marketing_event(event_id, "process-comment-event")
                    accepted += 1

        return accepted

    def ingest_whatsapp_webhook(self, payload: dict[str, Any]) -> int:
        accepted = 0
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    message_type = message.get("type")
                    if message_type not in {"text", "image"}:
                        continue

                    occurred_at = ensure_datetime(message.get("timestamp")) or utcnow()
                    wa_id = str(message.get("from", ""))
                    identifiers = {"wa_id": wa_id, "phone_e164": wa_id}
                    message_text = (
                        message.get("text", {}).get("body", "")
                        if message_type == "text"
                        else message.get("image", {}).get("caption") or "[image]"
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
                            "media_id": message.get("image", {}).get("id"),
                            "mime_type": message.get("image", {}).get("mime_type"),
                            "sha256": message.get("image", {}).get("sha256"),
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

                for status in value.get("statuses", []):
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
        return accepted

    def process_comment_event(self, event_id: str) -> dict[str, Any]:
        ref = self.db.collection("marketing_events").document(event_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise KeyError(f"Marketing event not found: {event_id}")

        runtime_settings = self.settings_service.get_settings()
        event = snapshot.to_dict()
        payload = event.get("payload", {})
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
        public_reply = (
            runtime_settings.get("crm_follow_up_rules", {})
            .get("comment_hook", {})
            .get("public_reply", {})
            .get("instruction")
            or settings.meta_comment_reply_template
        )
        private_reply = (
            runtime_settings.get("crm_follow_up_rules", {})
            .get("comment_hook", {})
            .get("private_opening", {})
            .get("instruction")
            or settings.meta_private_reply_template
        )
        self.meta_client.reply_to_comment(comment_id=payload.get("comment_id", ""), message=public_reply)
        self.meta_client.send_private_reply(comment_id=payload.get("comment_id", ""), message=private_reply)
        self.contact_service.append_message(
            contact_id=contact_id,
            channel="facebook",
            direction="outbound",
            role="assistant",
            text=private_reply,
            source="facebook_private_reply",
            provider_comment_id=payload.get("comment_id"),
            message_type="private_reply",
        )
        ref.set(
            {
                "status": "processed",
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "processed_at": utcnow(),
                "updated_at": utcnow(),
            },
            merge=True,
        )
        return {"status": "processed", "contact_id": contact_id}

    def process_inbound_message(self, event_id: str) -> dict[str, Any]:
        ref = self.db.collection("marketing_events").document(event_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise KeyError(f"Marketing event not found: {event_id}")

        event = snapshot.to_dict()
        payload = event.get("payload", {})
        if payload.get("message_type") == "image":
            return self._process_payment_receipt_event(ref=ref, event=event)

        if not self.gemini_service.is_ready():
            ref.set({"status": "blocked_configuration", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
            return {"status": "blocked_configuration"}

        runtime_settings = self.settings_service.get_settings()
        contact_id = event["contact_id"]
        conversation_id = event["conversation_id"]
        contact = self.contact_service.get_contact(contact_id)
        messages = self.contact_service.get_recent_messages(conversation_id)
        turn = self._normalize_turn(
            self.gemini_service.generate_chat_reply(
                contact=contact,
                messages=messages,
                incoming_text=payload.get("text", ""),
                channel=event["channel"],
                runtime_settings=runtime_settings,
            )
        )

        merged_order_fields = self._merge_order_fields(contact.get("order_fields", {}), turn.order_fields.model_dump())
        update_fields = {
            "lead_goal": turn.lead_goal,
            "recommended_package_code": turn.recommended_package_code,
            "upgrade_package_code": turn.upgrade_package_code,
            "selected_package_code": turn.selected_package_code,
            "order_fields": merged_order_fields,
            "missing_order_fields": turn.missing_order_fields,
            "future_contact_opt_in": bool(turn.opt_in_granted),
        }
        self.contact_service.update_contact_profile(contact_id, update_fields)

        if turn.escalate or turn.next_tag == "handoff_pending":
            escalation_id = self._escalate_contact(
                contact=contact,
                contact_id=contact_id,
                conversation_id=conversation_id,
                latest_customer_message=payload.get("text", ""),
                reason=turn.escalation_reason or "manual_handoff_requested",
                runtime_settings=runtime_settings,
            )
            ref.set({"status": "escalated", "processed_at": utcnow(), "updated_at": utcnow()}, merge=True)
            return {"status": "escalated", "escalation_id": escalation_id}

        checkout_session = None
        reply_text = turn.reply_text.strip()
        if turn.checkout_ready and turn.selected_package_code and not turn.missing_order_fields:
            checkout_session = self._create_checkout_session(
                contact_id=contact_id,
                conversation_id=conversation_id,
                selected_package_code=turn.selected_package_code,
                order_fields=merged_order_fields,
                runtime_settings=runtime_settings,
            )
            reply_text = self._append_paynow_summary(
                reply_text,
                order_id=checkout_session["order_id"],
                total_amount=checkout_session["total_amount"],
                paynow_settings=runtime_settings.get("payment", {}).get("paynow", {}),
            )

        if turn.next_tag != contact.get("current_tag"):
            self.contact_service.update_contact_tag(
                contact_id,
                turn.next_tag,
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
        return {"status": "processed", "checkout_session_id": checkout_session["session_id"] if checkout_session else None}

    def _create_checkout_session(
        self,
        *,
        contact_id: str,
        conversation_id: str,
        selected_package_code: str,
        order_fields: dict[str, Any],
        runtime_settings: dict[str, Any],
    ) -> dict[str, Any]:
        packages = runtime_settings.get("packages", {})
        package = packages.get(selected_package_code)
        if not package:
            raise KeyError(f"Unknown package code: {selected_package_code}")

        existing_id = self.contact_service.get_contact(contact_id).get("checkout_session_id")
        if existing_id:
            existing = self.db.collection("marketing_checkout_sessions").document(existing_id).get()
            if existing.exists:
                session = existing.to_dict()
                session["session_id"] = existing.id
                return session

        now = utcnow()
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
            "total_amount": total_amount,
            "payment_method": "paynow",
            "payment_status": "pending",
            "order_status": "pending",
            "payment_receipt_url": None,
            "source": "marketing_chatbot",
            "marketing_contact_id": contact_id,
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
            "total_amount": total_amount,
            "created_at": now,
            "updated_at": now,
        }
        self.db.collection("marketing_checkout_sessions").document(session_id).set(session_payload)
        self.db.collection("orders").document(order_id).set({"checkout_session_id": session_id, "updated_at": now}, merge=True)
        return {"session_id": session_id, **session_payload}

    def _escalate_contact(
        self,
        *,
        contact: dict[str, Any],
        contact_id: str,
        conversation_id: str,
        latest_customer_message: str,
        reason: str,
        runtime_settings: dict[str, Any],
    ) -> str:
        escalation_settings = runtime_settings.get("escalation", {})
        handoff_message = runtime_settings.get("handoff_message", "")
        if handoff_message:
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
        escalation_id = stable_id("escalation", contact_id, conversation_id, reason, utcnow().isoformat())
        template_variables = [
            contact.get("identifiers", {}).get("wa_id") or contact.get("identifiers", {}).get("psid") or contact_id,
            reason,
            latest_customer_message[:120],
        ]
        payload = {
            "contact_id": contact_id,
            "conversation_id": conversation_id,
            "reason": reason,
            "latest_customer_message": latest_customer_message,
            "status": "open",
            "private_whatsapp_number": escalation_settings.get("private_whatsapp_number", ""),
            "template_name": escalation_settings.get("whatsapp_template_name", ""),
            "template_variables": template_variables,
            "notified_at": utcnow(),
            "resolved_at": None,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        self.db.collection("marketing_escalations").document(escalation_id).set(payload)

        if escalation_settings.get("enabled") and escalation_settings.get("private_whatsapp_number") and escalation_settings.get("whatsapp_template_name"):
            self.meta_client.send_whatsapp_template(
                to=escalation_settings["private_whatsapp_number"],
                template_name=escalation_settings["whatsapp_template_name"],
                body_variables=template_variables,
            )
        return escalation_id

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
        receipt_url = self._store_inbound_receipt(event=event, order_id=order_id)
        order_snapshot = self.db.collection("orders").document(order_id).get()
        order = order_snapshot.to_dict() if order_snapshot.exists else {}
        total_amount = float(order.get("total_amount") or session.get("total_amount") or 0)
        payment_id = stable_id("payment", order_id)
        now = utcnow()
        self.db.collection("payments").document(payment_id).set(
            {
                "order_id": order_id,
                "method": "paynow",
                "payment_method": "paynow",
                "amount": total_amount,
                "status": "payment_submitted",
                "transaction_id": None,
                "screenshot_url": receipt_url,
                "source": "marketing_chatbot",
                "created_at": now,
                "updated_at": now,
            },
            merge=True,
        )
        self.db.collection("orders").document(order_id).set(
            {
                "payment_status": "payment_submitted",
                "payment_receipt_url": receipt_url,
                "updated_at": now,
            },
            merge=True,
        )
        self.db.collection("marketing_checkout_sessions").document(session["session_id"]).set(
            {"status": "receipt_submitted", "payment_receipt_url": receipt_url, "updated_at": now},
            merge=True,
        )
        reply_text = "收到您的 PayNow 付款截图了，我们会人工核对后尽快安排发货。"
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
                "processed_at": now,
                "updated_at": now,
            },
            merge=True,
        )
        return {"status": "payment_receipt_processed", "order_id": order_id}

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

    def _store_inbound_receipt(self, *, event: dict[str, Any], order_id: str) -> str:
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
        return upload_public_file_to_firebase(
            data=data,
            destination_path=f"payment_receipts/{order_id}/{receipt_id}.{extension}",
            content_type=content_type,
        )

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
        if code in {"pack1", "trial_3"}:
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
        return 0.0 if box_count >= 2 else 8.0

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
