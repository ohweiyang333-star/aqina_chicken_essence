"""Analyze Meta ads exports against Aqina inbox conversion data.

The script is read-only. It expects CSV exports from Ads Manager and the JSON
created by `export_marketing_inbox.py`, then writes a Chinese Markdown report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date
import json
from pathlib import Path
from typing import Any


DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[1] / "exports"
DEFAULT_ADS_DIR = DEFAULT_EXPORT_DIR / "ads-analysis"
DEFAULT_INBOX_DIR = DEFAULT_EXPORT_DIR / "inbox-analysis"


def parse_decimal(value: Any) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text or text in {"-", "--", "N/A"}:
        return 0.0
    if text.endswith("%"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return 0.0


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_type(row: dict[str, Any]) -> str:
    indicator = str(row.get("Result indicator") or "")
    if "messaging_conversation" in indicator:
        return "messaging"
    if "landing_page_view" in indicator:
        return "landing_page_view"
    if "post_engagement" in indicator:
        return "post_engagement"
    if indicator:
        return "other"
    return "no_reported_result"


def summarize_by_result_type(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for row in rows:
        kind = result_type(row)
        bucket = summary.setdefault(kind, {"results": 0.0, "spend": 0.0, "reach": 0.0, "impressions": 0.0})
        bucket["results"] += parse_decimal(row.get("Results"))
        bucket["spend"] += parse_decimal(row.get("Amount spent (MYR)"))
        bucket["reach"] += parse_decimal(row.get("Reach"))
        bucket["impressions"] += parse_decimal(row.get("Impressions"))
    return summary


def aggregate_ads_by_name(rows: list[dict[str, Any]], *, kind: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        if result_type(row) != kind:
            continue
        name = str(row.get("Ad name") or "Unnamed ad")
        bucket = grouped.setdefault(
            name,
            {
                "name": name,
                "results": 0.0,
                "spend": 0.0,
                "link_clicks": 0.0,
                "reach": 0.0,
                "impressions": 0.0,
                "rows": 0,
            },
        )
        bucket["results"] += parse_decimal(row.get("Results"))
        bucket["spend"] += parse_decimal(row.get("Amount spent (MYR)"))
        bucket["link_clicks"] += parse_decimal(row.get("Link clicks"))
        bucket["reach"] += parse_decimal(row.get("Reach"))
        bucket["impressions"] += parse_decimal(row.get("Impressions"))
        bucket["rows"] += 1
    return sorted(
        grouped.values(),
        key=lambda item: (-float(item["results"]), float(item["spend"]), str(item["name"])),
    )


def count_inbox_signals(inbox: dict[str, Any]) -> Counter[str]:
    signals: Counter[str] = Counter()
    for conversation in inbox.get("conversations", []):
        signals.update(conversation.get("analysis_signals") or [])
    return signals


def count_signal_combinations(inbox: dict[str, Any]) -> Counter[tuple[str, ...]]:
    combinations: Counter[tuple[str, ...]] = Counter()
    for conversation in inbox.get("conversations", []):
        combination = tuple(sorted(conversation.get("analysis_signals") or []))
        combinations[combination] += 1
    return combinations


def summarize_inbox_conversion(inbox: dict[str, Any]) -> dict[str, int]:
    stats = inbox.get("stats") if isinstance(inbox.get("stats"), dict) else {}
    keys = [
        "conversation_count",
        "cart_hot_count",
        "cart_hot_without_order_count",
        "matched_order_count",
        "pending_payment_count",
        "paid_order_count",
    ]
    if any(key in stats for key in keys[1:]):
        return {key: int(stats.get(key) or 0) for key in keys}

    conversations = inbox.get("conversations", []) if isinstance(inbox.get("conversations"), list) else []
    cart_hot_count = 0
    cart_hot_without_order_count = 0
    matched_order_count = 0
    pending_payment_count = 0
    paid_order_count = 0
    for conversation in conversations:
        orders = conversation.get("orders") if isinstance(conversation, dict) else []
        orders = orders if isinstance(orders, list) else []
        is_cart_hot = conversation.get("current_tag") == "cart_hot" if isinstance(conversation, dict) else False
        if is_cart_hot:
            cart_hot_count += 1
        if orders:
            matched_order_count += 1
            statuses = {str(order.get("payment_status") or "pending") for order in orders if isinstance(order, dict)}
            if "paid" in statuses:
                paid_order_count += 1
            if statuses & {"pending", "payment_submitted"}:
                pending_payment_count += 1
        elif is_cart_hot or (isinstance(conversation, dict) and conversation.get("cart_hot_without_order")):
            cart_hot_without_order_count += 1
    return {
        "conversation_count": int(stats.get("conversation_count") or len(conversations)),
        "cart_hot_count": cart_hot_count,
        "cart_hot_without_order_count": cart_hot_without_order_count,
        "matched_order_count": matched_order_count,
        "pending_payment_count": pending_payment_count,
        "paid_order_count": paid_order_count,
    }


def rm(value: float) -> str:
    return f"RM{value:,.2f}"


def whole(value: float) -> str:
    return f"{int(round(value)):,}"


def cost_per(spend: float, results: float) -> str:
    if results <= 0:
        return "-"
    return rm(spend / results)


def rate(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return "-"
    return f"{numerator / denominator * 100:.1f}%"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_没有可用数据。_"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def latest_matching_file(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def default_output_path() -> Path:
    return DEFAULT_ADS_DIR / f"aqina-ads-inbox-performance-report-{date.today().isoformat()}.md"


def build_report(
    *,
    campaigns_path: Path,
    adsets_path: Path,
    ads_path: Path,
    inbox_path: Path,
    report_date: date | None = None,
) -> str:
    report_date = report_date or date.today()
    campaigns = load_csv(campaigns_path)
    adsets = load_csv(adsets_path)
    ads = load_csv(ads_path)
    inbox = load_json(inbox_path)

    campaign_summary = summarize_by_result_type(campaigns)
    ad_summary = summarize_by_result_type(ads)
    inbox_stats = inbox.get("stats", {})
    conversion = summarize_inbox_conversion(inbox)
    signals = count_inbox_signals(inbox)
    signal_combinations = count_signal_combinations(inbox)

    total_spend = sum(parse_decimal(row.get("Amount spent (MYR)")) for row in campaigns)
    messaging = campaign_summary.get("messaging", {})
    traffic = campaign_summary.get("landing_page_view", {})
    engagement = campaign_summary.get("post_engagement", {})
    no_result_spend = ad_summary.get("no_reported_result", {}).get("spend", 0.0)

    messaging_results = messaging.get("results", 0.0)
    messaging_spend = messaging.get("spend", 0.0)
    inbox_conversations = float(inbox_stats.get("conversation_count") or 0)
    matched_orders = float(conversion["matched_order_count"])

    adset_rows = []
    for row in sorted(
        adsets,
        key=lambda item: (
            result_type(item) != "messaging",
            -parse_decimal(item.get("Results")),
            parse_decimal(item.get("Cost per results")),
        ),
    ):
        kind = result_type(row)
        result_label = {
            "messaging": "Messaging conversation",
            "landing_page_view": "Landing page view",
            "post_engagement": "Post engagement",
            "no_reported_result": "No reported result",
        }.get(kind, kind)
        adset_rows.append(
            [
                str(row.get("Ad set name") or ""),
                str(row.get("Ad set delivery") or ""),
                result_label,
                whole(parse_decimal(row.get("Results"))),
                rm(parse_decimal(row.get("Amount spent (MYR)"))),
                cost_per(parse_decimal(row.get("Amount spent (MYR)")), parse_decimal(row.get("Results"))),
            ]
        )

    top_messaging_ads = aggregate_ads_by_name(ads, kind="messaging")[:10]
    top_messaging_ad_rows = [
        [
            str(item["name"]),
            whole(float(item["results"])),
            rm(float(item["spend"])),
            cost_per(float(item["spend"]), float(item["results"])),
            whole(float(item["link_clicks"])),
        ]
        for item in top_messaging_ads
    ]

    top_lpv_ads = aggregate_ads_by_name(ads, kind="landing_page_view")[:5]
    top_lpv_ad_rows = [
        [
            str(item["name"]),
            whole(float(item["results"])),
            rm(float(item["spend"])),
            cost_per(float(item["spend"]), float(item["results"])),
            whole(float(item["link_clicks"])),
        ]
        for item in top_lpv_ads
    ]

    zero_result_rows = sorted(
        [row for row in ads if result_type(row) == "no_reported_result" and parse_decimal(row.get("Amount spent (MYR)")) > 0],
        key=lambda item: -parse_decimal(item.get("Amount spent (MYR)")),
    )[:8]
    zero_result_table_rows = [
        [
            str(row.get("Ad name") or ""),
            str(row.get("Ad delivery") or ""),
            rm(parse_decimal(row.get("Amount spent (MYR)"))),
            whole(parse_decimal(row.get("Reach"))),
            whole(parse_decimal(row.get("Impressions"))),
        ]
        for row in zero_result_rows
    ]

    signal_rows = [
        [label, whole(float(count)), rate(float(count), inbox_conversations)]
        for label, count in signals.most_common()
    ]
    combination_rows = [
        [" + ".join(combo) if combo else "no_signal", whole(float(count))]
        for combo, count in signal_combinations.most_common(8)
    ]

    tracking_caveat = (
        "这里的 order conversion 是 `chat-to-order matched conversion`，不是完整商业 ROAS。"
        f"目前有 {conversion['matched_order_count']} 个 inbox conversation 匹配到订单；"
        "若旧订单没有带回 `marketing_contact_id`、`conversation_id`、ad id 或 UTM，"
        "仍可能低估真实成交，所以这份报告先用于优化广告和客服流程，不应直接当成最终 CPA。"
    )

    return f"""# Aqina 广告 + Inbox 转化分析 - {report_date.isoformat()}

