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


class SendWhatsAppTextRequest(BaseModel):
    """Admin payload for sending a free-form WhatsApp message."""

    text: str = Field(..., min_length=1, max_length=4096)


class SendWhatsAppTemplateRequest(BaseModel):
    """Admin payload for sending an approved WhatsApp template."""

    template_name: str = Field(..., min_length=1, max_length=512)
    language_code: str = Field(default="en_US", min_length=2, max_length=32)
    body_variables: list[str] = Field(default_factory=list)


class UpdateWhatsAppAutomationRequest(BaseModel):
    """Admin payload for pausing or resuming automation on a contact."""

    paused: bool
    reason: str | None = Field(default=None, max_length=240)


class UpsertWhatsAppTemplateRequest(BaseModel):
    """Local WhatsApp template mirror used by admin campaign tooling."""

    name: str = Field(..., min_length=1, max_length=512)
    language_code: str = Field(default="en_US", min_length=2, max_length=32)
    category: str = Field(default="MARKETING", min_length=1, max_length=80)
    status: str = Field(default="APPROVED", min_length=1, max_length=80)
    components: list[dict[str, Any]] = Field(default_factory=list)


class WhatsAppCampaignRequest(BaseModel):
    """Draft or preview payload for a compliant WhatsApp template campaign."""

    name: str = Field(..., min_length=1, max_length=160)
    template_name: str = Field(..., min_length=1, max_length=512)
    language_code: str = Field(default="en_US", min_length=2, max_length=32)
    body_variables: list[str] = Field(default_factory=list)
    audience_tags: list[str] = Field(default_factory=list)


class LaunchWhatsAppCampaignRequest(BaseModel):
    """Confirmation payload for launching a prepared campaign."""

    preview_confirmed: bool = False


class ProcessWhatsAppCampaignRecipientRequest(BaseModel):
    """Internal task payload for one campaign recipient."""

    campaign_id: str = Field(..., min_length=1)
    recipient_id: str = Field(..., min_length=1)


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
