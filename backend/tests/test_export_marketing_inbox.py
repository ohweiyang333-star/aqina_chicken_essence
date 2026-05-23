from backend.scripts.export_marketing_inbox import (
    build_export,
    contact_display_name,
    conversation_signals,
    decode_firestore_value,
    find_order_matches,
    mask_identifier,
)


def test_decode_firestore_value_handles_nested_maps_and_arrays():
    value = {
        "mapValue": {
            "fields": {
                "name": {"stringValue": "Alice"},
                "count": {"integerValue": "2"},
                "flags": {
                    "arrayValue": {
                        "values": [
                            {"booleanValue": True},
                            {"nullValue": None},
                        ]
                    }
                },
            }
        }
    }

    assert decode_firestore_value(value) == {"name": "Alice", "count": 2, "flags": [True, None]}


def test_mask_identifier_preserves_only_small_edges():
    assert mask_identifier("+6596265734") == "+65***5734"
    assert mask_identifier("abcd") == "****"
    assert mask_identifier(None) is None


def test_contact_display_name_prefers_order_fields_then_profile():
    assert contact_display_name({"order_fields": {"name": "Order Name"}, "profile": {"name": "Profile Name"}}) == "Order Name"
    assert contact_display_name({"profile": {"name": "Profile Name"}}) == "Profile Name"
    assert contact_display_name({}) == "Unknown contact"


def test_find_order_matches_by_contact_id_or_whatsapp_identifier():
    contact = {"identifiers": {"wa_id": "+6596265734"}}
    orders = [
        {"_id": "order_contact", "marketing_contact_id": "contact_1", "created_at": "2026-05-02"},
        {"_id": "order_conversation", "conversation_id": "conversation_1", "created_at": "2026-05-04"},
        {"_id": "order_wa", "customer": {"whatsapp": "+6596265734"}, "created_at": "2026-05-01"},
        {"_id": "order_other", "customer": {"whatsapp": "+6500000000"}, "created_at": "2026-05-03"},
    ]

    matches = find_order_matches("contact_1", "conversation_1", contact, orders)

    assert [item["order_id"] for item in matches] == ["order_conversation", "order_contact", "order_wa"]


def test_conversation_signals_extracts_customer_blockers():
    messages = [
        {"direction": "outbound", "text": "Here is the package."},
        {"direction": "inbound", "text": "How much is delivery? I want for confinement."},
    ]

    assert conversation_signals(messages) == ["price_or_package", "delivery", "pregnancy_or_confinement"]


def test_conversation_signals_flags_bot_context_repetition():
    messages = [
        {"direction": "outbound", "text": "Should I remind you next month?"},
        {"direction": "inbound", "text": "This have already answer. The answer is upstair."},
    ]

    assert conversation_signals(messages) == ["bot_context_repetition"]


def test_build_export_marks_cart_hot_without_order_and_payment_counts():
    class FakeClient:
        project = "aqina-chicken-essence"
        database = "(default)"

        def run_collection_query(self, collection_id, **kwargs):
            assert collection_id == "marketing_conversations"
            return [
                {
                    "_id": "conv_hot",
                    "contact_id": "contact_hot",
                    "channel": "messenger",
                    "last_message_at": "2026-05-23T00:00:00Z",
                },
                {
                    "_id": "conv_paid",
                    "contact_id": "contact_paid",
                    "channel": "whatsapp",
                    "last_message_at": "2026-05-22T00:00:00Z",
                },
            ]

        def get_document(self, document_path):
            return {
                "marketing_contacts/contact_hot": {
                    "current_tag": "cart_hot",
                    "identifiers": {"psid": "273700003322"},
                },
                "marketing_contacts/contact_paid": {
                    "current_tag": "cart_hot",
                    "identifiers": {"wa_id": "6596265734"},
                },
            }.get(document_path)

        def list_documents(self, collection_path, **kwargs):
            if collection_path == "orders":
                return [
                    {
                        "_id": "order_paid",
                        "conversation_id": "conv_paid",
                        "payment_status": "paid",
                        "order_status": "processing",
                        "total_amount": 75.0,
                        "created_at": "2026-05-22T01:00:00Z",
                    }
                ]
            if collection_path == "marketing_conversations/conv_hot/messages":
                return [
                    {"_id": "msg_hot", "direction": "inbound", "role": "user", "text": "二盒 PayNow 怎么付？"}
                ]
            if collection_path == "marketing_conversations/conv_paid/messages":
                return [
                    {"_id": "msg_paid", "direction": "inbound", "role": "user", "text": "付款截图已发"}
                ]
            return []

    payload = build_export(
        FakeClient(),
        channel="all",
        limit=10,
        include_sensitive_identifiers=False,
        include_orders=True,
    )

    assert payload["stats"]["cart_hot_count"] == 2
    assert payload["stats"]["cart_hot_without_order_count"] == 1
    assert payload["stats"]["matched_order_count"] == 1
    assert payload["stats"]["paid_order_count"] == 1
    assert payload["conversations"][0]["cart_hot_without_order"] is True
    assert payload["conversations"][1]["orders"][0]["payment_status"] == "paid"
