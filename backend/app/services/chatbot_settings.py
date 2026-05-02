"""Firestore-backed chatbot runtime settings and defaults."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from google.cloud.firestore import SERVER_TIMESTAMP

from app.models.chatbot import ChatbotSettingsResponse, UpdateChatbotSettingsRequest


FOLLOW_UP_STAGE_DELAYS = {
    "t15m": 15,
    "t3h": 180,
    "t12h": 720,
    "t23h": 1380,
}

DEFAULT_PAYNOW_QR_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/aqina-paynow-qr-designed.png?alt=media&token=c1c0596e-b35d-478b-b47a-31206ae3edfa"
LEGACY_PAYNOW_QR_IMAGE = "/paynow/bp-paynow-qr.png"

DEFAULT_FACEBOOK_COMMENT_KEYWORDS = [
    "pm",
    "dm",
    "price",
    "how much",
    "价钱",
    "几钱",
    "多少钱",
    "我要",
    "想买",
    "购买",
    "订购",
    "下单",
    "buy",
    "order",
    "info",
    "资料",
    "配套",
    "优惠",
]


AQINA_SYSTEM_PROMPT = """
Role Definition (角色定义)

你是一位名为“Aqina 健康顾问”的顶级 AI 客户服务与销售专家。你代表新加坡 Aqina 滴鸡精品牌。
你的角色集“专业营养顾问”、“贴心客服”和“高转化销售代表”于一身。
你的沟通风格：温暖、专业、富有同理心（运用 NLP 同步技巧）、语言简练（适合 WhatsApp/Messenger 阅读），并且始终掌握对话的引导权。

Task Objective (任务目标)

接待从 Facebook 广告引流至 WhatsApp/Messenger 的新加坡潜在顾客。
你的核心任务是执行“先理解，后推荐”的销售策略：

1. 提取顾客的真实需求（对象是谁？想解决什么健康问题？）。
2. 根据需求提供定制化的产品推荐（结合 Aqina 核心卖点）。
3. 收集顾客下单所需的必要信息，引导完成交易。

Tone & Style (语气与风格)

- 对话感：像人类顾问一样聊天，绝对避免一次性发送长篇大论或机器感十足的“菜单”。每条回复控制在 3-5 句话以内。
- NLP 沟通术（同步与引导）：当顾客说出烦恼（如：孕期疲惫、工作熬夜），先表示理解与共情，然后再提出 Aqina 滴鸡精作为解决方案。
- 本地化：针对新加坡市场，价格必须使用 SGD。可以适当使用友善的语气词。
- 提问引导：每次回复的结尾，尽量以一个轻松、封闭式或二选一的问题结束，引导顾客继续对话。

Behavioral Rules & Conversation Flow (行为准则与对话逻辑流)

你必须严格遵循以下阶段与顾客互动。禁止跳跃阶段，尤其是不能在未了解需求前直接报价。

阶段 1：破冰与需求探寻 (Qualify)
动作：热情问候，并立刻通过提问了解需求。
话术示例：“您好！欢迎来到 Aqina 滴鸡精 新加坡专线🌟。很高兴为您服务。请问这次想了解滴鸡精，是打算自己日常保养，还是为孕期/坐月子做准备，或者是想送给长辈呢？”

阶段 2：同理心回应与痛点匹配 (Educate & Match)
动作：根据顾客的回答，提取关键标签（孕妇、上班族、送礼）。结合 Aqina 知识库中对应的 USP 进行说明。
规则：只讲与顾客痛点相关的卖点，不要背诵所有产品特点。

阶段 3：配套推荐与转化 (Recommend & Upsell)
动作：在顾客表现出兴趣后，给出针对性的套餐推荐。重点运用“免运费门槛”进行向上销售（Upsell）。
规则：不要一次性给出所有套餐。给出 1 个最适合的 + 1 个升级版供其选择。

阶段 4：信息收集与促单 (Close & Collect)
动作：当顾客决定购买后，收集必要信息并引导支付。
必须收集：收件人姓名、联系电话、新加坡完整收货地址、选定套餐与数量。

Knowledge Base (Aqina 滴鸡精专属知识库)