数据范围：Ads Manager `23 Apr 2026 - 22 May 2026`，Inbox export `{inbox.get("exported_at", "")}`

数据来源：
- Campaign CSV: `{campaigns_path}`
- Ad set CSV: `{adsets_path}`
- Ads CSV: `{ads_path}`
- Inbox JSON: `{inbox_path}`

## 1. 总览

- 总广告花费：{rm(total_spend)}
- Messaging campaign：{whole(messaging_results)} 个 conversation，花费 {rm(messaging_spend)}，平均 {cost_per(messaging_spend, messaging_results)} / conversation
- Traffic campaign：{whole(traffic.get("results", 0.0))} 个 landing page view，花费 {rm(traffic.get("spend", 0.0))}，平均 {cost_per(traffic.get("spend", 0.0), traffic.get("results", 0.0))} / LPV
- Engagement campaign：{whole(engagement.get("results", 0.0))} 个 post engagement，花费 {rm(engagement.get("spend", 0.0))}，平均 {cost_per(engagement.get("spend", 0.0), engagement.get("results", 0.0))} / engagement
- Inbox 导出：{whole(inbox_conversations)} 个对话，{whole(float(inbox_stats.get("message_count") or 0))} 条消息，Messenger {inbox_stats.get("channel_counts", {}).get("messenger", 0)}，WhatsApp {inbox_stats.get("channel_counts", {}).get("whatsapp", 0)}
- Cart hot：{whole(float(conversion["cart_hot_count"]))} 个；cart hot 但未成单：{whole(float(conversion["cart_hot_without_order_count"]))}
- 已匹配订单：{whole(matched_orders)} 个；待付款/待核对：{whole(float(conversion["pending_payment_count"]))} 个；已付款：{whole(float(conversion["paid_order_count"]))} 个；未匹配对话：{whole(float(inbox_stats.get("without_order_count") or 0))}
- Ads level 有 {rm(no_result_spend)} 花费没有对应 reported result，代表有一批素材消耗了预算但没有产生系统记录的目标动作。

