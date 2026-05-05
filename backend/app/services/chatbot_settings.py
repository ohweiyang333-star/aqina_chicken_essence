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
DEFAULT_BRAND_INTRO_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/create-a-high-impact-e-commerce-hero-product-image.jpg?alt=media&token=503ab227-91ad-41c9-a750-dadc9c3d86f0"
DEFAULT_PACK1_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/V2%2Fclean-product-photography-for-a-landing-page--exac%20(3).webp?alt=media&token=c3d2d10d-80a5-4cf8-8cf0-f48cbd5cd567"
DEFAULT_PACK2_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/V2%2Fclean-product-photography-for-a-landing-page--exac%20(2).webp?alt=media&token=9ebc16e0-a47b-48bf-8f21-e876612687bb"
DEFAULT_PACK4_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/V2%2Fclean-product-photography-for-a-landing-page--exac.webp?alt=media&token=5b9bbf35-9a73-424f-93a8-a47061e481fa"
DEFAULT_PACK6_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/V2%2Fclean-product-photography-for-a-landing-page--exac%20(1).webp?alt=media&token=088626b9-6409-406e-b7fe-ad466a02449a"

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
    "brand_intro": DEFAULT_BRAND_INTRO_IMAGE,
    "package_images": {
        "trial_3": DEFAULT_PACK1_IMAGE,
        "pack1": DEFAULT_PACK1_IMAGE,
        "pack2": DEFAULT_PACK2_IMAGE,
        "pack4": DEFAULT_PACK4_IMAGE,
        "pack6": DEFAULT_PACK6_IMAGE,
    },
    "captions": {
        "brand_intro": "Aqina 农场到上架，全程可追溯。",
        "trial_3": "新手体验装：3 包先试口感。",
        "pack1": "日常滋养装：1 盒 7 包。",
        "pack2": "活力升级装：2 盒 14 包，满足免运费。",
        "pack4": "孕产妇30天调理套餐：4 盒 28 包。",
        "pack6": "家庭月度订阅包：6 盒 42 包。",
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
        "required_questions": ["您会想先用新手体验装试口感，还是直接拿免运的活力升级装？"],
        "recommended_package_code": "trial_3",
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
        "recommended_package_code": "trial_3",
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
        "listening_goal": "确认套餐与数量，收齐姓名、电话、新加坡完整地址。",
        "instruction": "只有顾客明确购买并且姓名、电话、地址齐全时，才能 checkout_ready=true；资料不齐时逐项补齐。",
        "required_questions": ["我帮您安排，请发收件人姓名、联系电话和新加坡完整地址。"],
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
- 【新手体验装】3包 = SGD 18.00，适合先试口感，未满免运门槛。
- 【日常滋养装】1盒/7包 = SGD 39.90，适合基础补充，未满免运门槛。
- 【活力升级装】2盒/14包 = SGD 75.00，适合日常提神抗疲劳，满足免运费。
- 【孕产妇30天调理套餐】4盒/28包 = SGD 149.00，适合孕期、待产、坐月子与新手爸妈补养，满足免运费。
- 【家庭月度订阅包】6盒/42包 = SGD 219.00，适合长辈、送礼与家庭长期补养，满足免运费。
- 满 SGD 70 免运费；低于 SGD 70 的订单需加 SGD 8 新加坡配送费。
- PayNow 收款户名：Boong Poultry Pte Ltd。顾客付款后必须发送付款截图，才算完成提交。

推荐规则：
- 日常提神/上班族/学生：可先给【新手体验装】作为低门槛选择，但更推荐【活力升级装】因为刚好免运费。
- 孕期/产后/月子：优先推荐【孕产妇30天调理套餐】，必要时给【家庭月度订阅包】作为长期补养升级。
- 长辈/送礼/家庭共享：优先推荐【家庭月度订阅包】，若顾客犹豫可降到【活力升级装】。
- 只使用 Available packages 里存在的 package code，不要自行发明套餐 code。

Checkout Rules (下单规则)

- 顾客明确要购买后，才开始收集订单资料。
- 必须收集：收件人姓名、联系电话、新加坡完整收货地址、选定套餐与数量。
- 只有顾客明确购买且姓名、电话、地址都齐全时，才可以 checkout_ready=true。
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
            "trial_3": {
                "code": "trial_3",
                "name_zh": "新手体验装",
                "name_en": "Trial Pack",
                "description_zh": "3包低门槛体验装，适合先试口感；未满 SGD 70 免运门槛，需加 SGD 8 配送费。",
                "description_en": "Low-entry 3-pack trial; below the SGD 70 free-shipping threshold and adds SGD 8 delivery.",
                "price_sgd": 18.0,
                "pack_count": 3,
                "box_count": 1,
                "target_audience": ["self_care"],
                "hero": False,
                "free_shipping_eligible": False,
            },
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
                "qualified_warm": {"instruction": "刚才聊到一半您没消息了，估计是去忙工作或照顾宝宝了吧？😊 您先忙，等您空下来再告诉我，您会更想先试【新手体验装】还是直接拿免运的【活力升级装】呢？"},
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
