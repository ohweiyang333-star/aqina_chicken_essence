"""Deterministic router for Aqina chatbot skill playbooks."""
from __future__ import annotations

from typing import Any


class ChatbotSkillRouter:
    """Select the smallest relevant skill set for the current customer turn."""

    def __init__(self, runtime_settings: dict[str, Any]) -> None:
        self.runtime_settings = runtime_settings or {}
        self.skills = self.runtime_settings.get("chatbot_skills", {}) or {}

    def select_active_skill_ids(
        self,
        *,
        contact: dict[str, Any],
        incoming_text: str,
        max_skills: int = 3,
    ) -> list[str]:
        text = _normalize(incoming_text)
        lead_goal = _normalize(contact.get("lead_goal", ""))
        current_tag = _normalize(contact.get("current_tag", ""))
        selected: list[str] = []

        def add(skill_id: str) -> None:
            if skill_id in self.skills and skill_id not in selected and len(selected) < max_skills:
                selected.append(skill_id)

        if _contains_any(text, PAYMENT_KEYWORDS):
            add("payment_receipt")
            return selected

        if _contains_any(text, MEDICAL_KEYWORDS):
            add("medical_safety")
        if _contains_any(text, MATERNITY_KEYWORDS) or lead_goal in {"pregnancy", "postpartum"}:
            add("maternity_consultation")
        if _contains_any(text, ELDER_KEYWORDS) or lead_goal == "gift_elder":
            add("elder_gift_recovery")
        if _contains_any(text, TASTE_KEYWORDS):
            add("taste_objection")
        if _contains_any(text, PRICE_KEYWORDS):
            add("price_objection")
        if _contains_any(text, CHECKOUT_KEYWORDS) or current_tag == "cart_hot":
            add("checkout_collect")
        if _contains_any(text, SELF_CARE_KEYWORDS) or lead_goal == "self_care":
            add("self_care_fatigue")

        if (not selected or current_tag in {"", "lead_cold"}) and len(selected) < max_skills:
            add("ice_breaking")

        if not selected:
            add("ice_breaking")
        return selected[:max_skills]

    def active_skill_payloads(
        self,
        *,
        contact: dict[str, Any],
        incoming_text: str,
        max_skills: int = 3,
    ) -> dict[str, dict[str, Any]]:
        return {
            skill_id: self.skills[skill_id]
            for skill_id in self.select_active_skill_ids(
                contact=contact,
                incoming_text=incoming_text,
                max_skills=max_skills,
            )
            if skill_id in self.skills
        }


PAYMENT_KEYWORDS = {
    "付款",
    "完成付款",
    "已付款",
    "已经付",
    "付了",
    "paynow",
    "paid",
    "receipt",
    "payment",
    "截图",
}
MEDICAL_KEYWORDS = {"疾病", "治疗", "吃药", "药", "手术", "糖尿", "高血压", "癌", "医生", "肾", "病"}
MATERNITY_KEYWORDS = {"孕", "怀孕", "待产", "月子", "产后", "坐月", "新手妈妈", "哺乳"}
ELDER_KEYWORDS = {"长辈", "老人", "妈妈", "爸爸", "父母", "送礼", "术后", "恢复", "补身"}
TASTE_KEYWORDS = {"腥", "苦", "味道", "口感", "好喝", "难喝", "怕油"}
PRICE_KEYWORDS = {"多少钱", "价钱", "价格", "贵", "便宜", "price", "how much", "discount", "优惠"}
CHECKOUT_KEYWORDS = {
    "我要",
    "下单",
    "购买",
    "订购",
    "买",
    "order",
    "buy",
    "拿一盒",
    "拿两盒",
    "地址",
    "电话",
    "运费",
    "多久到",
    "delivery",
    "shipping",
}
SELF_CARE_KEYWORDS = {"自己", "熬夜", "疲劳", "很累", "累", "没精神", "上班", "学生", "考试", "提神", "日常"}


def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _normalize(value: Any) -> str:
    return str(value or "").casefold().strip()
