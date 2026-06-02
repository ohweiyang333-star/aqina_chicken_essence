"""Meta Conversions API event helpers."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
import time
from typing import Any

from app.core.config import settings
from app.services.meta_client import get_meta_client

logger = logging.getLogger(__name__)

ALLOWED_LANDING_VERSIONS = {"offer_reset", "home", "v2", "v3", "v4"}
ALLOWED_LANGUAGES = {"en", "zh"}


@dataclass(frozen=True)
class MetaAddToCartEventInput:
    """Normalized AddToCart data for Meta CAPI."""

    order_id: str
    product_id: str
    product_name: str
    value: float
    customer_name: str
    customer_phone: str
    currency: str = "SGD"
    quantity: int = 1
    marketing_consent: str | None = None
    event_id: str | None = None
    event_source_url: str | None = None
    page_path: str | None = None
    landing_version: str | None = None
    language: str | None = None
    fbp: str | None = None
    fbc: str | None = None
    client_ip_address: str | None = None
    client_user_agent: str | None = None


class MetaConversionsService:
    """Build and send Meta Conversions API events without blocking checkout."""

    def __init__(self, meta_client: Any | None = None) -> None:
        self.meta_client = meta_client or get_meta_client()

    def send_add_to_cart(self, event_input: MetaAddToCartEventInput) -> dict[str, Any]:
        """Send the receipt-submitted event as AddToCart to Meta CAPI."""
        event_id = _safe_text(event_input.event_id) or f"{event_input.order_id}_add_to_cart"

        if event_input.marketing_consent != "accepted":
            return {"status": "skipped", "reason": "marketing_consent_missing", "event_id": event_id}

        if not settings.meta_pixel_id or not settings.meta_conversions_access_token:
            return {"status": "skipped", "reason": "meta_conversions_not_configured", "event_id": event_id}

        try:
            event = self._build_add_to_cart_event(event_input, event_id)
            response = self.meta_client.send_conversion_event(
                pixel_id=settings.meta_pixel_id,
                access_token=settings.meta_conversions_access_token,
                events=[event],
                test_event_code=settings.meta_conversions_test_event_code or None,
            )
            return {
                "status": "sent",
                "event_id": event_id,
                "events_received": response.get("events_received"),
                "fbtrace_id": response.get("fbtrace_id"),
            }
        except Exception as exc:  # pragma: no cover - exercised through integration logs
            logger.warning("meta_capi_add_to_cart_failed order_id=%s error=%s", event_input.order_id, exc)
            return {"status": "failed", "event_id": event_id, "error": str(exc)[:300]}

    def _build_add_to_cart_event(
        self,
        event_input: MetaAddToCartEventInput,
        event_id: str,
    ) -> dict[str, Any]:
        page_path = _safe_page_path(event_input.page_path)
        landing_version = _safe_enum(event_input.landing_version, ALLOWED_LANDING_VERSIONS)
        language = _safe_enum(event_input.language, ALLOWED_LANGUAGES)
        value = round(float(event_input.value), 2)
        quantity = max(1, int(event_input.quantity or 1))

        custom_data: dict[str, Any] = {
            "currency": event_input.currency or "SGD",
            "value": value,
            "content_ids": [event_input.product_id],
            "contents": [
                {
                    "id": event_input.product_id,
                    "quantity": quantity,
                    "item_price": value,
                }
            ],
            "content_name": event_input.product_name,
            "content_type": "product",
            "num_items": quantity,
            "order_id": event_input.order_id,
            "page_path": page_path,
        }
        if landing_version:
            custom_data["landing_version"] = landing_version
        if language:
            custom_data["language"] = language

        return {
            "event_name": "AddToCart",
            "event_time": int(time.time()),
            "event_id": event_id,
            "action_source": "website",
            "event_source_url": _event_source_url(event_input.event_source_url, page_path),
            "user_data": self._user_data(event_input),
            "custom_data": custom_data,
        }

    def _user_data(self, event_input: MetaAddToCartEventInput) -> dict[str, Any]:
        phone_hash = _sha256_or_none(_digits_only(event_input.customer_phone))
        external_id = phone_hash
        user_data: dict[str, Any] = {
            "ph": [phone_hash] if phone_hash else None,
            "external_id": [external_id] if external_id else None,
            "client_ip_address": _safe_text(event_input.client_ip_address),
            "client_user_agent": _safe_text(event_input.client_user_agent),
            "fbp": _safe_text(event_input.fbp),
            "fbc": _safe_text(event_input.fbc),
        }

        first_name, last_name = _split_name(event_input.customer_name)
        first_name_hash = _sha256_or_none(first_name)
        last_name_hash = _sha256_or_none(last_name)
        if first_name_hash:
            user_data["fn"] = first_name_hash
        if last_name_hash:
            user_data["ln"] = last_name_hash

        return {key: value for key, value in user_data.items() if value}


def _digits_only(value: str | None) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _sha256_or_none(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _split_name(value: str | None) -> tuple[str | None, str | None]:
    parts = [part for part in str(value or "").strip().split() if part]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[-1]


def _safe_text(value: str | None, max_length: int = 500) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_length]


def _safe_page_path(value: str | None) -> str:
    text = _safe_text(value, max_length=200) or "/"
    if not text.startswith("/"):
        return f"/{text}"
    return text


def _safe_enum(value: str | None, allowed_values: set[str]) -> str | None:
    text = _safe_text(value, max_length=20)
    return text if text in allowed_values else None


def _event_source_url(value: str | None, page_path: str) -> str:
    text = _safe_text(value, max_length=1000)
    if text and (text.startswith("https://") or text.startswith("http://")):
        return text

    return f"{settings.frontend_base_url.rstrip('/')}{page_path}"
