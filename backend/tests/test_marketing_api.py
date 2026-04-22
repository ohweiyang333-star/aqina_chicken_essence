"""Regression tests for the upgraded marketing automation flows."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch

import httpx

from tests.fakes import FakeFirestore, FakeGeminiService, FakeMetaClient, FakeTaskQueue


class MarketingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["META_VERIFY_TOKEN"] = "test-verify-token"
        os.environ["META_APP_SECRET"] = "top-secret"
        os.environ["INTERNAL_TASK_SECRET"] = "internal-secret"
        os.environ["GEMINI_API_KEY"] = "test-api-key"
        os.environ["GEMINI_MODEL"] = "gemini-3-flash-preview"
        os.environ["FRONTEND_BASE_URL"] = "https://aqina.example.com"
        os.environ["META_WHATSAPP_PHONE_NUMBER_ID"] = "phone-number-id"

        self.db = FakeFirestore()
        self.task_queue = FakeTaskQueue()
        self.meta_client = FakeMetaClient()
        self.gemini_service = FakeGeminiService()

    def test_facebook_webhook_verification_returns_challenge(self) -> None:
        client = self._build_client()
        response = client.get(
            "/api/v1/marketing/webhooks/facebook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "challenge-token",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "challenge-token")

    def test_chatbot_settings_migrates_legacy_document(self) -> None:
        self.db.seed(
            "chatbotSettings/default",
            {
                "faq": [
                    {
                        "keywords": ["delivery"],
                        "response": {"en": "1-3 working days", "zh": "1-3 个工作日"},
                    }
                ],
                "abandonedCartMessage": {
                    "template": "legacy template",
                    "discountCode": "OLD",
                    "delay": 30,
                },
                "replenishmentReminder": {
                    "enabled": True,
                    "templates": {"en": "legacy en", "zh": "legacy zh"},
                    "triggerDays": [12, 25],
                },
            },
        )

        client = self._build_client()
        response = client.get(
            "/api/v1/chatbot/settings",
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("system_prompt", payload)
        self.assertIn("packages", payload)
        self.assertIn("knowledge_base", payload)
        self.assertIn("crm_follow_up_rules", payload)
        self.assertEqual(payload["faq"][0]["keywords"], ["delivery"])
        self.assertEqual(payload["payment"]["paynow"]["enabled"], True)
        self.assertEqual(payload["escalation"]["pause_automation_on_handoff"], True)

    def test_process_inbound_message_creates_paynow_checkout_session_without_email(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我已经为您准备好 PayNow 付款链接，您确认一下资料就可以付款了 🎈",
                "next_tag": "cart_hot",
                "lead_goal": "pregnancy",
                "recommended_package_code": "maternal_28",
                "upgrade_package_code": "family_42",
                "selected_package_code": "maternal_28",
                "order_fields": {
                    "name": "Alice Tan",
                    "phone": "6591112222",
                    "address": "1 Orchard Road, Singapore 238823",
                },
                "missing_order_fields": [],
                "checkout_ready": True,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-1",
            conversation_id="conv-1",
            event_id="event-1",
            channel="whatsapp",
            incoming_text="我要买孕产妇30天调理套餐",
            identifier_key="wa_id",
            identifier_value="6591112222",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-1"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        orders = self.db.collection("orders").stream()
        self.assertEqual(len(orders), 1)
        order = orders[0].to_dict()
        self.assertEqual(order["payment_method"], "paynow")
        self.assertEqual(order["customer"]["name"], "Alice Tan")
        self.assertTrue(order["customer"].get("email") in (None, ""))

        sessions = self.db.collection("marketing_checkout_sessions").stream()
        self.assertEqual(len(sessions), 1)
        session = sessions[0].to_dict()
        self.assertEqual(session["order_id"], orders[0].id)
        self.assertIn("https://aqina.example.com/paynow/", session["checkout_url"])

        contact = self.db.collection("marketing_contacts").document("contact-1").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")
        self.assertEqual(contact["selected_package_code"], "maternal_28")
        self.assertEqual(contact["order_fields"]["name"], "Alice Tan")

        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("/paynow/", message_calls[0][1]["text"])

    def test_process_inbound_message_escalates_and_pauses_contact(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "",
                "next_tag": "handoff_pending",
                "lead_goal": "unknown",
                "recommended_package_code": None,
                "upgrade_package_code": None,
                "selected_package_code": None,
                "order_fields": {"name": None, "phone": None, "address": None},
                "missing_order_fields": ["name", "phone", "address"],
                "checkout_ready": False,
                "escalate": True,
                "escalation_reason": "refund_request",
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-2",
            conversation_id="conv-2",
            event_id="event-2",
            channel="whatsapp",
            incoming_text="我要退款，帮我转人工",
            identifier_key="wa_id",
            identifier_value="6593334444",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-2"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        contact = self.db.collection("marketing_contacts").document("contact-2").get().to_dict()
        self.assertEqual(contact["current_tag"], "handoff_pending")
        escalation_docs = self.db.collection("marketing_escalations").stream()
        self.assertEqual(len(escalation_docs), 1)
        escalation = escalation_docs[0].to_dict()
        self.assertEqual(escalation["reason"], "refund_request")
        self.assertEqual(escalation["status"], "open")

        call_names = [call[0] for call in self.meta_client.calls]
        self.assertIn("send_whatsapp_text", call_names)
        self.assertIn("send_whatsapp_template", call_names)

    def test_checkout_token_endpoint_returns_paynow_payload(self) -> None:
        self._seed_runtime_settings()
        self.db.seed(
            "marketing_checkout_sessions/session-1",
            {
                "order_id": "order_123",
                "token": "token-123",
                "package_code": "energy_14",
                "checkout_url": "https://aqina.example.com/paynow/token-123",
                "status": "active",
            },
        )
        self.db.seed(
            "orders/order_123",
            {
                "customer": {
                    "name": "Joy Lim",
                    "email": None,
                    "whatsapp": "6598887777",
                    "address": "10 Bishan Street 11, Singapore",
                },
                "items": [
                    {
                        "product_id": "energy_14",
                        "product_name": "活力升级装",
                        "product_name_zh": "活力升级装",
                        "quantity": 1,
                        "unit_price": 75.0,
                        "total_price": 75.0,
                    }
                ],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "pending",
                "order_status": "pending",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.get("/api/v1/marketing/checkout/token-123")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["order_id"], "order_123")
        self.assertEqual(payload["payment_method"], "paynow")
        self.assertNotIn("shopee_url", payload)
        self.assertIn("payment_qr_image", payload["paynow"])

    def test_follow_up_job_skips_when_contact_is_handoff_pending(self) -> None:
        self._seed_runtime_settings()
        self.db.seed(
            "marketing_contacts/contact-3",
            {
                "channel": "whatsapp",
                "identifiers": {"wa_id": "6595556666"},
                "current_tag": "handoff_pending",
                "follow_up_stage": "none",
                "last_interaction_time": "2026-04-10T00:00:00Z",
                "window_expires_at": "2099-01-01T00:00:00Z",
                "latest_conversation_id": "conv-3",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-3",
            {
                "contact_id": "contact-3",
                "conversation_id": "conv-3",
                "stage": "t15m",
                "anchor_interaction_time": "2026-04-10T00:00:00Z",
                "due_at": "2026-04-10T00:15:00Z",
                "eligible_tags": ["lead_cold", "qualified_warm", "cart_hot"],
                "status": "scheduled",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-follow-up-job",
            json={"job_id": "job-3"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "skipped_handoff_pending")

    def _seed_runtime_settings(self) -> None:
        self.db.seed(
            "chatbotSettings/default",
            {
                "system_prompt": "Aqina health advisor prompt",
                "handoff_message": "我先为您转接人工同事优先处理，请稍等一下 🙏",
                "packages": {
                    "trial_3": {
                        "code": "trial_3",
                        "name_zh": "新手体验装",
                        "name_en": "Trial Pack",
                        "price_sgd": 18.0,
                        "pack_count": 3,
                        "target_audience": ["self_care"],
                        "hero": False,
                        "free_shipping_eligible": False,
                    },
                    "energy_14": {
                        "code": "energy_14",
                        "name_zh": "活力升级装",
                        "name_en": "Energy Upgrade Pack",
                        "price_sgd": 75.0,
                        "pack_count": 14,
                        "target_audience": ["self_care"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                    "maternal_28": {
                        "code": "maternal_28",
                        "name_zh": "孕产妇30天调理套餐",
                        "name_en": "Maternal 30-Day Pack",
                        "price_sgd": 149.0,
                        "pack_count": 28,
                        "target_audience": ["pregnancy", "postpartum"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                    "family_42": {
                        "code": "family_42",
                        "name_zh": "家庭月度订阅包",
                        "name_en": "Family Monthly Pack",
                        "price_sgd": 219.0,
                        "pack_count": 42,
                        "target_audience": ["gift_elder", "self_care"],
                        "hero": False,
                        "free_shipping_eligible": True,
                    },
                },
                "knowledge_base": {
                    "usps": ["无抗生素", "零脂肪", "BCAA 高蛋白"],
                    "faq": [
                        {"question": "多久送到", "answer": "1-3 个工作日"},
                    ],
                    "medical_disclaimer": "严重疾病请咨询医生",
                    "logistics": "新加坡现货 1-3 个工作日送达",
                    "consumption": "建议早晨空腹饮用",
                    "comparisons": "比传统鸡精更鲜甜",
                },
                "payment": {
                    "paynow": {
                        "enabled": True,
                        "payment_qr_image": "https://cdn.example.com/paynow.png",
                        "payment_qr_alt": "Aqina PayNow QR",
                        "payment_reference_prefix": "AQINA",
                        "payment_note": "请在参考栏填写订单号",
                    }
                },
                "escalation": {
                    "enabled": True,
                    "private_whatsapp_number": "6599990000",
                    "whatsapp_template_name": "aqina_escalation_alert",
                    "pause_automation_on_handoff": True,
                },
                "crm_follow_up_rules": {
                    "t15m": {"lead_cold": {"instruction": "冷线 15 分钟"}}
                },
            },
        )

    def _seed_contact_and_event(
        self,
        *,
        contact_id: str,
        conversation_id: str,
        event_id: str,
        channel: str,
        incoming_text: str,
        identifier_key: str,
        identifier_value: str,
    ) -> None:
        self.db.seed(
            f"marketing_contacts/{contact_id}",
            {
                "channel": channel,
                "identifiers": {identifier_key: identifier_value},
                "current_tag": "qualified_warm",
                "follow_up_stage": "none",
                "last_interaction_time": "2026-04-10T00:00:00Z",
                "window_expires_at": "2099-01-01T00:00:00Z",
                "latest_conversation_id": conversation_id,
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            f"marketing_conversations/{conversation_id}",
            {
                "contact_id": contact_id,
                "channel": channel,
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            f"marketing_conversations/{conversation_id}/messages/msg-1",
            {
                "direction": "inbound",
                "role": "user",
                "text": incoming_text,
                "source": f"{channel}_webhook",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            f"marketing_events/{event_id}",
            {
                "provider": "meta",
                "channel": channel,
                "event_type": f"{channel}_message_received",
                "status": "queued",
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "payload": {
                    "channel": channel,
                    "text": incoming_text,
                    identifier_key: identifier_value,
                    "provider_message_id": f"{event_id}-mid",
                },
                "received_at": "2026-04-10T00:00:00Z",
            },
        )

    def _build_client(self):
        from app.api.deps import get_db
        from app.core.security import get_current_admin
        from app.main import app

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_admin] = lambda: {"uid": "admin-user", "email": "admin@aqina.com"}

        patches = [
            patch("app.api.v1.marketing.get_task_queue_service", return_value=self.task_queue),
            patch("app.api.v1.marketing.get_meta_client", return_value=self.meta_client),
            patch("app.api.v1.marketing.get_gemini_service", return_value=self.gemini_service),
            patch("app.services.follow_up.get_task_queue_service", return_value=self.task_queue),
            patch("app.services.follow_up.get_meta_client", return_value=self.meta_client),
            patch("app.services.follow_up.get_gemini_service", return_value=self.gemini_service),
        ]

        for item in patches:
            item.start()
            self.addCleanup(item.stop)

        return AsyncAppClient(app)

    def _signature_for(self, payload: dict[str, object]) -> str:
        raw = json.dumps(payload).encode("utf-8")
        digest = hmac.new(b"top-secret", msg=raw, digestmod=hashlib.sha256).hexdigest()
        return f"sha256={digest}"


if __name__ == "__main__":
    unittest.main()


class AsyncAppClient:
    """Small sync wrapper around httpx ASGI transport for unittest."""

    def __init__(self, app):
        self._app = app

    def get(self, url: str, **kwargs):
        return asyncio.run(self._request("GET", url, **kwargs))

    def post(self, url: str, **kwargs):
        return asyncio.run(self._request("POST", url, **kwargs))

    async def _request(self, method: str, url: str, **kwargs):
        transport = httpx.ASGITransport(app=self._app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, **kwargs)
