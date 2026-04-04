"""Chatbot settings API endpoints."""
from fastapi import APIRouter, HTTPException, status
from typing import Optional
from google.cloud.firestore import SERVER_TIMESTAMP

from app.api.deps import DB, Admin
from app.models.chatbot import (
    ChatbotSettingsResponse,
    UpdateChatbotSettingsRequest,
    FAQItem,
    AbandonedCartMessage,
    ReplenishmentReminder,
)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.get("/settings", response_model=ChatbotSettingsResponse)
async def get_chatbot_settings(db: DB):
    """
    Get current chatbot configuration.

    Public endpoint - no authentication required.
    """
    doc = db.collection("chatbotSettings").document("default").get()

    if not doc.exists:
        # Return default settings if not configured
        return ChatbotSettingsResponse(
            faq=[],
            abandoned_cart_message=AbandonedCartMessage(
                template="Hi [Name]! 您的 Aqina 滴鸡精还在购物车中。",
                discount_code="HEALTHY10",
                delay_minutes=15,
            ),
            replenishment_reminder=ReplenishmentReminder(
                enabled=True,
                template_en="Hi [Name]! Your Aqina chicken essence is running low.",
                template_zh="Hi [Name]! 您的滴鸡精库存快用完啦。",
                trigger_days=[12, 25],
            ),
        )

    settings_data = doc.to_dict()

    # Convert FAQ items
    faq_data = settings_data.get("faq", [])
    faq = [
        FAQItem(
            keywords=item.get("keywords", []),
            response_en=item.get("response", {}).get("en", ""),
            response_zh=item.get("response", {}).get("zh", ""),
            recommend_product_id=item.get("recommendProductId"),
        )
        for item in faq_data
    ]

    # Convert abandoned cart message
    ac_data = settings_data.get("abandonedCartMessage", {})
    abandoned_cart_message = AbandonedCartMessage(
        template=ac_data.get("template", ""),
        discount_code=ac_data.get("discountCode"),
        delay_minutes=ac_data.get("delay", 15),
    )

    # Convert replenishment reminder
    rr_data = settings_data.get("replenishmentReminder", {})
    replenishment_reminder = ReplenishmentReminder(
        enabled=rr_data.get("enabled", True),
        template_en=rr_data.get("templates", {}).get("en", ""),
        template_zh=rr_data.get("templates", {}).get("zh", ""),
        trigger_days=rr_data.get("triggerDays", [12, 25]),
    )

    return ChatbotSettingsResponse(
        faq=faq,
        abandoned_cart_message=abandoned_cart_message,
        replenishment_reminder=replenishment_reminder,
    )


@router.put("/settings", response_model=ChatbotSettingsResponse)
async def update_chatbot_settings(
    update_data: UpdateChatbotSettingsRequest,
    db: DB,
    admin: Admin,
):
    """
    Update chatbot configuration.

    Requires admin authentication.
    """
    # Get current settings
    doc_ref = db.collection("chatbotSettings").document("default")
    doc = doc_ref.get()

    if doc.exists:
        current_settings = doc.to_dict()
    else:
        current_settings = {
            "faq": [],
            "abandonedCartMessage": {},
            "replenishmentReminder": {},
        }

    # Build update dict
    update_dict = {}

    if update_data.faq is not None:
        # Convert FAQ items to Firestore format
        faq_list = [
            {
                "keywords": item.keywords,
                "response": {
                    "en": item.response_en,
                    "zh": item.response_zh,
                },
                "recommendProductId": item.recommend_product_id,
            }
            for item in update_data.faq
        ]
        update_dict["faq"] = faq_list

    if update_data.abandoned_cart_message is not None:
        update_dict["abandonedCartMessage"] = {
            "template": update_data.abandoned_cart_message.template,
            "discountCode": update_data.abandoned_cart_message.discount_code,
            "delay": update_data.abandoned_cart_message.delay_minutes,
        }

    if update_data.replenishment_reminder is not None:
        update_dict["replenishmentReminder"] = {
            "enabled": update_data.replenishment_reminder.enabled,
            "templates": {
                "en": update_data.replenishment_reminder.template_en,
                "zh": update_data.replenishment_reminder.template_zh,
            },
            "triggerDays": update_data.replenishment_reminder.trigger_days,
        }

    update_dict["updated_at"] = SERVER_TIMESTAMP

    # Update or create settings
    if doc.exists:
        doc_ref.update(update_dict)
    else:
        update_dict["created_at"] = SERVER_TIMESTAMP
        doc_ref.set(update_dict)

    # Return updated settings
    return await get_chatbot_settings(db)
