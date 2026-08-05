"""Follow-up scheduling and processing engine."""
from __future__ import annotations

import ast
from copy import deepcopy
import logging
import re
from datetime import timedelta
from typing import Any

from app.services.chatbot_settings import (
    ChatbotSettingsService,
    FOLLOW_UP_STAGE_DELAYS,
    normalize_customer_facing_product_terms,
)
from app.services.gemini_service import (
    SAFE_CHECKOUT_FOLLOW_UP_FALLBACK_TEXT,
    SAFE_FOLLOW_UP_FALLBACK_TEXT,
    get_gemini_service,
)
from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_utils import ensure_datetime, stable_id, utcnow
from app.services.meta_media_assets import MetaMediaAssetService
from app.services.meta_client import get_meta_client
from app.services.task_queue import get_task_queue_service


logger = logging.getLogger(__name__)
SOCIAL_PROOF_FOLLOW_UP_STAGES = {"t3h"}
SOCIAL_PROOF_FOLLOW_UP_TAGS = {"lead_cold", "qualified_warm"}


class FollowUpEngine:
    """Manage delayed CRM follow-up jobs anchored to the last user interaction."""

    def __init__(
        self,
        *,
        db: Any,
        task_queue: Any | None = None,
        contact_service: MarketingContactService | None = None,
        meta_client: Any | None = None,
        gemini_service: Any | None = None,
    ) -> None:
        self.db = db
        self.task_queue = task_queue or get_task_queue_service()
        self.contact_service = contact_service or MarketingContactService(db)
        self.meta_client = meta_client or get_meta_client()
        self.gemini_service = gemini_service or get_gemini_service()
        self.settings_service = ChatbotSettingsService(db)

    def schedule_follow_up_jobs(
        self,
        *,
        contact_id: str,
        conversation_id: str,
        anchor_interaction_time: Any,
        current_tag: str,
    ) -> list[str]:
        del current_tag
        anchor_dt = ensure_datetime(anchor_interaction_time) or utcnow()
        runtime_settings = self.settings_service.get_settings(persist_migration=False)
        task_names: list[str] = []
        for stage, delay_minutes in FOLLOW_UP_STAGE_DELAYS.items():
            if stage not in runtime_settings.get("crm_follow_up_rules", {}):
                continue
            due_at = anchor_dt + timedelta(minutes=delay_minutes)
            job_id = stable_id("followup", contact_id, anchor_dt.isoformat(), stage)
            payload = {
                "contact_id": contact_id,
                "conversation_id": conversation_id,
                "stage": stage,
                "anchor_interaction_time": anchor_dt,
                "due_at": due_at,
                "eligible_tags": ["lead_cold", "qualified_warm", "cart_hot"],
                "status": "scheduled",
                "attempt_count": 0,
                "skip_reason": None,
                "last_error": None,
                "processed_at": None,
                "created_at": utcnow(),
                "updated_at": utcnow(),
            }
            ref = self.db.collection("marketing_follow_up_jobs").document(job_id)
            ref.set(payload, merge=True)
            task_name = self.task_queue.enqueue_follow_up_job(job_id, due_at)
            ref.set({"cloud_task_name": task_name, "updated_at": utcnow()}, merge=True)
            task_names.append(task_name)
        return task_names

    def process_follow_up_job(self, job_id: str) -> dict[str, Any]:
        ref = self.db.collection("marketing_follow_up_jobs").document(job_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise KeyError(f"Follow-up job not found: {job_id}")

        job = snapshot.to_dict()
        contact = self.contact_service.get_contact(job["contact_id"])
        if contact.get("current_tag") == "handoff_pending" or contact.get("automation_paused"):
            return self._mark_job(ref, status="skipped_handoff_pending", skip_reason="handoff_pending")
        if contact.get("marketing_status") == "opted_out" or contact.get("opt_out_at"):
            return self._mark_job(ref, status="skipped_opt_out", skip_reason="marketing_opt_out")

        last_interaction = ensure_datetime(contact.get("last_interaction_time"))
        anchor = ensure_datetime(job.get("anchor_interaction_time"))
        if last_interaction is None or anchor is None:
            return self._mark_job(ref, status="skipped_missing_anchor", skip_reason="missing_anchor")
        if last_interaction != anchor:
            return self._mark_job(ref, status="skipped_stale_anchor", skip_reason="stale_anchor")

        window_expires_at = ensure_datetime(contact.get("window_expires_at"))
        if window_expires_at is None or utcnow() > window_expires_at:
            return self._mark_job(ref, status="skipped_window_closed", skip_reason="window_closed")

        runtime_settings = self.settings_service.get_settings(persist_migration=False)
        current_tag = contact.get("current_tag", "lead_cold")
        stage_rule = self.settings_service.get_follow_up_rule(runtime_settings, job["stage"], current_tag)
        if not stage_rule:
            return self._mark_job(ref, status="skipped_tag_mismatch", skip_reason="tag_mismatch")
        if not self.gemini_service.is_ready():
            return self._mark_job(ref, status="blocked_configuration", skip_reason="configuration_incomplete")

        checkout_url = None
        if job["stage"] == "t12h":
            checkout_url = self._get_checkout_url(job["contact_id"])
            if not checkout_url:
                return self._mark_job(ref, status="skipped_missing_checkout", skip_reason="no_checkout_session")

        social_proof_media = self._select_social_proof_media(
            contact_id=job["contact_id"],
            contact=contact,
            stage=job["stage"],
            current_tag=current_tag,
            runtime_settings=runtime_settings,
        )

        instruction = str(stage_rule.get("instruction", ""))
        if social_proof_media:
            instruction = (
                f"{instruction} If natural, tell the customer you are also sharing one real customer usage photo "
                "for reference. Do not invent review quotes, medical outcomes, safety guarantees, or exact usage results."
            )

        conversation_id = job["conversation_id"]
        messages = self.contact_service.get_recent_messages(conversation_id)
        result = self.gemini_service.generate_follow_up_reply(
            contact=contact,
            messages=messages,
            stage=job["stage"],
            instruction=instruction,
            runtime_settings=runtime_settings,
            checkout_url=checkout_url,
        )
        reply_text, next_tag = self._normalize_follow_up_result(
            result,
            checkout_url=checkout_url,
            cart_hot=current_tag == "cart_hot",
        )
        self._send_reply(contact, reply_text)
        self.contact_service.append_message(
            contact_id=job["contact_id"],
            channel=contact["channel"],
            direction="outbound",
            role="assistant",
            text=reply_text,
            source="follow_up_engine",
            follow_up_stage=job["stage"],
            delivery_status="sent",
        )
        if social_proof_media:
            self._send_social_proof_media(
                contact_id=job["contact_id"],
                contact=contact,
                stage=job["stage"],
                media=social_proof_media,
            )
        if next_tag and next_tag != current_tag:
            self.contact_service.update_contact_tag(
                job["contact_id"],
                next_tag,
                source="follow_up_engine",
                metadata={"job_id": job_id},
            )
        self.db.collection("marketing_contacts").document(job["contact_id"]).set(
            {"follow_up_stage": job["stage"], "updated_at": utcnow()},
            merge=True,
        )
        return self._mark_job(ref, status="completed", skip_reason=None)

    def reconcile_due_jobs(self, limit: int = 100) -> dict[str, Any]:
        now = utcnow()
        jobs = (
            self.db.collection("marketing_follow_up_jobs")
            .where("status", "==", "scheduled")
            .where("due_at", "<=", now)
            .order_by("due_at", direction="ASCENDING")
            .limit(limit)
            .stream()
        )
        queued = []
        for doc in jobs:
            queued.append(self.task_queue.enqueue_follow_up_job(doc.id, now))
        return {"queued_jobs": len(queued)}

    def _get_checkout_url(self, contact_id: str) -> str | None:
        contact = self.contact_service.get_contact(contact_id)
        session_id = contact.get("checkout_session_id")
        if not session_id:
            return None
        snapshot = self.db.collection("marketing_checkout_sessions").document(session_id).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict().get("checkout_url")

    def _send_reply(self, contact: dict[str, Any], text: str) -> dict[str, Any]:
        channel = contact.get("channel")
        identifiers = contact.get("identifiers", {})
        if channel == "messenger":
            return self.meta_client.send_messenger_text(recipient_psid=identifiers["psid"], text=text)
        if channel == "whatsapp":
            return self.meta_client.send_whatsapp_text(to=identifiers["wa_id"], text=text)
        raise ValueError(f"Unsupported follow-up channel: {channel}")

    def _select_social_proof_media(
        self,
        *,
        contact_id: str,
        contact: dict[str, Any],
        stage: str,
        current_tag: str,
        runtime_settings: dict[str, Any],
    ) -> dict[str, Any] | None:
        if stage not in SOCIAL_PROOF_FOLLOW_UP_STAGES:
            return None
        if current_tag not in SOCIAL_PROOF_FOLLOW_UP_TAGS:
            return None
        if contact.get("channel") not in {"messenger", "whatsapp"}:
            return None

        sent_media = contact.get("sent_media") if isinstance(contact.get("sent_media"), dict) else {}
        social_proof_state = sent_media.get("follow_up_social_proof")
        if isinstance(social_proof_state, dict) and social_proof_state.get("sent"):
            return None

        locale = _follow_up_locale(contact)
        media_assets = runtime_settings.get("media_assets", {}) or {}
        images = _localized_media_list(media_assets.get("ugc_social_proof_images"), locale)
        if not images:
            return None

        index = _stable_media_index(contact_id, stage, len(images))
        captions = media_assets.get("captions", {}) if isinstance(media_assets.get("captions"), dict) else {}
        return {
            "source_url": images[index],
            "cache_key": f"ugc_social_proof_{locale}_{index}",
            "caption": _localized_media_value(captions.get("ugc_social_proof"), locale),
            "locale": locale,
            "index": index,
        }

    def _send_social_proof_media(
        self,
        *,
        contact_id: str,
        contact: dict[str, Any],
        stage: str,
        media: dict[str, Any],
    ) -> None:
        try:
            channel = contact["channel"]
            media_service = MetaMediaAssetService(db=self.db, meta_client=self.meta_client)
            result = media_service.send_chatbot_image(
                channel=channel,
                contact=contact,
                source_url=media["source_url"],
                cache_key=media["cache_key"],
                caption=media.get("caption"),
            )
            self.contact_service.append_message(
                contact_id=contact_id,
                channel=channel,
                direction="outbound",
                role="assistant",
                text=f"Customer social proof image sent: {media['locale']}:{media['index']}",
                source="follow_up_social_proof_media",
                provider_message_id=_extract_provider_message_id(channel, result),
                message_type="image",
                follow_up_stage=stage,
                delivery_status="sent",
                media_url=media["source_url"],
            )
            refreshed = self.contact_service.get_contact(contact_id)
            sent_media = deepcopy(refreshed.get("sent_media") or {})
            sent_media["follow_up_social_proof"] = {
                "sent": True,
                "locale": media["locale"],
                "image_url": media["source_url"],
                "image_index": media["index"],
            }
            self.contact_service.update_contact_profile(contact_id, {"sent_media": sent_media})
        except Exception as exc:  # noqa: BLE001 - follow-up text should still be delivered.
            logger.warning("follow_up_social_proof_media_failed contact_id=%s stage=%s error=%s", contact_id, stage, exc)

    @staticmethod
    def _normalize_follow_up_result(
        result: Any,
        *,
        checkout_url: str | None,
        cart_hot: bool = False,
    ) -> tuple[str, str | None]:
        payload: dict[str, Any] | None = None
        if isinstance(result, dict):
            payload = result
        elif isinstance(result, str):
            payload = FollowUpEngine._parse_structured_result_string(result)
        elif hasattr(result, "model_dump"):
            dumped = result.model_dump()
            if isinstance(dumped, dict):
                payload = dumped
        elif hasattr(result, "reply_text"):
            payload = {
                "reply_text": getattr(result, "reply_text", ""),
                "next_tag": getattr(result, "next_tag", None),
                "checkout_link_required": getattr(result, "checkout_link_required", False),
            }

        if payload is not None:
            reply_text = str(payload.get("reply_text", "")).strip()
            next_tag = payload.get("next_tag")
            if payload.get("checkout_link_required") and checkout_url:
                reminder = "请使用前面发送的 PayNow QR 图片付款，完成后把截图发回这里即可。"
                if reminder not in reply_text:
                    reply_text = f"{reply_text}\n\n{reminder}".strip()
            return _customer_safe_follow_up_text(reply_text, checkout_url=checkout_url, cart_hot=cart_hot), next_tag
        return _customer_safe_follow_up_text(str(result).strip(), checkout_url=checkout_url, cart_hot=cart_hot), None

    @staticmethod
    def _parse_structured_result_string(value: str) -> dict[str, Any] | None:
        """Recover customer text when a structured follow-up object was stringified."""
        text = str(value or "").strip()
        if "reply_text=" not in text:
            return None

        reply_text = _extract_python_literal_field(text, "reply_text")
        if reply_text is None:
            return None

        next_tag = _extract_python_literal_field(text, "next_tag")
        checkout_link_required = _extract_bool_field(text, "checkout_link_required")
        return {
            "reply_text": reply_text,
            "next_tag": next_tag,
            "checkout_link_required": bool(checkout_link_required),
        }

    def _mark_job(self, ref: Any, *, status: str, skip_reason: str | None) -> dict[str, Any]:
        payload = {
            "status": status,
            "skip_reason": skip_reason,
            "processed_at": utcnow(),
            "updated_at": utcnow(),
        }
        ref.set(payload, merge=True)
        return {"status": status}


def _follow_up_locale(contact: dict[str, Any]) -> str:
    locale = str(contact.get("chatbot_locale") or "").strip().lower()
    return locale if locale in {"zh", "en"} else "zh"


def _localized_media_list(value: Any, locale: str) -> list[str]:
    if isinstance(value, dict):
        localized = value.get(locale) or value.get("zh") or value.get("en")
        return _coerce_media_list(localized)
    return _coerce_media_list(value)


def _localized_media_value(value: Any, locale: str) -> str:
    normalized_locale = locale if locale in {"zh", "en"} else "zh"
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        localized = value.get(normalized_locale) or value.get("zh") or value.get("en")
        if localized:
            return str(localized).strip()
        for candidate in value.values():
            if candidate:
                return str(candidate).strip()
    return ""


def _coerce_media_list(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = value
    elif isinstance(value, tuple):
        candidates = list(value)
    else:
        candidates = []
    return [str(item).strip() for item in candidates if str(item).strip()]


def _stable_media_index(contact_id: str, stage: str, image_count: int) -> int:
    if image_count <= 0:
        return 0
    seed = f"{contact_id}:{stage}"
    return sum(ord(char) for char in seed) % image_count


def _extract_provider_message_id(channel: str, payload: dict[str, Any]) -> str | None:
    if channel == "messenger":
        return payload.get("message_id")
    messages = payload.get("messages") or []
    return messages[0].get("id") if messages else None


def _extract_python_literal_field(text: str, field_name: str) -> Any:
    prefix = f"{field_name}="
    start = text.find(prefix)
    if start < 0:
        return None
    index = start + len(prefix)
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] not in {"'", '"'}:
        raw_match = re.match(r"([^\s]+)", text[index:])
        if not raw_match:
            return None
        raw_value = raw_match.group(1)
        return None if raw_value == "None" else raw_value

    quote = text[index]
    escaped = False
    cursor = index + 1
    while cursor < len(text):
        char = text[cursor]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == quote:
            candidate = text[index : cursor + 1]
            try:
                return ast.literal_eval(candidate)
            except (SyntaxError, ValueError):
                return candidate[1:-1]
        cursor += 1
    return None


def _extract_bool_field(text: str, field_name: str) -> bool | None:
    match = re.search(rf"{re.escape(field_name)}=(True|False)", text)
    if not match:
        return None
    return match.group(1) == "True"


def _customer_safe_follow_up_text(text: str, *, checkout_url: str | None, cart_hot: bool = False) -> str:
    normalized = normalize_customer_facing_product_terms(str(text or "").strip())
    if not normalized or normalized.casefold() in {"none", "null"}:
        return _safe_follow_up_fallback_text(checkout_url=checkout_url, cart_hot=cart_hot)
    if _looks_like_internal_follow_up_instruction(normalized):
        return _safe_follow_up_fallback_text(checkout_url=checkout_url, cart_hot=cart_hot)
    return normalized


def _safe_follow_up_fallback_text(*, checkout_url: str | None, cart_hot: bool = False) -> str:
    if checkout_url or cart_hot:
        return SAFE_CHECKOUT_FOLLOW_UP_FALLBACK_TEXT
    return SAFE_FOLLOW_UP_FALLBACK_TEXT


def _looks_like_internal_follow_up_instruction(text: str) -> bool:
    folded = text.casefold()
    internal_markers = [
        "stage instruction",
        "follow-up stage",
        "checkout_link_required",
        "reply_text=",
        "next_tag=",
        "instruction",
        "输出 json",
        "字段固定",
        "internal only",
        "不要发送",
        "不要介绍",
        "不要重新",
        "不要把",
        "严禁",
        "用一句话",
        "直接帮顾客",
        "语气简短",
        "顾客若",
    ]
    if any(marker in folded for marker in internal_markers):
        return True
    return "提醒" in text and "询问" in text