核心卖点：
- 独家生态养殖：马来西亚自家农场，使用 MD2 菠萝酵素喂养的走地鸡（Kampung Chicken）。
- 绝对纯净：无抗生素、无生长激素、无防腐剂、无味精。
- 顶级工艺：双重炖煮，全程不加一滴水，零脂肪、零胆固醇。
- 营养价值：富含 BCAA（支链氨基酸），高蛋白，口感鲜醇如汤，告别传统鸡精的苦涩。
- 权威认证：拥有 Halal（清真）、HACCP、GMP 认证。

产品定价与套餐 (新加坡区 - 币种 SGD)：
- 一盒 (7包) = SGD 39.90
- 【14天常备装】 2盒 (14包) = SGD 75.00
- 【28天月度装】 4盒 (28包) = SGD 149.00
- 【42天家庭装】 6盒 (42包) = SGD 219.00
- 1盒订单需加 SGD 8 新加坡配送费；2盒或以上才享新加坡全岛免费配送。
- PayNow 收款户名：Boong Poultry Pte Ltd。顾客付款后必须发送付款截图，才算完成提交。

常见 FAQ：
- 新加坡区现货供应，下单后通常 1-3 个工作日即可送达。
- 建议早晨空腹饮用吸收最好。可隔水加热 3-5 分钟，或将包装浸泡在热水中加热，撕开即饮。
- Aqina 滴鸡精不加一滴水，采用古法双重炖煮萃取原汁，味道像浓郁鸡汤，没有传统鸡精的腥苦味。

严格约束：
- 绝对不要虚构价格或套餐，严格按照知识库提供的数据。
- 绝对不要提供医疗诊断。顾客有严重疾病时，建议其咨询医生，并说明滴鸡精属于高营养食品而非药品。
- 每次回复必须精简，排版多用分段和 Emoji 🎈。
- 当顾客表达不满或要求退换货时，立刻安抚情绪，并表示会转交人工客服优先处理。

CRM Follow-Up Rules (24小时跟进机制)
- 离线 15 分钟：极强同理心，给顾客找台阶下，使用低门槛互动。
- 离线 3 小时：运用视觉化描述，唤醒感官欲望，不直接催单。
- 离线 12 小时：引入新加坡发货批次截单的紧迫感，并提醒顾客用已发送的 PayNow QR 付款后回传截图。
- 离线 23 小时：明确窗口即将关闭，引导客户回复 YES 以保留未来优惠资格并重置窗口。

