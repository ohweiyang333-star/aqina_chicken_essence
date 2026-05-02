"""Follow-up scheduling and processing engine."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.services.chatbot_settings import ChatbotSettingsService, FOLLOW_UP_STAGE_DELAYS
from app.services.gemini_service import get_gemini_service
from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_utils import ensure_datetime, stable_id, utcnow
from app.services.meta_client import get_meta_client
from app.services.task_queue import get_task_queue_service


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

        conversation_id = job["conversation_id"]
        messages = self.contact_service.get_recent_messages(conversation_id)
        result = self.gemini_service.generate_follow_up_reply(
            contact=contact,
            messages=messages,
            stage=job["stage"],
            instruction=str(stage_rule.get("instruction", "")),
            runtime_settings=runtime_settings,
            checkout_url=checkout_url,
        )
        reply_text, next_tag = self._normalize_follow_up_result(result, checkout_url=checkout_url)
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

    @staticmethod
    def _normalize_follow_up_result(result: Any, *, checkout_url: str | None) -> tuple[str, str | None]:
        if isinstance(result, dict):
            reply_text = str(result.get("reply_text", "")).strip()
            next_tag = result.get("next_tag")
            if result.get("checkout_link_required") and checkout_url:
                reminder = "请使用前面发送的 PayNow QR 图片付款，完成后把截图发回这里即可。"
                if reminder not in reply_text:
                    reply_text = f"{reply_text}\n\n{reminder}".strip()
            return reply_text, next_tag
        return str(result).strip(), None

    def _mark_job(self, ref: Any, *, status: str, skip_reason: str | None) -> dict[str, Any]:
        payload = {
            "status": status,
            "skip_reason": skip_reason,
            "processed_at": utcnow(),
            "updated_at": utcnow(),
        }
        ref.set(payload, merge=True)
        return {"status": status}
