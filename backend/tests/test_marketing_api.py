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


RETIRED_PACKAGE_CODE = "trial" + "_3"
RETIRED_PACKAGE_NAME_ZH = "新手" + "体验装"
RETIRED_PACKAGE_NAME_EN = "Trial " + "Pack"
RETIRED_PACKAGE_PRICE_TEXT = "SGD " + "18.00"
RETIRED_PACKAGE_PACK_COUNT_TEXT = f"{3}包"
LEGACY_ENERGY_PACK_NAME_ZH = "活力" + "升级装"


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
        self.assertEqual(payload["conversion_optimization_version"], 11)
        self.assertIn("Pace -> Answer -> Diagnose -> Bridge -> Choice", payload["system_prompt"])
        self.assertIn("You are Aqina WhatsApp / Messenger private sales support", payload["system_prompt"])
        self.assertIn("1盒 = SGD47.90", payload["system_prompt"])
        self.assertIn("2盒 = SGD79.80", payload["system_prompt"])
        self.assertIn("French Poulet Cut Part", payload["system_prompt"])
        self.assertIn("already include Singapore delivery fee", payload["system_prompt"])
        self.assertIn("no separate delivery fee", payload["system_prompt"])
        self.assertIn("Aqina 是食品补养，不是药", payload["system_prompt"])
        self.assertNotIn(RETIRED_PACKAGE_CODE, payload["packages"])
        for code in ["pack1", "pack2"]:
            self.assertIn(code, payload["packages"])
        for code in ["pack4", "pack6"]:
            self.assertNotIn(code, payload["packages"])
        self.assertEqual(payload["packages"]["pack1"]["name_zh"], "7天启动装")
        self.assertEqual(payload["packages"]["pack1"]["price_sgd"], 47.9)
        self.assertEqual(payload["packages"]["pack2"]["price_sgd"], 79.8)
        self.assertEqual(payload["faq"][0]["keywords"], ["delivery"])
        self.assertEqual(payload["payment"]["paynow"]["enabled"], True)
        self.assertEqual(payload["escalation"]["private_whatsapp_number"], "+6591212369")
        self.assertEqual(payload["escalation"]["additional_private_whatsapp_numbers"], ["+60149449341"])
        self.assertEqual(payload["escalation"]["whatsapp_template_name"], "aqina_escalation_alert")
        self.assertEqual(payload["escalation"]["pause_automation_on_handoff"], True)
        self.assertTrue(payload["facebook_comment_automation"]["enabled"])
        self.assertIn("price", payload["facebook_comment_automation"]["keywords"])
        self.assertIn("paynow", payload["facebook_comment_automation"]["keywords"])
        self.assertIn("地址", payload["facebook_comment_automation"]["keywords"])
        self.assertIn("chatbot_skills", payload)
        self.assertIn("ice_breaking", payload["chatbot_skills"])
        self.assertIn("usage_consultation", payload["chatbot_skills"])
        self.assertIn("普通瓶装", payload["chatbot_skills"]["price_objection"]["required_questions"][0])
        self.assertIn("Use Pace -> Answer -> Diagnose -> Bridge -> Choice", payload["chatbot_skills"]["price_objection"]["instruction"])
        self.assertIn("Do not repeat prices", payload["crm_follow_up_rules"]["t3h"]["default"]["instruction"])
        self.assertIn("哈喽 [顾客名字]", payload["crm_follow_up_rules"]["comment_hook"]["public_reply"]["instruction"])
        self.assertIn("media_assets", payload)
        self.assertEqual(
            payload["media_assets"]["initial_promotion_images"]["zh"],
            "/chatbot/aqina-pack2-french-poulet-promotion-zh.jpg",
        )
        self.assertEqual(
            payload["media_assets"]["initial_promotion_images"]["en"],
            "/chatbot/aqina-pack2-french-poulet-promotion-en.jpg",
        )
        self.assertIn("French Poulet Cut Part", payload["media_assets"]["captions"]["initial_promotion"]["zh"])
        self.assertIn("brand_intro", payload["media_assets"])
        self.assertEqual(payload["media_assets"]["brand_intro_images"]["zh"], "/chatbot/aqina-purity-cycle-zh.jpg")
        self.assertEqual(payload["media_assets"]["brand_intro_images"]["en"], "/chatbot/aqina-purity-cycle-en.jpg")
        self.assertEqual(payload["media_assets"]["package_images"]["pack1"]["zh"], "/chatbot/aqina-offer-gift-guide-zh.jpg")
        self.assertEqual(payload["media_assets"]["package_images"]["pack1"]["en"], "/chatbot/aqina-offer-gift-guide-en.jpg")
        self.assertEqual(payload["media_assets"]["package_images"]["pack2"]["zh"], "/chatbot/aqina-offer-gift-guide-zh.jpg")
        self.assertEqual(payload["media_assets"]["package_images"]["pack2"]["en"], "/chatbot/aqina-offer-gift-guide-en.jpg")
        self.assertEqual(len(payload["media_assets"]["ugc_social_proof_images"]["zh"]), 16)
        self.assertEqual(len(payload["media_assets"]["ugc_social_proof_images"]["en"]), 16)
        self.assertEqual(
            payload["media_assets"]["ugc_social_proof_images"]["zh"][0],
            "/chatbot/ugc/customer-middle-aged-chinese-man-product.jpg",
        )
        self.assertIn("真实顾客使用照", payload["media_assets"]["captions"]["ugc_social_proof"]["zh"])
        self.assertNotIn("pack4", payload["media_assets"]["package_images"])
        self.assertNotIn("pack6", payload["media_assets"]["package_images"])
        self.assertNotIn(RETIRED_PACKAGE_CODE, payload["media_assets"]["package_images"])
        self.assertNotIn(RETIRED_PACKAGE_CODE, payload["media_assets"]["captions"])
        serialized_payload = json.dumps(payload, ensure_ascii=False)
        for retired_copy in ["SGD 75", "SGD75", "SGD 149", "SGD149", "SGD 219", "SGD219", "4盒", "6盒", "free shipping"]:
            self.assertNotIn(retired_copy, serialized_payload)
        for expected in [
            "SGD47.90",
            "SGD79.80",
            "SGD39.90/盒",
            "SGD16.00",
            "French Poulet 3 Joint Wing 500g",
            "French Poulet Minced 400g",
            "French Poulet Boneless Breast 350g",
            "French Poulet Whole Leg 400g",
            "French Poulet Half Chicken Cut 4 Pieces 500g",
            "double-boiled 双重蒸煮",
            "100% Pure Chicken Essence",
        ]:
            self.assertIn(expected, serialized_payload)

    def test_chatbot_settings_removes_retired_trial_package_from_saved_document(self) -> None:
        self.db.seed(
            "chatbotSettings/default",
            {
                "system_prompt": (
                    f"产品定价：- 【{RETIRED_PACKAGE_NAME_ZH}】{RETIRED_PACKAGE_PACK_COUNT_TEXT} = {RETIRED_PACKAGE_PRICE_TEXT}，适合先试口感。\n"
                    f"推荐规则：可先给【{RETIRED_PACKAGE_NAME_ZH}】作为低门槛选择。"
                ),
                "packages": {
                    RETIRED_PACKAGE_CODE: {
                        "code": RETIRED_PACKAGE_CODE,
                        "name_zh": RETIRED_PACKAGE_NAME_ZH,
                        "name_en": RETIRED_PACKAGE_NAME_EN,
                        "description_zh": f"{RETIRED_PACKAGE_PACK_COUNT_TEXT}低门槛体验装",
                        "description_en": "Low-entry 3-pack trial",
                        "price_sgd": 18.0,
                        "pack_count": 3,
                        "target_audience": ["self_care"],
                        "hero": False,
                        "free_shipping_eligible": False,
                    }
                },
                "chatbot_skills": {
                    "price_objection": {
                        "recommended_package_code": RETIRED_PACKAGE_CODE,
                        "required_questions": [f"您会想先用{RETIRED_PACKAGE_NAME_ZH}试口感，还是直接拿免运的{LEGACY_ENERGY_PACK_NAME_ZH}？"],
                    },
                    "taste_objection": {"recommended_package_code": RETIRED_PACKAGE_CODE},
                },
                "media_assets": {
                    "package_images": {RETIRED_PACKAGE_CODE: "/chatbot/legacy-trial.jpg"},
                    "captions": {RETIRED_PACKAGE_CODE: f"{RETIRED_PACKAGE_NAME_ZH}：{3} 包先试口感。"},
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
        serialized_payload = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(RETIRED_PACKAGE_CODE, payload["packages"])
        self.assertNotIn(RETIRED_PACKAGE_CODE, payload["media_assets"]["package_images"])
        self.assertNotIn(RETIRED_PACKAGE_CODE, payload["media_assets"]["captions"])
        self.assertEqual(payload["chatbot_skills"]["price_objection"]["recommended_package_code"], "pack1")
        self.assertEqual(payload["chatbot_skills"]["taste_objection"]["recommended_package_code"], "pack1")
        self.assertNotIn(RETIRED_PACKAGE_NAME_ZH, serialized_payload)
        self.assertNotIn(RETIRED_PACKAGE_NAME_EN, serialized_payload)
        self.assertNotIn(RETIRED_PACKAGE_PRICE_TEXT, serialized_payload)

    def test_chatbot_settings_normalizes_legacy_product_term_without_overwriting_custom_copy(self) -> None:
        legacy_term = "滴" + "鸡精"
        legacy_asset_path = f"/chatbot/产后妈妈喝{legacy_term}.jpg"
        self.db.seed(
            "chatbotSettings/default",
            {
                "conversion_optimization_version": 11,
                "system_prompt": f"Aqina {legacy_term} advisor prompt",
                "knowledge_base": {
                    "medical_disclaimer": f"Aqina {legacy_term}是食品补充剂，请咨询主治医生。",
                    "faq": [{"question": "适合谁？", "answer": f"Aqina {legacy_term}适合日常补养。"}],
                },
                "crm_follow_up_rules": {
                    "t15m": {
                        "lead_cold": {"instruction": f"询问顾客想了解 Aqina {legacy_term} 的哪个场景。"}
                    }
                },
                "media_assets": {
                    "package_images": {"pack1": {"zh": legacy_asset_path, "en": "/chatbot/pack1-en.jpg"}},
                    "captions": {"pack1": f"Aqina {legacy_term} 1盒体验。"},
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
        self.assertIn("Aqina 纯鸡精 advisor prompt", payload["system_prompt"])
        self.assertIn("Aqina 纯鸡精是食品补充剂", payload["knowledge_base"]["medical_disclaimer"])
        self.assertIn("Aqina 纯鸡精适合日常补养", payload["knowledge_base"]["faq"][0]["answer"])
        self.assertIn("Aqina 纯鸡精", payload["crm_follow_up_rules"]["t15m"]["lead_cold"]["instruction"])
        self.assertEqual(payload["media_assets"]["package_images"]["pack1"]["zh"], legacy_asset_path)
        self.assertEqual(payload["media_assets"]["captions"]["pack1"]["zh"], "Aqina 纯鸡精 1盒体验。")
        self.assertEqual(payload["media_assets"]["captions"]["pack1"]["en"], "Aqina 纯鸡精 1盒体验。")

        saved = self.db.collection("chatbotSettings").document("default").get().to_dict()
        self.assertEqual(saved["terminology_migration_version"], 1)
        self.assertEqual(saved["media_assets"]["package_images"]["pack1"]["zh"], legacy_asset_path)
        self.assertEqual(saved["media_assets"]["captions"]["pack1"]["zh"], "Aqina 纯鸡精 1盒体验。")
        self.assertEqual(saved["media_assets"]["captions"]["pack1"]["en"], "Aqina 纯鸡精 1盒体验。")

    def test_chatbot_settings_applies_conversion_playbook_without_overwriting_payment_or_handoff(self) -> None:
        self.db.seed(
            "chatbotSettings/default",
            {
                "conversion_optimization_version": 0,
                "system_prompt": "Old education-first prompt",
                "facebook_comment_automation": {
                    "enabled": False,
                    "keywords": ["old-keyword"],
                    "public_reply_enabled": False,
                    "private_reply_enabled": True,
                    "ignore_page_self_comments": True,
                },
                "payment": {
                    "paynow": {
                        "enabled": True,
                        "account_name": "Custom PayNow Name",
                        "payment_qr_image": "https://example.com/custom-qr.png",
                        "payment_qr_alt": "Custom QR",
                        "payment_reference_prefix": "CUSTOM",
                        "payment_note": "Custom payment note",
                    }
                },
                "escalation": {
                    "enabled": True,
                    "private_whatsapp_number": "+6599999999",
                    "whatsapp_template_name": "custom_template",
                    "pause_automation_on_handoff": True,
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
        self.assertEqual(payload["conversion_optimization_version"], 11)
        self.assertIn("Pace -> Answer -> Diagnose -> Bridge -> Choice", payload["system_prompt"])
        self.assertEqual(payload["payment"]["paynow"]["account_name"], "Custom PayNow Name")
        self.assertEqual(payload["payment"]["paynow"]["payment_reference_prefix"], "CUSTOM")
        self.assertEqual(payload["escalation"]["private_whatsapp_number"], "+6599999999")
        self.assertEqual(payload["escalation"]["additional_private_whatsapp_numbers"], ["+60149449341"])
        self.assertEqual(payload["escalation"]["whatsapp_template_name"], "custom_template")
        self.assertFalse(payload["facebook_comment_automation"]["enabled"])
        self.assertIn("paynow", payload["facebook_comment_automation"]["keywords"])

    def test_chatbot_settings_fills_missing_escalation_template(self) -> None:
        self.db.seed(
            "chatbotSettings/default",
            {
                "conversion_optimization_version": 11,
                "system_prompt": "Current prompt",
                "packages": {},
                "knowledge_base": {},
                "escalation": {
                    "enabled": True,
                    "private_whatsapp_number": "+6591212369",
                    "additional_private_whatsapp_numbers": ["+60149449341"],
                    "whatsapp_template_name": "",
                    "pause_automation_on_handoff": True,
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
        self.assertEqual(payload["escalation"]["whatsapp_template_name"], "aqina_escalation_alert")

    def test_chatbot_conversion_playbook_covers_planned_sales_scenarios(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings

        settings_doc = get_default_chatbot_settings()
        prompt = settings_doc["system_prompt"]
        skills = settings_doc["chatbot_skills"]
        serialized = json.dumps(settings_doc, ensure_ascii=False)

        self.assertIn("Customer-facing replies must follow the customer's language", prompt)
        self.assertIn("private sales support", prompt)
        self.assertIn("If the customer asks about price/how much/packages/offers, answer directly", prompt)
        self.assertIn("1盒 = SGD47.90", prompt)
        self.assertIn("2盒 = SGD79.80", prompt)
        self.assertIn("SGD39.90/盒", prompt)
        self.assertIn("SGD16.00", prompt)
        self.assertIn("already include Singapore delivery fee", prompt)
        self.assertIn("no separate delivery fee", prompt)
        self.assertIn("+6591212369", prompt)
        self.assertIn("non_product_human_help", prompt)
        self.assertIn("unknown_requires_human", prompt)
        self.assertIn("has not asked about price, package, shipping, or buying", prompt)
        self.assertIn("do not quote SGD prices again", prompt)
        self.assertIn("Never recommend retired multi-box packages", prompt)
        self.assertNotIn(RETIRED_PACKAGE_CODE, serialized)
        self.assertIn("address, phone number, payment screenshot", prompt)
        self.assertIn("PayNow", prompt)
        self.assertIn("send back the payment screenshot", prompt)
        self.assertIn("customer_request_remark", prompt)
        self.assertIn("Delivery timing requests during checkout", prompt)
        self.assertIn("price changes, discounts, extra gifts", prompt)
        self.assertIn("Vary your wording", prompt)
        self.assertIn("Only state certifications, approvals, lab results, or nutrition numbers", prompt)
        self.assertIn("clean and light like home-cooked chicken soup", skills["taste_objection"]["instruction"])
        self.assertIn("usage_consultation", skills)
        self.assertIn("Do not turn general health", skills["usage_consultation"]["listening_goal"])
        self.assertIn("usage, suitability, or body-condition question", skills["usage_consultation"]["instruction"])
        self.assertIn("Only mention SGD prices", skills["maternity_consultation"]["instruction"])
        self.assertIn("do not make medical promises", skills["maternity_consultation"]["instruction"])
        self.assertIn("Do not repeat prices", settings_doc["crm_follow_up_rules"]["t15m"]["qualified_warm"]["instruction"])
        self.assertIn("Do not send long sensory copy", settings_doc["crm_follow_up_rules"]["t3h"]["default"]["instruction"])
        self.assertIn("reply YES", settings_doc["crm_follow_up_rules"]["t23h"]["default"]["instruction"])
        price_skill = skills["price_objection"]
        price_copy = json.dumps(price_skill, ensure_ascii=False)
        self.assertIn("ordinary bottled chicken essence", price_copy)
        self.assertIn("premium sachet route", price_copy)
        self.assertIn("MD2 黄梨酵素鸡", price_copy)
        self.assertIn("7天慢炼", price_copy)
        self.assertIn("SGD79.80", price_copy)
        self.assertIn("why so expensive", price_copy)
        self.assertIn("double-boiled 双重蒸煮", price_copy)
        self.assertIn("not the ordinary low-price bottled route", price_copy)
        self.assertIn("price_positioning", settings_doc["knowledge_base"])
        self.assertIn("不需要另加邮费", settings_doc["knowledge_base"]["logistics"])
        for retired_copy in ["SGD 75", "SGD75", "SGD 149", "SGD149", "SGD 219", "SGD219", "4盒", "6盒", "free shipping"]:
            self.assertNotIn(retired_copy, serialized)

    def test_chatbot_settings_includes_cart_hot_checkout_skill(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings

        settings_doc = get_default_chatbot_settings()
        checkout_skill = settings_doc["chatbot_skills"]["cart_hot_checkout"]
        serialized = json.dumps(checkout_skill, ensure_ascii=False)

        for expected in ["confirm package", "recipient name", "phone number", "full Singapore delivery address", "PayNow", "付款截图", "客服"]:
            self.assertIn(expected, serialized)
        self.assertIn("customer_request_remark", serialized)
        self.assertIn("好的，我先帮您确认", serialized)
        self.assertIn("目前我们没有货到付款", serialized)
        self.assertIn("cart_hot", settings_doc["crm_follow_up_rules"]["t15m"])
        self.assertIn("recipient name", settings_doc["crm_follow_up_rules"]["t15m"]["cart_hot"]["instruction"])

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

    def test_messenger_webhook_records_referral_acquisition(self) -> None:
        client = self._build_client()
        payload = {
            "entry": [
                {
                    "id": "page-1",
                    "messaging": [
                        {
                            "sender": {"id": "psid-ad-1"},
                            "recipient": {"id": "page-1"},
                            "timestamp": 1770000000000,
                            "referral": {
                                "source": "ADS",
                                "type": "OPEN_THREAD",
                                "ref": "may-offer",
                                "ad_id": "ad-123",
                                "referer_uri": "https://facebook.com/ads/example",
                            },
                            "message": {"mid": "mid-ad-1", "text": "请问优惠配套？"},
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
        contact = self.db.collection("marketing_contacts").stream()[0].to_dict()
        self.assertEqual(contact["acquisition"]["source"], "ADS")
        self.assertEqual(contact["acquisition"]["ref"], "may-offer")
        self.assertEqual(contact["acquisition"]["ad_id"], "ad-123")
        event = self.db.collection("marketing_events").stream()[0].to_dict()
        self.assertEqual(event["payload"]["acquisition"]["ad_id"], "ad-123")
        self.assertEqual(event["payload"]["sender_psid"], "psid-ad-1")
        self.assertEqual(self.task_queue.created_tasks[0]["processor"], "process-inbound-message")

    def test_messenger_webhook_records_standalone_referral_before_first_message(self) -> None:
        client = self._build_client()
        referral_payload = {
            "entry": [
                {
                    "id": "page-1",
                    "messaging": [
                        {
                            "sender": {"id": "psid-ad-standalone"},
                            "recipient": {"id": "page-1"},
                            "timestamp": 1770000000000,
                            "referral": {
                                "source": "ADS",
                                "type": "OPEN_THREAD",
                                "ref": "may-offer",
                                "ad_id": "ad-standalone-123",
                            },
                        }
                    ],
                }
            ]
        }
        message_payload = {
            "entry": [
                {
                    "id": "page-1",
                    "messaging": [
                        {
                            "sender": {"id": "psid-ad-standalone"},
                            "recipient": {"id": "page-1"},
                            "timestamp": 1770000005000,
                            "message": {"mid": "mid-standalone-1", "text": "请问多少钱？"},
                        }
                    ],
                }
            ]
        }

        referral_response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(referral_payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(referral_payload),
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(referral_response.status_code, 202)
        self.assertEqual(referral_response.json()["accepted_events"], 1)
        self.assertFalse(self.task_queue.created_tasks)

        message_response = client.post(
            "/api/v1/marketing/webhooks/facebook",
            content=json.dumps(message_payload).encode("utf-8"),
            headers={
                "X-Hub-Signature-256": self._signature_for(message_payload),
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(message_response.status_code, 202)
        self.assertEqual(message_response.json()["accepted_events"], 1)
        event_tasks = [task for task in self.task_queue.created_tasks if task["type"] == "event"]
        self.assertEqual(len(event_tasks), 1)
        self.assertEqual(event_tasks[0]["processor"], "process-inbound-message")
        contact = self.db.collection("marketing_contacts").stream()[0].to_dict()
        self.assertEqual(contact["acquisition"]["source"], "ADS")
        self.assertEqual(contact["acquisition"]["ref"], "may-offer")
        self.assertEqual(contact["acquisition"]["ad_id"], "ad-standalone-123")
        events = [item.to_dict() for item in self.db.collection("marketing_events").stream()]
        self.assertEqual({event["event_type"] for event in events}, {"messenger_referral_received", "messenger_message_received"})
        referral_event = next(event for event in events if event["event_type"] == "messenger_referral_received")
        self.assertEqual(referral_event["status"], "processed_referral")
        self.assertEqual(referral_event["payload"]["acquisition"]["ad_id"], "ad-standalone-123")

    def test_messenger_postback_is_recorded_as_inbound_conversation_event(self) -> None:
        client = self._build_client()
        payload = {
            "entry": [
                {
                    "id": "page-1",
                    "messaging": [
                        {
                            "sender": {"id": "psid-postback-1"},
                            "recipient": {"id": "page-1"},
                            "timestamp": 1770000005000,
                            "postback": {
                                "title": "了解配套",
                                "payload": "VIEW_PACKAGES",
                                "referral": {"source": "SHORTLINK", "ref": "menu-button"},
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
        event = self.db.collection("marketing_events").stream()[0].to_dict()
        self.assertEqual(event["event_type"], "messenger_postback_received")
        self.assertEqual(event["payload"]["postback_payload"], "VIEW_PACKAGES")
        messages = self.db.collection("marketing_conversations").stream()[0].reference.collection("messages").stream()
        self.assertEqual(messages[0].to_dict()["message_type"], "postback")
        self.assertEqual(messages[0].to_dict()["text"], "了解配套")
        self.assertEqual(self.task_queue.created_tasks[0]["processor"], "process-inbound-message")

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
                    "pack1": {"code": "pack1", "price_sgd": 39.9},
                    "pack2": {"code": "pack2", "price_sgd": 75.0},
                },
                "knowledge_base": {},
            },
        )

        self.assertIn("Allowed package codes", prompt)
        self.assertIn("pack1", prompt)
        self.assertNotIn(RETIRED_PACKAGE_CODE, prompt)
        self.assertIn("Do not invent new package codes", prompt)
        self.assertIn("checkout_ready may be true only", prompt)

    def test_gemini_chat_prompt_treats_whatsapp_channel_phone_as_collected(self) -> None:
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_chat_prompt(
            contact={
                "current_tag": "qualified_warm",
                "lead_goal": "self_care",
                "identifiers": {"wa_id": "6591119999", "phone_e164": "6591119999"},
                "order_fields": {"phone": "6591119999"},
            },
            messages=[],
            incoming_text="我要两盒，地址是 1 Orchard Road Singapore 238823",
            channel="whatsapp",
            runtime_settings={
                "packages": {
                    "pack2": {"code": "pack2", "price_sgd": 75.0},
                },
                "knowledge_base": {},
            },
        )

        self.assertIn("Known channel phone: 6591119999", prompt)
        self.assertIn("the known WhatsApp sender number already counts as the phone field", prompt)
        self.assertIn("do not ask for the phone number again", prompt)

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
        for consultation_message in [
            "When to take?",
            "我是男的，可以喝吗？",
            "什么时候喝比较合适？",
            "便秘可以吗？",
            "适合上班族日常喝吗？",
            "Can I take it daily?",
        ]:
            selected = router.select_active_skill_ids(
                contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
                incoming_text=consultation_message,
            )
            self.assertIn("usage_consultation", selected)
            self.assertNotIn("price_objection", selected)
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
        self.assertIn(
            "checkout_collect",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
                incoming_text="运费怎么算？地址是 Jurong West",
            ),
        )
        self.assertIn(
            "checkout_collect",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
                incoming_text="I want to order 2 boxes. Delivery how long?",
            ),
        )
        self.assertIn(
            "price_objection",
            router.select_active_skill_ids(
                contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
                incoming_text="How much is it?",
            ),
        )
        self.assertIn(
            "price_objection",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
                incoming_text="为什么比 Brand's 贵？",
            ),
        )
        self.assertIn(
            "price_objection",
            router.select_active_skill_ids(
                contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
                incoming_text="Why so expensive? It feels pricey.",
            ),
        )

    def test_gemini_service_escalates_manual_handoff_without_model_call(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        turn = GeminiConversationService().generate_chat_reply(
            contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
            messages=[],
            incoming_text="我要找真人",
            channel="messenger",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertTrue(turn.escalate)
        self.assertEqual(turn.next_tag, "handoff_pending")
        self.assertEqual(turn.escalation_reason, "manual_handoff_requested")
        self.assertIn("+6591212369", turn.reply_text)

    def test_gemini_service_escalates_non_product_human_help(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        turn = GeminiConversationService().generate_chat_reply(
            contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
            messages=[],
            incoming_text="这不是鸡精的问题，我需要负责人帮忙",
            channel="whatsapp",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertTrue(turn.escalate)
        self.assertEqual(turn.next_tag, "handoff_pending")
        self.assertEqual(turn.escalation_reason, "non_product_human_help")
        self.assertIn("+6591212369", turn.reply_text)

    def test_gemini_service_escalates_complex_medical_judgment(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        turn = GeminiConversationService().generate_chat_reply(
            contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
            messages=[],
            incoming_text="我在化疗，可以停药改喝这个吗？",
            channel="messenger",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertTrue(turn.escalate)
        self.assertEqual(turn.next_tag, "handoff_pending")
        self.assertEqual(turn.escalation_reason, "medical_safety")
        self.assertIn("+6591212369", turn.reply_text)

    def test_gemini_service_escalates_unknown_requires_human(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        turn = GeminiConversationService().generate_chat_reply(
            contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
            messages=[],
            incoming_text="你不能确认库存和付款状态的话，请负责人处理",
            channel="messenger",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertTrue(turn.escalate)
        self.assertEqual(turn.next_tag, "handoff_pending")
        self.assertEqual(turn.escalation_reason, "unknown_requires_human")
        self.assertIn("+6591212369", turn.reply_text)

    def test_gemini_sales_turn_sanitizes_internal_reply_fields(self) -> None:
        from app.services.gemini_service import GeminiConversationService

        turn = GeminiConversationService._normalize_sales_turn_payload(
            {
                "reply_text": "skill_id=price_objection next_tag=cart_hot checkout_ready=false",
                "next_tag": "qualified_warm",
                "lead_goal": "unknown",
                "checkout_ready": False,
                "escalate": False,
                "opt_in_granted": False,
            }
        )

        self.assertNotIn("skill_id", turn.reply_text)
        self.assertNotIn("checkout_ready", turn.reply_text)
        self.assertFalse(turn.escalate)

    def test_chatbot_skill_router_selects_cart_hot_checkout_for_buying_intent(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.chatbot_skill_router import ChatbotSkillRouter

        router = ChatbotSkillRouter(get_default_chatbot_settings())
        hot_messages = [
            "二盒",
            "我要两盒",
            "2 boxes",
            "how to order",
            "是货到付款吗？",
            "PayNow 怎么付？",
            "下单后多久收到？",
            "可以送货吗？",
        ]

        for message in hot_messages:
            with self.subTest(message=message):
                selected = router.select_active_skill_ids(
                    contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
                    incoming_text=message,
                    max_skills=4,
                )
                self.assertIn("cart_hot_checkout", selected)
                self.assertNotEqual(selected, ["usage_consultation"])

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

    def test_gemini_chat_prompt_keeps_consultation_from_repeating_recent_price(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
            messages=[
                {"role": "user", "text": "多少钱？"},
                {"role": "assistant", "text": "1盒 SGD47.90，2盒 SGD79.80，等于 SGD39.90/盒。"},
            ],
            incoming_text="我是男的，可以喝吗？",
            channel="messenger",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertIn("Recent assistant price quote: yes", prompt)
        self.assertIn("Incoming asks price/order/shipping: no", prompt)
        self.assertIn("do not repeat any SGD prices", prompt)
        self.assertIn("usage_consultation", prompt)
        self.assertNotIn("price_objection", prompt)

    def test_gemini_chat_prompt_allows_price_when_customer_asks_price(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "qualified_warm", "lead_goal": "unknown"},
            messages=[
                {"role": "assistant", "text": "1盒 SGD47.90，2盒 SGD79.80，等于 SGD39.90/盒。"},
            ],
            incoming_text="多少钱？",
            channel="messenger",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertIn("Recent assistant price quote: yes", prompt)
        self.assertIn("Incoming asks price/order/shipping: yes", prompt)
        self.assertIn("price_objection", prompt)

    def test_gemini_chat_prompt_requires_direct_delivery_fee_answer(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "qualified_warm", "lead_goal": "pregnancy"},
            messages=[],
            incoming_text="How much is the delivery fees?",
            channel="messenger",
            runtime_settings=get_default_chatbot_settings(),
        )

        self.assertIn("Incoming asks price/order/shipping: yes", prompt)
        self.assertIn("reply_text must first state clearly", prompt)
        self.assertIn("current prices already include Singapore delivery fee", prompt)
        self.assertIn("there is no separate delivery fee", prompt)
        self.assertIn("Do not answer this with vague delivery-arrangement language", prompt)

    def test_process_inbound_message_creates_paynow_checkout_session_without_email(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我已经为您准备好 PayNow 付款链接，您确认一下资料就可以付款了 🎈",
                "next_tag": "cart_hot",
                "lead_goal": "pregnancy",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "gift_choice": "whole-leg",
                "order_fields": {
                    "name": "Alice Tan",
                    "phone": "6591112222",
                    "address": "1 Orchard Road, Singapore 238823",
                    "gift_choice": "French Poulet Whole Leg 400g",
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
            incoming_text="我要买2盒",
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
        self.assertEqual(order["marketing_contact_id"], "contact-1")
        self.assertEqual(order["conversation_id"], "conv-1")
        self.assertEqual(order["channel"], "whatsapp")
        self.assertEqual(order["subtotal_amount"], 79.8)
        self.assertEqual(order["shipping_fee"], 0.0)
        self.assertEqual(order["total_amount"], 79.8)
        self.assertEqual(order["box_count"], 2)
        self.assertEqual(order["gift_choice"]["code"], "whole-leg")
        self.assertEqual(order["gift_choice"]["display_name"], "French Poulet Whole Leg 400g")

        sessions = self.db.collection("marketing_checkout_sessions").stream()
        self.assertEqual(len(sessions), 1)
        session = sessions[0].to_dict()
        self.assertEqual(session["order_id"], orders[0].id)
        self.assertIn("https://aqina.example.com/paynow/", session["checkout_url"])
        self.assertEqual(session["gift_choice"]["code"], "whole-leg")

        contact = self.db.collection("marketing_contacts").document("contact-1").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")
        self.assertEqual(contact["selected_package_code"], "pack2")
        self.assertEqual(contact["order_fields"]["name"], "Alice Tan")
        self.assertEqual(contact["order_fields"]["gift_choice"]["display_name"], "French Poulet Whole Leg 400g")

        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("/paynow/", message_calls[0][1]["text"])
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 4)
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
            {
                "chatbot_initial_promotion_media",
                "chatbot_brand_intro_media",
                "chatbot_product_media",
                "paynow_qr_media",
            },
        )

    def test_process_inbound_message_alerts_staff_for_hot_lead_without_order(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "好的，2盒 SGD79.80 很适合您。麻烦发我新加坡收货地址，我就帮您安排付款链接。",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "gift_choice": None,
                "order_fields": {"name": "May Tan"},
                "missing_order_fields": ["address"],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-hot",
            conversation_id="conv-hot",
            event_id="event-hot",
            channel="whatsapp",
            incoming_text="我要 2 盒",
            identifier_key="wa_id",
            identifier_value="6591234567",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-hot"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        # No order is created because the delivery address is still missing.
        self.assertEqual(len(self.db.collection("orders").stream()), 0)
        # Staff are alerted so a human can step in and close the hot lead.
        escalations = [snapshot.to_dict() for snapshot in self.db.collection("marketing_escalations").stream()]
        hot_alert = next(item for item in escalations if item["reason"] == "cart_hot_no_order")
        self.assertEqual(hot_alert["status"], "open")
        contact = self.db.collection("marketing_contacts").document("contact-hot").get().to_dict()
        self.assertTrue(contact.get("hot_lead_alert_sent"))
        # Automation is NOT paused — the bot keeps nurturing while a human can also close.
        self.assertFalse(contact.get("automation_paused"))

    def test_should_not_send_paynow_qr_for_delivery_timing_question(self) -> None:
        from app.services.chatbot_skill_router import should_send_paynow_qr_for_checkout_intent

        # "下单后多久能收到" is a delivery-timing question, not a buying action, so it must
        # not auto-dump a PayNow QR before the customer has shown real buying intent.
        self.assertFalse(
            should_send_paynow_qr_for_checkout_intent("请问运费怎么算？下单后多久能收到？")
        )
        # A genuine order verb still triggers the QR.
        self.assertTrue(should_send_paynow_qr_for_checkout_intent("我要下单"))
        # An explicit quantity selection still triggers the QR.
        self.assertTrue(should_send_paynow_qr_for_checkout_intent("我要 2 盒"))

    def test_default_settings_include_seeded_templated_openers(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings

        openers = get_default_chatbot_settings()["templated_openers"]
        self.assertIsInstance(openers, list)
        self.assertIn("请问运费怎么算？下单后多久能收到？", openers)

    def test_templated_opener_detection_helpers(self) -> None:
        from app.services.chatbot_skill_router import has_typed_organic_message, is_templated_opener_text

        openers = ["📦 How much is shipping & delivery time?", "请问运费怎么算？下单后多久能收到？"]
        # Emoji / spacing / punctuation differences are ignored.
        self.assertTrue(is_templated_opener_text("How much is shipping & delivery time?", openers))
        self.assertTrue(is_templated_opener_text("请问运费怎么算？下单后多久能收到？", openers))
        # A genuinely typed question is not a preset opener.
        self.assertFalse(is_templated_opener_text("运费多少？我想买给妈妈", openers))
        # Organic-history detection.
        only_template = [{"role": "user", "text": "请问运费怎么算？下单后多久能收到？"}]
        self.assertFalse(has_typed_organic_message(only_template, openers))
        self.assertTrue(has_typed_organic_message(only_template + [{"role": "user", "text": "我想买给妈妈"}], openers))

    def test_gemini_chat_prompt_flags_preset_ad_opener(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import GeminiConversationService

        runtime_settings = get_default_chatbot_settings()
        opener_prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
            messages=[],
            incoming_text="请问运费怎么算？下单后多久能收到？",
            channel="messenger",
            runtime_settings=runtime_settings,
        )
        self.assertIn("Incoming is preset ad opener (tapped/auto, not typed): yes", opener_prompt)
        self.assertIn("ask exactly ONE qualifying question", opener_prompt)

        typed_prompt = GeminiConversationService._build_chat_prompt(
            contact={"current_tag": "lead_cold", "lead_goal": "unknown"},
            messages=[],
            incoming_text="运费多少？我想买给妈妈试试",
            channel="messenger",
            runtime_settings=runtime_settings,
        )
        self.assertIn("Incoming is preset ad opener (tapped/auto, not typed): no", typed_prompt)

    def test_templated_opener_first_message_is_not_marked_hot(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "新加坡现货通常 1-3 个工作日送达，价格已含运费。请问您是自己喝、送长辈，还是孕期调理呢？",
                "next_tag": "cart_hot",
                "lead_goal": "unknown",
                "recommended_package_code": None,
                "upgrade_package_code": None,
                "selected_package_code": None,
                "gift_choice": None,
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
            contact_id="contact-tpl",
            conversation_id="conv-tpl",
            event_id="event-tpl",
            channel="messenger",
            incoming_text="请问运费怎么算？下单后多久能收到？",
            identifier_key="psid",
            identifier_value="psid-tpl",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-tpl"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        contact = self.db.collection("marketing_contacts").document("contact-tpl").get().to_dict()
        # An over-eager LLM cart_hot is downgraded — a tapped preset opener is not a hot lead.
        self.assertNotEqual(contact.get("current_tag"), "cart_hot")
        # No staff hot-lead alert for a preset opener.
        escalations = [s.to_dict() for s in self.db.collection("marketing_escalations").stream()]
        self.assertFalse(any(e["reason"] == "cart_hot_no_order" for e in escalations))
        # No PayNow QR dumped on a preset opener.
        outbound_images = [
            s.to_dict()
            for s in self.db.collection("marketing_conversations").document("conv-tpl").collection("messages").stream()
            if s.to_dict().get("message_type") == "image"
        ]
        self.assertNotIn("paynow_qr_media", {item["source"] for item in outbound_images})

    def test_whatsapp_click_to_whatsapp_referral_is_captured(self) -> None:
        self._seed_runtime_settings()
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "您好！很高兴为您介绍 Aqina 纯鸡精。",
                "next_tag": "lead_cold",
                "lead_goal": "unknown",
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
                                        "from": "6591119988",
                                        "id": "wamid.ctwa.1",
                                        "timestamp": "1777957353",
                                        "type": "text",
                                        "text": {"body": "Hi, I saw your ad"},
                                        "referral": {
                                            "source_url": "https://fb.me/abc",
                                            "source_id": "120200000000000",
                                            "source_type": "ad",
                                            "headline": "Aqina Pure Chicken Essence",
                                            "body": "Hi Aqina SG, I'm interested in your premium chicken essence.",
                                            "ctwa_clid": "ctwa-123",
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
        contacts = [s.to_dict() for s in self.db.collection("marketing_contacts").stream()]
        self.assertEqual(len(contacts), 1)
        acquisition = contacts[0].get("acquisition") or {}
        self.assertEqual(acquisition.get("source"), "ad")
        self.assertEqual(acquisition.get("ad_id"), "120200000000000")

    def test_process_inbound_message_uses_whatsapp_sender_phone_for_checkout(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我还需要您的联系电话才可以安排付款。",
                "next_tag": "qualified_warm",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "order_fields": {
                    "name": "Christine Yon",
                    "phone": None,
                    "address": "Jurong West Street 92 #03-211 Singapore 640831",
                },
                "missing_order_fields": ["phone"],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-whatsapp-phone-default",
            conversation_id="conv-whatsapp-phone-default",
            event_id="event-whatsapp-phone-default",
            channel="whatsapp",
            incoming_text="Christine Yon, Jurong West Street 92 #03-211, 我要 2 盒",
            identifier_key="wa_id",
            identifier_value="6591119999",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-whatsapp-phone-default"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["checkout_session_id"])

        chat_calls = [call for call in self.gemini_service.calls if call[0] == "generate_chat_reply"]
        self.assertEqual(chat_calls[0][1]["contact"]["order_fields"]["phone"], "6591119999")

        orders = self.db.collection("orders").stream()
        self.assertEqual(len(orders), 1)
        order = orders[0].to_dict()
        self.assertEqual(order["customer"]["name"], "Christine Yon")
        self.assertEqual(order["customer"]["whatsapp"], "6591119999")
        self.assertEqual(order["customer"]["address"], "Jurong West Street 92 #03-211 Singapore 640831")
        self.assertEqual(order["items"][0]["product_id"], "pack2")
        self.assertEqual(order["total_amount"], 79.8)

        contact = self.db.collection("marketing_contacts").document("contact-whatsapp-phone-default").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")
        self.assertEqual(contact["order_fields"]["phone"], "6591119999")
        self.assertEqual(contact["missing_order_fields"], [])

        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("PayNow", message_calls[0][1]["text"])
        self.assertNotIn("联系电话", message_calls[0][1]["text"])
        self.assertNotIn("电话号码", message_calls[0][1]["text"])

        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertTrue(any("Amount: SGD 79.80" in call[1]["caption"] for call in image_calls))
        outbound_images = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-whatsapp-phone-default")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("message_type") == "image"
        ]
        self.assertIn("paynow_qr_media", {item["source"] for item in outbound_images})

    def test_create_order_preserves_marketing_conversation_attribution(self) -> None:
        client = self._build_client()
        response = client.post(
            "/api/v1/orders",
            json={
                "marketing_contact_id": "contact_dd588779c551c8bf1a3c",
                "conversation_id": "conversation_af0fe19285b39b372938",
                "channel": "messenger",
                "customer": {
                    "name": "Test Buyer",
                    "whatsapp": "+6500000000",
                    "address": "1 Orchard Road, Singapore 238823",
                },
                "items": [
                    {
                        "product_id": "pack2",
                        "product_name": "14-Day Care Pack",
                        "product_name_zh": "14天常备装",
                        "quantity": 1,
                        "unit_price": 75.0,
                        "total_price": 75.0,
                    }
                ],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "utm_source": "facebook",
                "utm_campaign": "may-offer",
                "meta_campaign_id": "cmp_1",
                "meta_adset_id": "adset_1",
                "meta_ad_id": "ad_1",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["marketing_contact_id"], "contact_dd588779c551c8bf1a3c")
        self.assertEqual(payload["conversation_id"], "conversation_af0fe19285b39b372938")
        self.assertEqual(payload["channel"], "messenger")
        self.assertEqual(payload["source"], "marketing_inbox")
        order = self.db.collection("orders").stream()[0].to_dict()
        self.assertEqual(order["created_from"], "marketing_inbox")
        self.assertEqual(order["utm_source"], "facebook")
        self.assertEqual(order["meta_ad_id"], "ad_1")

    def test_process_inbound_message_sends_paynow_qr_before_messenger_phone_checkout(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我帮您安排，请再发联系电话。",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "order_fields": {
                    "name": "Ben Lim",
                    "phone": None,
                    "address": "20 Tampines Central Singapore 529538",
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
            contact_id="contact-messenger-missing-phone",
            conversation_id="conv-messenger-missing-phone",
            event_id="event-messenger-missing-phone",
            channel="messenger",
            incoming_text="Ben Lim, 20 Tampines Central Singapore 529538, 我要 2 盒",
            identifier_key="psid",
            identifier_value="psid-missing-phone",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-messenger-missing-phone"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["checkout_session_id"])
        self.assertEqual(self.db.collection("orders").stream(), [])

        contact = self.db.collection("marketing_contacts").document("contact-messenger-missing-phone").get().to_dict()
        self.assertIn("phone", contact["missing_order_fields"])

        message_calls = [call for call in self.meta_client.calls if call[0] == "send_messenger_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("联系电话", message_calls[0][1]["text"])
        image_calls = [
            call
            for call in self.meta_client.calls
            if call[0] in {"send_messenger_image_attachment", "send_messenger_image_url"}
        ]
        self.assertGreaterEqual(len(image_calls), 1)
        outbound_images = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-messenger-missing-phone")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("message_type") == "image"
        ]
        self.assertIn("paynow_qr_media", {item["source"] for item in outbound_images})
        contact = self.db.collection("marketing_contacts").document("contact-messenger-missing-phone").get().to_dict()
        self.assertTrue(contact.get("precheckout_paynow_qr_sent"))

    def test_process_inbound_message_does_not_repeat_precheckout_paynow_qr(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "没问题，我等您的姓名、联系电话和新加坡地址。",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "order_fields": {"name": None, "phone": None, "address": None},
                "missing_order_fields": ["name", "phone", "address"],
                "checkout_ready": False,
                "escalate": False,
                "escalation_reason": None,
                "faq_topic": None,
                "opt_in_granted": False,
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-precheckout-qr-sent",
            conversation_id="conv-precheckout-qr-sent",
            event_id="event-precheckout-qr-sent",
            channel="messenger",
            incoming_text="好的，谢谢",
            identifier_key="psid",
            identifier_value="psid-precheckout-qr-sent",
        )
        self.db.collection("marketing_contacts").document("contact-precheckout-qr-sent").set(
            {
                "current_tag": "cart_hot",
                "selected_package_code": "pack2",
                "precheckout_paynow_qr_sent": True,
            },
            merge=True,
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-precheckout-qr-sent"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["checkout_session_id"])
        outbound_images = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-precheckout-qr-sent")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("message_type") == "image"
        ]
        self.assertNotIn("paynow_qr_media", {item["source"] for item in outbound_images})

    def test_process_inbound_message_records_customer_request_remark_and_alerts_internal_numbers(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "可以，我先帮您备注星期五傍晚后送。您先用 PayNow QR 付款，付款后把截图发回来，客服会按备注跟进。",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "gift_choice": "French Poulet Whole Leg 400g",
                "customer_request_remark": "Customer requested delivery on Friday after 6pm.",
                "order_fields": {
                    "name": "Ben Lim",
                    "phone": "6592223333",
                    "address": "20 Tampines Central, Singapore 529538",
                    "gift_choice": "French Poulet Whole Leg 400g",
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
            contact_id="contact-delivery-remark",
            conversation_id="conv-delivery-remark",
            event_id="event-delivery-remark",
            channel="messenger",
            incoming_text="我要两盒，星期五傍晚后可以送吗？Ben Lim 6592223333 20 Tampines Central Singapore 529538",
            identifier_key="psid",
            identifier_value="psid-delivery-remark",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-delivery-remark"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["checkout_session_id"])

        order = self.db.collection("orders").stream()[0].to_dict()
        self.assertEqual(order["payment_status"], "pending")
        self.assertEqual(order["customer_request_remark"], "Customer requested delivery on Friday after 6pm.")
        self.assertEqual(order["notes"], "Customer requested delivery on Friday after 6pm.")

        contact = self.db.collection("marketing_contacts").document("contact-delivery-remark").get().to_dict()
        self.assertEqual(contact["customer_request_remark"], "Customer requested delivery on Friday after 6pm.")

        escalations = [snapshot.to_dict() for snapshot in self.db.collection("marketing_escalations").stream()]
        order_alert = next(item for item in escalations if item["reason"] == "order_created_pending_payment")
        self.assertEqual(order_alert["remark"], "Customer requested delivery on Friday after 6pm.")
        self.assertEqual(order_alert["notification_status"], "sent")
        self.assertEqual(order_alert["private_whatsapp_numbers"], ["6599990000", "+60149449341"])
        template_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_template"]
        self.assertEqual([call[1]["to"] for call in template_calls], ["6599990000", "+60149449341"])

    def test_process_inbound_message_alerts_new_request_on_existing_checkout_session(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "可以，我先帮您备注明天上午10点送。您先用 PayNow QR 付款，付款后把截图发回来，客服会按备注跟进。",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": None,
                "selected_package_code": "pack2",
                "gift_choice": "French Poulet Whole Leg 400g",
                "customer_request_remark": "Customer requested delivery tomorrow at 10am.",
                "order_fields": {
                    "name": "Ben Lim",
                    "phone": "6592223333",
                    "address": "20 Tampines Central, Singapore 529538",
                    "gift_choice": "French Poulet Whole Leg 400g",
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
            contact_id="contact-existing-request",
            conversation_id="conv-existing-request",
            event_id="event-existing-request",
            channel="messenger",
            incoming_text="我已经下单了，可以明天上午10点送吗？",
            identifier_key="psid",
            identifier_value="psid-existing-request",
        )
        self.db.collection("marketing_contacts").document("contact-existing-request").set(
            {
                "checkout_session_id": "session-existing-request",
                "selected_package_code": "pack2",
                "customer_request_alert_sent": True,
                "customer_request_alert_id": "old-alert",
                "customer_request_alert_remark": "Customer requested Friday after 6pm.",
            },
            merge=True,
        )
        self.db.seed(
            "marketing_checkout_sessions/session-existing-request",
            {
                "contact_id": "contact-existing-request",
                "conversation_id": "conv-existing-request",
                "order_id": "order-existing-request",
                "checkout_url": "https://aqina.example/paynow/session-existing-request",
                "payment_reference": "AQINA-order-existing-request",
                "total_amount": 79.8,
                "package_code": "pack2",
            },
        )
        self.db.seed(
            "orders/order-existing-request",
            {
                "order_id": "order-existing-request",
                "payment_status": "pending",
                "order_status": "pending",
                "total_amount": 79.8,
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-existing-request"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checkout_session_id"], "session-existing-request")

        order = self.db.collection("orders").document("order-existing-request").get().to_dict()
        self.assertEqual(order["customer_request_remark"], "Customer requested delivery tomorrow at 10am.")
        self.assertEqual(order["notes"], "Customer requested delivery tomorrow at 10am.")

        contact = self.db.collection("marketing_contacts").document("contact-existing-request").get().to_dict()
        self.assertEqual(contact["customer_request_alert_remark"], "Customer requested delivery tomorrow at 10am.")

        escalations = [snapshot.to_dict() for snapshot in self.db.collection("marketing_escalations").stream()]
        request_alert = next(item for item in escalations if item["reason"] == "customer_request_remark")
        self.assertEqual(request_alert["remark"], "Customer requested delivery tomorrow at 10am.")
        self.assertEqual(request_alert["notification_status"], "sent")
        self.assertEqual(request_alert["private_whatsapp_numbers"], ["6599990000", "+60149449341"])

    def test_process_inbound_message_creates_pack1_checkout_with_shipping(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "可以的，我先帮您安排7天启动装，适合先试口感 🎈",
                "next_tag": "cart_hot",
                "lead_goal": "self_care",
                "recommended_package_code": "pack1",
                "upgrade_package_code": "pack2",
                "selected_package_code": "pack1",
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
            incoming_text="我要一盒",
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
        self.assertEqual(order["items"][0]["product_id"], "pack1")
        self.assertEqual(order["subtotal_amount"], 47.9)
        self.assertEqual(order["shipping_fee"], 0.0)
        self.assertEqual(order["total_amount"], 47.9)
        self.assertEqual(order["box_count"], 1)

        contact = self.db.collection("marketing_contacts").document("contact-trial").get().to_dict()
        self.assertEqual(contact["selected_package_code"], "pack1")
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 4)

    def test_process_inbound_message_prepends_direct_delivery_fee_answer(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": (
                    "Our customer service team will confirm the delivery arrangements with you during checkout. "
                    "Would you like to start with 1 box at SGD47.90 or the 2-box value pack at SGD79.80?"
                ),
                "next_tag": "qualified_warm",
                "lead_goal": "pregnancy",
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
            contact_id="contact-delivery-fee",
            conversation_id="conv-delivery-fee",
            event_id="event-delivery-fee",
            channel="messenger",
            incoming_text="How much is the delivery fees?",
            identifier_key="psid",
            identifier_value="psid-delivery-fee",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-delivery-fee"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-delivery-fee")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound" and snapshot.to_dict().get("message_type") == "text"
        ]
        self.assertEqual(len(outbound_messages), 1)
        reply_text = outbound_messages[0]["text"]
        self.assertTrue(reply_text.startswith("The listed prices already include Singapore delivery fee"))
        self.assertIn("there is no separate delivery fee", reply_text)

    def test_process_inbound_message_sends_brand_and_package_images_without_url_text(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "懂您，忙起来确实会想找简单一点的温热补给。我更建议您看2盒，SGD79.80，等于 SGD39.90/盒。",
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
        self.assertEqual(len(image_calls), 3)
        call_names = [call[0] for call in self.meta_client.calls]
        self.assertLess(call_names.index("send_whatsapp_image"), call_names.index("send_whatsapp_text"))

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
            ["chatbot_initial_promotion_media", "chatbot_brand_intro_media", "chatbot_product_media"],
        )
        contact = self.db.collection("marketing_contacts").document("contact-media").get().to_dict()
        self.assertTrue(contact["sent_media"]["initial_promotion"])
        self.assertTrue(contact["sent_media"]["initial_promotion_languages"]["zh"])
        self.assertTrue(contact["sent_media"]["brand_intro"])
        self.assertTrue(contact["sent_media"]["brand_intro_languages"]["zh"])
        self.assertTrue(contact["sent_media"]["package_images"]["pack2"])
        promo_media = self.db.collection("meta_media_assets").document("initial_promotion_zh_whatsapp").get().to_dict()
        brand_media = self.db.collection("meta_media_assets").document("brand_intro_zh_whatsapp").get().to_dict()
        pack_media = self.db.collection("meta_media_assets").document("package_pack2_zh_whatsapp").get().to_dict()
        self.assertEqual(
            promo_media["source_url"],
            "https://aqina.example.com/chatbot/aqina-pack2-french-poulet-promotion-zh.jpg",
        )
        self.assertEqual(brand_media["source_url"], "https://aqina.example.com/chatbot/aqina-purity-cycle-zh.jpg")
        self.assertEqual(pack_media["source_url"], "https://aqina.example.com/chatbot/aqina-offer-gift-guide-zh.jpg")

    def test_process_inbound_message_sends_english_chatbot_images_for_english_customer(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "I recommend the 2-box pack because it is SGD79.80 and includes one French Poulet Cut Part gift choice.",
                "next_tag": "qualified_warm",
                "lead_goal": "self_care",
                "recommended_package_code": "pack2",
                "upgrade_package_code": "pack1",
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
            contact_id="contact-media-en",
            conversation_id="conv-media-en",
            event_id="event-media-en",
            channel="whatsapp",
            incoming_text="How much is it?",
            identifier_key="wa_id",
            identifier_value="6592220101",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-media-en"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertNotIn("http", message_calls[0][1]["text"])
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 3)
        self.assertIn("current offer", image_calls[0][1]["caption"].lower())
        self.assertIn("french poulet cut part", image_calls[2][1]["caption"].lower())

        contact = self.db.collection("marketing_contacts").document("contact-media-en").get().to_dict()
        self.assertEqual(contact["chatbot_locale"], "en")
        self.assertTrue(contact["sent_media"]["initial_promotion"])
        self.assertTrue(contact["sent_media"]["initial_promotion_languages"]["en"])
        self.assertTrue(contact["sent_media"]["brand_intro_languages"]["en"])
        self.assertTrue(contact["sent_media"]["package_images"]["pack2"])
        promo_media = self.db.collection("meta_media_assets").document("initial_promotion_en_whatsapp").get().to_dict()
        brand_media = self.db.collection("meta_media_assets").document("brand_intro_en_whatsapp").get().to_dict()
        pack_media = self.db.collection("meta_media_assets").document("package_pack2_en_whatsapp").get().to_dict()
        self.assertEqual(
            promo_media["source_url"],
            "https://aqina.example.com/chatbot/aqina-pack2-french-poulet-promotion-en.jpg",
        )
        self.assertEqual(brand_media["source_url"], "https://aqina.example.com/chatbot/aqina-purity-cycle-en.jpg")
        self.assertEqual(pack_media["source_url"], "https://aqina.example.com/chatbot/aqina-offer-gift-guide-en.jpg")

    def test_process_inbound_message_does_not_resend_seen_chatbot_images(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我继续建议您拿2盒，SGD79.80，等于 SGD39.90/盒，也有 French Poulet Cut Part 赠品。",
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
                    "initial_promotion": True,
                    "initial_promotion_languages": {"zh": True},
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

    def test_process_inbound_message_marks_hot_quantity_as_cart_hot_when_model_underclassifies(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "您想了解 2 盒的话，我可以帮您确认。",
                "next_tag": "qualified_warm",
                "lead_goal": "unknown",
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
            }
        )
        self._seed_runtime_settings()
        self._seed_contact_and_event(
            contact_id="contact-hot-quantity",
            conversation_id="conv-hot-quantity",
            event_id="event-hot-quantity",
            channel="messenger",
            incoming_text="二盒",
            identifier_key="psid",
            identifier_value="273700003322",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-hot-quantity"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        contact = self.db.collection("marketing_contacts").document("contact-hot-quantity").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")

    def test_process_inbound_message_marks_hot_checkout_handoff_recommended_without_pausing(self) -> None:
        self.gemini_service = FakeGeminiService(
            chat_result={
                "reply_text": "我帮您确认两盒。",
                "next_tag": "qualified_warm",
                "lead_goal": "unknown",
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
            contact_id="contact-hot-handoff",
            conversation_id="conv-hot-handoff",
            event_id="event-hot-handoff",
            channel="messenger",
            incoming_text="二盒",
            identifier_key="psid",
            identifier_value="273700004444",
        )
        self.db.seed(
            "marketing_conversations/conv-hot-handoff/messages/msg-price",
            {
                "direction": "inbound",
                "role": "user",
                "text": "运费多少？可以 COD 吗？",
                "source": "messenger_webhook",
                "created_at": "2026-04-10T00:00:01Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-inbound-message",
            json={"event_id": "event-hot-handoff"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        contact = self.db.collection("marketing_contacts").document("contact-hot-handoff").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")
        self.assertTrue(contact["handoff_recommended"])
        self.assertEqual(contact["handoff_reason"], "high_intent_checkout")
        self.assertFalse(contact.get("automation_paused", False))

    def test_landing_order_with_receipt_uses_offer_reset_total_for_one_box(self) -> None:
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
        self.assertEqual(payload["subtotal_amount"], 47.9)
        self.assertEqual(payload["shipping_fee"], 0.0)
        self.assertEqual(payload["total_amount"], 47.9)
        self.assertEqual(payload["box_count"], 1)
        self.assertEqual(payload["payment_status"], "payment_submitted")
        self.assertEqual(payload["payment_receipt_url"], "https://storage.example.com/receipt.png")

    def test_landing_order_with_receipt_sends_meta_capi_add_to_cart_after_consent(self) -> None:
        client = self._build_client()

        with (
            patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"),
            patch("app.services.meta_conversions.settings.meta_pixel_id", "pixel-123"),
            patch("app.services.meta_conversions.settings.meta_conversions_access_token", "capi-token"),
            patch("app.services.meta_conversions.settings.meta_conversions_test_event_code", ""),
        ):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Janice Lee",
                    "customer_phone": "6598765432",
                    "customer_address": "20 Tanjong Pagar Road, Singapore 088443",
                    "product_id": "pack1",
                    "marketing_consent": "accepted",
                    "marketing_event_id": "receipt_add_to_cart_test_123",
                    "event_source_url": "https://aqina-sg.web.app/zh?fbclid=test-click",
                    "page_path": "/zh",
                    "landing_version": "offer_reset",
                    "language": "zh",
                    "marketing_fbp": "fb.1.1710000000.browser",
                    "marketing_fbc": "fb.1.1710000001.click",
                },
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
                headers={
                    "user-agent": "pytest-browser",
                    "x-forwarded-for": "203.0.113.8, 10.0.0.1",
                },
            )

        self.assertEqual(response.status_code, 201)
        calls = [call for call in self.meta_client.calls if call[0] == "send_conversion_event"]
        self.assertEqual(len(calls), 1)
        call = calls[0][1]
        self.assertEqual(call["pixel_id"], "pixel-123")

        event = call["events"][0]
        self.assertEqual(event["event_name"], "AddToCart")
        self.assertEqual(event["event_id"], "receipt_add_to_cart_test_123")
        self.assertEqual(event["action_source"], "website")
        self.assertEqual(event["event_source_url"], "https://aqina-sg.web.app/zh?fbclid=test-click")
        self.assertEqual(event["custom_data"]["value"], 47.9)
        self.assertEqual(event["custom_data"]["currency"], "SGD")
        self.assertEqual(event["custom_data"]["content_ids"], ["pack1"])
        self.assertEqual(event["custom_data"]["landing_version"], "offer_reset")
        self.assertEqual(event["custom_data"]["language"], "zh")
        self.assertEqual(event["custom_data"]["page_path"], "/zh")
        self.assertEqual(event["user_data"]["fbp"], "fb.1.1710000000.browser")
        self.assertEqual(event["user_data"]["fbc"], "fb.1.1710000001.click")
        self.assertEqual(event["user_data"]["client_ip_address"], "203.0.113.8")
        self.assertEqual(event["user_data"]["client_user_agent"], "pytest-browser")
        self.assertEqual(
            event["user_data"]["ph"],
            [hashlib.sha256("6598765432".encode("utf-8")).hexdigest()],
        )

        order = self.db.collection("orders").stream()[0].to_dict()
        self.assertEqual(order["meta_capi"]["add_to_cart"]["status"], "sent")
        self.assertEqual(order["meta_capi"]["add_to_cart"]["event_id"], "receipt_add_to_cart_test_123")

    def test_track_order_purchase_sends_meta_capi_purchase_and_is_idempotent(self) -> None:
        self.db.seed(
            "orders/order-paid-1",
            {
                "items": [{"product_id": "pack2", "product_name": "14天常备装", "quantity": 1}],
                "customer": {
                    "name": "Janice Lee",
                    "whatsapp": "6598765432",
                    "address": "20 Tanjong Pagar Road, Singapore 088443",
                },
                "total_amount": 79.8,
                "box_count": 2,
                "payment_status": "paid",
                "order_status": "pending",
            },
        )
        client = self._build_client()
        with (
            patch("app.services.meta_conversions.settings.meta_pixel_id", "pixel-123"),
            patch("app.services.meta_conversions.settings.meta_conversions_access_token", "capi-token"),
            patch("app.services.meta_conversions.settings.meta_conversions_test_event_code", ""),
        ):
            response = client.post(
                "/api/v1/orders/order-paid-1/track-purchase",
                headers={"Authorization": "Bearer admin-token"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "sent")

            calls = [call for call in self.meta_client.calls if call[0] == "send_conversion_event"]
            self.assertEqual(len(calls), 1)
            event = calls[0][1]["events"][0]
            self.assertEqual(event["event_name"], "Purchase")
            self.assertEqual(event["custom_data"]["value"], 79.8)
            self.assertEqual(event["custom_data"]["currency"], "SGD")
            self.assertEqual(
                event["user_data"]["ph"],
                [hashlib.sha256("6598765432".encode("utf-8")).hexdigest()],
            )
            order = self.db.collection("orders").document("order-paid-1").get().to_dict()
            self.assertEqual(order["meta_capi"]["purchase"]["status"], "sent")

            # Idempotent: a second call does not fire another Purchase event.
            second = client.post(
                "/api/v1/orders/order-paid-1/track-purchase",
                headers={"Authorization": "Bearer admin-token"},
            )
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.json()["status"], "already_sent")
            calls_after = [call for call in self.meta_client.calls if call[0] == "send_conversion_event"]
            self.assertEqual(len(calls_after), 1)

    def test_track_order_purchase_skips_when_consent_declined(self) -> None:
        self.db.seed(
            "orders/order-declined",
            {
                "items": [{"product_id": "pack1", "product_name": "7天启动装"}],
                "customer": {"name": "Sam", "whatsapp": "6591110000"},
                "total_amount": 47.9,
                "box_count": 1,
                "marketing_consent": "declined",
            },
        )
        client = self._build_client()
        with (
            patch("app.services.meta_conversions.settings.meta_pixel_id", "pixel-123"),
            patch("app.services.meta_conversions.settings.meta_conversions_access_token", "capi-token"),
        ):
            response = client.post(
                "/api/v1/orders/order-declined/track-purchase",
                headers={"Authorization": "Bearer admin-token"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "skipped")
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_conversion_event"])

    def test_landing_order_with_receipt_does_not_send_meta_capi_without_consent(self) -> None:
        client = self._build_client()

        with (
            patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"),
            patch("app.services.meta_conversions.settings.meta_pixel_id", "pixel-123"),
            patch("app.services.meta_conversions.settings.meta_conversions_access_token", "capi-token"),
        ):
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
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_conversion_event"])

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
        self.assertEqual(payload["subtotal_amount"], 79.8)
        self.assertEqual(payload["shipping_fee"], 0.0)
        self.assertEqual(payload["total_amount"], 79.8)
        self.assertEqual(payload["box_count"], 2)

    def test_landing_order_with_receipt_stores_two_box_gift_choice(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Kelvin Tan",
                    "customer_phone": "6591234567",
                    "customer_address": "1 Orchard Road, Singapore 238823",
                    "product_id": "pack2",
                    "gift_choice": "French Poulet 3 Joint Wing 500g",
                },
                files={"payment_receipt": ("receipt.webp", b"fake-image", "image/webp")},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["customer"]["name"], "Kelvin Tan")
        self.assertNotIn("赠", payload["customer"]["name"])
        self.assertEqual(payload["gift_choice"]["code"], "joint-wing")
        self.assertEqual(payload["gift_choice"]["display_name"], "French Poulet 3 Joint Wing 500g")

        order = self.db.collection("orders").stream()[0].to_dict()
        self.assertEqual(order["customer"]["name"], "Kelvin Tan")
        self.assertEqual(order["gift_choice"]["code"], "joint-wing")
        self.assertEqual(order["gift_choice"]["display_name"], "French Poulet 3 Joint Wing 500g")

    def test_landing_order_with_receipt_rejects_retired_offer_packages(self) -> None:
        client = self._build_client()

        for product_id in ["pack4", "pack6", "unknown-pack"]:
            with self.subTest(product_id=product_id):
                response = client.post(
                    "/api/v1/orders/with-receipt",
                    data={
                        "customer_name": "Kelvin Tan",
                        "customer_phone": "6591234567",
                        "customer_address": "1 Orchard Road, Singapore 238823",
                        "product_id": product_id,
                    },
                    files={"payment_receipt": ("receipt.webp", b"fake-image", "image/webp")},
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "Unknown package")

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
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 0)
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
                        "product_name": "14天常备装",
                        "product_name_zh": "14天常备装",
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
                "total_amount": 79.8,
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
                "subtotal_amount": 79.8,
                "shipping_fee": 0.0,
                "box_count": 2,
                "total_amount": 79.8,
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

    def test_whatsapp_receipt_ai_verification_records_matching_reference(self) -> None:
        self._seed_active_receipt_checkout(
            contact_id="contact-receipt-ok",
            conversation_id="conv-receipt-ok",
            session_id="session-receipt-ok",
            event_id="event-receipt-ok",
            order_id="order_receipt_ok",
            total_amount=79.8,
        )
        self.gemini_service.receipt_analysis = {
            "paid_amount": 79.8,
            "currency": "SGD",
            "bank_transaction_reference": "ABC123456",
            "recipient_reference": "AQINA-order_receipt_ok",
            "payment_datetime": "2026-04-10 10:30",
            "confidence": 0.94,
            "warnings": [],
        }

        client = self._build_client()
        with patch("app.services.marketing_orchestrator.upload_public_file_to_firebase", return_value="https://storage.example.com/chat-receipt-ok.jpg"):
            response = client.post(
                "/api/v1/marketing/tasks/process-inbound-message",
                json={"event_id": "event-receipt-ok"},
                headers={"X-Internal-Token": "internal-secret"},
            )

        self.assertEqual(response.status_code, 200)
        order = self.db.collection("orders").document("order_receipt_ok").get().to_dict()
        verification = order["payment_verification"]
        self.assertEqual(order["payment_status"], "payment_submitted")
        self.assertEqual(order["transaction_id"], "ABC123456")
        self.assertEqual(verification["status"], "ok")
        self.assertEqual(verification["expected_amount"], 79.8)
        self.assertEqual(verification["extracted_amount"], 79.8)
        self.assertEqual(verification["reference_number"], "ABC123456")
        self.assertEqual(verification["reference_normalized"], "ABC123456")
        self.assertTrue(verification["amount_match"])
        self.assertFalse(verification["duplicate_detected"])
        payments = self.db.collection("payments").stream()
        self.assertEqual(len(payments), 1)
        payment = payments[0].to_dict()
        self.assertEqual(payment["transaction_id"], "ABC123456")
        self.assertEqual(payment["payment_verification"]["status"], "ok")
        analysis_calls = [call for call in self.gemini_service.calls if call[0] == "analyze_payment_receipt_image"]
        self.assertEqual(len(analysis_calls), 1)
        self.assertEqual(analysis_calls[0][1]["expected_amount"], 79.8)

    def test_whatsapp_receipt_ai_verification_warns_underpaid_without_auto_paid(self) -> None:
        self._seed_active_receipt_checkout(
            contact_id="contact-receipt-underpaid",
            conversation_id="conv-receipt-underpaid",
            session_id="session-receipt-underpaid",
            event_id="event-receipt-underpaid",
            order_id="order_receipt_underpaid",
            total_amount=79.8,
        )
        self.gemini_service.receipt_analysis = {
            "paid_amount": 67.0,
            "currency": "SGD",
            "bank_transaction_reference": "PAY-777-888",
            "recipient_reference": "AQINA-order_receipt_underpaid",
            "confidence": 0.91,
            "warnings": ["Detected amount is lower than expected."],
        }

        client = self._build_client()
        with patch("app.services.marketing_orchestrator.upload_public_file_to_firebase", return_value="https://storage.example.com/chat-receipt-underpaid.jpg"):
            response = client.post(
                "/api/v1/marketing/tasks/process-inbound-message",
                json={"event_id": "event-receipt-underpaid"},
                headers={"X-Internal-Token": "internal-secret"},
            )

        self.assertEqual(response.status_code, 200)
        order = self.db.collection("orders").document("order_receipt_underpaid").get().to_dict()
        verification = order["payment_verification"]
        self.assertEqual(order["payment_status"], "payment_submitted")
        self.assertEqual(verification["status"], "warning")
        self.assertEqual(verification["expected_amount"], 79.8)
        self.assertEqual(verification["extracted_amount"], 67.0)
        self.assertFalse(verification["amount_match"])
        self.assertIn("Amount does not match expected total", verification["warnings"])
        payments = self.db.collection("payments").stream()
        self.assertEqual(payments[0].to_dict()["status"], "payment_submitted")

    def test_whatsapp_receipt_duplicate_reference_flags_order_payment_and_escalation(self) -> None:
        self._seed_active_receipt_checkout(
            contact_id="contact-receipt-duplicate",
            conversation_id="conv-receipt-duplicate",
            session_id="session-receipt-duplicate",
            event_id="event-receipt-duplicate",
            order_id="order_receipt_duplicate",
            total_amount=75.0,
        )
        self.db.seed(
            "payments/payment_existing_duplicate",
            {
                "order_id": "order_existing_duplicate",
                "method": "paynow",
                "payment_method": "paynow",
                "amount": 75.0,
                "status": "payment_submitted",
                "transaction_id": "ABC123456",
                "payment_verification": {
                    "reference_normalized": "ABC123456",
                    "duplicate_detected": False,
                },
                "created_at": "2026-04-09T00:00:00Z",
                "updated_at": "2026-04-09T00:00:00Z",
            },
        )
        self.gemini_service.receipt_analysis = {
            "paid_amount": 75.0,
            "currency": "SGD",
            "bank_transaction_reference": "ABC 123-456",
            "confidence": 0.93,
            "warnings": [],
        }

        client = self._build_client()
        with patch("app.services.marketing_orchestrator.upload_public_file_to_firebase", return_value="https://storage.example.com/chat-receipt-duplicate.jpg"):
            response = client.post(
                "/api/v1/marketing/tasks/process-inbound-message",
                json={"event_id": "event-receipt-duplicate"},
                headers={"X-Internal-Token": "internal-secret"},
            )

        self.assertEqual(response.status_code, 200)
        order = self.db.collection("orders").document("order_receipt_duplicate").get().to_dict()
        verification = order["payment_verification"]
        self.assertEqual(order["payment_status"], "payment_submitted")
        self.assertEqual(order["transaction_id"], "ABC 123-456")
        self.assertEqual(verification["status"], "warning")
        self.assertTrue(verification["duplicate_detected"])
        self.assertEqual(verification["duplicate_order_ids"], ["order_existing_duplicate"])
        self.assertEqual(verification["duplicate_payment_ids"], ["payment_existing_duplicate"])
        self.assertIn("duplicate_payment_reference", order["risk_flags"])
        new_payment = [
            snapshot.to_dict()
            for snapshot in self.db.collection("payments").stream()
            if snapshot.to_dict().get("order_id") == "order_receipt_duplicate"
        ][0]
        self.assertTrue(new_payment["payment_verification"]["duplicate_detected"])
        self.assertIn("duplicate_payment_reference", new_payment["risk_flags"])
        escalations = self.db.collection("marketing_escalations").stream()
        self.assertEqual(len(escalations), 1)
        self.assertEqual(escalations[0].to_dict()["reason"], "duplicate_payment_reference")

    def test_whatsapp_receipt_ai_verification_unavailable_when_model_fails(self) -> None:
        self._seed_active_receipt_checkout(
            contact_id="contact-receipt-unavailable",
            conversation_id="conv-receipt-unavailable",
            session_id="session-receipt-unavailable",
            event_id="event-receipt-unavailable",
            order_id="order_receipt_unavailable",
            total_amount=75.0,
        )
        self.gemini_service.receipt_analysis_error = RuntimeError("model unavailable")

        client = self._build_client()
        with patch("app.services.marketing_orchestrator.upload_public_file_to_firebase", return_value="https://storage.example.com/chat-receipt-unavailable.jpg"):
            response = client.post(
                "/api/v1/marketing/tasks/process-inbound-message",
                json={"event_id": "event-receipt-unavailable"},
                headers={"X-Internal-Token": "internal-secret"},
            )

        self.assertEqual(response.status_code, 200)
        order = self.db.collection("orders").document("order_receipt_unavailable").get().to_dict()
        verification = order["payment_verification"]
        self.assertEqual(order["payment_status"], "payment_submitted")
        self.assertEqual(order["payment_receipt_url"], "https://storage.example.com/chat-receipt-unavailable.jpg")
        self.assertEqual(verification["status"], "unavailable")
        self.assertEqual(verification["expected_amount"], 75.0)
        self.assertIsNone(verification["extracted_amount"])
        self.assertIn("AI receipt analysis unavailable", verification["warnings"])
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertIn("收到您的 PayNow 付款截图", message_calls[0][1]["text"])

    def test_landing_order_with_receipt_does_not_analyze_receipt_image(self) -> None:
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
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
            )

        self.assertEqual(response.status_code, 201)
        self.assertFalse([call for call in self.gemini_service.calls if call[0] == "analyze_payment_receipt_image"])

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

    def test_gemini_follow_up_fallback_does_not_return_stage_instruction(self) -> None:
        from app.services.gemini_service import GeminiConversationService, SAFE_FOLLOW_UP_FALLBACK_TEXT

        service = GeminiConversationService()
        stage_instruction = "提醒 Aqina 纯鸡精 1盒/2盒选择，询问顾客要先 1盒试喝还是 2盒更划算；不要发送长篇感官描述。"

        with patch.object(service, "_generate_json", return_value=None):
            result = service.generate_follow_up_reply(
                contact={"current_tag": "lead_cold"},
                messages=[],
                stage="t3h",
                instruction=stage_instruction,
                runtime_settings={"system_prompt": "Aqina health advisor prompt"},
        )

        self.assertEqual(result.reply_text, SAFE_FOLLOW_UP_FALLBACK_TEXT)
        self.assertIn("按您的情况", result.reply_text)
        self.assertNotIn("SGD75", result.reply_text)
        self.assertNotIn("SGD 75", result.reply_text)
        self.assertNotIn("不要发送长篇感官描述", result.reply_text)
        self.assertNotIn("询问顾客", result.reply_text)

    def test_gemini_follow_up_prompt_uses_english_engine_instructions(self) -> None:
        from app.services.gemini_service import GeminiConversationService

        prompt = GeminiConversationService._build_follow_up_prompt(
            contact={"current_tag": "qualified_warm", "selected_package_code": "pack2"},
            messages=[{"role": "user", "text": "晚点再看"}],
            stage="t3h",
            instruction="Low-pressure reminder; do not repeat prices.",
            checkout_url=None,
        )

        self.assertIn("Stage instruction is internal service strategy", prompt)
        self.assertIn("Rewrite it into natural, short customer-facing reply_text", prompt)
        self.assertIn("Do not copy Stage instruction verbatim", prompt)
        self.assertIn("Output JSON with exactly these fields", prompt)

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
            "reply_text='想象一下，早晨起来撕开一包 Aqina 纯鸡精，倒出来是清澈透亮的金黄色。它完全没有传统鸡精的腥苦味，喝起来像一碗精华鸡汤。' next_tag='lead_cold' checkout_link_required=False escalate=False escalation_reason=None opt_in_request=False",
            checkout_url=None,
        )

        self.assertEqual(next_tag, "lead_cold")
        self.assertEqual(
            reply_text,
            "想象一下，早晨起来撕开一包 Aqina 纯鸡精，倒出来是清澈透亮的金黄色。它完全没有传统鸡精的腥苦味，喝起来像一碗精华鸡汤。",
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

    def test_follow_up_result_replaces_internal_instruction_with_safe_fallback(self) -> None:
        from app.services.follow_up import FollowUpEngine
        from app.services.gemini_service import SAFE_FOLLOW_UP_FALLBACK_TEXT

        reply_text, next_tag = FollowUpEngine._normalize_follow_up_result(
            "提醒 Aqina 纯鸡精 1盒/2盒选择，询问顾客要先 1盒试喝还是 2盒更划算；不要发送长篇感官描述。",
            checkout_url=None,
        )

        self.assertIsNone(next_tag)
        self.assertEqual(reply_text, SAFE_FOLLOW_UP_FALLBACK_TEXT)
        self.assertIn("按您的情况", reply_text)
        self.assertNotIn("SGD75", reply_text)
        self.assertNotIn("不要发送长篇感官描述", reply_text)
        self.assertNotIn("询问顾客", reply_text)

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

    def test_cart_hot_follow_up_uses_checkout_fallback_not_generic_consultation(self) -> None:
        class NullFollowUpGemini(FakeGeminiService):
            def generate_follow_up_reply(self, **kwargs):
                self.calls.append(("generate_follow_up_reply", kwargs))
                return None

        self.gemini_service = NullFollowUpGemini()
        self._seed_runtime_settings()
        self.db.seed(
            "marketing_contacts/contact-cart-hot-followup",
            {
                "channel": "whatsapp",
                "identifiers": {"wa_id": "6595552222"},
                "current_tag": "cart_hot",
                "follow_up_stage": "none",
                "last_interaction_time": "2026-04-10T00:00:00Z",
                "window_expires_at": "2099-01-01T00:00:00Z",
                "latest_conversation_id": "conv-cart-hot-followup",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-cart-hot-followup",
            {
                "contact_id": "contact-cart-hot-followup",
                "channel": "whatsapp",
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-cart-hot-followup/messages/msg-1",
            {
                "direction": "inbound",
                "role": "user",
                "text": "二盒，PayNow 怎么付？",
                "source": "whatsapp_webhook",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-cart-hot-followup",
            {
                "contact_id": "contact-cart-hot-followup",
                "conversation_id": "conv-cart-hot-followup",
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
            json={"job_id": "job-cart-hot-followup"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        self.assertEqual(len(message_calls), 1)
        reply = message_calls[0][1]["text"]
        self.assertIn("收件人姓名", reply)
        self.assertIn("付款截图", reply)
        self.assertNotIn("自己喝、送长辈", reply)

    def test_t3h_follow_up_job_uses_safe_fallback_when_gemini_returns_none(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings
        from app.services.gemini_service import SAFE_FOLLOW_UP_FALLBACK_TEXT

        class NullFollowUpGemini(FakeGeminiService):
            def generate_follow_up_reply(self, **kwargs):
                self.calls.append(("generate_follow_up_reply", kwargs))
                return None

        self.gemini_service = NullFollowUpGemini()
        self.db.seed("chatbotSettings/default", get_default_chatbot_settings())
        self.db.seed(
            "marketing_contacts/contact-followup-t3h",
            {
                "channel": "messenger",
                "identifiers": {"psid": "psid-followup-t3h"},
                "current_tag": "lead_cold",
                "follow_up_stage": "none",
                "last_interaction_time": "2026-04-10T00:00:00Z",
                "window_expires_at": "2099-01-01T00:00:00Z",
                "latest_conversation_id": "conv-followup-t3h",
                "status": "active",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-followup-t3h",
            {
                "contact_id": "contact-followup-t3h",
                "channel": "messenger",
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_conversations/conv-followup-t3h/messages/msg-1",
            {
                "direction": "inbound",
                "role": "user",
                "text": "请问多少钱？",
                "source": "messenger_webhook",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-followup-t3h",
            {
                "contact_id": "contact-followup-t3h",
                "conversation_id": "conv-followup-t3h",
                "stage": "t3h",
                "anchor_interaction_time": "2026-04-10T00:00:00Z",
                "due_at": "2026-04-10T03:00:00Z",
                "eligible_tags": ["lead_cold", "qualified_warm", "cart_hot"],
                "status": "scheduled",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-follow-up-job",
            json={"job_id": "job-followup-t3h"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_messenger_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertEqual(message_calls[0][1]["text"], SAFE_FOLLOW_UP_FALLBACK_TEXT)
        self.assertIn("按您的情况", message_calls[0][1]["text"])
        self.assertNotIn("SGD75", message_calls[0][1]["text"])
        self.assertNotIn("SGD 75", message_calls[0][1]["text"])
        self.assertNotIn("不要发送长篇感官描述", message_calls[0][1]["text"])
        self.assertNotIn("询问顾客", message_calls[0][1]["text"])

    def test_t3h_follow_up_sends_customer_social_proof_image_for_warm_lead(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings

        self.gemini_service = FakeGeminiService(
            follow_up_result={
                "reply_text": "我也发一张真实顾客使用照给您参考，您可以慢慢看。",
                "next_tag": "qualified_warm",
                "checkout_link_required": False,
                "escalate": False,
                "escalation_reason": None,
                "opt_in_request": False,
            }
        )
        self.db.seed("chatbotSettings/default", get_default_chatbot_settings())
        self._seed_contact_and_event(
            contact_id="contact-followup-ugc",
            conversation_id="conv-followup-ugc",
            event_id="event-followup-ugc",
            channel="whatsapp",
            incoming_text="我想买给妈妈，但是还在考虑",
            identifier_key="wa_id",
            identifier_value="6595553333",
        )
        self.db.collection("marketing_contacts").document("contact-followup-ugc").set(
            {"current_tag": "qualified_warm", "chatbot_locale": "zh"},
            merge=True,
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-followup-ugc",
            {
                "contact_id": "contact-followup-ugc",
                "conversation_id": "conv-followup-ugc",
                "stage": "t3h",
                "anchor_interaction_time": "2026-04-10T00:00:00Z",
                "due_at": "2026-04-10T03:00:00Z",
                "eligible_tags": ["lead_cold", "qualified_warm", "cart_hot"],
                "status": "scheduled",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-follow-up-job",
            json={"job_id": "job-followup-ugc"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        text_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_text"]
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(text_calls), 1)
        self.assertEqual(len(image_calls), 1)
        self.assertIn("真实顾客使用照", image_calls[0][1]["caption"])
        self.assertIn("real customer usage photo", self.gemini_service.calls[0][1]["instruction"])

        media_docs = [snapshot.to_dict() for snapshot in self.db.collection("meta_media_assets").stream()]
        self.assertEqual(len(media_docs), 1)
        self.assertTrue(media_docs[0]["source_url"].startswith("https://aqina.example.com/chatbot/ugc/customer-"))

        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-followup-ugc")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound"
        ]
        self.assertEqual(
            [item["source"] for item in outbound_messages],
            ["follow_up_engine", "follow_up_social_proof_media"],
        )
        contact = self.db.collection("marketing_contacts").document("contact-followup-ugc").get().to_dict()
        self.assertTrue(contact["sent_media"]["follow_up_social_proof"]["sent"])
        self.assertTrue(contact["sent_media"]["follow_up_social_proof"]["image_url"].startswith("/chatbot/ugc/customer-"))

    def test_t3h_follow_up_does_not_resend_customer_social_proof_image(self) -> None:
        from app.services.chatbot_settings import get_default_chatbot_settings

        self.gemini_service = FakeGeminiService(
            follow_up_result={
                "reply_text": "如果还不确定，我可以按妈妈的情况帮您判断。",
                "next_tag": "lead_cold",
                "checkout_link_required": False,
                "escalate": False,
                "escalation_reason": None,
                "opt_in_request": False,
            }
        )
        self.db.seed("chatbotSettings/default", get_default_chatbot_settings())
        self._seed_contact_and_event(
            contact_id="contact-followup-ugc-seen",
            conversation_id="conv-followup-ugc-seen",
            event_id="event-followup-ugc-seen",
            channel="whatsapp",
            incoming_text="我晚点再看",
            identifier_key="wa_id",
            identifier_value="6595554444",
        )
        self.db.collection("marketing_contacts").document("contact-followup-ugc-seen").set(
            {
                "current_tag": "lead_cold",
                "chatbot_locale": "zh",
                "sent_media": {"follow_up_social_proof": {"sent": True}},
            },
            merge=True,
        )
        self.db.seed(
            "marketing_follow_up_jobs/job-followup-ugc-seen",
            {
                "contact_id": "contact-followup-ugc-seen",
                "conversation_id": "conv-followup-ugc-seen",
                "stage": "t3h",
                "anchor_interaction_time": "2026-04-10T00:00:00Z",
                "due_at": "2026-04-10T03:00:00Z",
                "eligible_tags": ["lead_cold", "qualified_warm", "cart_hot"],
                "status": "scheduled",
                "created_at": "2026-04-10T00:00:00Z",
                "updated_at": "2026-04-10T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/tasks/process-follow-up-job",
            json={"job_id": "job-followup-ugc-seen"},
            headers={"X-Internal-Token": "internal-secret"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        upload_calls = [call for call in self.meta_client.calls if call[0] == "upload_whatsapp_media"]
        self.assertEqual(len(image_calls), 0)
        self.assertEqual(len(upload_calls), 0)

    def test_follow_up_job_sends_only_reply_text_from_string_repr(self) -> None:
        self.gemini_service = FakeGeminiService(
            follow_up_result="reply_text='想象一下，早晨起来撕开一包 Aqina 纯鸡精，喝起来像一碗精华鸡汤。' next_tag='lead_cold' checkout_link_required=False escalate=False escalation_reason=None opt_in_request=False"
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
            "想象一下，早晨起来撕开一包 Aqina 纯鸡精，喝起来像一碗精华鸡汤。",
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
            incoming_text="之前想了解纯鸡精",
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

    def test_unified_conversations_api_lists_and_filters_marketing_inbox(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-unified-msgr",
            conversation_id="conv-unified-msgr",
            event_id="event-unified-msgr",
            channel="messenger",
            incoming_text="请问多少钱？",
            identifier_key="psid",
            identifier_value="psid-unified-1",
        )
        self.db.collection("marketing_contacts").document("contact-unified-msgr").set(
            {
                "acquisition": {
                    "source": "ADS",
                    "ref": "may-offer",
                    "ad_id": "ad-123",
                    "post_id": None,
                    "raw_referral": {"source": "ADS", "ad_id": "ad-123"},
                }
            },
            merge=True,
        )
        self._seed_contact_and_event(
            contact_id="contact-unified-wa",
            conversation_id="conv-unified-wa",
            event_id="event-unified-wa",
            channel="whatsapp",
            incoming_text="想订两盒",
            identifier_key="wa_id",
            identifier_value="6591880000",
        )

        client = self._build_client()
        all_response = client.get(
            "/api/v1/marketing/conversations",
            headers={"Authorization": "Bearer admin-token"},
        )
        messenger_response = client.get(
            "/api/v1/marketing/conversations",
            params={"channel": "messenger"},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(all_response.status_code, 200)
        self.assertEqual(len(all_response.json()["items"]), 2)
        self.assertEqual(messenger_response.status_code, 200)
        items = messenger_response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["channel"], "messenger")
        self.assertEqual(items[0]["platform_id"], "psid-unified-1")
        self.assertEqual(items[0]["acquisition"]["ad_id"], "ad-123")
        self.assertEqual(items[0]["latest_message"]["text"], "请问多少钱？")

    def test_unified_conversations_api_supports_more_than_50_and_full_ids(self) -> None:
        for index in range(55):
            channel = "whatsapp" if index % 2 else "messenger"
            identifier_key = "wa_id" if channel == "whatsapp" else "psid"
            identifier_value = f"65910000{index:02d}" if channel == "whatsapp" else f"psid-full-visible-{index:02d}"
            self._seed_contact_and_event(
                contact_id=f"contact-limit-{index:02d}",
                conversation_id=f"conv-limit-{index:02d}",
                event_id=f"event-limit-{index:02d}",
                channel=channel,
                incoming_text=f"message {index}",
                identifier_key=identifier_key,
                identifier_value=identifier_value,
            )

        client = self._build_client()
        response = client.get(
            "/api/v1/marketing/conversations",
            params={"limit": 55},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(len(items), 55)
        platform_ids = {item["platform_id"] for item in items}
        customer_names = {item["customer_name"] for item in items}
        self.assertIn("psid-full-visible-00", platform_ids)
        self.assertIn("6591000001", platform_ids)
        self.assertIn("psid-full-visible-00", customer_names)
        self.assertNotIn("psid...e-00", customer_names)

    def test_unified_conversation_detail_returns_messages_contact_and_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-detail-msgr",
            conversation_id="conv-detail-msgr",
            event_id="event-detail-msgr",
            channel="messenger",
            incoming_text="我要买给妈妈",
            identifier_key="psid",
            identifier_value="psid-detail-1",
        )

        client = self._build_client()
        response = client.get(
            "/api/v1/marketing/conversations/conv-detail-msgr",
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["conversation"]["channel"], "messenger")
        self.assertEqual(payload["conversation"]["platform_id"], "psid-detail-1")
        self.assertTrue(payload["window"]["is_open"])
        self.assertEqual(payload["messages"][0]["text"], "我要买给妈妈")
        self.assertEqual(payload["contact"]["contact_id"], "contact-detail-msgr")
        self.assertEqual(payload["conversation"]["customer_name"], "Messenger User")

    def test_unified_conversation_detail_flags_cart_hot_handoff_without_order(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-detail-hot",
            conversation_id="conv-detail-hot",
            event_id="event-detail-hot",
            channel="messenger",
            incoming_text="二盒，PayNow 怎么付？可以送货吗？",
            identifier_key="psid",
            identifier_value="273700003322",
        )
        self.db.collection("marketing_contacts").document("contact-detail-hot").set(
            {
                "current_tag": "cart_hot",
                "handoff_recommended": True,
                "handoff_reason": "high_intent_checkout",
            },
            merge=True,
        )

        client = self._build_client()
        response = client.get(
            "/api/v1/marketing/conversations/conv-detail-hot",
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        summary = response.json()["conversation"]
        self.assertEqual(summary["current_tag"], "cart_hot")
        self.assertTrue(summary["handoff_recommended"])
        self.assertEqual(summary["handoff_reason"], "high_intent_checkout")
        self.assertEqual(summary["matched_order_count"], 0)
        self.assertIsNone(summary["latest_order_status"])
        self.assertIsNone(summary["latest_payment_status"])
        self.assertIn("price_or_package", summary["latest_blockers"])
        self.assertIn("payment", summary["latest_blockers"])
        self.assertIn("delivery", summary["latest_blockers"])

    def test_unified_conversations_api_sends_messenger_manual_reply_inside_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-manual-msgr",
            conversation_id="conv-manual-msgr",
            event_id="event-manual-msgr",
            channel="messenger",
            incoming_text="可以今天送吗？",
            identifier_key="psid",
            identifier_value="psid-manual-1",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/conversations/conv-manual-msgr/messages",
            json={"text": "可以的，我先帮您确认今天发货批次。"},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "sent")
        message_calls = [call for call in self.meta_client.calls if call[0] == "send_messenger_text"]
        self.assertEqual(len(message_calls), 1)
        self.assertEqual(message_calls[0][1]["recipient_psid"], "psid-manual-1")
        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-manual-msgr")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound"
        ]
        self.assertEqual(outbound_messages[0]["role"], "admin")
        self.assertEqual(outbound_messages[0]["source"], "admin_messenger_console")

    def test_unified_conversations_api_sends_whatsapp_manual_image_inside_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-manual-image-wa",
            conversation_id="conv-manual-image-wa",
            event_id="event-manual-image-wa",
            channel="whatsapp",
            incoming_text="可以发图片给我看吗？",
            identifier_key="wa_id",
            identifier_value="6591000100",
        )

        client = self._build_client()
        with patch(
            "app.api.v1.marketing.upload_public_file_to_firebase",
            return_value="https://storage.example.com/manual.png",
            create=True,
        ):
            response = client.post(
                "/api/v1/marketing/conversations/conv-manual-image-wa/images",
                data={"caption": "这是 2 盒配套图片"},
                files={"image": ("manual.png", b"fake-image", "image/png")},
                headers={"Authorization": "Bearer admin-token"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "sent")
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"]
        self.assertEqual(len(image_calls), 1)
        self.assertEqual(image_calls[0][1]["to"], "6591000100")
        self.assertEqual(image_calls[0][1]["caption"], "这是 2 盒配套图片")
        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-manual-image-wa")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound"
        ]
        self.assertEqual(outbound_messages[0]["message_type"], "image")
        self.assertEqual(outbound_messages[0]["media_url"], "https://storage.example.com/manual.png")
        self.assertEqual(outbound_messages[0]["media_content_type"], "image/png")

    def test_unified_conversations_api_sends_messenger_manual_image_inside_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-manual-image-msgr",
            conversation_id="conv-manual-image-msgr",
            event_id="event-manual-image-msgr",
            channel="messenger",
            incoming_text="send photo",
            identifier_key="psid",
            identifier_value="psid-manual-image",
        )

        client = self._build_client()
        with patch(
            "app.api.v1.marketing.upload_public_file_to_firebase",
            return_value="https://storage.example.com/manual-msgr.webp",
            create=True,
        ):
            response = client.post(
                "/api/v1/marketing/conversations/conv-manual-image-msgr/images",
                data={"caption": "Product photo"},
                files={"image": ("manual.webp", b"fake-image", "image/webp")},
                headers={"Authorization": "Bearer admin-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "sent")
        image_calls = [call for call in self.meta_client.calls if call[0] == "send_messenger_image_attachment"]
        self.assertEqual(len(image_calls), 1)
        self.assertEqual(image_calls[0][1]["recipient_psid"], "psid-manual-image")
        outbound_messages = [
            snapshot.to_dict()
            for snapshot in self.db.collection("marketing_conversations")
            .document("conv-manual-image-msgr")
            .collection("messages")
            .stream()
            if snapshot.to_dict().get("direction") == "outbound"
        ]
        self.assertEqual(outbound_messages[0]["message_type"], "image")
        self.assertEqual(outbound_messages[0]["text"], "Product photo")
        self.assertEqual(outbound_messages[0]["media_filename"], "manual.webp")

    def test_unified_conversations_api_blocks_manual_image_after_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-manual-image-closed",
            conversation_id="conv-manual-image-closed",
            event_id="event-manual-image-closed",
            channel="whatsapp",
            incoming_text="之前问过图片",
            identifier_key="wa_id",
            identifier_value="6591000101",
        )
        self.db.collection("marketing_contacts").document("contact-manual-image-closed").set(
            {"window_expires_at": "2026-04-01T00:00:00Z"},
            merge=True,
        )

        client = self._build_client()
        with patch(
            "app.api.v1.marketing.upload_public_file_to_firebase",
            return_value="https://storage.example.com/manual.png",
            create=True,
        ):
            response = client.post(
                "/api/v1/marketing/conversations/conv-manual-image-closed/images",
                files={"image": ("manual.png", b"fake-image", "image/png")},
                headers={"Authorization": "Bearer admin-token"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Customer service window", response.json()["detail"])
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"])

    def test_unified_conversations_api_rejects_invalid_manual_image_uploads(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-manual-image-invalid",
            conversation_id="conv-manual-image-invalid",
            event_id="event-manual-image-invalid",
            channel="whatsapp",
            incoming_text="图片",
            identifier_key="wa_id",
            identifier_value="6591000102",
        )

        client = self._build_client()
        invalid_type_response = client.post(
            "/api/v1/marketing/conversations/conv-manual-image-invalid/images",
            files={"image": ("manual.txt", b"not-image", "text/plain")},
            headers={"Authorization": "Bearer admin-token"},
        )
        oversized_response = client.post(
            "/api/v1/marketing/conversations/conv-manual-image-invalid/images",
            files={"image": ("manual.png", b"x" * (8 * 1024 * 1024 + 1), "image/png")},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(invalid_type_response.status_code, 400)
        self.assertIn("JPG, PNG, or WebP", invalid_type_response.json()["detail"])
        self.assertEqual(oversized_response.status_code, 413)
        self.assertIn("too large", oversized_response.json()["detail"])
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_whatsapp_image"])

    def test_unified_conversations_api_blocks_messenger_manual_reply_after_window(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-manual-closed",
            conversation_id="conv-manual-closed",
            event_id="event-manual-closed",
            channel="messenger",
            incoming_text="之前问过配套",
            identifier_key="psid",
            identifier_value="psid-manual-closed",
        )
        self.db.collection("marketing_contacts").document("contact-manual-closed").set(
            {"window_expires_at": "2026-04-01T00:00:00Z"},
            merge=True,
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/conversations/conv-manual-closed/messages",
            json={"text": "现在还有优惠。"},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Customer service window", response.json()["detail"])
        self.assertFalse([call for call in self.meta_client.calls if call[0] == "send_messenger_text"])

    def test_marketing_contact_tag_update_is_restricted_to_known_tags(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-tag-update",
            conversation_id="conv-tag-update",
            event_id="event-tag-update",
            channel="messenger",
            incoming_text="我想考虑一下",
            identifier_key="psid",
            identifier_value="psid-tag-1",
        )

        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/contacts/contact-tag-update/tag",
            json={"current_tag": "cart_hot"},
            headers={"Authorization": "Bearer admin-token"},
        )
        invalid_response = client.post(
            "/api/v1/marketing/contacts/contact-tag-update/tag",
            json={"current_tag": "not_a_tag"},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        contact = self.db.collection("marketing_contacts").document("contact-tag-update").get().to_dict()
        self.assertEqual(contact["current_tag"], "cart_hot")
        tag_events = self.db.collection("marketing_contacts").document("contact-tag-update").collection("tag_events").stream()
        self.assertEqual(tag_events[0].to_dict()["source"], "admin_unified_inbox")
        self.assertEqual(invalid_response.status_code, 422)

    def test_escalation_queue_supports_remark_and_archive_without_hard_delete(self) -> None:
        self.db.seed(
            "marketing_escalations/escalation-open",
            {
                "contact_id": "contact-escalation-open",
                "conversation_id": "conv-escalation-open",
                "reason": "refund_request",
                "latest_customer_message": "I need help",
                "status": "open",
                "private_whatsapp_number": "+6591212369",
                "template_name": "aqina_escalation_alert",
                "template_variables": ["refund_request"],
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            "marketing_escalations/escalation-archived",
            {
                "contact_id": "contact-escalation-archived",
                "reason": "old_case",
                "status": "archived",
                "created_at": "2026-04-09T00:00:00Z",
            },
        )

        client = self._build_client()
        list_response = client.get(
            "/api/v1/marketing/escalations",
            headers={"Authorization": "Bearer admin-token"},
        )
        remark_response = client.post(
            "/api/v1/marketing/escalations/escalation-open/remark",
            json={"remark": "Customer asked for refund evidence."},
            headers={"Authorization": "Bearer admin-token"},
        )
        archive_response = client.post(
            "/api/v1/marketing/escalations/escalation-open/archive",
            json={"remark": "Handled by staff, remove from active queue."},
            headers={"Authorization": "Bearer admin-token"},
        )
        after_archive_response = client.get(
            "/api/v1/marketing/escalations",
            headers={"Authorization": "Bearer admin-token"},
        )
        include_archived_response = client.get(
            "/api/v1/marketing/escalations",
            params={"include_archived": True},
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual([item["escalation_id"] for item in list_response.json()["items"]], ["escalation-open"])
        self.assertEqual(remark_response.status_code, 200)
        self.assertEqual(archive_response.status_code, 200)
        archived_doc = self.db.collection("marketing_escalations").document("escalation-open").get()
        self.assertTrue(archived_doc.exists)
        archived = archived_doc.to_dict()
        self.assertEqual(archived["status"], "archived")
        self.assertEqual(archived["remark"], "Handled by staff, remove from active queue.")
        self.assertEqual(archived["archived_by"], "admin@aqina.com")
        self.assertEqual(after_archive_response.json()["items"], [])
        self.assertEqual(len(include_archived_response.json()["items"]), 2)

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

    def test_order_contact_context_keeps_landing_page_on_manual_draft(self) -> None:
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
        self.assertEqual(payload["source_label"], "Landing Checkout")
        self.assertEqual(payload["source_channel"], "whatsapp")
        self.assertEqual(payload["normalized_whatsapp"], "6591112222")
        self.assertIsNone(payload["conversation_id"])
        self.assertIsNone(payload["backend_send_method"])
        self.assertEqual(payload["whatsapp_draft_url"], "https://wa.me/6591112222")
        self.assertIsNone(payload["conversation_url"])

    def test_order_contact_context_keeps_messenger_chatbot_on_manual_draft(self) -> None:
        self._seed_contact_and_event(
            contact_id="contact-order-messenger",
            conversation_id="conv-order-messenger",
            event_id="event-order-messenger",
            channel="messenger",
            incoming_text="I want to buy",
            identifier_key="psid",
            identifier_value="psid-123",
        )
        self.db.seed(
            "orders/order_messenger_context",
            {
                "customer": {
                    "name": "Megan Ong",
                    "email": None,
                    "whatsapp": "80099008",
                    "address": "317 Bukit Batok, Singapore 660066",
                },
                "items": [],
                "total_amount": 75.0,
                "payment_method": "paynow",
                "payment_status": "payment_submitted",
                "order_status": "pending",
                "source": "marketing_chatbot",
                "marketing_contact_id": "contact-order-messenger",
                "created_at": "2026-05-05T00:00:00Z",
            },
        )

        client = self._build_client()
        response = client.get(
            "/api/v1/orders/order_messenger_context/contact-context",
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source_label"], "Messenger Chatbot")
        self.assertEqual(payload["source_channel"], "messenger")
        self.assertEqual(payload["normalized_whatsapp"], "6580099008")
        self.assertIsNone(payload["conversation_id"])
        self.assertIsNone(payload["backend_send_method"])
        self.assertEqual(payload["whatsapp_draft_url"], "https://wa.me/6580099008")
        self.assertIsNone(payload["conversation_url"])

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
        context_response = client.get(
            "/api/v1/orders/order_send/contact-context",
            headers={"Authorization": "Bearer admin-token"},
        )
        self.assertEqual(context_response.status_code, 200)
        context_payload = context_response.json()
        self.assertEqual(context_payload["source_label"], "WhatsApp Chatbot")
        self.assertEqual(context_payload["source_channel"], "whatsapp")
        self.assertEqual(context_payload["conversation_id"], "conv-order-send")
        self.assertEqual(context_payload["conversation_url"], "/admin/inbox?conversation=conv-order-send")
        self.assertEqual(context_payload["backend_send_method"], "free_text")

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

    def test_submit_whatsapp_template_posts_to_meta_and_mirrors_pending_status(self) -> None:
        client = self._build_client()
        response = client.post(
            "/api/v1/marketing/whatsapp/templates/submit",
            json={
                "name": "aqina_pack2_french_poulet_offer_en",
                "language_code": "en_US",
                "category": "MARKETING",
                "components": [
                    {
                        "type": "BODY",
                        "text": (
                            "AQINA Pure Chicken Essence offer: 2 boxes for SGD79.80 "
                            "with 1 French Poulet Cut Part gift choice."
                        ),
                    },
                    {"type": "FOOTER", "text": "Reply STOP to opt out"},
                ],
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "PENDING")
        self.assertEqual(payload["source"], "meta_submission")
        self.assertEqual(payload["meta_template_id"], "template-created-id")
        template_call = [call for call in self.meta_client.calls if call[0] == "create_whatsapp_template"][0]
        self.assertEqual(template_call[1]["payload"]["language"], "en_US")
        self.assertTrue(template_call[1]["payload"]["allow_category_change"])
        saved = self.db.collection("whatsapp_templates").document(payload["template_id"]).get().to_dict()
        self.assertEqual(saved["status"], "PENDING")
        self.assertEqual(saved["name"], "aqina_pack2_french_poulet_offer_en")

    def test_whatsapp_campaign_preview_filters_by_customer_locale(self) -> None:
        self._seed_campaign_contact(
            contact_id="contact-zh",
            wa_id="6592100001",
            name="Chen",
            marketing_opt_in=True,
            chatbot_locale="zh",
        )
        self._seed_campaign_contact(
            contact_id="contact-en",
            wa_id="6592100002",
            name="Emily",
            marketing_opt_in=True,
            chatbot_locale="en",
        )
        self._seed_campaign_contact(
            contact_id="contact-unknown",
            wa_id="6592100003",
            name="May",
            marketing_opt_in=True,
        )
        self.db.seed(
            "whatsapp_templates/campaign-template-locale",
            {
                "name": "aqina_pack2_french_poulet_offer_en",
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
                "name": "Pack 2 EN",
                "template_name": "aqina_pack2_french_poulet_offer_en",
                "language_code": "en_US",
                "customer_locale": "en",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["eligible_count"], 1)
        self.assertEqual(payload["recipients"][0]["contact_id"], "contact-en")
        self.assertEqual(payload["recipients"][0]["customer_locale"], "en")

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
                "conversion_optimization_version": 11,
                "handoff_message": "",
                "packages": {
                    "pack1": {
                        "code": "pack1",
                        "name_zh": "7天启动装",
                        "name_en": "7-Day Starter Pack",
                        "description_zh": "1盒/7包，适合第一次先确认口感。",
                        "description_en": "1 box / 7 sachets for first taste confirmation.",
                        "price_sgd": 47.9,
                        "pack_count": 7,
                        "box_count": 1,
                        "target_audience": ["self_care"],
                        "hero": False,
                        "free_shipping_eligible": True,
                    },
                    "pack2": {
                        "code": "pack2",
                        "name_zh": "14天常备装",
                        "name_en": "14-Day Care Pack",
                        "description_zh": "2盒/14包，等于 SGD39.90/盒，并送 French Poulet Cut Part 五选一。",
                        "description_en": "2 boxes / 14 sachets at SGD39.90 per box, with one French Poulet Cut Part gift choice.",
                        "price_sgd": 79.8,
                        "pack_count": 14,
                        "box_count": 2,
                        "target_audience": ["self_care"],
                        "hero": True,
                        "free_shipping_eligible": True,
                    },
                },
                "knowledge_base": {
                    "usps": ["MD2 黄梨酵素鸡", "double-boiled 双重蒸煮", "100% Pure Chicken Essence"],
                    "faq": [
                        {"question": "多久送到", "answer": "1-3 个工作日"},
                    ],
                    "medical_disclaimer": "Aqina 是食品补养，不是药；特殊健康状况请先问医生。",
                    "logistics": "当前 1盒 SGD47.90 和 2盒 SGD79.80 已包含新加坡配送费，不需要另加邮费；库存、送达时间和具体配送安排会在下单时由客服确认。",
                    "consumption": "建议早晨空腹饮用",
                    "comparisons": "Aqina 纯鸡精不是 ordinary bottled chicken essence 的普通低价路线。",
                    "price_positioning": "1盒 SGD47.90；2盒 SGD79.80，等于 SGD39.90/盒，并送 French Poulet Cut Part 五选一。",
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

    def _seed_active_receipt_checkout(
        self,
        *,
        contact_id: str,
        conversation_id: str,
        session_id: str,
        event_id: str,
        order_id: str,
        total_amount: float,
    ) -> None:
        self._seed_runtime_settings()
        self.db.seed(
            f"marketing_contacts/{contact_id}",
            {
                "channel": "whatsapp",
                "identifiers": {"wa_id": "6591112222"},
                "current_tag": "cart_hot",
                "checkout_session_id": session_id,
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
                "channel": "whatsapp",
                "status": "open",
                "message_count": 1,
                "opened_at": "2026-04-10T00:00:00Z",
                "last_message_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            f"marketing_checkout_sessions/{session_id}",
            {
                "order_id": order_id,
                "token": f"token-{order_id}",
                "package_code": "pack2",
                "checkout_url": f"https://aqina.example.com/paynow/token-{order_id}",
                "status": "active",
                "contact_id": contact_id,
                "total_amount": total_amount,
            },
        )
        self.db.seed(
            f"orders/{order_id}",
            {
                "customer": {
                    "name": "Alice Tan",
                    "email": None,
                    "whatsapp": "6591112222",
                    "address": "1 Orchard Road, Singapore 238823",
                },
                "items": [],
                "subtotal_amount": total_amount,
                "shipping_fee": 0.0,
                "box_count": 2,
                "total_amount": total_amount,
                "payment_method": "paynow",
                "payment_status": "pending",
                "order_status": "pending",
                "source": "marketing_chatbot",
                "created_at": "2026-04-10T00:00:00Z",
            },
        )
        self.db.seed(
            f"marketing_events/{event_id}",
            {
                "provider": "meta",
                "channel": "whatsapp",
                "event_type": "whatsapp_message_received",
                "status": "queued",
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "payload": {
                    "channel": "whatsapp",
                    "text": "[image]",
                    "message_type": "image",
                    "media_id": f"{event_id}-media-id",
                    "provider_message_id": f"{event_id}-message-id",
                    "wa_id": "6591112222",
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
        chatbot_locale: str | None = None,
    ) -> None:
        contact_payload = {
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
        }
        if chatbot_locale:
            contact_payload["chatbot_locale"] = chatbot_locale
        self.db.seed(f"marketing_contacts/{contact_id}", contact_payload)
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
