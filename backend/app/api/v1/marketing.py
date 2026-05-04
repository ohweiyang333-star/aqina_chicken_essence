"""Marketing automation webhook and internal task endpoints."""
from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse

from app.api.deps import Admin, DB
from app.core.config import settings
from app.models.chatbot import CheckoutSessionResponse
from app.models.marketing import (
    LaunchWhatsAppCampaignRequest,
    ProcessWhatsAppCampaignRecipientRequest,
    ProcessFollowUpJobRequest,
    ProcessMarketingEventRequest,
    ReconcileDueJobsRequest,
    SendWhatsAppTemplateRequest,
    SendWhatsAppTextRequest,
    UpdateWhatsAppAutomationRequest,
    UpsertWhatsAppTemplateRequest,
    WhatsAppCampaignRequest,
)
from app.services.chatbot_settings import ChatbotSettingsService
from app.services.follow_up import FollowUpEngine
from app.services.gemini_service import get_gemini_service
from app.services.marketing_contacts import MarketingContactService
from app.services.marketing_orchestrator import MarketingAutomationOrchestrator
from app.services.meta_client import get_meta_client
from app.services.task_queue import get_task_queue_service
from app.services.whatsapp_console import WhatsAppConsoleService

router = APIRouter(prefix="/marketing", tags=["Marketing"])


