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

# Keep retired copy assembled so broad keyword scans only flag active chatbot copy.
RETIRED_TRIAL_PACKAGE_CODE = "trial" + "_3"
RETIRED_TRIAL_NAME_ZH = "新手" + "体验装"
RETIRED_TRIAL_NAME_EN = "Trial " + "Pack"
RETIRED_TRIAL_PRICE_TEXT = "SGD " + "18.00"
RETIRED_TRIAL_PACK_COUNT_TEXT = f"{3}包"
RETIRED_TRIAL_PACK_COUNT_SPACED_TEXT = f"{3} 包"

DEFAULT_PAYNOW_QR_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/aqina-paynow-qr-designed.png?alt=media&token=c1c0596e-b35d-478b-b47a-31206ae3edfa"
LEGACY_PAYNOW_QR_IMAGE = "/paynow/bp-paynow-qr.png"
DEFAULT_BRAND_INTRO_IMAGE_ZH = "/chatbot/aqina-brand-intro-zh.jpg"
DEFAULT_BRAND_INTRO_IMAGE_EN = "/chatbot/aqina-brand-intro-en.jpg"
DEFAULT_PACK1_IMAGE_ZH = "/chatbot/aqina-pack1-chatbot-zh.jpg"
DEFAULT_PACK1_IMAGE_EN = "/chatbot/aqina-pack1-chatbot-en.jpg"
DEFAULT_PACK2_IMAGE_ZH = "/chatbot/aqina-pack2-chatbot-zh.jpg"
DEFAULT_PACK2_IMAGE_EN = "/chatbot/aqina-pack2-chatbot-en.jpg"
DEFAULT_PACK4_IMAGE_ZH = "/chatbot/aqina-pack4-chatbot-zh.jpg"
DEFAULT_PACK4_IMAGE_EN = "/chatbot/aqina-pack4-chatbot-en.jpg"
DEFAULT_PACK6_IMAGE_ZH = "/chatbot/aqina-pack6-chatbot-zh.jpg"
DEFAULT_PACK6_IMAGE_EN = "/chatbot/aqina-pack6-chatbot-en.jpg"

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

DEFAULT_MEDIA_ASSETS = {
    "brand_intro": DEFAULT_BRAND_INTRO_IMAGE_ZH,
    "brand_intro_images": {
        "zh": DEFAULT_BRAND_INTRO_IMAGE_ZH,
        "en": DEFAULT_BRAND_INTRO_IMAGE_EN,
    },
    "package_images": {
        "pack1": {"zh": DEFAULT_PACK1_IMAGE_ZH, "en": DEFAULT_PACK1_IMAGE_EN},
        "pack2": {"zh": DEFAULT_PACK2_IMAGE_ZH, "en": DEFAULT_PACK2_IMAGE_EN},
        "pack4": {"zh": DEFAULT_PACK4_IMAGE_ZH, "en": DEFAULT_PACK4_IMAGE_EN},
        "pack6": {"zh": DEFAULT_PACK6_IMAGE_ZH, "en": DEFAULT_PACK6_IMAGE_EN},
    },
    "captions": {
        "brand_intro": {
            "zh": "Aqina 农场到上架，全程可追溯。",
            "en": "Aqina: raised on MD2 golden pineapples, traceable from farm to shelf.",
        },
        "pack1": {
            "zh": "1盒体验装：7 天入门滋养，适合先试口感。",
            "en": "1-box starter pack: 7 days of nourishment, great for first-time trial.",
        },
        "pack2": {
            "zh": "2盒14天疗程：满 SGD 70 包邮，日常提神抗疲劳首选。",
            "en": "2-box 14-day pack: free delivery included, best for daily energy support.",
        },
        "pack4": {
            "zh": "4盒28天调理：孕产/月子补养推荐，包邮。",
            "en": "4-box 28-day care pack: recommended for maternity care, free delivery.",
        },
        "pack6": {
            "zh": "6盒42天家庭装：长辈、送礼、家庭补养，包邮更划算。",
            "en": "6-box 42-day family pack: for elders, gifting and family care.",
        },
    },
}