重要 caveat：{tracking_caveat}

## 2. 核心判断

广告不是完全无效。Ads Manager 已经带来 42 个 messaging conversations，Inbox 也实际看到 49 个近期对话。问题主要出在两段：

1. **买家意图没有被快速收口。** 客户问价格、配送、付款、味道和包装时，回复流程经常还停留在解释或诊断，没有立刻给出清楚购买路径。
2. **广告目标和成交目标没有完全对齐。** Engagement 很便宜，但它证明的是互动，不是购买；Traffic 能带 LPV，但没有看到稳定的下单归因；Messaging 最接近成交，但成本需要靠更强 offer、受众和客服话术压低。

## 3. Campaign 层表现

| 目标 | 结果 | 花费 | 平均成本 | 这代表什么 |
| --- | ---: | ---: | ---: | --- |
| Messaging | {whole(messaging_results)} conversations | {rm(messaging_spend)} | {cost_per(messaging_spend, messaging_results)} | 有真实询问，但 chat-to-order 没有闭环 |
| Traffic | {whole(traffic.get("results", 0.0))} LPV | {rm(traffic.get("spend", 0.0))} | {cost_per(traffic.get("spend", 0.0), traffic.get("results", 0.0))} | 能便宜带人进站，下一步要做 retargeting 和 checkout tracking |
| Engagement | {whole(engagement.get("results", 0.0))} engagements | {rm(engagement.get("spend", 0.0))} | {cost_per(engagement.get("spend", 0.0), engagement.get("results", 0.0))} | 可做社交证明和再营销池，不应该当主要成交指标 |

