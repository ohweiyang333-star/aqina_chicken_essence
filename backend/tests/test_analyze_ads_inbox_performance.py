from collections import Counter
from pathlib import Path
import subprocess
import sys

from backend.scripts.analyze_ads_inbox_performance import (
    aggregate_ads_by_name,
    count_inbox_signals,
    parse_decimal,
    result_type,
    summarize_inbox_conversion,
    summarize_by_result_type,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_parse_decimal_handles_blank_commas_and_percent():
    assert parse_decimal("") == 0.0
    assert parse_decimal(None) == 0.0
    assert parse_decimal("1,234.50") == 1234.5
    assert parse_decimal("2.5%") == 2.5


def test_result_type_maps_meta_indicators():
    assert result_type({"Result indicator": "actions:onsite_conversion.messaging_conversation_started_7d"}) == "messaging"
    assert result_type({"Result indicator": "actions:omni_landing_page_view"}) == "landing_page_view"
    assert result_type({"Result indicator": "actions:post_engagement"}) == "post_engagement"
    assert result_type({"Result indicator": ""}) == "no_reported_result"


def test_summarize_by_result_type_totals_spend_and_results():
    rows = [
        {
            "Result indicator": "actions:onsite_conversion.messaging_conversation_started_7d",
            "Results": "2",
            "Amount spent (MYR)": "20",
            "Reach": "100",
            "Impressions": "200",
        },
        {
            "Result indicator": "",
            "Results": "",
            "Amount spent (MYR)": "5.50",
            "Reach": "10",
            "Impressions": "20",
        },
    ]

    summary = summarize_by_result_type(rows)

    assert summary["messaging"]["results"] == 2
    assert summary["messaging"]["spend"] == 20
    assert summary["no_reported_result"]["spend"] == 5.5


def test_aggregate_ads_by_name_groups_only_requested_kind():
    rows = [
        {
            "Ad name": "Offer A",
            "Result indicator": "actions:onsite_conversion.messaging_conversation_started_7d",
            "Results": "2",
            "Amount spent (MYR)": "30",
            "Link clicks": "5",
            "Reach": "100",
            "Impressions": "200",
        },
        {
            "Ad name": "Offer A",
            "Result indicator": "actions:onsite_conversion.messaging_conversation_started_7d",
            "Results": "1",
            "Amount spent (MYR)": "9",
            "Link clicks": "2",
            "Reach": "50",
            "Impressions": "100",
        },
        {
            "Ad name": "Offer A",
            "Result indicator": "actions:omni_landing_page_view",
            "Results": "10",
            "Amount spent (MYR)": "4",
            "Link clicks": "12",
            "Reach": "70",
            "Impressions": "80",
        },
    ]

    grouped = aggregate_ads_by_name(rows, kind="messaging")

    assert grouped == [
        {
            "name": "Offer A",
            "results": 3.0,
            "spend": 39.0,
            "link_clicks": 7.0,
            "reach": 150.0,
            "impressions": 300.0,
            "rows": 2,
        }
    ]


def test_count_inbox_signals_counts_all_conversation_labels():
    inbox = {
        "conversations": [
            {"analysis_signals": ["price_or_package", "delivery"]},
            {"analysis_signals": ["price_or_package"]},
            {"analysis_signals": []},
        ]
    }

    assert count_inbox_signals(inbox) == Counter({"price_or_package": 2, "delivery": 1})


def test_summarize_inbox_conversion_prefers_export_stats_and_falls_back_to_rows():
    inbox = {
        "stats": {
            "conversation_count": 10,
            "cart_hot_count": 3,
            "cart_hot_without_order_count": 1,
            "matched_order_count": 2,
            "pending_payment_count": 1,
            "paid_order_count": 1,
        },
        "conversations": [
            {"current_tag": "cart_hot", "cart_hot_without_order": True, "orders": []},
        ],
    }

    assert summarize_inbox_conversion(inbox) == {
        "conversation_count": 10,
        "cart_hot_count": 3,
        "cart_hot_without_order_count": 1,
        "matched_order_count": 2,
        "pending_payment_count": 1,
        "paid_order_count": 1,
    }

    fallback = summarize_inbox_conversion(
        {
            "conversations": [
                {"current_tag": "cart_hot", "cart_hot_without_order": True, "orders": []},
                {
                    "current_tag": "cart_hot",
                    "orders": [{"payment_status": "pending"}, {"payment_status": "paid"}],
                },
            ]
        }
    )

    assert fallback["conversation_count"] == 2
    assert fallback["cart_hot_count"] == 2
    assert fallback["cart_hot_without_order_count"] == 1
    assert fallback["matched_order_count"] == 1
    assert fallback["pending_payment_count"] == 1
    assert fallback["paid_order_count"] == 1


def test_run_conversion_report_entrypoint_can_show_help():
    completed = subprocess.run(
        [sys.executable, "backend/scripts/run_conversion_report.py", "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Run Aqina weekly conversion report" in completed.stdout