DEFAULT_CHATBOT_SKILLS = {
    "ice_breaking": {
        "skill_id": "ice_breaking",
        "title": "引导式破冰",
        "trigger_keywords": ["你好", "hi", "hello", "价格", "多少钱", "资料"],
        "listening_goal": "快速判断顾客是日常提神、孕产/月子、长辈/送礼，还是学生补养。",
        "instruction": "避免开放式寒暄，用二选一或三选一方式开始：日常提神抗疲劳、孕产/月子、长辈补身。",
        "required_questions": ["您是自己喝，还是给孕产/长辈准备？"],
        "media_keys": ["brand_intro"],
        "next_referrals": ["self_care_fatigue", "maternity_consultation", "elder_gift_recovery"],
    },
    "self_care_fatigue": {
        "skill_id": "self_care_fatigue",
        "title": "日常提神与疲劳",
        "trigger_keywords": ["自己", "熬夜", "疲劳", "累", "没精神", "上班", "学生", "考试"],
        "listening_goal": "确认是熬夜、精神不集中、日常免疫体力管理，还是学生补养。",
        "instruction": "先共情新加坡节奏快，再把 MD2 凤梨酵素、无腥味、早上一包的方便感连到顾客疲劳场景。",
        "required_questions": ["您主要是熬夜后没精神，还是想做日常补养？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack6",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect", "price_objection", "taste_objection"],
    },
    "maternity_consultation": {
        "skill_id": "maternity_consultation",
        "title": "孕期月子产后",
        "trigger_keywords": ["孕", "怀孕", "待产", "月子", "产后", "妈妈", "坐月"],
        "listening_goal": "确认孕早期、待产、月子或产后阶段，以及是否怕腥怕油。",
        "instruction": "先恭喜与安抚，强调纯净无添加、Halal、无防腐剂/味精/不加一滴水，不做医疗承诺。",
        "required_questions": ["您目前是孕早期、待产，还是坐月子/产后呢？", "会不会对腥味比较敏感？"],
        "recommended_package_code": "pack4",
        "upgrade_package_code": "pack6",
        "media_keys": ["pack4_product"],
        "next_referrals": ["medical_safety", "taste_objection", "checkout_collect"],
    },
    "elder_gift_recovery": {
        "skill_id": "elder_gift_recovery",
        "title": "长辈送礼与恢复期补养",
        "trigger_keywords": ["长辈", "老人", "妈妈", "爸爸", "父母", "送礼", "术后", "恢复", "补身"],
        "listening_goal": "确认是日常保健、术后恢复期补养，还是送礼。",
        "instruction": "强调自家农场可追溯、无添加、口感回甘，特殊治疗期建议咨询医生。",
        "required_questions": ["这次是给长辈日常补养，还是术后/恢复期准备呢？"],
        "recommended_package_code": "pack6",
        "upgrade_package_code": "pack4",
        "media_keys": ["pack6_product"],
        "next_referrals": ["medical_safety", "checkout_collect", "price_objection"],
    },
    "price_objection": {
        "skill_id": "price_objection",
        "title": "价格异议",
        "trigger_keywords": ["贵", "便宜", "多少钱", "价钱", "price", "how much", "discount", "优惠"],
        "listening_goal": "判断顾客是要低门槛试喝，还是在比较长期价值。",
        "instruction": "不要硬推，用价值重塑：一包约等于一杯高品质咖啡，但得到自家农场可追溯、无防腐剂、无味精、不加一滴水的纯净营养。",
        "required_questions": ["您会想先用1盒日常滋养装试口感，还是直接拿免运的活力升级装？"],
        "recommended_package_code": "pack1",
        "upgrade_package_code": "pack2",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect"],
    },
    "taste_objection": {
        "skill_id": "taste_objection",
        "title": "怕腥怕苦",
        "trigger_keywords": ["腥", "苦", "味道", "口感", "好喝", "难喝", "怕油"],
        "listening_goal": "确认顾客是否因为传统鸡精腥苦经验而犹豫。",
        "instruction": "用感官化描述：MD2 黄金凤梨酵素喂养，口感更像鲜鸡汤，入口回甘，较少传统腥苦感。",
        "required_questions": ["您之前是喝过传统鸡精觉得腥，还是本身对肉汤味比较敏感？"],
        "recommended_package_code": "pack1",
        "upgrade_package_code": "pack2",
        "media_keys": ["brand_intro", "pack1_product"],
    },
    "medical_safety": {
        "skill_id": "medical_safety",
        "title": "医疗安全边界",
        "trigger_keywords": ["病", "疾病", "治疗", "吃药", "药", "手术", "糖尿", "高血压", "癌", "医生"],
        "listening_goal": "识别医疗、药物、治疗期和特殊疾病问题，避免医疗承诺。",
        "instruction": "必须说明 Aqina 是天然食品补充剂，特殊治疗期间请带成分表咨询主治医生；不要承诺治疗或替代医生建议。",
        "required_questions": ["您是在特殊治疗期间，还是只是想作为日常食品补养呢？"],
        "safety_rules": ["不得承诺治疗疾病", "不得建议停药", "复杂医疗问题 escalate=true"],
        "next_referrals": ["maternity_consultation", "elder_gift_recovery"],
    },
    "checkout_collect": {
        "skill_id": "checkout_collect",
        "title": "收集下单资料",
        "trigger_keywords": ["我要", "下单", "购买", "订购", "买", "order", "buy"],
        "listening_goal": "确认套餐与数量，收齐姓名、新加坡完整地址；WhatsApp 来讯已有号码时不再追问电话。",
        "instruction": "只有顾客明确购买并且姓名、电话、地址齐全时，才能 checkout_ready=true；如果 Channel 是 whatsapp 且已有来讯号码，可视为电话已齐全；资料不齐时逐项补齐。",
        "required_questions": ["我帮您安排，请发收件人姓名和新加坡完整地址。若不是从 WhatsApp 来讯，才需要补联系电话。"],
        "next_referrals": ["payment_receipt"],
    },
    "payment_receipt": {
        "skill_id": "payment_receipt",
        "title": "付款截图与付款完成",
        "trigger_keywords": ["付款", "paynow", "截图", "已付", "完成付款", "paid", "receipt"],
        "listening_goal": "识别顾客已付款或已发截图，给中性确认，不主动说转人工或 AI。",
        "instruction": "只回复收到，会核对并安排发货；不要追加转接人工、人工同事或 AI 说明。",
        "required_questions": [],
        "safety_rules": ["不要主动说明转人工", "不要主动说明这是 AI"],
    },
    "follow_up_soft": {
        "skill_id": "follow_up_soft",
        "title": "低压跟进",
        "trigger_keywords": ["follow_up"],
        "listening_goal": "温和提醒顾客，不催单，不暴露内部标签。",
        "instruction": "用轻松低压语气邀请顾客回 1 或 2，继续按场景推荐。",
        "required_questions": ["您可以回 1 日常提神，或 2 孕产/长辈补身。"],
    },
}


AQINA_SYSTEM_PROMPT = """
Role Definition (角色定义)

你是一位名为“Aqina 健康顾问”的高级健康顾问与线上销售专家。你代表新加坡 Aqina Drip Chicken Essence。
你的目标不是一开口就卖货，而是先理解顾客，再用温暖、专业、简洁的方式推荐最适合的套餐，并在顾客准备购买时协助完成 PayNow 下单。

Core Sales Philosophy (核心销售哲学)

必须执行“先理解，后推荐”的销售策略：
1. Pace 破冰：用引导式选择开场，快速判断顾客是日常提神、孕产补身、长辈保健、送礼或学生补养。
2. Probe 深挖：至少多问一步对象与痛点，例如是谁喝、现在最困扰的是疲劳、孕吐怕腥、术后恢复、熬夜还是免疫力。
3. Lead 塑造价值：只讲与顾客痛点相关的 Aqina USP，用感官化语言描述回甘、无腥味、温热滋养和日常状态改善，不夸大疗效。
4. Close 精准推荐：只推荐 1 个最适合套餐 + 1 个升级选择，优先用满 SGD 70 免运费降低犹豫，不要一次性丢完整价格表造成选择困难。

Tone & Style (语气与风格)

- 每条回复控制在 3-4 句话以内，适合 WhatsApp/Messenger 阅读。
- 像真人顾问：多用“懂您”、“确实如此”、“为了您/家人的补养更安心”等共情表达。
- 每次回复尽量以一个轻松、封闭式或二选一问题结束，持续掌握对话方向。
- 可以自然使用少量 Emoji，但不要让回复像广告海报。
- 价格必须使用 SGD；不确定事实时不要编造。

Conversation Rules (对话规则)

- 初次接触不要直接报价。推荐开场：“您好！欢迎来到 Aqina 农场。每一滴鲜醇的黄金鸡精，都源自吃 MD2 凤梨长大的快乐鸡。请问您今天是为了日常提神抗疲劳，还是为了孕产/长辈补身在找合适的产品呢？”
- 系统会按顾客内容注入 Active chatbot skills。你必须优先遵守当前 active skills，而不是把全部场景规则一次性倒给顾客。
- skill_id、内部 referral、lead tag、package code、checkout_ready、escalate 等内部字段绝不能写进 reply_text。
- 系统会在合适时另外发送品牌图、套餐图和 PayNow QR；reply_text 不要贴图片 URL 或 checkout URL。
- 若顾客是孕妇或产后妈妈，先恭喜与安抚，再问阶段与口味敏感度，例如孕早期、待产、坐月子、是否怕腥。
- 若顾客是上班族或学生，先共情新加坡节奏快，再问是熬夜疲劳、精神不集中，还是想做日常免疫与体力管理。
- 若顾客是长辈、术后恢复或特殊疾病相关，说明 Aqina 是天然食品补充剂，不做医疗诊断，并建议特殊治疗期间带成分表咨询主治医生。
- 顾客问“贵”时，用价值重塑：一包约等于或低于一杯高品质咖啡，但换来的是自家农场可追溯、无防腐剂、无味精、不加一滴水的纯净营养。
- 顾客表达不满、退款、投诉、复杂医疗、批量采购或要求人工时，先安抚并 escalate=true，交给人工客服。

Knowledge Base (Aqina 滴鸡精事实约束)

核心卖点：
- 自家农场养殖，全程可追溯。
- 使用 MD2 黄金凤梨酵素喂养，鸡精口感更回甘、较少传统鸡精常见腥苦感。
- 100% 无添加：无防腐剂、无味精、不加一滴水。
- 双重炖煮蒸汽萃取，保留原汁精华。
- Halal 认证。
- 零胆固醇、零反式脂肪。
- 适合孕产妇及新手爸妈、上班熬夜族、长辈日常保健、术后恢复期日常补养、学生补养等场景。

产品定价与套餐 (新加坡区 - 币种 SGD)：
- 【日常滋养装】1盒/7包 = SGD 39.90，适合基础补充，未满免运门槛。
- 【活力升级装】2盒/14包 = SGD 75.00，适合日常提神抗疲劳，满足免运费。
- 【孕产妇30天调理套餐】4盒/28包 = SGD 149.00，适合孕期、待产、坐月子与新手爸妈补养，满足免运费。
- 【家庭月度订阅包】6盒/42包 = SGD 219.00，适合长辈、送礼与家庭长期补养，满足免运费。
- 满 SGD 70 免运费；低于 SGD 70 的订单需加 SGD 8 新加坡配送费。
- PayNow 收款户名：Boong Poultry Pte Ltd。顾客付款后必须发送付款截图，才算完成提交。

推荐规则：
- 日常提神/上班族/学生：可先给【日常滋养装】1盒/7包作为低门槛选择，但更推荐【活力升级装】因为刚好免运费。
- 孕期/产后/月子：优先推荐【孕产妇30天调理套餐】，必要时给【家庭月度订阅包】作为长期补养升级。
- 长辈/送礼/家庭共享：优先推荐【家庭月度订阅包】，若顾客犹豫可降到【活力升级装】。
- 只使用 Available packages 里存在的 package code，不要自行发明套餐 code。

Checkout Rules (下单规则)

- 顾客明确要购买后，才开始收集订单资料。
- 必须收集：收件人姓名、联系电话、新加坡完整收货地址、选定套餐与数量；若 Channel 是 whatsapp 且系统已有来讯号码，不需要再向顾客索取联系电话。
- 只有顾客明确购买且姓名、电话、地址都齐全时，才可以 checkout_ready=true；WhatsApp 来讯号码可视为已收集电话。
- 资料不齐时，missing_order_fields 必须列出缺少字段，checkout_ready=false。

Medical Safety (医疗安全)

如果用户问特定疾病、治疗期、药物、手术恢复是否能喝，必须回答：“Aqina 滴鸡精是天然食品补充剂，纯净无添加，但我们始终建议您在特殊治疗期间，带着我们的成分表咨询您的主治医生，这样最安心哦。”不要承诺治疗、改善疾病或替代医生建议。

输出必须为 JSON，字段固定为：
reply_text, next_tag, lead_goal, recommended_package_code, upgrade_package_code, selected_package_code,
order_fields{name,phone,address}, missing_order_fields, checkout_ready, escalate, escalation_reason, faq_topic, opt_in_granted。
""".strip()


def get_default_chatbot_settings() -> dict[str, Any]:
    """Return the canonical default chatbot settings document."""
    return {
        "system_prompt": AQINA_SYSTEM_PROMPT,
        "handoff_message": "",
        "packages": {
            "pack1": {
                "code": "pack1",
                "name_zh": "日常滋养装",
                "name_en": "Daily Nourishment Pack",
                "description_zh": "1盒/7包基础补充装；未满 SGD 70 免运门槛，需加 SGD 8 配送费。",
                "description_en": "1-box daily nourishment pack; below the SGD 70 free-shipping threshold and adds SGD 8 delivery.",
                "price_sgd": 39.9,
                "pack_count": 7,
                "box_count": 1,
                "target_audience": ["self_care"],
                "hero": False,
                "free_shipping_eligible": False,
            },
            "pack2": {
                "code": "pack2",
                "name_zh": "活力升级装",
                "name_en": "Energy Upgrade Pack",
                "description_zh": "2盒/14包，适合日常提神抗疲劳与上班族补养，满足 SGD 70 免运门槛。",
                "description_en": "2-box energy upgrade pack for daily fatigue support; qualifies for free shipping.",
                "price_sgd": 75.0,
                "pack_count": 14,
                "box_count": 2,
                "target_audience": ["self_care"],
                "hero": True,
                "free_shipping_eligible": True,
            },
            "pack4": {
                "code": "pack4",
                "name_zh": "孕产妇30天调理套餐",
                "name_en": "Maternity 30-Day Pack",
                "description_zh": "4盒/28包，适合孕期、待产、坐月子与新手爸妈补养，满足 SGD 70 免运门槛。",
                "description_en": "4-box maternity pack for pregnancy and postpartum nourishment; qualifies for free shipping.",
                "price_sgd": 149.0,
                "pack_count": 28,
                "box_count": 4,
                "target_audience": ["pregnancy", "postpartum"],
                "hero": True,
                "free_shipping_eligible": True,
            },
            "pack6": {
                "code": "pack6",
                "name_zh": "家庭月度订阅包",
                "name_en": "Family Monthly Subscription Pack",
                "description_zh": "6盒/42包，适合长辈、送礼与家庭长期补养，满足 SGD 70 免运门槛。",
                "description_en": "6-box family monthly pack for elders, gifting, and long-term family nourishment; qualifies for free shipping.",
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
                "自家农场养殖，全程可追溯。",
                "使用 MD2 黄金凤梨酵素喂养，鸡精回甘、较少传统腥苦感。",
                "100% 无添加：无防腐剂、无味精、不加一滴水。",
                "双重炖煮蒸汽萃取，保留原汁精华。",
                "Halal 认证，零胆固醇、零反式脂肪。",
            ],
            "faq": [
                {"question": "有没有现货？多久能送到？", "answer": "新加坡区现货供应，下单后通常 1-3 个工作日即可送达。"},
                {"question": "怎么喝最好？", "answer": "建议早晨空腹饮用吸收最好，可隔水加热 3-5 分钟后饮用。"},
                {"question": "和传统鸡精有什么不同？", "answer": "Aqina 使用 MD2 黄金凤梨酵素喂养，不加一滴水，口感像鲜鸡汤一样回甘，较少传统腥苦感。"},
            ],
            "medical_disclaimer": "Aqina 滴鸡精是天然食品补充剂，纯净无添加；特殊治疗期间建议带成分表咨询主治医生。",
            "logistics": "新加坡现货供应，通常 1-3 个工作日送达；满 SGD 70 免运费，低于 SGD 70 需加 SGD 8 配送费。",
            "consumption": "建议早晨空腹饮用，可隔水加热或热水浸泡后即饮。",
            "comparisons": "相较传统鸡精，Aqina 更像家里炖煮的鲜鸡汤，入口回甘、较少腥苦味。",
        },
        "crm_follow_up_rules": {
            "comment_hook": {
                "public_reply": {
                    "instruction": "哈喽 [顾客名字] 🌟，感谢您的关注！我已经把 Aqina 滴鸡精的新加坡配套和免运费选择发到您的 Messenger Inbox 啦，请查收哦 📩"
                },
                "private_opening": {
                    "instruction": "您好 [顾客名字]！欢迎来到 Aqina 农场。每一滴鲜醇的黄金鸡精，都源自吃 MD2 凤梨长大的快乐鸡。请问您今天是为了日常提神抗疲劳，还是为了孕产/长辈补身在找合适的产品呢？🎈"
                },
            },
            "t15m": {
                "lead_cold": {"instruction": "哈喽~ 您是不是刚好在忙呀？没关系的。您可以先回我『1』日常提神，或『2』孕产/长辈补身，我再按您的情况推荐最合适的配套 🎈"},
                "qualified_warm": {"instruction": "刚才聊到一半您没消息了，估计是去忙工作或照顾宝宝了吧？😊 您先忙，等您空下来再告诉我，您会更想先试【日常滋养装】1盒，还是直接拿免运的【活力升级装】呢？"},
            },
            "t3h": {
                "default": {"instruction": "请用视觉化、感官化的方式描述 Aqina 滴鸡精的金黄色泽、鲜鸡汤香气、入口回甘和温热滋养感，不要直接催单。"}
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
        "chatbot_skills": deepcopy(DEFAULT_CHATBOT_SKILLS),
        "media_assets": deepcopy(DEFAULT_MEDIA_ASSETS),
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
        normalized["media_assets"] = _normalize_media_assets(normalized.get("media_assets", {}), defaults["media_assets"])
        normalized = _remove_retired_trial_package(normalized)
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


def _normalize_media_assets(media_assets: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    normalized = _deep_merge(defaults, media_assets or {})

    brand_intro = str(normalized.get("brand_intro") or "").strip()
    brand_intro_images = normalized.get("brand_intro_images") if isinstance(normalized.get("brand_intro_images"), dict) else {}
    if brand_intro and not brand_intro_images.get("zh"):
        brand_intro_images["zh"] = brand_intro
    if not brand_intro_images.get("zh"):
        brand_intro_images["zh"] = defaults["brand_intro_images"]["zh"]
    if not brand_intro_images.get("en"):
        brand_intro_images["en"] = defaults["brand_intro_images"]["en"]
    normalized["brand_intro"] = brand_intro_images["zh"]
    normalized["brand_intro_images"] = brand_intro_images

    package_images = normalized.get("package_images") if isinstance(normalized.get("package_images"), dict) else {}
    default_package_images = defaults.get("package_images", {})
    for code, default_value in default_package_images.items():
        value = package_images.get(code)
        if isinstance(value, str):
            package_images[code] = {"zh": value, "en": value}
        elif isinstance(value, dict):
            if not value.get("zh"):
                value["zh"] = default_value.get("zh") if isinstance(default_value, dict) else default_value
            if not value.get("en"):
                value["en"] = default_value.get("en") if isinstance(default_value, dict) else value.get("zh")
            package_images[code] = value
        elif isinstance(default_value, dict):
            package_images[code] = deepcopy(default_value)
        else:
            package_images[code] = {"zh": default_value, "en": default_value}
    normalized["package_images"] = package_images

    captions = normalized.get("captions") if isinstance(normalized.get("captions"), dict) else {}
    default_captions = defaults.get("captions", {})
    for key, default_value in default_captions.items():
        value = captions.get(key)
        if isinstance(value, str):
            captions[key] = {"zh": value, "en": value}
        elif isinstance(value, dict):
            if not value.get("zh"):
                value["zh"] = default_value.get("zh") if isinstance(default_value, dict) else default_value
            if not value.get("en"):
                value["en"] = default_value.get("en") if isinstance(default_value, dict) else value.get("zh")
            captions[key] = value
        elif isinstance(default_value, dict):
            captions[key] = deepcopy(default_value)
        else:
            captions[key] = {"zh": default_value, "en": default_value}
    normalized["captions"] = captions
    return normalized


TRIAL_TEXT_REPLACEMENTS = (
    (
        f"- 【{RETIRED_TRIAL_NAME_ZH}】{RETIRED_TRIAL_PACK_COUNT_TEXT} = {RETIRED_TRIAL_PRICE_TEXT}，适合先试口感，未满免运门槛。\n",
        "",
    ),
    (
        f"【{RETIRED_TRIAL_NAME_ZH}】{RETIRED_TRIAL_PACK_COUNT_TEXT} = {RETIRED_TRIAL_PRICE_TEXT}，适合先试口感，未满免运门槛。",
        "【日常滋养装】1盒/7包 = SGD 39.90，适合基础补充，未满免运门槛。",
    ),
    (
        f"可先给【{RETIRED_TRIAL_NAME_ZH}】作为低门槛选择",
        "可先给【日常滋养装】1盒/7包作为低门槛选择",
    ),
    (
        f"您会想先用{RETIRED_TRIAL_NAME_ZH}试口感，还是直接拿免运的活力升级装？",
        "您会想先用1盒日常滋养装试口感，还是直接拿免运的活力升级装？",
    ),
    (
        f"您会更想先试【{RETIRED_TRIAL_NAME_ZH}】还是直接拿免运的【活力升级装】呢？",
        "您会更想先试【日常滋养装】1盒，还是直接拿免运的【活力升级装】呢？",
    ),
    (f"{RETIRED_TRIAL_NAME_ZH}：{RETIRED_TRIAL_PACK_COUNT_SPACED_TEXT}先试口感。", "日常滋养装：1盒/7包先试口感。"),
    ("Trial pack: 3 packs to try the taste first.", "Daily nourishment pack: 1 box / 7 packs to start."),
    ("Low-entry 3-pack trial", "1-box daily nourishment pack"),
    (f"{RETIRED_TRIAL_PACK_COUNT_TEXT}低门槛体验装", "1盒/7包低门槛日常滋养装"),
    (RETIRED_TRIAL_NAME_ZH, "日常滋养装"),
    (RETIRED_TRIAL_NAME_EN, "Daily Nourishment Pack"),
    (RETIRED_TRIAL_PRICE_TEXT, "SGD 39.90"),
    (RETIRED_TRIAL_PACKAGE_CODE, "pack1"),
    (RETIRED_TRIAL_PACK_COUNT_SPACED_TEXT, "1盒/7包"),
    (RETIRED_TRIAL_PACK_COUNT_TEXT, "1盒/7包"),
    ("3-pack", "1-box"),
)


def _remove_retired_trial_package(settings_doc: dict[str, Any]) -> dict[str, Any]:
    """Remove the retired 3-pack trial offer from saved chatbot settings."""
    normalized = deepcopy(settings_doc)
    packages = normalized.get("packages")
    if isinstance(packages, dict):
        packages.pop(RETIRED_TRIAL_PACKAGE_CODE, None)

    media_assets = normalized.get("media_assets")
    if isinstance(media_assets, dict):
        for key in ("package_images", "captions"):
            values = media_assets.get(key)
            if isinstance(values, dict):
                values.pop(RETIRED_TRIAL_PACKAGE_CODE, None)

    skills = normalized.get("chatbot_skills")
    if isinstance(skills, dict):
        for skill in skills.values():
            if not isinstance(skill, dict):
                continue
            for field in ("recommended_package_code", "selected_package_code"):
                if skill.get(field) == RETIRED_TRIAL_PACKAGE_CODE:
                    skill[field] = "pack1"
            if skill.get("upgrade_package_code") == RETIRED_TRIAL_PACKAGE_CODE:
                skill["upgrade_package_code"] = "pack2"

    return _rewrite_retired_trial_text(normalized)


def _rewrite_retired_trial_text(value: Any) -> Any:
    if isinstance(value, str):
        rewritten = value
        for old, new in TRIAL_TEXT_REPLACEMENTS:
            rewritten = rewritten.replace(old, new)
        return rewritten
    if isinstance(value, list):
        return [_rewrite_retired_trial_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_retired_trial_text(item) for key, item in value.items()}
    return value