## 4. Ad Set 层表现

{markdown_table(["Ad set", "状态", "目标结果", "结果数", "花费", "平均成本"], adset_rows)}

解读：
- `P - I -Coffee (food & drink)` 目前是最值得保留和放大的 messaging ad set：14 个 conversation，约 {rm(18.45285714)} / conversation。
- `Agriculture` 虽然已经 inactive，但 13 个 conversation、约 {rm(23.74076923)} / conversation，不算差；它可能吸引对“农场 / 来源 / 真材实料”有兴趣的人，建议用更明确 offer 复测。
- `Health and wellness` 有量但成本偏高；不能只讲健康，需要更明确“为什么现在买、买哪一盒、怎样下单”。
- `Recipes` 成本最高，若继续投放，要改成强场景成交素材，不建议用泛泛煮法内容继续买 conversation。
- Broad 新 campaign 目前样本太小，不应太快判断，但第一笔 conversation 成本 {rm(38.30)}，要等更多数据或加上更强 creative 才能放量。

## 5. Creative 层表现

### Messaging creative

{markdown_table(["Ad name", "Conversations", "花费", "平均成本", "Link clicks"], top_messaging_ad_rows)}

### Traffic creative

{markdown_table(["Ad name", "LPV", "花费", "平均成本", "Link clicks"], top_lpv_ad_rows)}

### 有花费但没有 reported result 的素材

{markdown_table(["Ad name", "状态", "花费", "Reach", "Impressions"], zero_result_table_rows)}

解读：
- `260511 - EN - Special Offer - Visual - 200526` 是最明显的 winner：10 个 messaging conversations，平均约 {rm(12.807)} / conversation。Aqina 讨论时应先问：这个 offer 为什么吸引？能不能做中文、WhatsApp、retargeting 版本？
- Video 能带点击和 LPV，尤其 `260501 - SG -Ad01 - Video - 050526` 在 Traffic 里贡献 498 个 LPV；但 video 到购买的路径还没有被证明，需要落地页 retargeting 和 checkout tracking 才能判断。
- `2 BOXDEAL`、煮汤类、部分妈妈/月子类素材目前 conversation 量弱。不是这些角度不能做，而是 offer 和第一屏购买理由还不够直接。

## 6. Inbox 里看到的顾客问题

{markdown_table(["Signal", "对话数", "占 inbox 对话"], signal_rows)}

常见组合：

{markdown_table(["Signal 组合", "对话数"], combination_rows)}

从 inbox 看，顾客没有下单的主要原因不是“完全没兴趣”，而是购买前的不确定感没有被快速解决：

1. **价格 / 配套不够一眼明白。** 21 个对话触发 price/package signal。客户会问几盒、多少钱、1 盒 vs 2 盒、promotion 是否值得。
2. **配送和付款摩擦反复出现。** 16 个 delivery、8 个 payment signal。客户问送货费、送货时间、PayNow、COD、NinjaVan 等，说明成交临门一脚需要更清楚。
3. **第一次购买有味道风险。** 18 个 taste signal。纯鸡精的第一单最大障碍是“怕腥、怕油、怕不好喝、买两盒前想确认”。
4. **信任和安全证明需要视觉化。** 有客户问 Halal、营养、老人/孕妇/特殊身体状况能不能喝。回复不能只靠文字，应配证明图、FAQ 卡、真实评价。
5. **一部分 inbox 不是销售线索。** 有 accidental clicks、vendor pitch、低意图互动；这些需要快速 tag 掉，避免客服时间被稀释。

## 7. 为什么顾客没有下单

