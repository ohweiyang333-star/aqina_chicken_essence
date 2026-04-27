"""Chatbot settings, runtime, and structured AI output models."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


MarketingTag = Literal["lead_cold", "qualified_warm", "cart_hot", "handoff_pending"]
LeadGoal = Literal["self_care", "pregnancy", "postpartum", "gift_elder", "unknown"]


class FAQItem(BaseModel):
    """Backward-compatible FAQ item from the legacy admin UI."""

    keywords: list[str] = Field(default_factory=list)
    response_en: str = ""
    response_zh: str = ""
    recommend_product_id: str | None = None


class ChatbotPackage(BaseModel):
    """Single package definition available to the sales bot."""

    code: str
    name_zh: str
    name_en: str
    description_zh: str = ""
    description_en: str = ""
    price_sgd: float = Field(ge=0)
    pack_count: int = Field(ge=1)
    box_count: int | None = Field(default=None, ge=1)
    target_audience: list[LeadGoal] = Field(default_factory=list)
    hero: bool = False
    free_shipping_eligible: bool = False


class KnowledgeBaseFAQ(BaseModel):
    """Customer-facing FAQ entry stored in the knowledge base."""

    question: str
    answer: str


class KnowledgeBase(BaseModel):
    """Marketing knowledge base used to compose the system prompt."""

    usps: list[str] = Field(default_factory=list)
    faq: list[KnowledgeBaseFAQ] = Field(default_factory=list)
    medical_disclaimer: str = ""
    logistics: str = ""
    consumption: str = ""
    comparisons: str = ""


class PayNowSettings(BaseModel):
    """PayNow-only checkout instructions."""

    enabled: bool = True
    account_name: str = "Boong Poultry Pte Ltd"
    payment_qr_image: str = ""
    payment_qr_alt: str = "Aqina PayNow QR"
    payment_reference_prefix: str = "AQINA"
    payment_note: str = "请在参考栏填写订单号"


class PaymentSettings(BaseModel):
    """Payment configuration wrapper."""

    paynow: PayNowSettings = Field(default_factory=PayNowSettings)


class EscalationSettings(BaseModel):
    """Configuration for human handoff and private WhatsApp alerts."""

    enabled: bool = True
    private_whatsapp_number: str = ""
    whatsapp_template_name: str = ""
    pause_automation_on_handoff: bool = True


class ChatbotSettingsResponse(BaseModel):
    """Canonical chatbot settings document returned to admin UI."""

    system_prompt: str
    handoff_message: str
    packages: dict[str, ChatbotPackage]
    knowledge_base: KnowledgeBase
    crm_follow_up_rules: dict[str, dict[str, dict[str, Any]]]
    payment: PaymentSettings
    escalation: EscalationSettings
    faq: list[FAQItem] = Field(default_factory=list)


class UpdateChatbotSettingsRequest(BaseModel):
    """Partial settings update payload."""

    system_prompt: str | None = None
    handoff_message: str | None = None
    packages: dict[str, ChatbotPackage] | None = None
    knowledge_base: KnowledgeBase | None = None
    crm_follow_up_rules: dict[str, dict[str, dict[str, Any]]] | None = None
    payment: PaymentSettings | None = None
    escalation: EscalationSettings | None = None
    faq: list[FAQItem] | None = None


class OrderFields(BaseModel):
    """Collected order fields extracted from chat."""

    name: str | None = None
    phone: str | None = None
    address: str | None = None


class SalesConversationTurn(BaseModel):
    """Structured Gemini response for a normal inbound chat turn."""

    reply_text: str = ""
    next_tag: MarketingTag = "lead_cold"
    lead_goal: LeadGoal = "unknown"
    recommended_package_code: str | None = None
    upgrade_package_code: str | None = None
    selected_package_code: str | None = None
    order_fields: OrderFields = Field(default_factory=OrderFields)
    missing_order_fields: list[str] = Field(default_factory=list)
    checkout_ready: bool = False
    escalate: bool = False
    escalation_reason: str | None = None
    faq_topic: str | None = None
    opt_in_granted: bool = False


class FollowUpTurnResult(BaseModel):
    """Structured Gemini response for a CRM follow-up job."""

    reply_text: str
    next_tag: MarketingTag | None = None
    checkout_link_required: bool = False
    escalate: bool = False
    escalation_reason: str | None = None
    opt_in_request: bool = False


class EscalationRecord(BaseModel):
    """Response model for escalation queue rows."""

    escalation_id: str
    contact_id: str
    conversation_id: str | None = None
    reason: str
    latest_customer_message: str = ""
    status: Literal["open", "acknowledged", "resolved"] = "open"
    private_whatsapp_number: str = ""
    template_name: str = ""
    template_variables: list[str] = Field(default_factory=list)


class CheckoutSessionResponse(BaseModel):
    """Public PayNow checkout payload."""

    order_id: str
    payment_method: Literal["paynow"] = "paynow"
    payment_status: str = "pending"
    order_status: str = "pending"
    total_amount: float
    customer_name: str
    customer_whatsapp: str
    delivery_address: str
    items: list[dict[str, Any]] = Field(default_factory=list)
    paynow: PayNowSettings
    checkout_url: str
    package_code: str | None = None
