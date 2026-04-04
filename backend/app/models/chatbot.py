"""Chatbot settings models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional


class FAQItem(BaseModel):
    """FAQ item with keywords and response."""

    keywords: list[str] = Field(..., description="Keywords to trigger this FAQ")
    response_en: str = Field(..., description="Response in English")
    response_zh: str = Field(..., description="Response in Chinese")
    recommend_product_id: Optional[str] = Field(None, description="Product ID to recommend")


class AbandonedCartMessage(BaseModel):
    """Abandoned cart message configuration."""

    template: str = Field(..., description="Message template with placeholders")
    discount_code: Optional[str] = Field(None, description="Discount code to offer")
    delay_minutes: int = Field(default=15, ge=0, description="Delay in minutes before sending")


class ReplenishmentReminder(BaseModel):
    """Replenishment reminder configuration."""

    enabled: bool = Field(default=True)
    template_en: str = Field(..., description="Template in English")
    template_zh: str = Field(..., description="Template in Chinese")
    trigger_days: list[int] = Field(default=[12, 25], description="Days after purchase to trigger")


class ChatbotSettingsResponse(BaseModel):
    """Response model for chatbot settings."""

    faq: list[FAQItem]
    abandoned_cart_message: AbandonedCartMessage
    replenishment_reminder: ReplenishmentReminder


class UpdateChatbotSettingsRequest(BaseModel):
    """Request model for updating chatbot settings."""

    faq: Optional[list[FAQItem]] = None
    abandoned_cart_message: Optional[AbandonedCartMessage] = None
    replenishment_reminder: Optional[ReplenishmentReminder] = None
