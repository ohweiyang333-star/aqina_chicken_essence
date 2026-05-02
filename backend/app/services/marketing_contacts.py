"""Persistence helpers for marketing contacts and message history."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.services.marketing_utils import ensure_datetime, stable_id, utcnow


class MarketingContactService:
    """Manage contacts, conversations, message history, and tags."""

    def __init__(self, db: Any):
        self.db = db

    def upsert_contact_from_event(
        self,
        *,
        channel: str,
        identifiers: dict[str, str],
        current_tag: str,
        status: str,
        interaction_time: Any = None,
        comment_time: Any = None,
    ) -> tuple[str, str]:
        now = utcnow()
        interaction_dt = ensure_datetime(interaction_time)
        comment_dt = ensure_datetime(comment_time)

        contact_id, existing = self._find_contact_by_identifiers(identifiers)
        if existing is None:
            seed = identifiers.get("psid") or identifiers.get("wa_id") or identifiers.get("phone_e164") or now.isoformat()
            contact_id = stable_id("contact", channel, seed)
            existing = {
                "channel": channel,
                "identifiers": {},
                "linked_customer_id": None,
                "current_tag": current_tag,
                "follow_up_stage": "none",
                "status": status,
                "created_at": now,
            }

        merged_identifiers = {
            **existing.get("identifiers", {}),
            **{key: value for key, value in identifiers.items() if value},
        }
        update = {
            "channel": channel,
            "identifiers": merged_identifiers,
            "current_tag": current_tag,
            "status": status,
            "updated_at": now,
        }

        if interaction_dt is not None:
            update["last_interaction_time"] = interaction_dt
            update["window_expires_at"] = interaction_dt + timedelta(hours=24)

        if comment_dt is not None:
            update["last_comment_time"] = comment_dt

        conversation_id = existing.get("latest_conversation_id")
        if not conversation_id:
            conversation_id = self._ensure_conversation(contact_id, channel, opened_at=interaction_dt or comment_dt or now)
            update["latest_conversation_id"] = conversation_id

        ref = self.db.collection("marketing_contacts").document(contact_id)
        if ref.get().exists:
            ref.update(update)
        else:
            ref.set({**existing, **update})

        return contact_id, conversation_id

    def append_message(
        self,
        *,
        contact_id: str,
        channel: str,
        direction: str,
        role: str,
        text: str,
        source: str,
        provider_message_id: str | None = None,
        provider_comment_id: str | None = None,
        message_type: str = "text",
        follow_up_stage: str | None = None,
        delivery_status: str = "accepted",
        created_at: Any = None,
    ) -> tuple[str, str]:
        created_dt = ensure_datetime(created_at) or utcnow()
        contact = self.db.collection("marketing_contacts").document(contact_id).get().to_dict()
        conversation_id = (contact or {}).get("latest_conversation_id") or self._ensure_conversation(contact_id, channel, opened_at=created_dt)
        messages_ref = self.db.collection("marketing_conversations").document(conversation_id).collection("messages")

        message_id = stable_id(
            "message",
            provider_message_id or provider_comment_id or f"{direction}:{created_dt.isoformat()}:{text[:80]}",
        )
        messages_ref.document(message_id).set(
            {
                "direction": direction,
                "role": role,
                "text": text,
                "provider_message_id": provider_message_id,
                "provider_comment_id": provider_comment_id,
                "message_type": message_type,
                "source": source,
                "follow_up_stage": follow_up_stage,
                "delivery_status": delivery_status,
                "created_at": created_dt,
            }
        )

        all_messages = list(messages_ref.stream())
        self.db.collection("marketing_conversations").document(conversation_id).set(
            {
                "contact_id": contact_id,
                "channel": channel,
                "status": "open",
                "last_message_at": created_dt,
                "message_count": len(all_messages),
            },
            merge=True,
        )

        contact_update = {
            "latest_conversation_id": conversation_id,
            "updated_at": utcnow(),
        }
        if direction == "outbound":
            contact_update["last_outbound_time"] = created_dt
        self.db.collection("marketing_contacts").document(contact_id).set(contact_update, merge=True)

        return conversation_id, message_id

    def update_contact_tag(
        self,
        contact_id: str,
        next_tag: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        contact_ref = self.db.collection("marketing_contacts").document(contact_id)
        snapshot = contact_ref.get()
        if not snapshot.exists:
            raise KeyError(f"Contact not found: {contact_id}")

        current = snapshot.to_dict()
        previous = current.get("current_tag")
        now = utcnow()
        contact_ref.update({"current_tag": next_tag, "updated_at": now})

        tag_event_id = stable_id("tag", contact_id, next_tag, now.isoformat())
        contact_ref.collection("tag_events").document(tag_event_id).set(
            {
                "from_tag": previous,
                "to_tag": next_tag,
                "source": source,
                "metadata": metadata or {},
                "created_at": now,
            }
        )

    def update_contact_profile(self, contact_id: str, fields: dict[str, Any]) -> None:
        """Merge arbitrary contact fields onto the contact document."""
        self.db.collection("marketing_contacts").document(contact_id).set(
            {**fields, "updated_at": utcnow()},
            merge=True,
        )

    def pause_automation(self, contact_id: str, *, reason: str) -> None:
        """Pause automation for contacts under manual handoff."""
        self.update_contact_profile(
            contact_id,
            {
                "current_tag": "handoff_pending",
                "automation_paused": True,
                "handoff_reason": reason,
            },
        )

    def resume_automation(self, contact_id: str, *, next_tag: str = "qualified_warm") -> None:
        """Resume automation after a manual handoff is resolved."""
        self.update_contact_profile(
            contact_id,
            {
                "current_tag": next_tag,
                "automation_paused": False,
                "handoff_reason": None,
            },
        )

    def grant_marketing_opt_in(self, contact_id: str, *, source: str) -> None:
        """Mark a WhatsApp contact as eligible for template marketing campaigns."""
        self.update_contact_profile(
            contact_id,
            {
                "marketing_opt_in": True,
                "opt_in_source": source,
                "opt_in_at": utcnow(),
                "opt_out_at": None,
                "marketing_status": "opted_in",
            },
        )

    def mark_marketing_opt_out(self, contact_id: str, *, source: str) -> None:
        """Mark a WhatsApp contact as opted out from marketing broadcasts."""
        self.update_contact_profile(
            contact_id,
            {
                "marketing_opt_in": False,
                "opt_out_source": source,
                "opt_out_at": utcnow(),
                "marketing_status": "opted_out",
            },
        )

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        snapshot = self.db.collection("marketing_contacts").document(contact_id).get()
        if not snapshot.exists:
            raise KeyError(f"Contact not found: {contact_id}")
        return snapshot.to_dict()

    def get_recent_messages(self, conversation_id: str, limit: int = 12) -> list[dict[str, Any]]:
        docs = (
            self.db.collection("marketing_conversations")
            .document(conversation_id)
            .collection("messages")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        messages = [doc.to_dict() for doc in docs]
        messages.reverse()
        return messages

    def _ensure_conversation(self, contact_id: str, channel: str, opened_at: Any) -> str:
        opened_dt = ensure_datetime(opened_at) or utcnow()
        conversation_id = stable_id("conversation", contact_id)
        ref = self.db.collection("marketing_conversations").document(conversation_id)
        if not ref.get().exists:
            ref.set(
                {
                    "contact_id": contact_id,
                    "channel": channel,
                    "status": "open",
                    "opened_at": opened_dt,
                    "last_message_at": opened_dt,
                    "message_count": 0,
                    "context_summary": None,
                }
            )
        return conversation_id

    def _find_contact_by_identifiers(self, identifiers: dict[str, str]) -> tuple[str | None, dict[str, Any] | None]:
        for field, value in identifiers.items():
            if not value:
                continue
            docs = list(
                self.db.collection("marketing_contacts")
                .where(f"identifiers.{field}", "==", value)
                .limit(1)
                .stream()
            )
            if docs:
                snapshot = docs[0]
                return snapshot.id, snapshot.to_dict()
        return None, None
