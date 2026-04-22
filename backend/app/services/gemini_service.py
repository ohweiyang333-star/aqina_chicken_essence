"""Gemini API wrapper for structured sales and follow-up responses."""
from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import settings
from app.models.chatbot import FollowUpTurnResult, SalesConversationTurn


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
        return SalesConversationTurn.model_validate(payload)

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
            return FollowUpTurnResult(reply_text=instruction)
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
        packages = json.dumps(runtime_settings.get("packages", {}), ensure_ascii=False)
        knowledge_base = json.dumps(runtime_settings.get("knowledge_base", {}), ensure_ascii=False)
        return (
            f"Channel: {channel}\n"
            f"Current tag: {contact.get('current_tag', 'lead_cold')}\n"
            f"Lead goal: {contact.get('lead_goal', 'unknown')}\n"
            f"Known order fields: {json.dumps(contact.get('order_fields', {}), ensure_ascii=False)}\n"
            f"Available packages: {packages}\n"
            f"Knowledge base: {knowledge_base}\n"
            f"Incoming message: {incoming_text}\n"
            f"Conversation history:\n{history}"
        )

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
            f"Checkout URL: {checkout_url or ''}\n"
            f"Stage instruction: {instruction}\n"
            f"Conversation history:\n{history}\n\n"
            "输出 JSON，字段固定为：reply_text, next_tag, checkout_link_required, escalate, escalation_reason, opt_in_request。"
        )


_gemini_service: GeminiConversationService | None = None


def get_gemini_service() -> GeminiConversationService:
    """Get the shared Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiConversationService()
    return _gemini_service
