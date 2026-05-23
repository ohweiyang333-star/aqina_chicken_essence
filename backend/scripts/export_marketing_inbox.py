"""Export Aqina marketing inbox conversations for offline analysis.

The script is read-only. It uses Firestore's REST API with a short-lived
access token from `gcloud auth print-access-token`, so callers can pin the
Google account without changing the machine-wide gcloud configuration.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import requests


DEFAULT_PROJECT = "aqina-chicken-essence"
DEFAULT_GCLOUD_ACCOUNT = "ohweiyang333@gmail.com"
DEFAULT_DATABASE = "(default)"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "exports" / "inbox-analysis"
SUPPORTED_CHANNELS = {"all", "messenger", "whatsapp"}
SENSITIVE_IDENTIFIER_KEYS = {"phone", "phone_e164", "wa_id", "psid", "email"}

SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "price_or_package": (
        "price",
        "how much",
        "多少钱",
        "价钱",
        "价格",
        "配套",
        "package",
        "pack",
        "盒",
        "$",
    ),
    "delivery": ("delivery", "deliver", "shipping", "运费", "送货", "寄", "邮寄", "免运"),
    "payment": ("pay", "payment", "paynow", "付款", "转账", "bank", "checkout", "下单"),
    "taste": ("taste", "口味", "味道", "腥", "drink", "喝"),
    "pregnancy_or_confinement": (
        "pregnant",
        "pregnancy",
        "confinement",
        "maternity",
        "孕",
        "月子",
        "产后",
        "妈妈",
    ),
    "gift_or_family": ("gift", "family", "parent", "mother", "father", "送", "家人", "长辈", "父母"),
    "trust_or_proof": ("halal", "cert", "认证", "证明", "review", "评价", "real", "真的吗"),
    "human_handoff": ("agent", "human", "staff", "真人", "客服", "人工", "call", "whatsapp"),
    "bot_context_repetition": (
        "already answer",
        "already answered",
        "answer is upstair",
        "answer is above",
        "you already asked",
        "repeat",
        "repetition",
        "已经回答",
        "回答过",
        "上面",
        "重复",
        "又问",
    ),
}


class FirestoreRestClient:
    def __init__(self, *, project: str, database: str, access_token: str) -> None:
        self.project = project
        self.database = database
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{project}/databases/{database}/documents"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    def run_collection_query(
        self,
        collection_id: str,
        *,
        order_field: str | None = None,
        descending: bool = False,
        limit: int | None = None,
        field_equals: tuple[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"structuredQuery": {"from": [{"collectionId": collection_id}]}}
        structured_query = query["structuredQuery"]
        if field_equals is not None:
            field, value = field_equals
            structured_query["where"] = {
                "fieldFilter": {
                    "field": {"fieldPath": field},
                    "op": "EQUAL",
                    "value": {"stringValue": value},
                }
            }
        if order_field:
            structured_query["orderBy"] = [
                {
                    "field": {"fieldPath": order_field},
                    "direction": "DESCENDING" if descending else "ASCENDING",
                }
            ]
        if limit is not None:
            structured_query["limit"] = limit

        response = self.session.post(f"{self.base_url}:runQuery", data=json.dumps(query), timeout=60)
        response.raise_for_status()
        return [decode_document(item["document"]) for item in response.json() if item.get("document")]

    def get_document(self, document_path: str) -> dict[str, Any] | None:
        response = self.session.get(f"{self.base_url}/{document_path}", timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return decode_document(response.json())

    def list_documents(self, collection_path: str, *, order_by: str | None = None, page_size: int = 100) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"pageSize": page_size}
            if order_by:
                params["orderBy"] = order_by
            if page_token:
                params["pageToken"] = page_token
            response = self.session.get(f"{self.base_url}/{collection_path}", params=params, timeout=60)
            if response.status_code == 404:
                return docs
            response.raise_for_status()
            payload = response.json()
            docs.extend(decode_document(doc) for doc in payload.get("documents", []))
            page_token = payload.get("nextPageToken")
            if not page_token:
                return docs


def decode_document(document: dict[str, Any]) -> dict[str, Any]:
    document_path = document.get("name", "").split("/documents/")[-1]
    document_id = document_path.split("/")[-1] if document_path else ""
    decoded = {key: decode_firestore_value(value) for key, value in document.get("fields", {}).items()}
    decoded["_path"] = document_path
    decoded["_id"] = document_id
    return decoded


def decode_firestore_value(value: dict[str, Any]) -> Any:
    if "nullValue" in value:
        return None
    if "stringValue" in value:
        return value["stringValue"]
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "booleanValue" in value:
        return bool(value["booleanValue"])
    if "timestampValue" in value:
        return value["timestampValue"]
    if "mapValue" in value:
        return {
            key: decode_firestore_value(nested)
            for key, nested in value.get("mapValue", {}).get("fields", {}).items()
        }
    if "arrayValue" in value:
        return [decode_firestore_value(item) for item in value.get("arrayValue", {}).get("values", [])]
    if "referenceValue" in value:
        return value["referenceValue"].split("/documents/")[-1]
    if "geoPointValue" in value:
        point = value["geoPointValue"]
        return {"latitude": point.get("latitude"), "longitude": point.get("longitude")}
    if "bytesValue" in value:
        return value["bytesValue"]
    return None


def get_access_token(gcloud_account: str) -> str:
    return subprocess.check_output(
        ["gcloud", "auth", "print-access-token", f"--account={gcloud_account}"],
        text=True,
    ).strip()


def contact_display_name(contact: dict[str, Any]) -> str:
    order_fields = contact.get("order_fields") if isinstance(contact.get("order_fields"), dict) else {}
    profile = contact.get("profile") if isinstance(contact.get("profile"), dict) else {}
    return str(
        order_fields.get("name")
        or profile.get("name")
        or contact.get("name")
        or "Unknown contact"
    )


def mask_identifier(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= 4:
        return "*" * len(text)
    if len(text) <= 8:
        return f"{text[:1]}***{text[-1:]}"
    return f"{text[:3]}***{text[-4:]}"


def maybe_mask_identifiers(contact: dict[str, Any], *, include_sensitive_identifiers: bool) -> dict[str, Any]:
    identifiers = contact.get("identifiers")
    if not isinstance(identifiers, dict):
        return {}
    if include_sensitive_identifiers:
        return dict(identifiers)
    return {
        key: mask_identifier(value) if key in SENSITIVE_IDENTIFIER_KEYS else value
        for key, value in identifiers.items()
    }


def find_order_matches(
    contact_id: str,
    conversation_id: str | None,
    contact: dict[str, Any],
    orders: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    identifiers = contact.get("identifiers") if isinstance(contact.get("identifiers"), dict) else {}
    wa_values = {str(value) for key, value in identifiers.items() if key in {"wa_id", "phone_e164", "phone"} and value}
    matches = []
    for order in orders:
        customer = order.get("customer") if isinstance(order.get("customer"), dict) else {}
        order_whatsapp = str(customer.get("whatsapp") or "")
        if (
            order.get("marketing_contact_id") == contact_id
            or (conversation_id and order.get("conversation_id") == conversation_id)
            or (order_whatsapp and order_whatsapp in wa_values)
        ):
            matches.append(
                {
                    "order_id": order.get("_id"),
                    "created_at": order.get("created_at"),
                    "payment_status": order.get("payment_status"),
                    "order_status": order.get("order_status"),
                    "total_amount": order.get("total_amount"),
                }
            )
    matches.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return matches


def conversation_signals(messages: list[dict[str, Any]]) -> list[str]:
    inbound_text = "\n".join(
        str(message.get("text") or "").lower()
        for message in messages
        if message.get("direction") == "inbound"
    )
    if not inbound_text.strip():
        return ["no_customer_text"]
    signals = [
        signal
        for signal, keywords in SIGNAL_KEYWORDS.items()
        if any(keyword.lower() in inbound_text for keyword in keywords)
    ]
    return signals or ["general_inquiry"]


def summarize_message(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id": message.get("_id"),
        "created_at": message.get("created_at"),
        "direction": message.get("direction"),
        "role": message.get("role"),
        "message_type": message.get("message_type", "text"),
        "delivery_status": message.get("delivery_status"),
        "source": message.get("source"),
        "text": message.get("text") or "",
        "media_url": message.get("media_url"),
        "media_content_type": message.get("media_content_type"),
        "media_filename": message.get("media_filename"),
    }


def build_export(
    client: FirestoreRestClient,
    *,
    channel: str,
    limit: int,
    include_sensitive_identifiers: bool,
    include_orders: bool,
) -> dict[str, Any]:
    if channel not in SUPPORTED_CHANNELS:
        raise ValueError(f"Unsupported channel: {channel}")

    field_equals = None if channel == "all" else ("channel", channel)
    conversations = client.run_collection_query(
        "marketing_conversations",
        order_field="last_message_at",
        descending=True,
        limit=limit * 3 if channel == "all" else limit,
        field_equals=field_equals,
    )

    orders = client.list_documents("orders", order_by="created_at desc") if include_orders else []
    exported_conversations = []
    channel_counts: Counter[str] = Counter()
    total_messages = 0
    with_order_count = 0
    cart_hot_count = 0
    cart_hot_without_order_count = 0
    pending_payment_count = 0
    paid_order_count = 0

    for conversation in conversations:
        conversation_channel = conversation.get("channel")
        if conversation_channel not in {"messenger", "whatsapp"}:
            continue
        if len(exported_conversations) >= limit:
            break

        conversation_id = conversation.get("_id")
        contact_id = conversation.get("contact_id")
        contact = client.get_document(f"marketing_contacts/{contact_id}") if contact_id else None
        contact = contact or {}
        messages = client.list_documents(
            f"marketing_conversations/{conversation_id}/messages",
            order_by="created_at",
        )
        order_matches = find_order_matches(str(contact_id), str(conversation_id), contact, orders) if include_orders else []
        if order_matches:
            with_order_count += 1
        current_tag = contact.get("current_tag")
        is_cart_hot = current_tag == "cart_hot"
        if is_cart_hot:
            cart_hot_count += 1
        cart_hot_without_order = is_cart_hot and not order_matches
        if cart_hot_without_order:
            cart_hot_without_order_count += 1
        if order_matches:
            if any(str(order.get("payment_status") or "") == "paid" for order in order_matches):
                paid_order_count += 1
            if any(str(order.get("payment_status") or "pending") in {"pending", "payment_submitted"} for order in order_matches):
                pending_payment_count += 1

        exported_conversations.append(
            {
                "conversation_id": conversation_id,
                "contact_id": contact_id,
                "channel": conversation_channel,
                "customer_name": contact_display_name(contact),
                "current_tag": current_tag,
                "marketing_status": contact.get("marketing_status"),
                "automation_paused": bool(contact.get("automation_paused")),
                "window_expires_at": contact.get("window_expires_at"),
                "acquisition": contact.get("acquisition") if isinstance(contact.get("acquisition"), dict) else {},
                "identifiers": maybe_mask_identifiers(
                    contact,
                    include_sensitive_identifiers=include_sensitive_identifiers,
                ),
                "has_order": bool(order_matches),
                "orders": order_matches,
                "cart_hot_without_order": cart_hot_without_order,
                "analysis_signals": conversation_signals(messages),
                "message_count": len(messages),
                "messages": [summarize_message(message) for message in messages],
            }
        )
        channel_counts[str(conversation_channel)] += 1
        total_messages += len(messages)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "project": client.project,
            "database": client.database,
            "collections": ["marketing_conversations", "marketing_contacts", "orders"],
        },
        "filters": {
            "channel": channel,
            "limit": limit,
            "include_orders": include_orders,
            "include_sensitive_identifiers": include_sensitive_identifiers,
        },
        "stats": {
            "conversation_count": len(exported_conversations),
            "message_count": total_messages,
            "channel_counts": dict(channel_counts),
            "with_order_count": with_order_count,
            "without_order_count": len(exported_conversations) - with_order_count,
            "cart_hot_count": cart_hot_count,
            "cart_hot_without_order_count": cart_hot_without_order_count,
            "matched_order_count": with_order_count,
            "pending_payment_count": pending_payment_count,
            "paid_order_count": paid_order_count,
        },
        "conversations": exported_conversations,
    }


def resolve_output_path(out: str | None) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if out is None:
        return DEFAULT_OUTPUT_DIR / f"marketing-inbox-export-{timestamp}.json"
    path = Path(out)
    if path.suffix.lower() == ".json":
        return path
    return path / f"marketing-inbox-export-{timestamp}.json"


def write_export(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Aqina marketing inbox conversations for offline analysis.")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help=f"Firestore project ID. Default: {DEFAULT_PROJECT}")
    parser.add_argument("--database", default=DEFAULT_DATABASE, help=f"Firestore database ID. Default: {DEFAULT_DATABASE}")
    parser.add_argument(
        "--gcloud-account",
        default=DEFAULT_GCLOUD_ACCOUNT,
        help=f"gcloud account to use for the read token. Default: {DEFAULT_GCLOUD_ACCOUNT}",
    )
    parser.add_argument("--channel", choices=sorted(SUPPORTED_CHANNELS), default="all")
    parser.add_argument("--limit", type=int, default=100, help="Max supported inbox conversations to export.")
    parser.add_argument("--out", help="Output JSON path or directory. Default: backend/exports/inbox-analysis/")
    parser.add_argument("--skip-orders", action="store_true", help="Do not scan orders for conversion matching.")
    parser.add_argument(
        "--include-sensitive-identifiers",
        action="store_true",
        help="Include full phone/WhatsApp/Messenger identifiers. Default masks them.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    token = get_access_token(args.gcloud_account)
    client = FirestoreRestClient(project=args.project, database=args.database, access_token=token)
    payload = build_export(
        client,
        channel=args.channel,
        limit=args.limit,
        include_sensitive_identifiers=args.include_sensitive_identifiers,
        include_orders=not args.skip_orders,
    )
    output_path = resolve_output_path(args.out)
    write_export(payload, output_path)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "stats": payload["stats"],
                "project": args.project,
                "gcloud_account": args.gcloud_account,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