@router.api_route("/webhooks/facebook", methods=["GET", "HEAD"], response_class=PlainTextResponse)
@router.api_route(
    "/webhooks/facebook/",
    methods=["GET", "HEAD"],
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def verify_facebook_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Verify the Facebook / Messenger webhook subscription challenge."""
    return _verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@router.api_route("/webhooks/whatsapp", methods=["GET", "HEAD"], response_class=PlainTextResponse)
@router.api_route(
    "/webhooks/whatsapp/",
    methods=["GET", "HEAD"],
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Verify the WhatsApp webhook subscription challenge."""
    return _verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@router.post("/webhooks/facebook", status_code=status.HTTP_202_ACCEPTED)
async def receive_facebook_webhook(
    request: Request,
    db: DB,
    x_hub_signature_256: str | None = Header(default=None),
):
    """Receive Facebook page, comment, and Messenger webhook events."""
    payload = await _parse_and_verify_request(request, x_hub_signature_256)
    orchestrator = _build_orchestrator(db)
    accepted = orchestrator.ingest_facebook_webhook(payload)
    return {"status": "accepted", "accepted_events": accepted}


@router.post("/webhooks/whatsapp", status_code=status.HTTP_202_ACCEPTED)
async def receive_whatsapp_webhook(
    request: Request,
    db: DB,
    x_hub_signature_256: str | None = Header(default=None),
):
    """Receive WhatsApp webhook events."""
    payload = await _parse_and_verify_request(request, x_hub_signature_256)
    orchestrator = _build_orchestrator(db)
    accepted = orchestrator.ingest_whatsapp_webhook(payload)
    return {"status": "accepted", "accepted_events": accepted}


@router.post("/tasks/process-comment-event")
async def process_comment_event(
    body: ProcessMarketingEventRequest,
    db: DB,
    x_internal_token: str | None = Header(default=None),
):
    """Internal task endpoint for processing comment automation."""
    _verify_internal_token(x_internal_token)
    orchestrator = _build_orchestrator(db)
    return orchestrator.process_comment_event(body.event_id)


@router.post("/tasks/process-inbound-message")
async def process_inbound_message(
    body: ProcessMarketingEventRequest,
    db: DB,
    x_internal_token: str | None = Header(default=None),
):
    """Internal task endpoint for Gemini chatbot responses."""
    _verify_internal_token(x_internal_token)
    orchestrator = _build_orchestrator(db)
    return orchestrator.process_inbound_message(body.event_id)


@router.post("/tasks/process-follow-up-job")
async def process_follow_up_job(
    body: ProcessFollowUpJobRequest,
    db: DB,
    x_internal_token: str | None = Header(default=None),
):
    """Internal task endpoint for delayed CRM follow-up jobs."""
    _verify_internal_token(x_internal_token)
    engine = _build_follow_up_engine(db)
    return engine.process_follow_up_job(body.job_id)


@router.post("/tasks/reconcile-due-jobs")
async def reconcile_due_jobs(
    body: ReconcileDueJobsRequest,
    db: DB,
    x_internal_token: str | None = Header(default=None),
):
    """Internal task endpoint for Cloud Scheduler follow-up reconciliation."""
    _verify_internal_token(x_internal_token)
    engine = _build_follow_up_engine(db)
    return engine.reconcile_due_jobs(limit=body.limit)


@router.post("/tasks/process-whatsapp-campaign-recipient")
async def process_whatsapp_campaign_recipient(
    body: ProcessWhatsAppCampaignRecipientRequest,
    db: DB,
    x_internal_token: str | None = Header(default=None),
):
    """Internal task endpoint for one WhatsApp campaign recipient."""
    _verify_internal_token(x_internal_token)
    service = _build_whatsapp_console(db)
    return service.process_campaign_recipient(body.campaign_id, body.recipient_id)


@router.get("/facebook/comment-events")
async def list_facebook_comment_events(db: DB, admin: Admin, limit: int = Query(default=20, ge=1, le=50)):
    """List recent Facebook comment-to-Messenger automation events for the CRM console."""
    del admin
    docs = (
        db.collection("marketing_events")
        .order_by("received_at", direction="DESCENDING")
        .limit(150)
        .stream()
    )
    items = []
    for doc in docs:
        row = doc.to_dict()
        if row.get("event_type") != "facebook_comment_created":
            continue
        payload = row.get("payload", {})
        items.append(
            {
                "event_id": doc.id,
                "status": row.get("status", ""),
                "comment_id": payload.get("comment_id", ""),
                "post_id": payload.get("post_id", ""),
                "comment_text": payload.get("comment_text", ""),
                "from_name": payload.get("from_name") or "",
                "matched_keyword": row.get("matched_keyword") or payload.get("matched_keyword") or "",
                "public_reply_status": row.get("public_reply_status") or "pending",
                "private_reply_status": row.get("private_reply_status") or "pending",
                "reply_errors": row.get("reply_errors") or {},
                "received_at": row.get("received_at"),
                "processed_at": row.get("processed_at"),
            }
        )
        if len(items) >= limit:
            break
    return {"items": items}


@router.get("/whatsapp/health")
async def whatsapp_health(db: DB, admin: Admin):
    """Return WhatsApp Cloud API configuration health for the admin console."""
    del admin
    return _build_whatsapp_console(db).health()


@router.get("/whatsapp/conversations")
async def list_whatsapp_conversations(db: DB, admin: Admin, limit: int = Query(default=50, ge=1, le=100)):
    """List WhatsApp conversations for the admin inbox."""
    del admin
    return _build_whatsapp_console(db).list_conversations(limit=limit)


@router.get("/whatsapp/conversations/{conversation_id}")
async def get_whatsapp_conversation(conversation_id: str, db: DB, admin: Admin):
    """Return a WhatsApp conversation with messages and customer context."""
    del admin
    try:
        return _build_whatsapp_console(db).get_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/whatsapp/conversations/{conversation_id}/messages")
async def send_whatsapp_manual_message(
    conversation_id: str,
    body: SendWhatsAppTextRequest,
    db: DB,
    admin: Admin,
):
    """Send a free-form WhatsApp reply inside the active customer service window."""
    try:
        return _build_whatsapp_console(db).send_manual_text(conversation_id, body.text, admin)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/whatsapp/conversations/{conversation_id}/templates")
async def send_whatsapp_template_message(
    conversation_id: str,
    body: SendWhatsAppTemplateRequest,
    db: DB,
    admin: Admin,
):
    """Send an approved WhatsApp template from the admin inbox."""
    try:
        return _build_whatsapp_console(db).send_template(
            conversation_id,
            template_name=body.template_name,
            language_code=body.language_code,
            body_variables=body.body_variables,
            admin=admin,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/whatsapp/conversations/{conversation_id}/automation")
async def update_whatsapp_automation(
    conversation_id: str,
    body: UpdateWhatsAppAutomationRequest,
    db: DB,
    admin: Admin,
):
    """Pause or resume chatbot automation for a WhatsApp conversation."""
    del admin
    try:
        return _build_whatsapp_console(db).update_automation(
            conversation_id,
            paused=body.paused,
            reason=body.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/whatsapp/templates")
async def list_whatsapp_templates(db: DB, admin: Admin):
    """List locally mirrored WhatsApp templates."""
    del admin
    return _build_whatsapp_console(db).list_templates()


@router.post("/whatsapp/templates")
async def upsert_whatsapp_template(body: UpsertWhatsAppTemplateRequest, db: DB, admin: Admin):
    """Save a local WhatsApp template mirror for inbox and campaigns."""
    del admin
    return _build_whatsapp_console(db).upsert_template(body.model_dump())


@router.post("/whatsapp/templates/sync")
async def sync_whatsapp_templates(db: DB, admin: Admin):
    """Sync WhatsApp templates from Meta into the local admin console."""
    del admin
    try:
        return _build_whatsapp_console(db).sync_templates()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/whatsapp/campaigns")
async def list_whatsapp_campaigns(db: DB, admin: Admin):
    """List WhatsApp broadcast campaigns."""
    del admin
    return _build_whatsapp_console(db).list_campaigns()


@router.post("/whatsapp/campaigns/preview")
async def preview_whatsapp_campaign(body: WhatsAppCampaignRequest, db: DB, admin: Admin):
    """Preview a compliant template campaign audience before launch."""
    del admin
    try:
        return _build_whatsapp_console(db).preview_campaign(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/whatsapp/campaigns", status_code=status.HTTP_201_CREATED)
async def create_whatsapp_campaign(body: WhatsAppCampaignRequest, db: DB, admin: Admin):
    """Create a WhatsApp template campaign draft."""
    try:
        return _build_whatsapp_console(db).create_campaign(body, admin)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/whatsapp/campaigns/{campaign_id}")
async def get_whatsapp_campaign(campaign_id: str, db: DB, admin: Admin):
    """Get a campaign and its recipient statuses."""
    del admin
    try:
        return _build_whatsapp_console(db).get_campaign(campaign_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/whatsapp/campaigns/{campaign_id}/launch")
async def launch_whatsapp_campaign(
    campaign_id: str,
    body: LaunchWhatsAppCampaignRequest,
    db: DB,
    admin: Admin,
):
    """Queue a WhatsApp campaign after an admin confirms the preview."""
    del admin
    try:
        return _build_whatsapp_console(db).launch_campaign(
            campaign_id,
            preview_confirmed=body.preview_confirmed,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/whatsapp/campaigns/{campaign_id}/pause")
async def pause_whatsapp_campaign(campaign_id: str, db: DB, admin: Admin):
    """Pause a queued or sending WhatsApp campaign."""
    del admin
    try:
        return _build_whatsapp_console(db).pause_campaign(campaign_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/whatsapp/campaigns/{campaign_id}/cancel")
async def cancel_whatsapp_campaign(campaign_id: str, db: DB, admin: Admin):
    """Cancel a WhatsApp campaign."""
    del admin
    try:
        return _build_whatsapp_console(db).cancel_campaign(campaign_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/checkout/{token}", response_model=CheckoutSessionResponse)
async def get_marketing_checkout(token: str, db: DB):
    """Public PayNow checkout payload used by the tokenized checkout page."""
    settings_service = ChatbotSettingsService(db)
    runtime_settings = settings_service.get_settings(persist_migration=False)
    sessions = list(
        db.collection("marketing_checkout_sessions")
        .where("token", "==", token)
        .limit(1)
        .stream()
    )
    if not sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout session not found")

    session_doc = sessions[0]
    session = session_doc.to_dict()
    if session.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout session not active")

    order_snapshot = db.collection("orders").document(session["order_id"]).get()
    if not order_snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    order = order_snapshot.to_dict()
    customer = order.get("customer", {})
    return {
        "order_id": session["order_id"],
        "payment_method": order.get("payment_method", "paynow"),
        "payment_status": order.get("payment_status", "pending"),
        "order_status": order.get("order_status", "pending"),
        "total_amount": order.get("total_amount", 0),
        "customer_name": customer.get("name", ""),
        "customer_whatsapp": customer.get("whatsapp", ""),
        "delivery_address": customer.get("address", ""),
        "items": order.get("items", []),
        "paynow": runtime_settings.get("payment", {}).get("paynow", {}),
        "checkout_url": session.get("checkout_url", ""),
        "package_code": session.get("package_code"),
    }


@router.get("/escalations")
async def list_escalations(db: DB, admin: Admin):
    """List escalation queue for the admin UI."""
    del admin
    docs = (
        db.collection("marketing_escalations")
        .order_by("created_at", direction="DESCENDING")
        .stream()
    )
    results = []
    for doc in docs:
        row = doc.to_dict()
        row["escalation_id"] = doc.id
        results.append(row)
    return {"items": results}


@router.post("/escalations/{escalation_id}/acknowledge")
async def acknowledge_escalation(escalation_id: str, db: DB, admin: Admin):
    """Mark an escalation as acknowledged by staff."""
    del admin
    ref = db.collection("marketing_escalations").document(escalation_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    ref.set({"status": "acknowledged", "updated_at": _now()}, merge=True)
    return {"status": "acknowledged"}


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_escalation(escalation_id: str, db: DB, admin: Admin):
    """Resolve an escalation and optionally resume automation."""
    del admin
    ref = db.collection("marketing_escalations").document(escalation_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    row = snapshot.to_dict()
    contact_service = MarketingContactService(db)
    contact_service.resume_automation(row["contact_id"])
    ref.set({"status": "resolved", "resolved_at": _now(), "updated_at": _now()}, merge=True)
    return {"status": "resolved"}


def _build_orchestrator(db):
    contact_service = MarketingContactService(db)
    follow_up_engine = _build_follow_up_engine(db, contact_service=contact_service)
    return MarketingAutomationOrchestrator(
        db=db,
        task_queue=get_task_queue_service(),
        contact_service=contact_service,
        follow_up_engine=follow_up_engine,
        meta_client=get_meta_client(),
        gemini_service=get_gemini_service(),
    )


def _build_follow_up_engine(db, contact_service: MarketingContactService | None = None) -> FollowUpEngine:
    return FollowUpEngine(
        db=db,
        task_queue=get_task_queue_service(),
        contact_service=contact_service or MarketingContactService(db),
        meta_client=get_meta_client(),
        gemini_service=get_gemini_service(),
    )


def _build_whatsapp_console(db) -> WhatsAppConsoleService:
    return WhatsAppConsoleService(
        db=db,
        task_queue=get_task_queue_service(),
        contact_service=MarketingContactService(db),
        meta_client=get_meta_client(),
    )


async def _parse_and_verify_request(request: Request, signature: str | None) -> dict:
    raw_body = await request.body()
    meta_client = get_meta_client()
    if not meta_client.verify_signature(raw_body, signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")
    try:
        return json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc


def _verify_webhook(mode: str | None, verify_token: str | None, challenge: str | None) -> Response:
    if mode != "subscribe" or verify_token != settings.meta_verify_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verify token")
    return PlainTextResponse(challenge or "")


def _verify_internal_token(token: str | None) -> None:
    if not settings.internal_task_secret or token != settings.internal_task_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")


def _now():
    from app.services.marketing_utils import utcnow

    return utcnow()
