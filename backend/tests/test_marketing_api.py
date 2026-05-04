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
        os.environ["META_PAGE_ID"] = "page-1"
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

    def test_webhook_verification_accepts_head_and_trailing_slash(self) -> None:
        client = self._build_client()
        trailing_slash_response = client.get(
            "/api/v1/marketing/webhooks/whatsapp/",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "slash-challenge",
            },
        )
        head_response = client.head(
            "/api/v1/marketing/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "head-challenge",
            },
        )

        self.assertEqual(trailing_slash_response.status_code, 200)
        self.assertEqual(trailing_slash_response.text, "slash-challenge")
        self.assertEqual(head_response.status_code, 200)

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
        self.assertTrue(payload["facebook_comment_automation"]["enabled"])
        self.assertIn("price", payload["facebook_comment_automation"]["keywords"])

    def test_facebook_comment_webhook_processes_keyword_comment_to_private_reply(self) -> None:
        self._seed_runtime_settings()
        client = self._build_client()
        payload = self._facebook_comment_payload(
            comment_id="comment-keyword-1",
            message="请问多少钱？我要买给妈妈",
            from_name="Alice Tan",
        )

        response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(payload),
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["accepted_events"], 1)
        self.assertEqual(self.task_queue.created_tasks[0]["processor"], "process-comment-event")

        event_id = self.task_queue.created_tasks[0]["event_id"]
        task_response = client.post(
            "/api/v1/marketing/tasks/process-comment-event",
            json={"event_id": event_id},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(task_response.status_code, 200)
        self.assertEqual(task_response.json()["status"], "processed")
        public_calls = [call for call in self.meta_client.calls if call[0] == "reply_to_comment"]
        private_calls = [call for call in self.meta_client.calls if call[0] == "send_private_reply"]
        self.assertEqual(len(public_calls), 1)
        self.assertEqual(len(private_calls), 1)
        self.assertEqual(private_calls[0][1]["comment_id"], "comment-keyword-1")
        self.assertEqual(len(private_calls[0][1]["quick_replies"]), 3)

        event = self.db.collection("marketing_events").document(event_id).get().to_dict()
        self.assertEqual(event["public_reply_status"], "sent")
        self.assertEqual(event["private_reply_status"], "sent")
        self.assertEqual(event["matched_keyword"], "多少钱")

    def test_facebook_comment_webhook_skips_unmatched_self_and_duplicate_comments(self) -> None:
        client = self._build_client()

        no_keyword = self._facebook_comment_payload(
            comment_id="comment-no-keyword",
            message="看起来不错，支持一下",
        )
        no_keyword_response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(no_keyword).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(no_keyword),
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(no_keyword_response.status_code, 202)
        self.assertEqual(no_keyword_response.json()["accepted_events"], 0)

        self_comment = self._facebook_comment_payload(
            comment_id="comment-page-self",
            message="PM 我们了解更多优惠",
            from_id="page-1",
            from_name="Aqina SG",
        )
        self_comment_response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(self_comment).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(self_comment),
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(self_comment_response.status_code, 202)
        self.assertEqual(self_comment_response.json()["accepted_events"], 0)

        duplicate = self._facebook_comment_payload(
            comment_id="comment-duplicate",
            message="price pls",
        )
        first_response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(duplicate).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(duplicate),
                "Content-Type": "application/json",
            },
        )
        second_response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(duplicate).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(duplicate),
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(first_response.json()["accepted_events"], 1)
        self.assertEqual(second_response.json()["accepted_events"], 0)
        self.assertEqual(len(self.task_queue.created_tasks), 1)

    def test_facebook_private_reply_failure_is_recorded_without_retrying_duplicate_dm(self) -> None:
        class FailingPrivateReplyMetaClient(FakeMetaClient):
            def send_private_reply(self, **kwargs):
                self.calls.append(("send_private_reply", kwargs))
                raise RuntimeError("Meta private reply failed")

        self.meta_client = FailingPrivateReplyMetaClient()
        client = self._build_client()
        payload = self._facebook_comment_payload(
            comment_id="comment-private-fail",
            message="how much for 4 boxes?",
        )
        response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(payload),
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 202)
        event_id = self.task_queue.created_tasks[0]["event_id"]

        first_task = client.post(
            "/api/v1/marketing/tasks/process-comment-event",
            json={"event_id": event_id},
            headers={"X-Internal-Token": "internal-secret"},
        )
        second_task = client.post(
            "/api/v1/marketing/tasks/process-comment-event",
            json={"event_id": event_id},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(first_task.status_code, 200)
        self.assertEqual(first_task.json()["status"], "processed_with_errors")
        self.assertEqual(second_task.json()["status"], "processed_with_errors")
        private_calls = [call for call in self.meta_client.calls if call[0] == "send_private_reply"]
        self.assertEqual(len(private_calls), 1)
        event = self.db.collection("marketing_events").document(event_id).get().to_dict()
        self.assertEqual(event["private_reply_status"], "failed")
        self.assertIn("private_reply", event["reply_errors"])

    def test_messenger_opt_out_marks_contact_and_skips_ai_queue(self) -> None:
        client = self._build_client()
        payload = {
            "entry": [
                {
                    "id": "page-1",
                    "messaging": [
                        {
                            "sender": {"id": "psid-stop-1"},
                            "timestamp": 1770000000000,
                            "message": {"mid": "mid-stop-1", "text": "STOP"},
                        }
                    ],
                }
            ]
        }

        response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(payload),
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["accepted_events"], 1)
        self.assertFalse(self.task_queue.created_tasks)
        contacts = self.db.collection("marketing_contacts").stream()
        self.assertEqual(len(contacts), 1)
        contact = contacts[0].to_dict()
        self.assertEqual(contact["marketing_status"], "opted_out")
        events = self.db.collection("marketing_events").stream()
        self.assertEqual(events[0].to_dict()["status"], "processed_opt_out")

    def test_process_inbound_message_creates_paynow_checkout_session_without_email(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我已经为您准备好 PayNow 付款链接，您确认一下资料就可以付款了 🎈",
                "next_tag": "cart_hot",
                "lead_goal": "pregnancy",
                "recommended_package_code": "pack4",
                "upgrade_package_code": "pack6",
                "selected_package_code": "pack4",
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
        self.assertEqual(order["subtotal_amount"], 149.0)
        self.assertEqual(order["shipping_fee"], 0.0)
        self.assertEqual(order["total_amount"], 149.0)
        self.assertEqual(order["box_count"], 4)

        sessions = self.db.collection("marketing_checkout_sessions").stream()
        self.assertEqual(len(sessions), 1)
        session = sessions[0].to_dict()
        self.assertEqual(session["order_id"], orders[0].id)
        self.assertIn("https://aqina.example.com/paynow/", session["checkout_url"])

        contact = self.db.collection("marketing_contacts").document("contact-1").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")
        self.assertEqual(contact["selected_package_code"], "pack4")
        self.assertEqual(contact["order_fields"]["name"], "Alice Tan")

        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertNotIn("/paynow/", message_calls[0][1]["text"])
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 1)
        self.assertEqual(image_calls[0][1]["media_id"], "whatsapp-media-id")

    def test_landing_order_with_receipt_charges_shipping_for_one_box(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Janice Lee",
                    "customer_phone": "6598765432",
                    "customer_address": "20 Tanjong Pagar Road, Singapore 088443",
                    "product_id": "pack1",
                },
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["subtotal_amount"], 39.9)
        self.assertEqual(payload["shipping_fee"], 8.0)
        self.assertEqual(payload["total_amount"], 47.9)
        self.assertEqual(payload["box_count"], 1)
        self.assertEqual(payload["payment_status"], "payment_submitted")
        self.assertEqual(payload["payment_receipt_url"], "https://storage.example.com/receipt.png")

    def test_landing_order_with_receipt_has_free_shipping_for_two_boxes(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Kelvin Tan",
                    "customer_phone": "6591234567",
                    "customer_address": "1 Orchard Road, Singapore 238823",
                    "product_id": "pack2",
                },
                files={"payment_receipt": ("receipt.webp", b"fake-image", "image/webp")},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["subtotal_amount"], 75.0)
        self.assertEqual(payload["shipping_fee"], 0.0)
        self.assertEqual(payload["total_amount"], 75.0)
        self.assertEqual(payload["box_count"], 2)

    def test_landing_order_rejects_missing_receipt(self) -> None:
        client = self._build_client()
        response = client.post(
            "/api/v1/orders/with-receipt",
            data={
                "customer_name": "Janice Lee",
                "customer_phone": "6598765432",
                "customer_address": "20 Tanjong Pagar Road, Singapore 088443",
                "product_id": "pack1",
            },
        )

        self.assertEqual(response.status_code, 422)

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

    def test_whatsapp_receipt_image_updates_checkout_order(self) -> None:
        self._seed_runtime_settings()
        self.db.seed(
            "marketing_contacts/contact-4",
            {
                "channel": "whatsapp",
                "identifiers": {"wa_id": "6591112222"},
                "current_tag": "cart_hot",
                "checkout_session_id": "session-4",
                "latest_conversation_id": "conv-4",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-4",
            {
                "contact_id": "contact-4",
                "channel": "whatsapp",
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_checkout_sessions/session-4",
            {
                "order_id": "order_444",
                "token": "token-444",
                "package_code": "pack2",
                "checkout_url": "https://aqina.example.com/paynow/token-444",
                "status": "active",
                "contact_id": "contact-4",
                "total_amount": 75.0,
            },
        )
        self.db.seed(
            "orders/order_444",
            {
                "customer": {
                    "name": "Alice Tan",
                    "email": None,
                    "whatsapp": "6591112222",
                    "address": "1 Orchard Road, Singapore 238823",
                },
                "items": [],
                "subtotal_amount": 75.0,
                "shipping_fee": 0.0,
                "box_count": 2,
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "pending",
                "order_status": "pending",
                "source": "marketing_chatbot",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_events/event-4",
            {
                "provider": "meta",
                "channel": "whatsapp",
                "event_type": "whatsapp_message_received",
                "status": "queued",
                "contact_id": "contact-4",
                "conversation_id": "conv-4",
                "payload": {
                    "channel": "whatsapp",
                    "text": "[image]",
                    "message_type": "image",
                    "media_id": "receipt-media-id",
                    "provider_message_id": "receipt-message-id",
                    "wa_id": "6591112222",
                },
                "received_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        with patch("app.services.marketing_orchestrator.upload_public_file_to_firebase", return_value="https://storage.example.com/chat-receipt.jpg"):
            response = client.post(
                "/api/v1/marketing/tasks/process-inbound-message",
                json={"event_id": "event-4"},
                headers={"X-Internal-Token": "internal-secret"},
            )

        self.assertEqual(response.status_code, 200)
        order = self.db.collection("orders").document("order_444").get().to_dict()
        self.assertEqual(order["payment_status"], "payment_submitted")
        self.assertEqual(order["payment_receipt_url"], "https://storage.example.com/chat-receipt.jpg")
        payments = self.db.collection("payments").stream()
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0].to_dict()["status"], "payment_submitted")

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

    def test_whatsapp_console_allows_manual_text_inside_customer_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-window-open",
            conversation_id="conv-window-open",
            event_id="event-window-open",
            channel="whatsapp",
            incoming_text="请问今天可以下单吗？",
            identifier_key="wa_id",
            identifier_value="6591000001",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/whatsapp/conversations/conv-window-open/messages",
            json={"text": "可以的，我们今天可以帮您安排。"},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "sent")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertEqual(message_calls[0][1]["to"], "6591000001")

    def test_whatsapp_console_blocks_manual_text_after_customer_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-window-closed",
            conversation_id="conv-window-closed",
            event_id="event-window-closed",
            channel="whatsapp",
            incoming_text="之前想了解滴鸡精",
            identifier_key="wa_id",
            identifier_value="6591000002",
        )
        self.db.collection("marketing_contacts").document("contact-window-closed").set(
            {"window_expires_at": "2026-04-01T00:00:00Z"},
            merge=True,
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/whatsapp/conversations/conv-window-closed/messages",
            json={"text": "现在还有优惠。"},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Customer service window", response.json()["detail"])
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"])

    def test_whatsapp_console_allows_template_after_customer_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-template",
            conversation_id="conv-template",
            event_id="event-template",
            channel="whatsapp",
            incoming_text="之前想了解配套",
            identifier_key="wa_id",
            identifier_value="6591000003",
        )
        self.db.collection("marketing_contacts").document("contact-template").set(
            {"window_expires_at": "2026-04-01T00:00:00Z"},
            merge=True,
        )
        self.db.seed(
            "whatsapp_templates/approved-template",
            {
                "name": "aqina_follow_up",
                "language_code": "en_US",
                "category": "MARKETING",
                "status": "APPROVED",
                "components": [],
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/whatsapp/conversations/conv-template/templates",
            json={
                "template_name": "aqina_follow_up",
                "language_code": "en_US",
                "body_variables": ["Alice"],
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "sent")
        template_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_template"]
        self.assertEqual(len(template_calls), 1)
        self.assertEqual(template_calls[0][1]["template_name"], "aqina_follow_up")

    def test_whatsapp_campaign_preview_skips_opted_out_contacts(self) -> None:
        self._seed_campaign_contact(
            contact_id="contact-opted-in",
            wa_id="6592000001",
            name="Alice",
            marketing_opt_in=True,
        )
        self._seed_campaign_contact(
            contact_id="contact-opted-out",
            wa_id="6592000002",
            name="Ben",
            marketing_opt_in=False,
            marketing_status="opted_out",
        )
        self.db.seed(
            "whatsapp_templates/campaign-template",
            {
                "name": "aqina_may_offer",
                "language_code": "en_US",
                "category": "MARKETING",
                "status": "APPROVED",
                "components": [],
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/whatsapp/campaigns/preview",
            json={
                "name": "May offer",
                "template_name": "aqina_may_offer",
                "language_code": "en_US",
                "body_variables": ["May"],
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["eligible_count"], 1)
        self.assertEqual(payload["skipped_opt_out_count"], 1)
        self.assertEqual(payload["recipients"][0]["contact_id"], "contact-opted-in")

    def test_whatsapp_campaign_launch_queues_recipients_without_sync_broadcast(self) -> None:
        self._seed_campaign_contact(
            contact_id="contact-campaign-1",
            wa_id="6593000001",
            name="Alice",
            marketing_opt_in=True,
        )
        self._seed_campaign_contact(
            contact_id="contact-campaign-2",
            wa_id="6593000002",
            name="Joy",
            marketing_opt_in=True,
        )
        self.db.seed(
            "whatsapp_templates/launch-template",
            {
                "name": "aqina_launch_offer",
                "language_code": "en_US",
                "category": "MARKETING",
                "status": "APPROVED",
                "components": [],
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        create_response = client.post(
            "/api/v1/marketing/whatsapp/campaigns",
            json={
                "name": "Launch offer",
                "template_name": "aqina_launch_offer",
                "language_code": "en_US",
                "body_variables": ["Launch"],
            },
            headers={"Authorization": "Bearer admin-token"},
        )
        self.assertEqual(create_response.status_code, 201)
        campaign_id = create_response.json()["campaign_id"]

        launch_response = client.post(
            f"/api/v1/marketing/whatsapp/campaigns/{campaign_id}/launch",
            json={"preview_confirmed": True},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(launch_response.status_code, 200)
        payload = launch_response.json()
        self.assertEqual(payload["status"], "queued")
        self.assertEqual(payload["queued_count"], 2)
        self.assertEqual(len([task for task in self.task_queue.created_tasks if task["type"] == "campaign-recipient"]), 2)
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_whatsapp_template"])

    def test_whatsapp_status_webhook_updates_message_and_campaign_recipient(self) -> None:
        self.db.seed(
            "marketing_conversations/conv-status/messages/msg-status",
            {
                "direction": "outbound",
                "role": "assistant",
                "text": "Campaign template aqina_offer sent",
                "provider_message_id": "wamid.status.1",
                "message_type": "template",
                "source": "whatsapp_campaign",
                "campaign_id": "campaign-status",
                "campaign_recipient_id": "recipient-status",
                "delivery_status": "accepted",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "whatsapp_campaigns/campaign-status/recipients/recipient-status",
            {
                "contact_id": "contact-status",
                "wa_id": "6594000001",
                "status": "sent",
                "provider_message_id": "wamid.status.1",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": "wamid.status.1",
                                        "recipient_id": "6594000001",
                                        "status": "failed",
                                        "errors": [{"code": 132015, "message": "Dropped by quality assessment"}],
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        client = self._build_client()
        raw_body = json.dumps(payload).encode("utf-8")
        response = client.post(
            "/api/v1/marketing/webhooks/whatsapp",
            content=raw_body,
            headers={
                "X-Hub-Signature-256": self._signature_for(payload),
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(response.status_code, 202)
        message = self.db.collection("marketing_conversations").document("conv-status").collection("messages").document("msg-status").get().to_dict()
        self.assertEqual(message["delivery_status"], "failed")
        recipient = self.db.collection("whatsapp_campaigns").document("campaign-status").collection("recipients").document("recipient-status").get().to_dict()
        self.assertEqual(recipient["status"], "failed")
        self.assertEqual(recipient["error_code"], 132015)

    def _seed_runtime_settings(self) -> None:
        self.db.seed(
            "chatbotSettings/default",
            {
                "system_prompt": "Aqina health advisor prompt",
                "handoff_message": "我先为您转接人工同事优先处理，请稍等一下 🙏",
                "packages": {
                    "pack1": {
                        "code": "pack1",
                        "name_zh": "7天启动装",
                        "name_en": "7-Day Starter Pack",
                        "price_sgd": 39.9,
                        "pack_count": 7,
                        "box_count": 1,
                        "target_audience": ["self_care"],
                        "hero": False,
                        "free_shipping_eligible": False,
                    },
                    "pack2": {
                        "code": "pack2",
                        "name_zh": "14天常备装",
                        "name_en": "14-Day Care Pack",
                        "price_sgd": 75.0,
                        "pack_count": 14,
                        "box_count": 2,
                        "target_audience": ["self_care"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                    "pack4": {
                        "code": "pack4",
                        "name_zh": "28天月度装",
                        "name_en": "28-Day Monthly Pack",
                        "price_sgd": 149.0,
                        "pack_count": 28,
                        "box_count": 4,
                        "target_audience": ["pregnancy", "postpartum"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                    "pack6": {
                        "code": "pack6",
                        "name_zh": "42天家庭装",
                        "name_en": "42-Day Family Pack",
                        "price_sgd": 219.0,
                        "pack_count": 42,
                        "box_count": 6,
                        "target_audience": ["gift_elder", "self_care"],
                        "hero": False,
                        "free_shipping_eligible": True,
                    },
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
                        "account_name": "Boong Poultry Pte Ltd",
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

    def _seed_campaign_contact(
        self,
        *,
        contact_id: str,
        wa_id: str,
        name: str,
        marketing_opt_in: bool,
        marketing_status: str = "opted_in",
    ) -> None:
        self.db.seed(
            f"marketing_contacts/{contact_id}",
            {
                "channel": "whatsapp",
                "identifiers": {"wa_id": wa_id, "phone_e164": wa_id},
                "profile": {"name": name},
                "order_fields": {"name": name, "phone": wa_id},
                "current_tag": "qualified_warm",
                "marketing_opt_in": marketing_opt_in,
                "opt_in_source": "test",
                "opt_in_at": "2026-04-10T00:00:00Z" if marketing_opt_in else None,
                "opt_out_at": None if marketing_opt_in else "2026-04-10T00:00:00Z",
                "marketing_status": marketing_status,
                "latest_conversation_id": f"conv-{contact_id}",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            f"marketing_conversations/conv-{contact_id}",
            {
                "contact_id": contact_id,
                "channel": "whatsapp",
                "status": "open",
                "last_message_at": "2026-04-10T00:00:00Z",
                "message_count": 0,
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
            patch("app.services.meta_media_assets.requests.get", return_value=FakeHttpResponse()),
        ]

        for item in patches:
            item.start()
            self.addCleanup(item.stop)

        return AsyncAppClient(app)

    def _signature_for(self, payload: dict[str, object]) -> str:
        raw = json.dumps(payload).encode("utf-8")
        digest = hmac.new(b"top-secret", msg=raw, digestmod=hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def _facebook_comment_payload(
        self,
        *,
        comment_id: str,
        message: str,
        from_id: str = "fb-user-1",
        from_name: str = "Facebook User",
    ) -> dict[str, object]:
        return {
            "entry": [
                {
                    "id": "page-1",
                    "changes": [
                        {
                            "field": "feed",
                            "value": {
                                "item": "comment",
                                "verb": "add",
                                "comment_id": comment_id,
                                "post_id": "post-1",
                                "message": message,
                                "from": {"id": from_id, "name": from_name},
                            },
                        }
                    ],
                }
            ]
        }


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

    def head(self, url: str, **kwargs):
        return asyncio.run(self._request("HEAD", url, **kwargs))

    async def _request(self, method: str, url: str, **kwargs):
        transport = httpx.ASGITransport(app=self._app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, **kwargs)


class FakeHttpResponse:
    content = b"fake-paynow-qr"
    headers = {"content-type": "image/png"}

    def raise_for_status(self) -> None:
        return None
