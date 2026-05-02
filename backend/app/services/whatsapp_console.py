"""Admin WhatsApp inbox, template, and campaign operations."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.core.config import settings
from app.models.marketing import WhatsAppCampaignRequest
from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_utils import ensure_datetime, stable_id, utcnow
from app.services.meta_client import get_meta_client
from app.services.task_queue import get_task_queue_service


OPT_OUT_KEYWORDS = {
    "stop",
    "unsubscribe",
    "退订",
    "不要再发",
    "不要发",
    "别发",
}


class WhatsAppConsoleService:
    """Business logic for the admin WhatsApp operating console."""

    def __init__(
        self,
        *,
        db: Any,
        meta_client: Any | None = None,
        task_queue: Any | None = None,
        contact_service: MarketingContactService | None = None,
    ) -> None:
        self.db = db
        self.meta_client = meta_client or get_meta_client()
        self.task_queue = task_queue or get_task_queue_service()
        self.contact_service = contact_service or MarketingContactService(db)

    def list_conversations(self, limit: int = 50) -> dict[str, Any]:
        docs = (
            self.db.collection("marketing_conversations")
            .where("channel", "==", "whatsapp")
            .order_by("last_message_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        items = [self._conversation_summary(doc.id, doc.to_dict()) for doc in docs]
        return {"items": items}

    def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        contact["contact_id"] = conversation["contact_id"]
        messages = self._messages_for(conversation_id, limit=100)
        return {
            "conversation": self._conversation_summary(conversation_id, conversation),
            "contact": contact,
            "messages": messages,
            "orders": self._orders_for_contact(contact),
            "window": self._window_payload(contact),
        }

    def send_manual_text(self, conversation_id: str, text: str, admin: dict[str, Any]) -> dict[str, Any]:
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        if not self._customer_window_open(contact):
            raise ValueError("Customer service window is closed. Use an approved WhatsApp template.")

        result = self.meta_client.send_whatsapp_text(
            to=contact.get("identifiers", {}).get("wa_id", ""),
            text=text,
        )
        provider_message_id = self._extract_provider_message_id(result)
        _, message_id = self.contact_service.append_message(
            contact_id=conversation["contact_id"],
            channel="whatsapp",
            direction="outbound",
            role="admin",
            text=text,
            source="admin_whatsapp_console",
            provider_message_id=provider_message_id,
            delivery_status="sent",
            created_at=utcnow(),
        )
        self._index_provider_message(
            provider_message_id=provider_message_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        return {
            "status": "sent",
            "provider_message_id": provider_message_id,
            "message_id": message_id,
            "sent_by": admin.get("email") or admin.get("uid"),
        }

    def send_template(
        self,
        conversation_id: str,
        *,
        template_name: str,
        language_code: str,
        body_variables: list[str],
        admin: dict[str, Any],
    ) -> dict[str, Any]:
        conversation = self._get_conversation(conversation_id)
        contact = self.contact_service.get_contact(conversation["contact_id"])
        self._require_approved_template(template_name, language_code)
        result = self.meta_client.send_whatsapp_template(
            to=contact.get("identifiers", {}).get("wa_id", ""),
            template_name=template_name,
            language_code=language_code,
            body_variables=body_variables,
        )
        provider_message_id = self._extract_provider_message_id(result)
        text = f"Template {template_name} sent"
        _, message_id = self.contact_service.append_message(
            contact_id=conversation["contact_id"],
            channel="whatsapp",
            direction="outbound",
            role="admin",
            text=text,
            source="admin_whatsapp_template",
            provider_message_id=provider_message_id,
            message_type="template",
            delivery_status="sent",
            created_at=utcnow(),
        )
        self._index_provider_message(
            provider_message_id=provider_message_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        return {
            "status": "sent",
            "provider_message_id": provider_message_id,
            "message_id": message_id,
            "sent_by": admin.get("email") or admin.get("uid"),
        }

    def update_automation(self, conversation_id: str, *, paused: bool, reason: str | None) -> dict[str, Any]:
        conversation = self._get_conversation(conversation_id)
        if paused:
            self.contact_service.pause_automation(
                conversation["contact_id"],
                reason=reason or "manual_whatsapp_console",
            )
            return {"status": "paused"}
        self.contact_service.resume_automation(conversation["contact_id"])
        return {"status": "resumed"}

    def list_templates(self) -> dict[str, Any]:
        docs = self.db.collection("whatsapp_templates").stream()
        items = []
        for doc in docs:
            item = doc.to_dict()
            item["template_id"] = doc.id
            items.append(item)
        items.sort(key=lambda item: (item.get("name", ""), item.get("language_code", "")))
        return {"items": items}

    def upsert_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = utcnow()
        template_id = self._template_id(payload["name"], payload.get("language_code", "en_US"))
        doc = {
            "name": payload["name"],
            "language_code": payload.get("language_code", "en_US"),
            "category": payload.get("category", "MARKETING").upper(),
            "status": payload.get("status", "APPROVED").upper(),
            "components": payload.get("components", []),
            "source": "admin",
            "updated_at": now,
        }
        ref = self.db.collection("whatsapp_templates").document(template_id)
        if not ref.get().exists:
            doc["created_at"] = now
        ref.set(doc, merge=True)
        return {"template_id": template_id, **doc}

    def sync_templates(self) -> dict[str, Any]:
        response = self.meta_client.list_whatsapp_templates()
        synced = []
        for item in response.get("data", []):
            payload = {
                "name": item.get("name", ""),
                "language_code": item.get("language") or item.get("language_code") or "en_US",
                "category": item.get("category", "MARKETING"),
                "status": item.get("status", "UNKNOWN"),
                "components": item.get("components", []),
            }
            if not payload["name"]:
                continue
            saved = self.upsert_template(payload)
            saved["source"] = "meta"
            self.db.collection("whatsapp_templates").document(saved["template_id"]).set(
                {"source": "meta", "synced_at": utcnow()},
                merge=True,
            )
            synced.append(saved)
        return {"synced_count": len(synced), "items": synced}

    def health(self) -> dict[str, Any]:
        config = {
            "access_token": bool(settings.meta_whatsapp_access_token),
            "phone_number_id": bool(settings.meta_whatsapp_phone_number_id),
            "business_account_id": bool(settings.meta_whatsapp_business_account_id),
            "cloud_tasks_enabled": settings.cloud_tasks_enabled,
            "campaign_queue": settings.cloud_tasks_campaigns_queue,
        }
        phone = None
        phone_error = None
        if all([config["access_token"], config["phone_number_id"]]):
            try:
                phone = self.meta_client.get_whatsapp_phone_number_health()
            except Exception as exc:  # pragma: no cover - exercised against Meta in production
                phone_error = str(exc)
        templates = self.list_templates()["items"]
        return {
            "ready": all([config["access_token"], config["phone_number_id"], config["business_account_id"]]),
            "config": config,
            "phone": phone,
            "phone_error": phone_error,
            "local_template_count": len(templates),
        }

    def preview_campaign(self, request: WhatsAppCampaignRequest) -> dict[str, Any]:
        self._require_approved_template(request.template_name, request.language_code)
        return self._campaign_preview_payload(request)

    def create_campaign(self, request: WhatsAppCampaignRequest, admin: dict[str, Any]) -> dict[str, Any]:
        preview = self.preview_campaign(request)
        now = utcnow()
        campaign_id = stable_id("whatsapp_campaign", request.name, request.template_name, now.isoformat())
        payload = {
            "name": request.name,
            "template_name": request.template_name,
            "language_code": request.language_code,
            "body_variables": request.body_variables,
            "audience_tags": request.audience_tags,
            "status": "draft",
            "eligible_count": preview["eligible_count"],
            "skipped_opt_out_count": preview["skipped_opt_out_count"],
            "window_closed_count": preview["window_closed_count"],
            "queued_count": 0,
            "sent_count": 0,
            "failed_count": 0,
            "created_by": admin.get("email") or admin.get("uid"),
            "created_at": now,
            "updated_at": now,
        }
        self.db.collection("whatsapp_campaigns").document(campaign_id).set(payload)
        return {"campaign_id": campaign_id, **payload, "preview": preview}

    def list_campaigns(self, limit: int = 50) -> dict[str, Any]:
        docs = (
            self.db.collection("whatsapp_campaigns")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        items = []
        for doc in docs:
            row = doc.to_dict()
            row["campaign_id"] = doc.id
            items.append(row)
        return {"items": items}

    def get_campaign(self, campaign_id: str) -> dict[str, Any]:
        ref = self.db.collection("whatsapp_campaigns").document(campaign_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise KeyError(f"Campaign not found: {campaign_id}")
        campaign = snapshot.to_dict()
        campaign["campaign_id"] = campaign_id
        recipients = []
        for doc in ref.collection("recipients").stream():
            recipient = doc.to_dict()
            recipient["recipient_id"] = doc.id
            recipients.append(recipient)
        recipients.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        return {"campaign": campaign, "recipients": recipients}

    def launch_campaign(self, campaign_id: str, *, preview_confirmed: bool) -> dict[str, Any]:
        if not preview_confirmed:
            raise ValueError("Campaign preview must be confirmed before launch.")
        campaign_ref = self.db.collection("whatsapp_campaigns").document(campaign_id)
        snapshot = campaign_ref.get()
        if not snapshot.exists:
            raise KeyError(f"Campaign not found: {campaign_id}")
        campaign = snapshot.to_dict()
        if campaign.get("status") not in {"draft", "paused"}:
            raise ValueError("Only draft or paused campaigns can be launched.")

        request = WhatsAppCampaignRequest(
            name=campaign["name"],
            template_name=campaign["template_name"],
            language_code=campaign.get("language_code", "en_US"),
            body_variables=campaign.get("body_variables", []),
            audience_tags=campaign.get("audience_tags", []),
        )
        self._require_approved_template(request.template_name, request.language_code)
        preview = self._campaign_preview_payload(request)
        now = utcnow()
        queued_count = 0
        for index, recipient in enumerate(preview["recipients"]):
            recipient_id = stable_id("campaign_recipient", campaign_id, recipient["contact_id"])
            payload = {
                **recipient,
                "campaign_id": campaign_id,
                "template_name": campaign["template_name"],
                "language_code": campaign.get("language_code", "en_US"),
                "body_variables": campaign.get("body_variables", []),
                "status": "queued",
                "provider_message_id": None,
                "error_code": None,
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
            campaign_ref.collection("recipients").document(recipient_id).set(payload, merge=True)
            schedule_at = now + timedelta(seconds=index * 8)
            task_name = self.task_queue.enqueue_campaign_recipient(campaign_id, recipient_id, schedule_at)
            campaign_ref.collection("recipients").document(recipient_id).set(
                {"cloud_task_name": task_name, "updated_at": utcnow()},
                merge=True,
            )
            queued_count += 1

        campaign_ref.set(
            {
                "status": "queued",
                "queued_count": queued_count,
                "eligible_count": preview["eligible_count"],
                "skipped_opt_out_count": preview["skipped_opt_out_count"],
                "window_closed_count": preview["window_closed_count"],
                "launched_at": now,
                "updated_at": utcnow(),
            },
            merge=True,
        )
        return {"status": "queued", "campaign_id": campaign_id, "queued_count": queued_count}

    def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        self._set_campaign_status(campaign_id, "paused")
        return {"status": "paused", "campaign_id": campaign_id}

    def cancel_campaign(self, campaign_id: str) -> dict[str, Any]:
        self._set_campaign_status(campaign_id, "cancelled")
        return {"status": "cancelled", "campaign_id": campaign_id}

    def process_campaign_recipient(self, campaign_id: str, recipient_id: str) -> dict[str, Any]:
        campaign_ref = self.db.collection("whatsapp_campaigns").document(campaign_id)
        campaign_snapshot = campaign_ref.get()
        if not campaign_snapshot.exists:
            raise KeyError(f"Campaign not found: {campaign_id}")
        campaign = campaign_snapshot.to_dict()
        if campaign.get("status") not in {"queued", "sending"}:
            return {"status": "skipped_campaign_not_active"}

        recipient_ref = campaign_ref.collection("recipients").document(recipient_id)
        recipient_snapshot = recipient_ref.get()
        if not recipient_snapshot.exists:
            raise KeyError(f"Campaign recipient not found: {recipient_id}")
        recipient = recipient_snapshot.to_dict()
        if recipient.get("status") not in {"queued", "retry"}:
            return {"status": "skipped_recipient_not_queued"}

        contact = self.contact_service.get_contact(recipient["contact_id"])
        if not self._contact_marketing_eligible(contact, campaign.get("audience_tags", [])):
            recipient_ref.set(
                {
                    "status": "skipped_opt_out",
                    "error_message": "Contact is not opted in for marketing.",
                    "updated_at": utcnow(),
                },
                merge=True,
            )
            self._recount_campaign(campaign_id)
            return {"status": "skipped_opt_out"}

        try:
            self._require_approved_template(campaign["template_name"], campaign.get("language_code", "en_US"))
            result = self.meta_client.send_whatsapp_template(
                to=recipient["wa_id"],
                template_name=campaign["template_name"],
                language_code=campaign.get("language_code", "en_US"),
                body_variables=campaign.get("body_variables", []),
            )
        except Exception as exc:
            recipient_ref.set(
                {
                    "status": "failed",
                    "error_message": str(exc),
                    "updated_at": utcnow(),
                },
                merge=True,
            )
            self._recount_campaign(campaign_id)
            return {"status": "failed", "error_message": str(exc)}

        provider_message_id = self._extract_provider_message_id(result)
        conversation_id = contact.get("latest_conversation_id")
        if conversation_id:
            _, message_id = self.contact_service.append_message(
                contact_id=recipient["contact_id"],
                channel="whatsapp",
                direction="outbound",
                role="assistant",
                text=f"Campaign template {campaign['template_name']} sent",
                source="whatsapp_campaign",
                provider_message_id=provider_message_id,
                message_type="template",
                delivery_status="sent",
                created_at=utcnow(),
            )
            message_ref = (
                self.db.collection("marketing_conversations")
                .document(conversation_id)
                .collection("messages")
                .document(message_id)
            )
            message_ref.set(
                {
                    "campaign_id": campaign_id,
                    "campaign_recipient_id": recipient_id,
                    "updated_at": utcnow(),
                },
                merge=True,
            )
            self._index_provider_message(
                provider_message_id=provider_message_id,
                conversation_id=conversation_id,
                message_id=message_id,
                campaign_id=campaign_id,
                campaign_recipient_id=recipient_id,
            )

        recipient_ref.set(
            {
                "status": "sent",
                "provider_message_id": provider_message_id,
                "sent_at": utcnow(),
                "updated_at": utcnow(),
            },
            merge=True,
        )
        campaign_ref.set({"status": "sending", "updated_at": utcnow()}, merge=True)
        self._recount_campaign(campaign_id)
        return {"status": "sent", "provider_message_id": provider_message_id}

    def handle_inbound_opt_out(self, contact_id: str, message_text: str) -> bool:
        if not is_marketing_opt_out_text(message_text):
            return False
        self.contact_service.mark_marketing_opt_out(contact_id, source="whatsapp_inbound_keyword")
        return True

    def update_delivery_status(self, status_payload: dict[str, Any]) -> dict[str, Any]:
        provider_message_id = status_payload.get("id")
        delivery_status = status_payload.get("status")
        if not provider_message_id or not delivery_status:
            return {"updated": 0}

        errors = status_payload.get("errors") or []
        first_error = errors[0] if errors else {}
        update = {
            "delivery_status": delivery_status,
            "status_payload": status_payload,
            "updated_at": utcnow(),
        }
        if first_error:
            update["error_code"] = first_error.get("code")
            update["error_message"] = first_error.get("message") or first_error.get("title")

        updated = 0
        for message_snapshot in self._find_messages_by_provider_id(provider_message_id):
            message_snapshot.reference.set(update, merge=True)
            message = message_snapshot.to_dict()
            campaign_id = message.get("campaign_id")
            recipient_id = message.get("campaign_recipient_id")
            if campaign_id and recipient_id:
                self._update_campaign_recipient_status(
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    delivery_status=delivery_status,
                    error_code=update.get("error_code"),
                    error_message=update.get("error_message"),
                )
            updated += 1

        if updated == 0:
            for recipient_snapshot in self._find_recipients_by_provider_id(provider_message_id):
                path_ref = recipient_snapshot.reference
                recipient = recipient_snapshot.to_dict()
                campaign_id = recipient.get("campaign_id")
                path_ref.set(
                    {
                        "status": delivery_status,
                        "error_code": update.get("error_code"),
                        "error_message": update.get("error_message"),
                        "status_payload": status_payload,
                        "updated_at": utcnow(),
                    },
                    merge=True,
                )
                if campaign_id:
                    self._recount_campaign(campaign_id)
                updated += 1
        return {"updated": updated}

    def _conversation_summary(self, conversation_id: str, conversation: dict[str, Any]) -> dict[str, Any]:
        contact = self.contact_service.get_contact(conversation["contact_id"])
        contact["contact_id"] = conversation["contact_id"]
        latest_messages = self._messages_for(conversation_id, limit=1, descending=True)
        latest = latest_messages[0] if latest_messages else None
        return {
            "conversation_id": conversation_id,
            "contact_id": conversation["contact_id"],
            "channel": "whatsapp",
            "customer_name": self._contact_name(contact),
            "wa_id": contact.get("identifiers", {}).get("wa_id", ""),
            "current_tag": contact.get("current_tag", ""),
            "automation_paused": bool(contact.get("automation_paused")),
            "marketing_status": contact.get("marketing_status", "unknown"),
            "last_message_at": conversation.get("last_message_at"),
            "latest_message": latest,
            "window": self._window_payload(contact),
            "orders": self._orders_for_contact(contact)[:3],
        }

    def _campaign_preview_payload(self, request: WhatsAppCampaignRequest) -> dict[str, Any]:
        recipients = []
        skipped_opt_out_count = 0
        window_closed_count = 0
        for contact_doc in self.db.collection("marketing_contacts").stream():
            contact = contact_doc.to_dict()
            if contact.get("channel") != "whatsapp":
                continue
            wa_id = contact.get("identifiers", {}).get("wa_id") or contact.get("identifiers", {}).get("phone_e164")
            if not wa_id:
                continue
            if not self._contact_marketing_eligible(contact, request.audience_tags):
                skipped_opt_out_count += 1
                continue
            if not self._customer_window_open(contact):
                window_closed_count += 1
            recipients.append(
                {
                    "contact_id": contact_doc.id,
                    "conversation_id": contact.get("latest_conversation_id"),
                    "wa_id": wa_id,
                    "customer_name": self._contact_name(contact),
                    "current_tag": contact.get("current_tag", ""),
                    "window_open": self._customer_window_open(contact),
                }
            )
        recipients.sort(key=lambda item: item.get("customer_name") or item["wa_id"])
        return {
            "eligible_count": len(recipients),
            "skipped_opt_out_count": skipped_opt_out_count,
            "window_closed_count": window_closed_count,
            "missing_variable_count": 0,
            "recipients": recipients,
        }

    def _get_conversation(self, conversation_id: str) -> dict[str, Any]:
        snapshot = self.db.collection("marketing_conversations").document(conversation_id).get()
        if not snapshot.exists:
            raise KeyError(f"Conversation not found: {conversation_id}")
        conversation = snapshot.to_dict()
        if conversation.get("channel") != "whatsapp":
            raise ValueError("Only WhatsApp conversations are supported by this console.")
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
        wa_id = contact.get("identifiers", {}).get("wa_id")
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
    def _contact_marketing_eligible(contact: dict[str, Any], audience_tags: list[str]) -> bool:
        if contact.get("marketing_opt_in") is not True:
            return False
        if contact.get("marketing_status") == "opted_out":
            return False
        if contact.get("opt_out_at"):
            return False
        if audience_tags and contact.get("current_tag") not in audience_tags:
            return False
        return True

    @staticmethod
    def _contact_name(contact: dict[str, Any]) -> str:
        order_fields = contact.get("order_fields") or {}
        profile = contact.get("profile") or {}
        return str(order_fields.get("name") or profile.get("name") or contact.get("name") or "")

    def _require_approved_template(self, template_name: str, language_code: str) -> dict[str, Any]:
        docs = list(
            self.db.collection("whatsapp_templates")
            .where("name", "==", template_name)
            .where("language_code", "==", language_code)
            .limit(1)
            .stream()
        )
        if not docs:
            raise ValueError(f"WhatsApp template is not saved locally: {template_name} ({language_code})")
        template = docs[0].to_dict()
        if str(template.get("status", "")).upper() != "APPROVED":
            raise ValueError(f"WhatsApp template is not approved: {template_name}")
        return template

    def _find_messages_by_provider_id(self, provider_message_id: str) -> list[Any]:
        if hasattr(self.db, "collection_group"):
            return list(
                self.db.collection_group("messages")
                .where("provider_message_id", "==", provider_message_id)
                .limit(20)
                .stream()
            )
        return []

    def _find_recipients_by_provider_id(self, provider_message_id: str) -> list[Any]:
        if hasattr(self.db, "collection_group"):
            return list(
                self.db.collection_group("recipients")
                .where("provider_message_id", "==", provider_message_id)
                .limit(20)
                .stream()
            )
        return []

    def _update_campaign_recipient_status(
        self,
        *,
        campaign_id: str,
        recipient_id: str,
        delivery_status: str,
        error_code: Any = None,
        error_message: str | None = None,
    ) -> None:
        self.db.collection("whatsapp_campaigns").document(campaign_id).collection("recipients").document(recipient_id).set(
            {
                "status": delivery_status,
                "error_code": error_code,
                "error_message": error_message,
                "updated_at": utcnow(),
            },
            merge=True,
        )
        self._recount_campaign(campaign_id)
        if delivery_status == "failed":
            failed_count = self.db.collection("whatsapp_campaigns").document(campaign_id).get().to_dict().get("failed_count", 0)
            if failed_count >= 10:
                self._set_campaign_status(campaign_id, "paused")

    def _recount_campaign(self, campaign_id: str) -> None:
        ref = self.db.collection("whatsapp_campaigns").document(campaign_id)
        recipients = [doc.to_dict() for doc in ref.collection("recipients").stream()]
        counts = {
            "queued_count": sum(1 for item in recipients if item.get("status") == "queued"),
            "sent_count": sum(1 for item in recipients if item.get("status") in {"sent", "delivered", "read"}),
            "delivered_count": sum(1 for item in recipients if item.get("status") == "delivered"),
            "read_count": sum(1 for item in recipients if item.get("status") == "read"),
            "failed_count": sum(1 for item in recipients if item.get("status") == "failed"),
            "updated_at": utcnow(),
        }
        ref.set(counts, merge=True)

    def _set_campaign_status(self, campaign_id: str, status: str) -> None:
        ref = self.db.collection("whatsapp_campaigns").document(campaign_id)
        if not ref.get().exists:
            raise KeyError(f"Campaign not found: {campaign_id}")
        ref.set({"status": status, "updated_at": utcnow()}, merge=True)

    def _index_provider_message(
        self,
        *,
        provider_message_id: str | None,
        conversation_id: str,
        message_id: str,
        campaign_id: str | None = None,
        campaign_recipient_id: str | None = None,
    ) -> None:
        if not provider_message_id:
            return
        payload = {
            "provider_message_id": provider_message_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "campaign_id": campaign_id,
            "campaign_recipient_id": campaign_recipient_id,
            "updated_at": utcnow(),
        }
        self.db.collection("whatsapp_message_index").document(stable_id("wamid", provider_message_id)).set(payload, merge=True)

    @staticmethod
    def _extract_provider_message_id(payload: dict[str, Any]) -> str | None:
        messages = payload.get("messages") or []
        if not messages:
            return None
        return messages[0].get("id")

    @staticmethod
    def _template_id(name: str, language_code: str) -> str:
        return stable_id("whatsapp_template", name, language_code)


def is_marketing_opt_out_text(message_text: str) -> bool:
    normalized = message_text.strip().lower()
    return any(keyword in normalized for keyword in OPT_OUT_KEYWORDS)