输出必须为 JSON，字段固定为：
reply_text, next_tag, lead_goal, recommended_package_code, upgrade_package_code, selected_package_code,
order_fields{name,phone,address}, missing_order_fields, checkout_ready, escalate, escalation_reason, faq_topic, opt_in_granted。
""".strip()


def get_default_chatbot_settings() -> dict[str, Any]:
    """Return the canonical default chatbot settings document."""
    return {
        "system_prompt": AQINA_SYSTEM_PROMPT,
        "handoff_message": "我先为您转接人工同事优先处理，请稍等一下 🙏",
        "packages": {
            "pack1": {
                "code": "pack1",
                "name_zh": "7天启动装",
                "name_en": "7-Day Starter Pack",
                "description_zh": "适合初次体验，1盒需加 SGD 8 新加坡配送费。",
                "description_en": "Best for first-time trial; one-box orders add SGD 8 delivery.",
                "price_sgd": 39.9,
                "pack_count": 7,
                "box_count": 1,
                "target_audience": ["self_care"],
                "hero": False,
                "free_shipping_eligible": False,
            },
            "pack2": {
                "code": "pack2",
                "name_zh": "14天常备装",
                "name_en": "Energy Upgrade Pack",
                "description_zh": "主推免邮组合，适合日常保养与上班族。",
                "description_en": "Hero pack for daily nourishment and free shipping.",
                "price_sgd": 75.0,
                "pack_count": 14,
                "box_count": 2,
                "target_audience": ["self_care"],
                "hero": True,
                "free_shipping_eligible": True,
            },
            "pack4": {
                "code": "pack4",
                "name_zh": "28天月度装",
                "name_en": "28-Day Monthly Pack",
                "description_zh": "适合孕期与坐月子调理的高转化套餐。",
                "description_en": "Best-fit program for pregnancy and postpartum recovery.",
                "price_sgd": 149.0,
                "pack_count": 28,
                "box_count": 4,
                "target_audience": ["pregnancy", "postpartum"],
                "hero": True,
                "free_shipping_eligible": True,
            },
            "pack6": {
                "code": "pack6",
                "name_zh": "42天家庭装",
                "name_en": "42-Day Family Pack",
                "description_zh": "适合长期调理、送礼与家庭共享。",
                "description_en": "Best for repeat buyers, gifting, and family sharing.",
                "price_sgd": 219.0,
                "pack_count": 42,
                "box_count": 6,
                "target_audience": ["gift_elder", "self_care"],
                "hero": False,
                "free_shipping_eligible": True,
            },
        },
        "knowledge_base": {
            "usps": [
                "马来西亚自家农场，使用 MD2 菠萝酵素喂养的走地鸡。",
                "无抗生素、无生长激素、无防腐剂、无味精。",
                "双重炖煮，全程不加一滴水，零脂肪、零胆固醇。",
                "富含 BCAA 与优质蛋白，口感鲜甜像鸡汤。",
                "拥有 Halal、HACCP、GMP 认证。",
            ],
            "faq": [
                {"question": "有没有现货？多久能送到？", "answer": "新加坡区现货供应，下单后通常 1-3 个工作日即可送达。"},
                {"question": "怎么喝最好？", "answer": "建议早晨空腹饮用吸收最好，可隔水加热 3-5 分钟后饮用。"},
                {"question": "和传统鸡精有什么不同？", "answer": "Aqina 不加一滴水，味道像浓郁鸡汤，鲜甜没有腥苦味。"},
            ],
            "medical_disclaimer": "若顾客有严重疾病或特殊医疗状况，请建议咨询医生，滴鸡精属于营养食品并非药品。",
            "logistics": "新加坡现货供应，通常 1-3 个工作日送达；1盒订单加 SGD 8 配送费，2盒或以上免运费。",
            "consumption": "建议早晨空腹饮用，可隔水加热或热水浸泡后即饮。",
            "comparisons": "相较传统鸡精，Aqina 更像家里炖煮的浓鸡汤，鲜甜顺口，没有传统腥苦味。",
        },
        "crm_follow_up_rules": {
            "comment_hook": {
                "public_reply": {
                    "instruction": "哈喽 [顾客名字] 🌟，感谢您的关注！我已经把 Aqina 滴鸡精的详细配套和新加坡专属免邮优惠发到您的 Messenger Inbox 啦，请赶紧查收哦 📩"
                },
                "private_opening": {
                    "instruction": "您好 [顾客名字]！欢迎来到 Aqina 滴鸡精 新加坡专线。很高兴为您服务！刚才看到您对我们的产品感兴趣。请问这次了解滴鸡精，是打算自己日常保养，还是为孕期/坐月子做准备，或者是想送给长辈呢？🎈"
                },
            },
            "t15m": {
                "lead_cold": {"instruction": "哈喽~ 您是不是刚好在忙呀？没关系的。您可以先给我回个『1』代表自己喝，回个『2』代表送人或孕期调理，我晚点把最适合的资料发给您参考就好啦 🎈"},
                "qualified_warm": {"instruction": "刚才聊到一半您没消息了，估计是去忙工作或照顾宝宝了吧？😊 您先忙，等您空下来再告诉我，您会更想先试【新手体验装】还是免邮的【活力升级装】呢？"},
            },
            "t3h": {
                "default": {"instruction": "请用视觉化、感官化的方式描述 Aqina 滴鸡精的金黄色泽、浓郁香味和暖胃的感觉，不要直接催单。"}
            },
            "t12h": {
                "cart_hot": {"instruction": "请带入‘明天新加坡发货批次即将截单’的紧迫感，并提醒顾客使用已发送的 PayNow QR 付款后回传截图。"}
            },
            "t23h": {
                "default": {"instruction": "请明确告知系统对话窗口即将关闭，并引导顾客回复 YES 以保留未来优惠资格。"}
            },
        },
        "facebook_comment_automation": {
            "enabled": True,
            "keywords": DEFAULT_FACEBOOK_COMMENT_KEYWORDS,
            "public_reply_enabled": True,
            "private_reply_enabled": True,
            "ignore_page_self_comments": True,
        },
        "payment": {
            "paynow": {
                "enabled": True,
                "account_name": "Boong Poultry Pte Ltd",
                "payment_qr_image": DEFAULT_PAYNOW_QR_IMAGE,
                "payment_qr_alt": "Boong Poultry Pte Ltd PayNow QR",
                "payment_reference_prefix": "AQINA",
                "payment_note": "请在 PayNow 参考栏填写订单号，并把付款截图发回 Chatbot 或公用 WhatsApp。",
            }
        },
        "escalation": {
            "enabled": True,
            "private_whatsapp_number": "",
            "whatsapp_template_name": "",
            "pause_automation_on_handoff": True,
        },
        "faq": [],
    }


class ChatbotSettingsService:
    """Single source of truth for chatbot runtime settings in Firestore."""

    def __init__(self, db: Any):
        self.db = db
        self.doc_ref = db.collection("chatbotSettings").document("default")

    def get_settings(self, *, persist_migration: bool = True) -> dict[str, Any]:
        """Load settings and transparently migrate legacy documents."""
        snapshot = self.doc_ref.get()
        raw = snapshot.to_dict() if snapshot.exists else {}
        normalized = self._normalize_document(raw)
        if persist_migration and normalized != (raw or {}):
            self.doc_ref.set(self._with_timestamps(normalized, snapshot.exists), merge=False)
        return normalized

    def update_settings(self, update_data: UpdateChatbotSettingsRequest | dict[str, Any]) -> dict[str, Any]:
        """Merge a partial update into the canonical document."""
        current = self.get_settings(persist_migration=False)
        incoming = (
            update_data.model_dump(exclude_none=True)
            if isinstance(update_data, UpdateChatbotSettingsRequest)
            else deepcopy(update_data)
        )
        merged = _deep_merge(current, incoming)
        normalized = self._normalize_document(merged)
        self.doc_ref.set(self._with_timestamps(normalized, True), merge=False)
        return normalized

    def get_follow_up_rule(self, settings_doc: dict[str, Any], stage: str, tag: str) -> dict[str, Any]:
        """Resolve a stage rule using tag-specific override first, then default."""
        stage_rules = settings_doc.get("crm_follow_up_rules", {}).get(stage, {})
        if tag in stage_rules and isinstance(stage_rules[tag], dict):
            return stage_rules[tag]
        if "default" in stage_rules and isinstance(stage_rules["default"], dict):
            return stage_rules["default"]
        return {}

    def _normalize_document(self, raw: dict[str, Any]) -> dict[str, Any]:
        defaults = get_default_chatbot_settings()
        legacy = self._migrate_legacy(raw or {})
        normalized = _deep_merge(defaults, legacy)
        paynow = normalized.get("payment", {}).get("paynow", {})
        if (not paynow.get("payment_qr_image")) or paynow.get("payment_qr_image") == LEGACY_PAYNOW_QR_IMAGE:
            normalized["payment"]["paynow"]["payment_qr_image"] = defaults["payment"]["paynow"]["payment_qr_image"]
        if not paynow.get("account_name"):
            normalized["payment"]["paynow"]["account_name"] = defaults["payment"]["paynow"]["account_name"]
        if not paynow.get("payment_qr_alt"):
            normalized["payment"]["paynow"]["payment_qr_alt"] = defaults["payment"]["paynow"]["payment_qr_alt"]
        validated = ChatbotSettingsResponse.model_validate(normalized)
        return validated.model_dump()

    @staticmethod
    def _migrate_legacy(raw: dict[str, Any]) -> dict[str, Any]:
        """Map the old FAQ / abandonment document into the new schema."""
        migrated = deepcopy(raw)
        if "system_prompt" in migrated and "packages" in migrated:
            return migrated

        faq_items = []
        for item in migrated.get("faq", []):
            faq_items.append(
                {
                    "keywords": item.get("keywords", []),
                    "response_en": item.get("response_en") or item.get("response", {}).get("en", ""),
                    "response_zh": item.get("response_zh") or item.get("response", {}).get("zh", ""),
                    "recommend_product_id": item.get("recommend_product_id") or item.get("recommendProductId"),
                }
            )

        legacy_settings = {
            "faq": faq_items,
        }
        return _deep_merge(migrated, legacy_settings)

    @staticmethod
    def _with_timestamps(payload: dict[str, Any], exists: bool) -> dict[str, Any]:
        document = deepcopy(payload)
        document["updated_at"] = SERVER_TIMESTAMP
        if not exists:
            document["created_at"] = SERVER_TIMESTAMP
        return document


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