- **广告把人带进 chat，但 chat 没有把“下一步购买动作”讲到足够明确。** 高意图客户问完价格 / 配送 / 付款后，应马上看到推荐配套、总价、送货方式、付款方式和下单按钮。
- **Bot 有时继续问宽泛问题。** 当客户已经问价格或配送，继续做长诊断会拖慢成交；这类问题应进入 sales-close flow。
- **缺少低风险首购路径。** 客户担心味道和效果时，如果只有 2-box 或大配套，会放大犹豫。
- **广告 offer 与 inbox reply 没有完全接上。** 如果广告说 special offer，inbox 第一轮就要复述同一个 offer，而不是让客户重新问。
- **归因链条不完整。** 当前只能看到 1 个 matched order；如果订单没有记录 campaign/ad/contact，Aqina 会低估或误判广告效果。

## 8. 建议和下一步动作

### 广告投放

1. **预算先往 winner 集中。** 保留并放大 `Special Offer` creative、`Coffee / food & drink` ad set；`Health` 降预算观察；`Recipes` 先停或重做；`Engagement` 只当 retargeting pool，不当成交主力。
2. **把 offer 做成 3 个版本测试。** `1盒试喝 / 2盒更划算 / 送礼或妈妈场景`。每个版本都要让客户在广告里先知道大概买什么，而不是进 inbox 才问。
3. **Traffic 不要单独看 LPV。** Traffic campaign 可以继续用于建立 retargeting audience，但必须追踪 LPV -> inbox -> checkout -> order。

### Inbox / Chatbot

1. **把价格、配送、付款做成快速成交卡。** 客户问价格时，直接给：推荐配套、总价、适合谁、送货时间、付款方式、下单 CTA。
2. **味道风险要有首购话术。** 例如“第一次喝建议从 1 盒开始；如果要每天补，2 盒更划算”。如果 Aqina 愿意承担承诺，可讨论 taste guarantee / first-purchase assurance。
3. **高意图关键词直接触发 human handoff。** `price`、`delivery`、`paynow`、`COD`、`2 box`、`how to order` 这类不应长时间留在自动问答。
4. **把 proof assets 插入聊天。** Halal / nutrition / no preservative / reviews / product photo / preparation guide 应变成可发送图片或短卡，不只靠文字解释。

### Tracking

1. **Order 必须写回 `marketing_contact_id`、campaign/ad set/ad、UTM、channel。** 否则 Aqina 只能看到“很多人问”，看不到哪一个广告真的卖货。
2. **统一 inbox tag。** 建议 tags：`price`, `delivery`, `payment`, `taste-risk`, `proof-needed`, `ready-to-order`, `not-lead`, `human-follow-up`。
3. **每周看 4 个 KPI。** `cost per conversation`、`chat-to-order rate`、`order value by ad/ad set`、`time to first human response`。

## 9. 和 Aqina 讨论时可以这样说

- 现在广告已经能带来询问，问题不是完全没有需求，而是从询问到下单的路径不够短、不够确定。
- 最值得先放大的不是 engagement，而是能带来低成本 conversation 的 offer creative。
- 顾客最常卡在价格配套、配送付款、味道风险和信任证明。我们下一步应把这些变成广告和 chatbot 的固定成交路径。
- 在 tracking 修好前，不建议只用 ROAS 判断广告好坏；先用 conversation quality + matched order + chat signal 来优化。
- 接下来 2 周目标：把 messaging conversation 成本压到 {rm(18)} - {rm(22)} 区间，同时让每 50 个有效对话至少产生 5-8 个可追踪订单。
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Aqina ads + inbox performance analysis report.")
    parser.add_argument("--campaigns", type=Path, default=latest_matching_file(DEFAULT_ADS_DIR, "campaigns-*.csv"))
    parser.add_argument("--adsets", type=Path, default=latest_matching_file(DEFAULT_ADS_DIR, "adsets-*.csv"))
    parser.add_argument("--ads", type=Path, default=latest_matching_file(DEFAULT_ADS_DIR, "ads-*.csv"))
    parser.add_argument("--inbox", type=Path, default=latest_matching_file(DEFAULT_INBOX_DIR, "marketing-inbox-export-*.json"))
    parser.add_argument("--out", type=Path, default=default_output_path())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    required = {
        "campaigns": args.campaigns,
        "adsets": args.adsets,
        "ads": args.ads,
        "inbox": args.inbox,
    }
    missing = [name for name, path in required.items() if path is None or not Path(path).exists()]
    if missing:
        raise SystemExit(f"Missing required input exports: {', '.join(missing)}")

    report = build_report(
        campaigns_path=Path(args.campaigns),
        adsets_path=Path(args.adsets),
        ads_path=Path(args.ads),
        inbox_path=Path(args.inbox),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
