"""Gemini API wrapper for structured sales and follow-up responses."""
from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import settings
from app.models.chatbot import FollowUpTurnResult, SalesConversationTurn
from app.services.chatbot_skill_router import ChatbotSkillRouter


VALID_LEAD_GOALS = {"self_care", "pregnancy", "postpartum", "gift_elder", "unknown"}
VALID_MARKETING_TAGS = {"lead_cold", "qualified_warm", "cart_hot", "handoff_pending"}
SAFE_FOLLOW_UP_FALLBACK_TEXT = "如果刚才的问题还不确定，我可以按您的情况帮您判断适不适合。请问是自己喝、送长辈，还是孕期/月子调理？"
SAFE_CHECKOUT_FOLLOW_UP_FALLBACK_TEXT = (
    "您好，我帮您保留刚才的配套。您可以直接把收件人姓名、联系电话和新加坡地址发来；"
    "如果已经 PayNow 付款，也可以把付款截图发回来，我会让客服帮您确认订单。"
)

PRICE_OR_ORDER_INTENT_KEYWORDS = {
    "多少钱",
    "价钱",
    "价格",
    "贵",
    "便宜",
    "price",
    "how much",
    "discount",
    "优惠",
    "配套",
    "套餐",
    "运费",
    "多久到",
    "shipping",
    "delivery",
    "我要",
    "下单",
    "购买",
    "订购",
    "买",
    "order",
    "buy",
    "拿一盒",
    "拿两盒",
}


