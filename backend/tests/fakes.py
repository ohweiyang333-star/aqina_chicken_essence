"""Test fakes for Firestore-backed marketing automation flows."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import os
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FakeSnapshot:
    id: str
    _data: dict[str, Any] | None

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self._data or {})

    def get(self, field_path: str, default: Any = None) -> Any:
        data = self._data or {}
        current: Any = data
        for part in field_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return deepcopy(current)


class FakeDocumentRef:
    def __init__(self, db: "FakeFirestore", path: tuple[str, ...]):
        self._db = db
        self._path = path

    @property
    def id(self) -> str:
        return self._path[-1]

    @property
    def path(self) -> str:
        return "/".join(self._path)

    def collection(self, name: str) -> "FakeCollectionRef":
        return FakeCollectionRef(self._db, self._path + (name,))

    def get(self) -> FakeSnapshot:
        return FakeSnapshot(self.id, self._db._docs.get(self._path))

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        existing = self._db._docs.get(self._path, {}) if merge else {}
        existing.update(_normalize_payload(data))
        self._db._docs[self._path] = existing

    def update(self, data: dict[str, Any]) -> None:
        existing = self._db._docs.get(self._path)
        if existing is None:
            raise KeyError(f"Document does not exist: {self.path}")
        existing.update(_normalize_payload(data))
        self._db._docs[self._path] = existing

    def delete(self) -> None:
        self._db._docs.pop(self._path, None)


class FakeQuery:
    def __init__(
        self,
        db: "FakeFirestore",
        path: tuple[str, ...],
        filters: list[tuple[str, str, Any]] | None = None,
        order: tuple[str, bool] | None = None,
        limit_size: int | None = None,
    ):
        self._db = db
        self._path = path
        self._filters = filters or []
        self._order = order
        self._limit_size = limit_size

    def where(self, field: str, op: str, value: Any) -> "FakeQuery":
        return FakeQuery(
            self._db,
            self._path,
            filters=[*self._filters, (field, op, value)],
            order=self._order,
            limit_size=self._limit_size,
        )

    def order_by(self, field: str, direction: str = "ASCENDING") -> "FakeQuery":
        descending = direction == "DESCENDING"
        return FakeQuery(
            self._db,
            self._path,
            filters=self._filters,
            order=(field, descending),
            limit_size=self._limit_size,
        )

    def limit(self, limit_size: int) -> "FakeQuery":
        return FakeQuery(
            self._db,
            self._path,
            filters=self._filters,
            order=self._order,
            limit_size=limit_size,
        )

    def stream(self) -> list[FakeSnapshot]:
        docs = []
        prefix = self._path
        for path, data in self._db._docs.items():
            if len(path) != len(prefix) + 1:
                continue
            if path[: len(prefix)] != prefix:
                continue
            if all(_matches_filter(data, field, op, value) for field, op, value in self._filters):
                docs.append(FakeSnapshot(path[-1], data))

        if self._order:
            field, descending = self._order
            docs.sort(key=lambda doc: doc.get(field), reverse=descending)

        if self._limit_size is not None:
            docs = docs[: self._limit_size]

        return docs


class FakeCollectionRef(FakeQuery):
    def __init__(self, db: "FakeFirestore", path: tuple[str, ...]):
        super().__init__(db, path)

    def document(self, doc_id: str) -> FakeDocumentRef:
        return FakeDocumentRef(self._db, self._path + (doc_id,))


class FakeFirestore:
    def __init__(self):
        self._docs: dict[tuple[str, ...], dict[str, Any]] = {}

    def collection(self, name: str) -> FakeCollectionRef:
        return FakeCollectionRef(self, (name,))

    def seed(self, path: str, data: dict[str, Any]) -> None:
        self._docs[tuple(path.split("/"))] = _normalize_payload(data)


class FakeTaskQueue:
    def __init__(self):
        self.created_tasks: list[dict[str, Any]] = []

    def enqueue_marketing_event(self, event_id: str, processor: str) -> str:
        task = {"type": "event", "event_id": event_id, "processor": processor}
        self.created_tasks.append(task)
        return f"task-event-{len(self.created_tasks)}"

    def enqueue_follow_up_job(self, job_id: str, schedule_at: datetime) -> str:
        task = {"type": "follow-up", "job_id": job_id, "schedule_at": schedule_at}
        self.created_tasks.append(task)
        return f"task-follow-up-{len(self.created_tasks)}"

    def enqueue_reconcile_jobs(self) -> str:
        task = {"type": "reconcile"}
        self.created_tasks.append(task)
        return f"task-reconcile-{len(self.created_tasks)}"

    def enqueue_escalation_notification(self, escalation_id: str) -> str:
        task = {"type": "escalation", "escalation_id": escalation_id}
        self.created_tasks.append(task)
        return f"task-escalation-{len(self.created_tasks)}"


class FakeMetaClient:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def verify_signature(self, raw_body: bytes, signature_header: str | None) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        secret = os.environ.get("META_APP_SECRET", "")
        digest = hmac.new(secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature_header.split("=", 1)[1], digest)

    def reply_to_comment(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("reply_to_comment", kwargs))
        return {"id": "comment-reply-id"}

    def send_private_reply(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("send_private_reply", kwargs))
        return {"message_id": "private-reply-id"}

    def send_messenger_text(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("send_messenger_text", kwargs))
        return {"message_id": "messenger-id"}

    def send_whatsapp_text(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("send_whatsapp_text", kwargs))
        return {"messages": [{"id": "whatsapp-id"}]}

    def send_whatsapp_template(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("send_whatsapp_template", kwargs))
        return {"messages": [{"id": "template-id"}]}


class FakeGeminiService:
    def __init__(
        self,
        reply_text: str = "stubbed model reply",
        chat_result: dict[str, Any] | None = None,
        follow_up_result: dict[str, Any] | None = None,
    ):
        self.reply_text = reply_text
        self.chat_result = chat_result
        self.follow_up_result = follow_up_result
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def is_ready(self) -> bool:
        return True

    def generate_chat_reply(self, **kwargs: Any) -> Any:
        self.calls.append(("generate_chat_reply", kwargs))
        return self.chat_result or self.reply_text

    def generate_follow_up_reply(self, **kwargs: Any) -> Any:
        self.calls.append(("generate_follow_up_reply", kwargs))
        return self.follow_up_result or self.reply_text


def _matches_filter(data: dict[str, Any], field: str, op: str, value: Any) -> bool:
    current = _lookup(data, field)
    if op == "==":
        return current == value
    if op == "<=":
        return current is not None and current <= value
    if op == ">=":
        return current is not None and current >= value
    raise NotImplementedError(f"Unsupported operator: {op}")


def _lookup(data: dict[str, Any], field: str) -> Any:
    current: Any = data
    for part in field.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(data)
    for key, value in list(normalized.items()):
        if isinstance(value, dict):
            normalized[key] = _normalize_payload(value)
        elif isinstance(value, list):
            normalized[key] = [deepcopy(item) for item in value]
        elif value.__class__.__name__ == "Sentinel":
            normalized[key] = utcnow()
    return normalized
