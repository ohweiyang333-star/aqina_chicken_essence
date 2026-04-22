"""Models for marketing automation routes and services."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProcessMarketingEventRequest(BaseModel):
    """Payload for processing a queued marketing event."""

    event_id: str = Field(..., min_length=1)


class ProcessFollowUpJobRequest(BaseModel):
    """Payload for processing a queued follow-up job."""

    job_id: str = Field(..., min_length=1)


class ReconcileDueJobsRequest(BaseModel):
    """Payload for reconciling scheduled jobs."""

    limit: int = Field(default=100, ge=1, le=500)


class NormalizedMarketingEvent(BaseModel):
    """Internal normalized event shape written to Firestore."""

    provider: Literal["meta"]
    channel: Literal["facebook", "messenger", "whatsapp"]
    event_type: str
    dedupe_key: str
    occurred_at: datetime
    contact_id: str | None = None
    conversation_id: str | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)

