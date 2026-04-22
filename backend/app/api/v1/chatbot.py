"""Chatbot settings API endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import Admin, DB
from app.models.chatbot import ChatbotSettingsResponse, UpdateChatbotSettingsRequest
from app.services.chatbot_settings import ChatbotSettingsService

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.get("/settings", response_model=ChatbotSettingsResponse)
async def get_chatbot_settings(db: DB, admin: Admin):
    """Get the canonical chatbot settings document for admin configuration."""
    del admin
    service = ChatbotSettingsService(db)
    return service.get_settings()


@router.put("/settings", response_model=ChatbotSettingsResponse)
async def update_chatbot_settings(
    update_data: UpdateChatbotSettingsRequest,
    db: DB,
    admin: Admin,
):
    """Update chatbot runtime settings from the admin UI."""
    del admin
    service = ChatbotSettingsService(db)
    return service.update_settings(update_data)