class GeminiConversationService:
    """Generate structured chatbot output with Google Gemini."""

    def is_ready(self) -> bool:
        """Whether chat generation can safely execute."""
        return settings.gemini_ready

    def generate_chat_reply(
        self,
        *,
        contact: dict[str, Any],
        messages: list[dict[str, Any]],
        incoming_text: str,
        channel: str,
        runtime_settings: dict[str, Any] | None = None,
    ) -> SalesConversationTurn:
        prompt = self._build_chat_prompt(
            contact=contact,
            messages=messages,
            incoming_text=incoming_text,
            channel=channel,
            runtime_settings=runtime_settings or {},
        )
        payload = self._generate_json(
            prompt,
            system_prompt=(runtime_settings or {}).get("system_prompt") or settings.gemini_system_prompt,
        )
        if payload is None:
            return SalesConversationTurn(
                reply_text="明白，我先帮您了解一下需求。请问这次是自己日常保养、孕期调理，还是想送给长辈呢？🎈",
                next_tag="lead_cold",
            )
        return self._normalize_sales_turn_payload(payload)

    def generate_follow_up_reply(
        self,
        *,
        contact: dict[str, Any],
        messages: list[dict[str, Any]],
        stage: str,
        instruction: str,
        runtime_settings: dict[str, Any] | None = None,
        checkout_url: str | None = None,
    ) -> FollowUpTurnResult:
        prompt = self._build_follow_up_prompt(
            contact=contact,
            messages=messages,
            stage=stage,
            instruction=instruction,
            checkout_url=checkout_url,
        )
        payload = self._generate_json(
            prompt,
            system_prompt=(runtime_settings or {}).get("system_prompt") or settings.gemini_system_prompt,
        )
        if payload is None:
            return FollowUpTurnResult(
                reply_text=_safe_follow_up_fallback_text(
                    checkout_url=checkout_url,
                    cart_hot=str(contact.get("current_tag") or "").casefold() == "cart_hot",
                )
            )
        return FollowUpTurnResult.model_validate(payload)

    def _generate_json(self, prompt: str, *, system_prompt: str) -> dict[str, Any] | None:
        if not self.is_ready():
            raise RuntimeError("Gemini configuration is incomplete")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.45,
                response_mime_type="application/json",
            ),
        )
        raw_text = (response.text or "").strip()
        if not raw_text:
            return None

        json_text = self._extract_json(raw_text)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return None

    def transcribe_audio_bytes(self, *, data: bytes, mime_type: str) -> str:
        """Transcribe customer audio with Gemini and return only the transcript."""
        if not self.is_ready():
            raise RuntimeError("Gemini configuration is incomplete")

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                "Transcribe this customer audio in the original language. Return only the transcript text.",
                types.Part.from_bytes(data=data, mime_type=mime_type or "audio/ogg"),
            ],
        )
        return (response.text or "").strip()

    def analyze_payment_receipt_image(
        self,
        *,
        data: bytes,
        mime_type: str,
        expected_amount: float,
    ) -> dict[str, Any]:
        """Extract structured payment fields from a PayNow receipt image."""
        if not self.is_ready():
            raise RuntimeError("Gemini configuration is incomplete")

        from google import genai
        from google.genai import types

        prompt = (
            "Read this Singapore PayNow or bank transfer receipt image for manual payment verification.\n"
            f"Expected order total: SGD {float(expected_amount):.2f}\n"
            "Return only JSON with these exact keys: "
            "paid_amount, currency, bank_transaction_reference, recipient_reference, "
            "payment_datetime, confidence, warnings.\n"
            "Use bank_transaction_reference for the bank transaction id/reference number from the receipt, "
            "not the customer's free-text recipient reference. If a field is not visible, use null. "
            "confidence must be a number from 0 to 1. warnings must be an array of short strings."
        )
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                prompt,
                types.Part.from_bytes(data=data, mime_type=mime_type or "image/jpeg"),
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        raw_text = (response.text or "").strip()
        if not raw_text:
            return {}

        json_text = self._extract_json(raw_text)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _normalize_sales_turn_payload(payload: dict[str, Any]) -> SalesConversationTurn:
        normalized = dict(payload)
        normalized["reply_text"] = str(normalized.get("reply_text") or "").strip()
        if not normalized["reply_text"]:
            normalized["reply_text"] = "明白，我先帮您了解一下需求。请问这次是自己日常保养、孕期调理，还是想送给长辈呢？"

        normalized["next_tag"] = GeminiConversationService._normalize_marketing_tag(
            normalized.get("next_tag"),
            normalized,
        )
        normalized["lead_goal"] = GeminiConversationService._normalize_lead_goal(normalized.get("lead_goal"))
        if not isinstance(normalized.get("order_fields"), dict):
            normalized["order_fields"] = {}
        if not isinstance(normalized.get("missing_order_fields"), list):
            normalized["missing_order_fields"] = []
        for key in ["checkout_ready", "escalate", "opt_in_granted"]:
            normalized[key] = bool(normalized.get(key))

        try:
            return SalesConversationTurn.model_validate(normalized)
        except Exception:
            return SalesConversationTurn(reply_text=normalized["reply_text"], next_tag="lead_cold")

    @staticmethod
    def _normalize_marketing_tag(value: Any, payload: dict[str, Any]) -> str:
        tag = str(value or "").strip().lower()
        if tag in VALID_MARKETING_TAGS:
            return tag
        if bool(payload.get("escalate")) or "handoff" in tag or "human" in tag:
            return "handoff_pending"
        if bool(payload.get("checkout_ready")) or payload.get("selected_package_code") or "cart" in tag or "hot" in tag:
            return "cart_hot"
        if payload.get("recommended_package_code") or "warm" in tag or "qualified" in tag:
            return "qualified_warm"
        return "lead_cold"

    @staticmethod
    def _normalize_lead_goal(value: Any) -> str:
        goal = str(value or "").strip().lower()
        if goal in VALID_LEAD_GOALS:
            return goal
        if any(term in goal for term in ["pregnan", "maternity", "孕"]):
            return "pregnancy"
        if any(term in goal for term in ["postpartum", "confinement", "月子", "产后"]):
            return "postpartum"
        if any(term in goal for term in ["elder", "parent", "gift", "长辈", "父母", "送"]):
            return "gift_elder"
        if any(term in goal for term in ["self", "daily", "自己", "日常"]):
            return "self_care"
        return "unknown"

    @staticmethod
    def _extract_json(raw_text: str) -> str:
        fenced = re.search(r"```json\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        return raw_text

    @staticmethod
    def _build_chat_prompt(
        *,
        contact: dict[str, Any],
        messages: list[dict[str, Any]],
        incoming_text: str,
        channel: str,
        runtime_settings: dict[str, Any],
    ) -> str:
        history = "\n".join(
            f"{item.get('role', 'user')}: {item.get('text', '')}"
            for item in messages[-12:]
        )
        recently_quoted_price = GeminiConversationService._recent_assistant_message_mentions_price(messages)
        incoming_requests_price_or_order = GeminiConversationService._incoming_requests_price_or_order(incoming_text)
        available_packages = runtime_settings.get("packages", {})
        package_codes = sorted(str(code) for code in available_packages.keys())
        packages = json.dumps(available_packages, ensure_ascii=False)
        knowledge_base = json.dumps(runtime_settings.get("knowledge_base", {}), ensure_ascii=False)
        order_fields = contact.get("order_fields", {}) if isinstance(contact.get("order_fields"), dict) else {}
        identifiers = contact.get("identifiers", {}) if isinstance(contact.get("identifiers"), dict) else {}
        known_channel_phone = ""
        if channel == "whatsapp":
            known_channel_phone = str(order_fields.get("phone") or identifiers.get("wa_id") or identifiers.get("phone_e164") or "")
        active_skills = ChatbotSkillRouter(runtime_settings).active_skill_payloads(
            contact=contact,
            incoming_text=incoming_text,
            max_skills=3,
        )
        active_skills_json = json.dumps(active_skills, ensure_ascii=False)
        return (
            f"Channel: {channel}\n"
            f"Current tag: {contact.get('current_tag', 'lead_cold')}\n"
            f"Lead goal: {contact.get('lead_goal', 'unknown')}\n"
            f"Known order fields: {json.dumps(order_fields, ensure_ascii=False)}\n"
            f"Known channel phone: {known_channel_phone}\n"
            f"Allowed package codes: {json.dumps(package_codes, ensure_ascii=False)}\n"
            f"Available packages: {packages}\n"
            f"Active chatbot skills: {active_skills_json}\n"
            f"Knowledge base: {knowledge_base}\n"
            f"Recent assistant price quote: {'yes' if recently_quoted_price else 'no'}\n"
            f"Incoming asks price/order/shipping: {'yes' if incoming_requests_price_or_order else 'no'}\n"
            f"Incoming message: {incoming_text}\n"
            f"Conversation history:\n{history}\n\n"
            "只使用 Active chatbot skills 作为当前场景 playbook；不要把未注入的 skill 规则写进回复。\n"
            "默认使用 Pace -> Answer -> Diagnose -> Bridge -> Choice：先承接原话，先回答真实问题，再问一个必要问题，需求明确后才推荐。\n"
            "不要在 reply_text 里输出 skill_id、lead tag、package code、checkout_ready、escalate 或任何内部字段。\n"
            "图片会由系统作为媒体文件另发；不要把图片 URL 或 checkout URL 写进 reply_text。\n"
            "严禁夸大痛点、制造焦虑、暗示治疗效果、假装稀缺或用操控式话术逼单。\n"
            "如果 Recent assistant price quote 是 yes 且 Incoming asks price/order/shipping 是 no，"
            "不要重复任何 SGD 价格，只回答顾客当前咨询并问一个低压场景问题。\n"
            "如果 Channel 是 whatsapp 且 Known order fields.phone 或 Known channel phone 已有号码，"
            "这个 WhatsApp 来讯号码已经可以作为联系电话；不要再询问联系电话，也不要把 phone 放进 missing_order_fields。\n"
            "如果 Channel 不是 whatsapp，仍必须向顾客收集联系电话。\n"
            "输出 JSON，字段固定为：reply_text, next_tag, lead_goal, recommended_package_code, "
            "upgrade_package_code, selected_package_code, order_fields, missing_order_fields, "
            "checkout_ready, escalate, escalation_reason, faq_topic, opt_in_granted。\n"
            "next_tag 只能是 lead_cold, qualified_warm, cart_hot, handoff_pending。\n"
            "lead_goal 只能是 self_care, pregnancy, postpartum, gift_elder, unknown。\n"
            "recommended_package_code, upgrade_package_code, selected_package_code 只能使用 Allowed package codes 中存在的值，"
            "如果没有合适套餐请填 null，不要发明新的 package code。\n"
            "只有顾客明确购买，并且 name、phone、address 都已经收集完整时，checkout_ready 才能为 true；"
            "WhatsApp channel 已有 Known channel phone 时可视为 phone 已收集；"
            "资料不齐时 checkout_ready=false，missing_order_fields 必须列出缺少字段。"
        )

    @staticmethod
    def _recent_assistant_message_mentions_price(messages: list[dict[str, Any]]) -> bool:
        assistant_messages = [
            str(item.get("text") or "")
            for item in messages
            if str(item.get("role") or "").casefold() == "assistant"
        ]
        return any("sgd" in text.casefold() for text in assistant_messages[-6:])

    @staticmethod
    def _incoming_requests_price_or_order(incoming_text: str) -> bool:
        text = str(incoming_text or "").casefold()
        return any(keyword in text for keyword in PRICE_OR_ORDER_INTENT_KEYWORDS)

    @staticmethod
    def _build_follow_up_prompt(
        *,
        contact: dict[str, Any],
        messages: list[dict[str, Any]],
        stage: str,
        instruction: str,
        checkout_url: str | None,
    ) -> str:
        history = "\n".join(
            f"{item.get('role', 'user')}: {item.get('text', '')}"
            for item in messages[-12:]
        )
        return (
            f"Follow-up stage: {stage}\n"
            f"Current tag: {contact.get('current_tag', 'lead_cold')}\n"
            f"Selected package: {contact.get('selected_package_code')}\n"
            f"Checkout URL (internal only, do not send as text): {checkout_url or ''}\n"
            f"Stage instruction: {instruction}\n"
            f"Conversation history:\n{history}\n\n"
            "Stage instruction 是内部客服策略，不是顾客文案；必须转写成自然、简短、可直接发送给顾客的 reply_text。\n"
            "严禁逐字复制 Stage instruction，严禁在 reply_text 里输出“提醒、询问、不要发送、Stage instruction、instruction”等内部指令语气。\n"
            "输出 JSON，字段固定为：reply_text, next_tag, checkout_link_required, escalate, escalation_reason, opt_in_request。"
        )


_gemini_service: GeminiConversationService | None = None


def get_gemini_service() -> GeminiConversationService:
    """Get the shared Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiConversationService()
    return _gemini_service


def _safe_follow_up_fallback_text(*, checkout_url: str | None, cart_hot: bool = False) -> str:
    if checkout_url or cart_hot:
        return SAFE_CHECKOUT_FOLLOW_UP_FALLBACK_TEXT
    return SAFE_FOLLOW_UP_FALLBACK_TEXT
