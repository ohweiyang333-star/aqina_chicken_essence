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
        self.assertIn("先理解，后推荐", payload["system_prompt"])
        self.assertIn("MD2 凤梨长大的快乐鸡", payload["system_prompt"])
        self.assertIn("主治医生", payload["system_prompt"])
        self.assertIn("trial_3", payload["packages"])
        self.assertEqual(payload["packages"]["trial_3"]["price_sgd"], 18.0)
        self.assertEqual(payload["packages"]["pack1"]["name_zh"], "日常滋养装")
        self.assertEqual(payload["faq"][0]["keywords"], ["delivery"])
        self.assertEqual(payload["payment"]["paynow"]["enabled"], True)
        self.assertEqual(payload["escalation"]["pause_automation_on_handoff"], True)
        self.assertTrue(payload["facebook_comment_automation"]["enabled"])
        self.assertIn("price", payload["facebook_comment_automation"]["keywords"])
        self.assertIn("chatbot_skills", payload)
        self.assertIn("ice_breaking", payload["chatbot_skills"])
        self.assertIn("media_assets", payload)
        self.assertIn("brand_intro", payload["media_assets"])

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

    def test_whatsapp_webhook_accepts_unix_timestamp_string(self) -> None:
        client = self._build_client()
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messages": [
                                    {
                                        "from": "6591112222",
                                        "id": "wamid.test.1",
                                        "timestamp": "1777957353",
                                        "type": "text",
                                        "text": {"body": "你好"},
                                    }
                                ]
                            },
                        }
                    ]
                }
            ]
        }

        response = client.post(
            "/api/v1/marketing/webhooks/whatsapp",
            content=json.dumps(payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(payload),
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["accepted_events"], 1)
        events = self.db.collection("marketing_events").stream()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].to_dict()["channel"], "whatsapp")
        self.assertEqual(self.task_queue.created_tasks[0]["type"], "event")
        self.assertEqual(self.task_queue.created_tasks[0]["processor"], "process-inbound-message")

    def test_whatsapp_audio_message_is_transcribed_before_chatbot_reply(self) -> None:
        self._seed_runtime_settings()
        self.gemini_service = FakeGeminiService(
            audio_transcript="请问多少钱？我想自己喝",
            chat_result={
                "reply_text": "您好！如果是自己日常提神，我会先了解您是经常熬夜还是想日常补养。",
                "next_tag": "lead_cold",
                "lead_goal": "self_care",
                "recommended_package_code": None,
                "upgrade_package_code": None,
                "selected_package_code": None,
                "order_fields": {"name": None, "phone": None, "address": None},
                "missing_order_fields": [],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            },
        )
        client = self._build_client()
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messages": [
                                    {
                                        "from": "6591113333",
                                        "id": "wamid.audio.1",
                                        "timestamp": "1777957353",
                                        "type": "audio",
                                        "audio": {
                                            "id": "audio-media-id",
                                            "mime_type": "audio/ogg",
                                            "sha256": "audio-sha",
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                }
            ]
        }

        response = client.post(
            "/api/v1/marketing/webhooks/whatsapp",
            content=json.dumps(payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(payload),
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["accepted_events"], 1)
        event_id = self.task_queue.created_tasks[0]["event_id"]

        task_response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": event_id},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(task_response.status_code, 200)
        transcript_calls = [call for call in self.gemini_service.calls if call[0] == "transcribe_audio_bytes"]
        self.assertEqual(len(transcript_calls), 1)
        chat_calls = [call for call in self.gemini_service.calls if call[0] == "generate_chat_reply"]
        self.assertEqual(chat_calls[0][1]["incoming_text"], "请问多少钱？我想自己喝")
        event = self.db.collection("marketing_events").document(event_id).get().to_dict()
        self.assertEqual(event["payload"]["transcribed_text"], "请问多少钱？我想自己喝")

    def test_messenger_audio_message_is_transcribed_before_chatbot_reply(self) -> None:
        self._seed_runtime_settings()
        self.gemini_service = FakeGeminiService(
            audio_transcript="我要买给妈妈补身",
            chat_result={
                "reply_text": "懂您，买给妈妈补身的话，我先帮您看更适合长辈的配套。",
                "next_tag": "qualified_warm",
                "lead_goal": "gift_elder",
                "recommended_package_code": "pack6",
                "upgrade_package_code": None,
                "selected_package_code": None,
                "order_fields": {"name": None, "phone": None, "address": None},
                "missing_order_fields": [],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            },
        )
        client = self._build_client()
        payload = {
            "entry": [
                {
                    "id": "page-1",
                    "messaging": [
                        {
                            "sender": {"id": "psid-audio-1"},
                            "timestamp": 1770000000000,
                            "message": {
                                "mid": "mid-audio-1",
                                "attachments": [
                                    {
                                        "type": "audio",
                                        "payload": {"url": "https://cdn.example.com/audio.ogg"},
                                    }
                                ],
                            },
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
        event_id = self.task_queue.created_tasks[0]["event_id"]

        with patch("app.services.marketing_orchestrator.requests.get", return_value=FakeHttpResponse(content_type="audio/ogg")):
            task_response = client.post(
                "/api/v1/marketing/tasks/process-inbound-message",
                json={"event_id": event_id},
                headers={"X-Internal-Token": "internal-secret"},
            )

        self.assertEqual(task_response.status_code, 200)
        transcript_calls = [call for call in self.gemini_service.calls if call[0] == "transcribe_audio_bytes"]
        self.assertEqual(len(transcript_calls), 1)
        chat_calls = [call for call in self.gemini_service.calls if call[0] == "generate_chat_reply"]
        self.assertEqual(chat_calls[0][1]["incoming_text"], "我要买给妈妈补身")

    def test_gemini_sales_turn_normalizes_unexpected_schema_values(self) -> None:
        from app.services.gemini_service import GeminiConversationService

        service = GeminiConversationService()
        with patch.object(
            service,
            "_generate_json",
            return_value={
                "reply_text": "可以的，请问您是自己喝还是送人？",
                "next_tag": "warm",
                "lead_goal": "general",
                "order_fields": [],
                "checkout_ready": False,
                "escalate": False,
            },
        ):
            result = service.generate_chat_reply(
                contact={},
                messages=[],
                incoming_text="请问多少钱？",
                channel="whatsapp",
                runtime_settings={"system_prompt": "Aqina advisor"},
            )

        self.assertEqual(result.reply_text, "可以的，请问您是自己喝还是送人？")
        self.assertEqual(result.next_tag, "qualified_warm")
        self.assertEqual(result.lead_goal, "unknown")
        self.assertEqual(result.order_fields.name, None)

    def test_gemini_chat_prompt_restricts_package_codes_and_checkout_readiness(self) -> None:
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "qualified_warm", "lead_goal": "self_care"},
            messages=[],
            incoming_text="我要先试试看",
            channel="whatsapp",
            runtime_settings={
                "packages": {
                    "trial_3": {"code": "trial_3", "price_sgd": 18.0},
                    "pack2": {"code": "pack2", "price_sgd": 75.0},
                },
                "knowledge_base": {},
            },
        )

        self.assertIn("Allowed package codes", prompt)
        self.assertIn("trial_3", prompt)
        self.assertIn("不要发明新的 package code", prompt)
        self.assertIn("checkout_ready 才能为 true", prompt)

    def test_chatbot_skill_router_selects_contextual_skills(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.chatbot_skill_router import ChatbotSkillRouter

        settings_doc = get_default_chatbot_settings()
        router = ChatbotSkillRouter(settings_doc)

        self.assertIn(
            "self_care_fatigue",
            router.select_active_skill_ids(
                contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
                incoming_text="最近熬夜很累，白天没精神",
            ),
        )
        self.assertIn(
            "maternity_consultation",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "pregnancy"},
                incoming_text="孕早期可以喝吗？我有点怕腥",
            ),
        )
        self.assertIn(
            "elder_gift_recovery",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "gift_elder"},
                incoming_text="想买给妈妈术后恢复补身",
            ),
        )
        self.assertIn(
            "price_objection",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "self_care"},
                incoming_text="多少钱？会不会太贵？",
            ),
        )
        self.assertIn(
            "medical_safety",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
                incoming_text="我在吃药治疗糖尿病，可以喝吗？",
            ),
        )
        self.assertIn(
            "payment_receipt",
            router.select_active_skill_ids(
                contact={"current_tag": "cart_hot", "lead_goal": "self_care"},
                incoming_text="我已经完成付款，截图发了",
            ),
        )

    def test_gemini_chat_prompt_injects_only_active_skill_playbooks(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "qualified_warm", "lead_goal": "self_care"},
            messages=[],
            incoming_text="多少钱？有点贵",
            channel="whatsapp",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertIn("Active chatbot skills", prompt)
        self.assertIn("price_objection", prompt)
        self.assertNotIn('"maternity_consultation"', prompt)

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
        self.assertEqual(len(image_calls), 3)
        outbound_images = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-1")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("message_type") == "image"
        ]
        self.assertEqual(
            {item["source"] for item in outbound_images},
            {"chatbot_brand_intro_media", "chatbot_product_media", "paynow_qr_media"},
        )

    def test_process_inbound_message_creates_trial_checkout_with_shipping(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "可以的，我先帮您安排新手体验装，适合先试口感 🎈",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "trial_3",
                "upgrade_package_code": "pack2",
                "selected_package_code": "trial_3",
                "order_fields": {
                    "name": "Ben Lim",
                    "phone": "6592223333",
                    "address": "20 Tampines Central, Singapore 529538",
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
            contact_id="contact-trial",
            conversation_id="conv-trial",
            event_id="event-trial",
            channel="whatsapp",
            incoming_text="我要新手体验装",
            identifier_key="wa_id",
            identifier_value="6592223333",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-trial"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        order = self.db.collection("orders").stream()[0].to_dict()
        self.assertEqual(order["items"][0]["product_id"], "trial_3")
        self.assertEqual(order["subtotal_amount"], 18.0)
        self.assertEqual(order["shipping_fee"], 8.0)
        self.assertEqual(order["total_amount"], 26.0)
        self.assertEqual(order["box_count"], 1)

        contact = self.db.collection("marketing_contacts").document("contact-trial").get().to_dict()
        self.assertEqual(contact["selected_package_code"], "trial_3")
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 3)

    def test_process_inbound_message_sends_brand_and_package_images_without_url_text(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "懂您，经常熬夜确实很容易白天没精神。我更建议您看【活力升级装】，刚好两盒免运费。",
                "next_tag": "qualified_warm",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": None,
                "order_fields": {"name": None, "phone": None, "address": None},
                "missing_order_fields": [],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-media",
            conversation_id="conv-media",
            event_id="event-media",
            channel="whatsapp",
            incoming_text="我经常熬夜很累",
            identifier_key="wa_id",
            identifier_value="6592220000",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-media"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertNotIn("firebasestorage.googleapis.com", message_calls[0][1]["text"])
        self.assertNotIn("http", message_calls[0][1]["text"])
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 2)

        outbound_images = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-media")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("message_type") == "image"
        ]
        self.assertEqual(
            [item["source"] for item in outbound_images],
            ["chatbot_brand_intro_media", "chatbot_product_media"],
        )
        contact = self.db.collection("marketing_contacts").document("contact-media").get().to_dict()
        self.assertTrue(contact["sent_media"]["brand_intro"])
        self.assertTrue(contact["sent_media"]["package_images"]["pack2"])

    def test_process_inbound_message_does_not_resend_seen_chatbot_images(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我继续建议您拿【活力升级装】，两盒刚好免运费。",
                "next_tag": "qualified_warm",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": None,
                "order_fields": {"name": None, "phone": None, "address": None},
                "missing_order_fields": [],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-media-seen",
            conversation_id="conv-media-seen",
            event_id="event-media-seen",
            channel="whatsapp",
            incoming_text="那两盒如何？",
            identifier_key="wa_id",
            identifier_value="6592221111",
        )
        self.db.collection("marketing_contacts").document("contact-media-seen").set(
            {
                "sent_media": {
                    "brand_intro": True,
                    "package_images": {"pack2": True},
                }
            },
            merge=True,
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-media-seen"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 0)

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

    def test_landing_order_with_receipt_normalizes_formatted_phone(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Kelvin Tan",
                    "customer_phone": "+65 9123 4567",
                    "customer_address": "1 Orchard Road, Singapore 238823",
                    "product_id": "pack2",
                },
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["customer"]["whatsapp"], "6591234567")
        order = self.db.collection("orders").stream()[0].to_dict()
        self.assertEqual(order["customer"]["whatsapp"], "6591234567")
        customer = self.db.collection("customers").document("customer_6591234567").get()
        self.assertTrue(customer.exists)

    def test_landing_order_rejects_invalid_phone_with_clear_error(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Kelvin Tan",
                    "customer_phone": "123",
                    "customer_address": "1 Orchard Road, Singapore 238823",
                    "product_id": "pack2",
                },
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "WhatsApp phone must contain 8 to 20 digits")

    def test_landing_order_rejects_short_address_with_clear_error(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Kelvin Tan",
                    "customer_phone": "6591234567",
                    "customer_address": "SG",
                    "product_id": "pack2",
                },
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Delivery address must be 10 to 500 characters")

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
        self.assertIn("send_whatsapp_template", call_names)
        customer_texts = [call[1]["text"] for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertFalse(any("转接人工" in text or "人工同事" in text for text in customer_texts))

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
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("收到您的 PayNow 付款截图", message_calls[0][1]["text"])
        self.assertNotIn("转接人工", message_calls[0][1]["text"])
        self.assertNotIn("人工同事", message_calls[0][1]["text"])
        self.assertNotIn("人工核对", message_calls[0][1]["text"])

    def test_payment_confirmation_text_does_not_send_extra_handoff_message(self) -> None:
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-payment-text",
            conversation_id="conv-payment-text",
            event_id="event-payment-text",
            channel="whatsapp",
            incoming_text="完成付款",
            identifier_key="wa_id",
            identifier_value="6591115555",
        )
        self.db.collection("marketing_contacts").document("contact-payment-text").set(
            {
                "current_tag": "cart_hot",
                "checkout_session_id": "session-payment-text",
            },
            merge=True,
        )
        self.db.seed(
            "marketing_checkout_sessions/session-payment-text",
            {
                "order_id": "order_payment_text",
                "token": "token-payment-text",
                "package_code": "pack2",
                "checkout_url": "https://aqina.example.com/paynow/token-payment-text",
                "status": "active",
                "contact_id": "contact-payment-text",
                "total_amount": 75.0,
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-payment-text"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "payment_confirmation_processed")
        self.assertFalse([call for call in self.gemini_service.calls if call[0] == "generate_chat_reply"])
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("收到", message_calls[0][1]["text"])
        self.assertIn("核对", message_calls[0][1]["text"])
        self.assertNotIn("转接人工", message_calls[0][1]["text"])
        self.assertNotIn("人工同事", message_calls[0][1]["text"])

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

    def test_follow_up_result_model_normalizes_to_reply_text_only(self) -> None:
        from app.models.chatbot import FollowUpTurnResult
        from app.services.follow_up import FollowUpEngine

        reply_text, next_tag = FollowUpEngine._normalize_follow_up_result(
            FollowUpTurnResult(
                reply_text="哈喽~ 您是不是刚好在忙呀？没关系的。",
                next_tag="lead_cold",
                checkout_link_required=False,
                escalate=False,
                escalation_reason=None,
                opt_in_request=False,
            ),
            checkout_url=None,
        )

        self.assertEqual(reply_text, "哈喽~ 您是不是刚好在忙呀？没关系的。")
        self.assertEqual(next_tag, "lead_cold")
        self.assertNotIn("reply_text=", reply_text)
        self.assertNotIn("next_tag=", reply_text)
        self.assertNotIn("checkout_link_required", reply_text)

    def test_follow_up_result_string_repr_normalizes_to_reply_text_only(self) -> None:
        from app.services.follow_up import FollowUpEngine

        reply_text, next_tag = FollowUpEngine._normalize_follow_up_result(
            "reply_text='想象一下，早晨起来撕开一包 Aqina 滴鸡精，倒出来是清澈透亮的金黄色。它完全没有传统鸡精的腥苦味，喝起来像一碗精华鸡汤。' next_tag='lead_cold' checkout_link_required=False escalate=False escalation_reason=None opt_in_request=False",
            checkout_url=None,
        )

        self.assertEqual(next_tag, "lead_cold")
        self.assertEqual(
            reply_text,
            "想象一下，早晨起来撕开一包 Aqina 滴鸡精，倒出来是清澈透亮的金黄色。它完全没有传统鸡精的腥苦味，喝起来像一碗精华鸡汤。",
        )
        self.assertNotIn("reply_text=", reply_text)
        self.assertNotIn("next_tag=", reply_text)
        self.assertNotIn("checkout_link_required", reply_text)

    def test_follow_up_result_model_appends_customer_readable_paynow_reminder(self) -> None:
        from app.models.chatbot import FollowUpTurnResult
        from app.services.follow_up import FollowUpEngine

        reply_text, next_tag = FollowUpEngine._normalize_follow_up_result(
            FollowUpTurnResult(
                reply_text="明天新加坡发货批次快截单了，您可以用前面那张 PayNow QR 完成付款。",
                next_tag="cart_hot",
                checkout_link_required=True,
            ),
            checkout_url="https://aqina.example.com/paynow/token-123",
        )

        self.assertEqual(next_tag, "cart_hot")
        self.assertIn("请使用前面发送的 PayNow QR 图片付款", reply_text)
        self.assertNotIn("checkout_link_required", reply_text)
        self.assertNotIn("https://aqina.example.com/paynow/token-123", reply_text)

    def test_follow_up_result_string_repr_appends_paynow_reminder_without_url_or_fields(self) -> None:
        from app.services.follow_up import FollowUpEngine

        reply_text, next_tag = FollowUpEngine._normalize_follow_up_result(
            "reply_text='明天新加坡发货批次快截单了，您可以用前面那张 PayNow QR 完成付款。' next_tag='cart_hot' checkout_link_required=True escalate=False escalation_reason=None opt_in_request=False",
            checkout_url="https://aqina.example.com/paynow/token-123",
        )

        self.assertEqual(next_tag, "cart_hot")
        self.assertIn("请使用前面发送的 PayNow QR 图片付款", reply_text)
        self.assertNotIn("reply_text=", reply_text)
        self.assertNotIn("checkout_link_required", reply_text)
        self.assertNotIn("https://aqina.example.com/paynow/token-123", reply_text)

    def test_follow_up_job_sends_only_reply_text_from_structured_model(self) -> None:
        from app.models.chatbot import FollowUpTurnResult

        self.gemini_service = FakeGeminiService(
            follow_up_result=FollowUpTurnResult(
                reply_text="哈喽~ 您是不是刚好在忙呀？没关系的。",
                next_tag="lead_cold",
                checkout_link_required=False,
                escalate=False,
                escalation_reason=None,
                opt_in_request=False,
            )
        )
        self._seed_runtime_settings()
        self.db.seed(
            "marketing_contacts/contact-followup",
            {
                "channel": "whatsapp",
                "identifiers": {"wa_id": "6595551111"},
                "current_tag": "lead_cold",
                "follow_up_stage": "none",
                "last_interaction_time": "2026-04-10T00:00:00Z",
                "window_expires_at": "2099-01-01T00:00:00Z",
                "latest_conversation_id": "conv-followup",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-followup",
            {
                "contact_id": "contact-followup",
                "channel": "whatsapp",
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-followup/messages/msg-1",
            {
                "direction": "inbound",
                "role": "user",
                "text": "请问多少钱？",
                "source": "whatsapp_webhook",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-followup",
            {
                "contact_id": "contact-followup",
                "conversation_id": "conv-followup",
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
            json={"job_id": "job-followup"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertEqual(message_calls[0][1]["text"], "哈喽~ 您是不是刚好在忙呀？没关系的。")
        self.assertNotIn("reply_text=", message_calls[0][1]["text"])

        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-followup")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound"
        ]
        self.assertEqual(len(outbound_messages), 1)
        self.assertEqual(outbound_messages[0]["text"], "哈喽~ 您是不是刚好在忙呀？没关系的。")

    def test_follow_up_job_sends_only_reply_text_from_string_repr(self) -> None:
        self.gemini_service = FakeGeminiService(
            follow_up_result="reply_text='想象一下，早晨起来撕开一包 Aqina 滴鸡精，喝起来像一碗精华鸡汤。' next_tag='lead_cold' checkout_link_required=False escalate=False escalation_reason=None opt_in_request=False"
        )
        self._seed_runtime_settings()
        self.db.seed(
            "marketing_contacts/contact-followup-repr",
            {
                "channel": "messenger",
                "identifiers": {"psid": "psid-followup-repr"},
                "current_tag": "lead_cold",
                "follow_up_stage": "none",
                "last_interaction_time": "2026-04-10T00:00:00Z",
                "window_expires_at": "2099-01-01T00:00:00Z",
                "latest_conversation_id": "conv-followup-repr",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-followup-repr",
            {
                "contact_id": "contact-followup-repr",
                "channel": "messenger",
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-followup-repr/messages/msg-1",
            {
                "direction": "inbound",
                "role": "user",
                "text": "请问多少钱？",
                "source": "messenger_webhook",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-followup-repr",
            {
                "contact_id": "contact-followup-repr",
                "conversation_id": "conv-followup-repr",
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
            json={"job_id": "job-followup-repr"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_messenger_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertEqual(
            message_calls[0][1]["text"],
            "想象一下，早晨起来撕开一包 Aqina 滴鸡精，喝起来像一碗精华鸡汤。",
        )
        self.assertNotIn("reply_text=", message_calls[0][1]["text"])
        self.assertNotIn("next_tag=", message_calls[0][1]["text"])

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

    def test_order_contact_context_links_phone_to_whatsapp_thread(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-order-context",
            conversation_id="conv-order-context",
            event_id="event-order-context",
            channel="whatsapp",
            incoming_text="我刚刚下单了",
            identifier_key="wa_id",
            identifier_value="6591112222",
        )
        self.db.seed(
            "orders/order_context",
            {
                "customer": {
                    "name": "Alice Tan",
                    "email": None,
                    "whatsapp": "91112222",
                    "address": "1 Orchard Road, Singapore 238823",
                },
                "items": [],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "payment_submitted",
                "order_status": "pending",
                "source": "landing_page",
                "created_at": "2026-05-05T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.get(
            "/api/v1/orders/order_context/contact-context",
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source_label"], "Landing checkout")
        self.assertEqual(payload["normalized_whatsapp"], "6591112222")
        self.assertEqual(payload["conversation_id"], "conv-order-context")
        self.assertEqual(payload["backend_send_method"], "free_text")
        self.assertEqual(payload["whatsapp_draft_url"], "https://wa.me/6591112222")
        self.assertEqual(payload["conversation_url"], "/admin/whatsapp?conversation=conv-order-context")

    def test_order_whatsapp_notification_sends_free_text_inside_customer_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-order-send",
            conversation_id="conv-order-send",
            event_id="event-order-send",
            channel="whatsapp",
            incoming_text="付款截图已发",
            identifier_key="wa_id",
            identifier_value="6592223333",
        )
        self.db.seed(
            "orders/order_send",
            {
                "customer": {
                    "name": "Ben Lim",
                    "email": None,
                    "whatsapp": "6592223333",
                    "address": "20 Tampines Central, Singapore 529538",
                },
                "items": [],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "paid",
                "order_status": "pending",
                "source": "marketing_chatbot",
                "marketing_contact_id": "contact-order-send",
                "created_at": "2026-05-05T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/orders/order_send/whatsapp-notifications",
            json={
                "expected_ship_date": "2026-05-08",
                "message": "Hi Ben, your order will be arranged for shipment on 8 May 2026.",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "sent")
        self.assertEqual(payload["method"], "free_text")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertEqual(message_calls[0][1]["to"], "6592223333")
        order = self.db.collection("orders").document("order_send").get().to_dict()
        self.assertEqual(order["expected_ship_date"], "2026-05-08")
        self.assertEqual(order["last_customer_contact_method"], "free_text")
        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-order-send")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound"
        ]
        self.assertEqual(len(outbound_messages), 1)

    def test_order_whatsapp_notification_blocks_free_text_when_window_closed_without_template(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-order-closed",
            conversation_id="conv-order-closed",
            event_id="event-order-closed",
            channel="whatsapp",
            incoming_text="之前下单了",
            identifier_key="wa_id",
            identifier_value="6593334444",
        )
        self.db.collection("marketing_contacts").document("contact-order-closed").set(
            {"window_expires_at": "2026-04-01T00:00:00Z"},
            merge=True,
        )
        self.db.seed(
            "orders/order_closed",
            {
                "customer": {
                    "name": "Chloe Ng",
                    "email": None,
                    "whatsapp": "6593334444",
                    "address": "88 Bedok North, Singapore",
                },
                "items": [],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "paid",
                "order_status": "pending",
                "source": "marketing_chatbot",
                "marketing_contact_id": "contact-order-closed",
                "created_at": "2026-05-05T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/orders/order_closed/whatsapp-notifications",
            json={
                "expected_ship_date": "2026-05-08",
                "message": "Your order will ship soon.",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("approved WhatsApp template", response.json()["detail"])
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"])

    def test_order_whatsapp_notification_sends_template_when_window_closed(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-order-template",
            conversation_id="conv-order-template",
            event_id="event-order-template",
            channel="whatsapp",
            incoming_text="上周下单了",
            identifier_key="wa_id",
            identifier_value="6594445555",
        )
        self.db.collection("marketing_contacts").document("contact-order-template").set(
            {"window_expires_at": "2026-04-01T00:00:00Z"},
            merge=True,
        )
        self.db.seed(
            "whatsapp_templates/order-template",
            {
                "name": "aqina_order_update",
                "language_code": "en_US",
                "category": "UTILITY",
                "status": "APPROVED",
                "components": [],
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "orders/order_template",
            {
                "customer": {
                    "name": "Daniel Koh",
                    "email": None,
                    "whatsapp": "6594445555",
                    "address": "8 Raffles Place, Singapore",
                },
                "items": [],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "paid",
                "order_status": "pending",
                "source": "marketing_chatbot",
                "marketing_contact_id": "contact-order-template",
                "created_at": "2026-05-05T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/orders/order_template/whatsapp-notifications",
            json={
                "expected_ship_date": "2026-05-08",
                "message": "Your order will be arranged for shipment on 8 May 2026.",
                "template_name": "aqina_order_update",
                "language_code": "en_US",
                "body_variables": ["Daniel Koh", "8 May 2026", "order_template"],
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["method"], "template")
        template_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_template"]
        self.assertEqual(len(template_calls), 1)
        self.assertEqual(template_calls[0][1]["template_name"], "aqina_order_update")
        self.assertEqual(template_calls[0][1]["body_variables"], ["Daniel Koh", "8 May 2026", "order_template"])
        order = self.db.collection("orders").document("order_template").get().to_dict()
        self.assertEqual(order["last_customer_contact_method"], "template")
        self.assertEqual(order["last_customer_contact_template_name"], "aqina_order_update")

    def test_order_whatsapp_notification_returns_errors_for_missing_order_or_phone(self) -> None:
        self.db.seed(
            "orders/order_no_phone",
            {
                "customer": {
                    "name": "No Phone",
                    "email": None,
                    "whatsapp": "",
                    "address": "1 Orchard Road, Singapore",
                },
                "items": [],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "paid",
                "order_status": "pending",
                "source": "landing_page",
                "created_at": "2026-05-05T00:00:00Z",
            },
        )

        client = self._build_client()
        missing_order = client.get(
            "/api/v1/orders/missing_order/contact-context",
            headers={"Authorization": "Bearer admin-token"},
        )
        missing_phone = client.post(
            "/api/v1/orders/order_no_phone/whatsapp-notifications",
            json={
                "expected_ship_date": "2026-05-08",
                "message": "Your order will ship soon.",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(missing_order.status_code, 404)
        self.assertEqual(missing_phone.status_code, 400)
        self.assertIn("No WhatsApp conversation", missing_phone.json()["detail"])

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
                "handoff_message": "",
                "packages": {
                    "pack1": {
                        "code": "pack1",
                        "name_zh": "日常滋养装",
                        "name_en": "Daily Nourishment Pack",
                        "price_sgd": 39.9,
                        "pack_count": 7,
                        "box_count": 1,
                        "target_audience": ["self_care"],
                        "hero": False,
                        "free_shipping_eligible": False,
                    },
                    "pack2": {
                        "code": "pack2",
                        "name_zh": "活力升级装",
                        "name_en": "Energy Upgrade Pack",
                        "price_sgd": 75.0,
                        "pack_count": 14,
                        "box_count": 2,
                        "target_audience": ["self_care"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                    "pack4": {
                        "code": "pack4",
                        "name_zh": "孕产妇30天调理套餐",
                        "name_en": "Maternity 30-Day Pack",
                        "price_sgd": 149.0,
                        "pack_count": 28,
                        "box_count": 4,
                        "target_audience": ["pregnancy", "postpartum"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                    "pack6": {
                        "code": "pack6",
                        "name_zh": "家庭月度订阅包",
                        "name_en": "Family Monthly Subscription Pack",
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
            patch("app.api.v1.orders.get_task_queue_service", return_value=self.task_queue),
            patch("app.api.v1.orders.get_meta_client", return_value=self.meta_client),
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
    def __init__(self, *, content: bytes = b"fake-paynow-qr", content_type: str = "image/png") -> None:
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self) -> None:
        return None
