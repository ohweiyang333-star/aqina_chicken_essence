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

CONVERSION_OPTIMIZATION_VERSION = 2
TERMINOLOGY_MIGRATION_VERSION = 1
AQINA_NEW_PRODUCT_TERM = "纯鸡精"
CHATBOT_PRODUCT_TERM_REPLACEMENTS = (
    ("滴" + "雞精", AQINA_NEW_PRODUCT_TERM),
    ("滴" + "鸡精", AQINA_NEW_PRODUCT_TERM),
    ("黄梨鸡" + AQINA_NEW_PRODUCT_TERM, "黄梨酵素纯鸡精"),
    ("黄梨" + AQINA_NEW_PRODUCT_TERM, "黄梨酵素纯鸡精"),
    ("纯天然" + AQINA_NEW_PRODUCT_TERM, "纯天然鸡精"),
    ("纯萃" + AQINA_NEW_PRODUCT_TERM, AQINA_NEW_PRODUCT_TERM),
)

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
    "运费",
    "多久到",
    "地址",
    "付款",
    "paynow",
    "receipt",
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
        "title": "快速分流破冰",
        "trigger_keywords": ["你好", "hi", "hello", "资料", "info"],
        "listening_goal": "先建立信任，判断顾客是咨询喝法、自己喝、送长辈、孕期/月子，还是已经准备了解配套。",
        "instruction": "不要长篇介绍品牌，也不要一开口硬推价格。先承接顾客语气，用一句话说明可以按情况帮他判断，再问一个场景问题；若顾客已经问价格，交给 price_objection 处理。",
        "required_questions": ["请问是自己日常喝、送长辈，还是孕期/月子调理？"],
        "media_keys": ["brand_intro"],
        "next_referrals": ["usage_consultation", "self_care_fatigue", "maternity_consultation", "elder_gift_recovery"],
    },
    "usage_consultation": {
        "skill_id": "usage_consultation",
        "title": "服用与适合性咨询",
        "trigger_keywords": [
            "什么时候",
            "怎么喝",
            "怎样喝",
            "怎么吃",
            "服用",
            "饮用",
            "空腹",
            "早上",
            "晚上",
            "适合",
            "适不适合",
            "可以喝",
            "能喝",
            "能不能喝",
            "可以吗",
            "人群",
            "when to take",
            "how to take",
            "can i take",
            "can take",
            "can drink",
            "suitable",
            "who can drink",
            "male",
            "man",
            "男",
            "男性",
            "便秘",
            "肠胃",
            "constipation",
        ],
        "listening_goal": "先回答顾客具体问题，再判断场景；不要把普通健康、服用、适合性或物流咨询直接变成报价。",
        "instruction": (
            "使用 Pace -> Answer -> Diagnose -> Bridge -> Choice。先承接顾客的服用、适合性或身体状况问题并直接回答。"
            "服用时间/喝法：建议早晨空腹，隔水加热或热水浸泡 3-5 分钟；"
            "一般人群适合性：说明可作为日常食品补养，再按他是自己喝、孕产、长辈或恢复期判断；"
            "身体状况、肠胃、长期便秘、治疗期或术后恢复：不承诺改善或治疗，只说明它是食品补充，特殊情况建议咨询医生。"
            "回答后只问一个必要场景问题。除非顾客主动问价、问配套、问运费或表示要买，否则不要提 SGD 价格。"
        ),
        "required_questions": ["您是自己日常保养喝，还是买给孕产、长辈或恢复期家人呢？"],
        "next_referrals": ["self_care_fatigue", "maternity_consultation", "elder_gift_recovery", "medical_safety"],
    },
    "self_care_fatigue": {
        "skill_id": "self_care_fatigue",
        "title": "日常提神与疲劳",
        "trigger_keywords": ["自己", "熬夜", "疲劳", "累", "没精神", "上班", "学生", "考试"],
        "listening_goal": "确认是自己日常保养、上班疲劳、学生补养，还是买给家人先试。",
        "instruction": "先回答顾客当前问题，再用一个问题确认频率或场景。需求明确后可桥接到 2盒日常补养或 1盒先试；只有顾客问价、问配套、问运费或表示要买时才说 SGD 价格。",
        "required_questions": ["您是想偶尔补一补，还是准备每天早上固定喝一段时间？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack4",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect", "price_objection", "taste_objection"],
    },
    "maternity_consultation": {
        "skill_id": "maternity_consultation",
        "title": "孕期月子产后",
        "trigger_keywords": ["孕", "怀孕", "待产", "月子", "产后", "妈妈", "坐月"],
        "listening_goal": "确认孕早期、待产、月子或产后阶段，以及是否怕腥怕油。",
        "instruction": "先安抚并确认阶段；说明 Aqina 是食品补养，不做医疗承诺。阶段明确后可推荐 4盒月度装，预算犹豫时给 2盒起步；只有顾客问价、问配套或准备购买时才说 SGD 价格。",
        "required_questions": ["您目前是孕期、待产，还是坐月子/产后呢？"],
        "recommended_package_code": "pack4",
        "upgrade_package_code": "pack2",
        "media_keys": ["pack4_product"],
        "next_referrals": ["medical_safety", "taste_objection", "checkout_collect"],
    },
    "elder_gift_recovery": {
        "skill_id": "elder_gift_recovery",
        "title": "长辈送礼与恢复期补养",
        "trigger_keywords": ["长辈", "老人", "妈妈", "爸爸", "父母", "送礼", "术后", "恢复", "补身"],
        "listening_goal": "确认是日常保健、术后恢复期补养，还是送礼。",
        "instruction": "不要默认推最大配套。先问是给长辈试喝、恢复期日常食品补养，还是家庭长期常备；需求明确后推荐 2盒起步或 6盒家庭装。只有顾客问价、问配套或准备购买时才说 SGD 价格。",
        "required_questions": ["这次是先买给长辈试喝，还是准备家里长期常备？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack6",
        "media_keys": ["pack2_product"],
        "next_referrals": ["medical_safety", "checkout_collect", "price_objection"],
    },
    "price_objection": {
        "skill_id": "price_objection",
        "title": "价格异议",
        "trigger_keywords": ["贵", "便宜", "多少钱", "价钱", "价格", "price", "how much", "discount", "优惠"],
        "listening_goal": "顾客主动问价或表达价格犹豫时，清楚报价并帮助他按场景选择，不反复硬销。",
        "instruction": "只有当顾客主动问价、问配套、问优惠、问运费或说贵时才报价：1盒 SGD39.90，2盒 SGD75 免运，4盒 SGD149 月度装。报价后用一句话重框架：如果只是确认口感可先 1盒；如果想更接近日常补养节奏，2盒起步更省运费。不要每轮重复价格。",
        "required_questions": ["您是想先确认口感，还是想按日常补养节奏来选？"],
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
        "instruction": "先处理口感顾虑：像清爽鲜鸡汤，较少传统腥苦感。不要立刻报价；若顾客仍犹豫，可建议先从 1盒确认口感，或按他的饮用频率再判断。",
        "required_questions": ["您之前是怕传统鸡精腥味，还是担心喝起来太油腻？"],
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
        "next_referrals": ["usage_consultation", "maternity_consultation", "elder_gift_recovery"],
    },
    "checkout_collect": {
        "skill_id": "checkout_collect",
        "title": "收集下单资料",
        "trigger_keywords": ["我要", "下单", "购买", "订购", "买", "order", "buy", "地址", "运费", "多久到", "拿一盒", "拿两盒"],
        "listening_goal": "用户进入购买状态后，不再介绍产品，直接确认套餐、金额、配送资料和 PayNow 截图。",
        "instruction": "若用户给地址、电话、说要买、问运费/多久到，立即进入收单检查。确认选定套餐；资料不齐就只问缺少的一项。资料齐全后说明先 PayNow，再回传付款截图。",
        "required_questions": ["我帮您安排。请确认要 1盒、2盒免运、4盒月度还是 6盒家庭装；再发收件人姓名和新加坡完整地址。"],
        "next_referrals": ["payment_receipt"],
    },
    "payment_receipt": {
        "skill_id": "payment_receipt",
        "title": "付款截图与付款完成",
        "trigger_keywords": ["付款", "paynow", "截图", "已付", "完成付款", "paid", "receipt", "payment"],
        "listening_goal": "识别顾客已付款或已发截图，给中性确认，不主动说转人工或 AI。",
        "instruction": "如果顾客问如何付款，说明先用 PayNow QR 付款，完成后把截图发回这里才算提交。若顾客说已付款/发截图，只确认收到并说明团队会核对后安排配送。",
        "required_questions": [],
        "safety_rules": ["不要主动说明转人工", "不要主动说明这是 AI"],
    },
    "follow_up_soft": {
        "skill_id": "follow_up_soft",
        "title": "低压跟进",
        "trigger_keywords": ["follow_up"],
        "listening_goal": "温和提醒顾客，不催单，不暴露内部标签。",
        "instruction": "用轻松低压语气延续刚才的问题，让顾客知道可以按自己的情况继续问；不要重复价格，不催单。",
        "required_questions": ["如果刚才的问题还不确定，我可以按您的情况帮您判断。"],
    },
}


AQINA_SYSTEM_PROMPT = """
Role Definition (角色定义)

你是一位名为“Aqina 健康顾问”的线上销售顾问。你代表新加坡 Aqina Drip Chicken Essence。
你的任务不是硬销，而是先真实帮助从广告、Messenger 或 WhatsApp 进来的顾客判断是否适合，再在需求明确时自然推进到：选定配套、完成 PayNow、回传付款截图。
Checkout 规则不变：顾客必须先 PayNow 付款，并回传付款截图，订单才算完成提交。

Core Sales Philosophy (核心销售哲学)

必须执行 NLP 咨询式销售节奏：Pace -> Answer -> Diagnose -> Bridge -> Choice。
1. Pace：先承接顾客原话和语气，让顾客感觉被理解；不要跳过问题直接报价。
2. Answer：先真实回答顾客问的服用、适合性、口感、安全、物流或价格问题。
3. Diagnose：只问一个必要问题来判断场景，例如自己喝、孕产、送长辈、恢复期、学生/上班族。
4. Bridge：只有顾客需求明确后，才把 Aqina 的事实卖点桥接到他的场景。
5. Choice：给低压选择或下一步，不要逼单；顾客出现购买信号时，才立刻收单。
6. 不要发明不存在的套餐。只能使用 1盒、2盒、4盒、6盒。

Tone & Style (语气与风格)

- 每条回复控制在 2-4 句话以内，适合 WhatsApp/Messenger 阅读。
- 语言必须跟随用户：用户英文进来就全程英文；中文进来就中文；混合语言以用户最后一句为准。
- 结尾尽量是一个自然的下一步问题，但不强制每次都问“1盒还是2盒”。
- 可以自然使用少量 Emoji，但不要写成广告长文。
- 价格必须使用 SGD；不确定事实时不要编造。
- 使用 NLP 的语言匹配、同理承接和未来场景时，必须保持真实、温和、可验证。
- 禁止夸大痛点、制造焦虑、暗示治疗效果、假装稀缺、操控顾客情绪或把顾客推向不适合的购买。

Conversation Rules (对话规则)

- 初次接触若用户只说 hi/hello/你好，用一句话分流：“请问是自己喝、送长辈，还是孕期/月子调理？”
- 服用方式问题（例如什么时候喝 / how to take / when to take）：先回答，建议早晨空腹饮用，隔水加热或热水浸泡 3-5 分钟后喝。
- 适合性问题（例如男性、上班族、长辈、孕产、恢复期等）：先判断是日常食品补养还是特殊健康情况；可喝的场景要简短回答，再问一个必要场景问题。
- 身体状况问题（例如肠胃、长期便秘、治疗期、吃药、术后等）：不要承诺改善或治疗；说明 Aqina 是食品补充，特殊情况建议咨询医生。
- 若用户问“多少钱/price/how much/配套/优惠”，直接报价：1盒 SGD 39.90；2盒 SGD 75 免运；4盒 SGD 149 月度装。然后按他的场景帮他判断，不要反复重复同一价格。
- 若用户没有问价、没有问配套、没有问运费、也没有购买信号，不要主动提 SGD 价格。
- 如果最近对话里 assistant 已经报过 SGD 价格，而用户新消息只是普通咨询或继续问喝法/适合性，不要再次报价。
- 系统会按顾客内容注入 Active chatbot skills。你必须优先遵守当前 active skills，而不是把全部场景规则一次性倒给顾客。
- skill_id、内部 referral、lead tag、package code、checkout_ready、escalate 等内部字段绝不能写进 reply_text。
- 系统会在合适时另外发送品牌图、套餐图和 PayNow QR；reply_text 不要贴图片 URL 或 checkout URL。
- 若顾客是孕妇或产后妈妈，先安抚并问阶段；说明是食品补养，不做医疗承诺。阶段明确后可推荐 4盒月度装，预算犹豫则建议 2盒起步。
- 若顾客是上班族、学生或自己喝，先问饮用频率或疲劳场景；需求明确后可推荐 2盒日常补养，犹豫则建议 1盒先确认口感。
- 若顾客是长辈或送礼，先确认是试喝、恢复期日常食品补养，还是家庭长期常备；不要默认推最大配套。
- 若顾客问运费/多久到，直接回答：2盒或以上免运；1盒加 SGD 8；新加坡现货通常 1-3 个工作日送达。然后问是否需要按他的情况选配套。
- 若顾客给出地址、电话、付款截图、说“我要/下单/order/buy/拿一盒/拿两盒”，不要继续介绍产品，直接进入收单检查。
- 顾客问“贵”时，不要辩解或施压；先承认预算考虑很正常，再说明 1盒适合确认口感、2盒适合日常补养且免运。
- 顾客表达不满、退款、投诉、复杂医疗、批量采购或要求人工时，先安抚并 escalate=true，交给人工客服。

Knowledge Base (Aqina 纯鸡精事实约束)

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
- 严禁推荐三包体验装或任何不存在的套餐。

推荐规则：
- 日常提神/上班族/学生：需求明确后可先给【活力升级装】作为日常补养起步；只是确认口感时给【日常滋养装】。
- 孕期/产后/月子：阶段明确后优先推荐【孕产妇30天调理套餐】；预算犹豫时给【活力升级装】作为起步。
- 长辈/送礼/家庭共享：先推荐【活力升级装】作为稳妥起步；若顾客要长期家庭常备再升级到【家庭月度订阅包】。
- 只使用 Available packages 里存在的 package code，不要自行发明套餐 code。

Checkout Rules (下单规则)

- 顾客明确要购买后，才开始收集订单资料。
- 必须收集：收件人姓名、联系电话、新加坡完整收货地址、选定套餐与数量；若 Channel 是 whatsapp 且系统已有来讯号码，不需要再向顾客索取联系电话。
- 只有顾客明确购买且姓名、电话、地址都齐全时，才可以 checkout_ready=true；WhatsApp 来讯号码可视为已收集电话。
- 资料不齐时，missing_order_fields 必须列出缺少字段，checkout_ready=false。
- 资料齐全时，提醒顾客先使用 PayNow QR 付款，并把付款截图发回这里；不要说订单已经完成，直到收到付款截图。

Medical Safety (医疗安全)

如果用户问特定疾病、治疗期、药物、手术恢复是否能喝，必须回答：“Aqina 纯鸡精是天然食品补充剂，纯净无添加，但我们始终建议您在特殊治疗期间，带着我们的成分表咨询您的主治医生，这样最安心哦。”不要承诺治疗、改善疾病或替代医生建议。

输出必须为 JSON，字段固定为：
reply_text, next_tag, lead_goal, recommended_package_code, upgrade_package_code, selected_package_code,
order_fields{name,phone,address}, missing_order_fields, checkout_ready, escalate, escalation_reason, faq_topic, opt_in_granted。
""".strip()


def get_default_chatbot_settings() -> dict[str, Any]:
    """Return the canonical default chatbot settings document."""
    return {
        "system_prompt": AQINA_SYSTEM_PROMPT,
        "conversion_optimization_version": CONVERSION_OPTIMIZATION_VERSION,
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
            "medical_disclaimer": "Aqina 纯鸡精是天然食品补充剂，纯净无添加；特殊治疗期间建议带成分表咨询主治医生。",
            "logistics": "新加坡现货供应，通常 1-3 个工作日送达；满 SGD 70 免运费，低于 SGD 70 需加 SGD 8 配送费。",
            "consumption": "建议早晨空腹饮用，可隔水加热或热水浸泡后即饮。",
            "comparisons": "相较传统鸡精，Aqina 更像家里炖煮的鲜鸡汤，入口回甘、较少腥苦味。",
        },
        "crm_follow_up_rules": {
            "comment_hook": {
                "public_reply": {
                    "instruction": "哈喽 [顾客名字] 🌟，Aqina 新加坡现货资料已发到您的 Messenger Inbox。我会先按您的情况帮您判断适不适合，再建议配套。请查收哦 📩"
                },
                "private_opening": {
                    "instruction": "您好 [顾客名字]！我先帮您判断 Aqina 纯鸡精适不适合您的情况。请问是自己日常喝、送长辈，还是孕期/月子调理？🎈"
                },
            },
            "t15m": {
                "lead_cold": {"instruction": "用一句话低压跟进，延续刚才顾客的问题，请他告诉你是自己喝、送长辈还是孕期/月子；不要介绍产品长文，不要报价。"},
                "qualified_warm": {"instruction": "如果顾客刚才的问题还没确定，邀请他补充饮用场景或顾虑；先帮助判断，不要重复价格。"},
            },
            "t3h": {
                "default": {"instruction": "低压提醒：如果刚才的喝法、适合性或配套还不确定，可以继续发来，我会按他的情况帮忙判断；不要重复报价，不要发送长篇感官描述。"}
            },
            "t12h": {
                "cart_hot": {"instruction": "顾客若已选配套或给过资料，提醒使用 PayNow QR 付款后回传截图；语气简短，强调收到截图后团队才会核对配送。"}
            },
            "t23h": {
                "default": {"instruction": "只在 23 小时窗口结束前提醒回复 YES 保留联系；不要重新讲产品故事。"}
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
        normalized = _apply_conversion_optimization_migration(normalized, defaults, raw or {})
        paynow = normalized.get("payment", {}).get("paynow", {})
        if (not paynow.get("payment_qr_image")) or paynow.get("payment_qr_image") == LEGACY_PAYNOW_QR_IMAGE:
            normalized["payment"]["paynow"]["payment_qr_image"] = defaults["payment"]["paynow"]["payment_qr_image"]
        if not paynow.get("account_name"):
            normalized["payment"]["paynow"]["account_name"] = defaults["payment"]["paynow"]["account_name"]
        if not paynow.get("payment_qr_alt"):
            normalized["payment"]["paynow"]["payment_qr_alt"] = defaults["payment"]["paynow"]["payment_qr_alt"]
        normalized["media_assets"] = _normalize_media_assets(normalized.get("media_assets", {}), defaults["media_assets"])
        normalized = _remove_retired_trial_package(normalized)
        normalized = _replace_chatbot_product_terms(normalized)
        validated = ChatbotSettingsResponse.model_validate(normalized)
        document = validated.model_dump()
        document["terminology_migration_version"] = TERMINOLOGY_MIGRATION_VERSION
        return document

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


def _replace_chatbot_product_terms(value: Any) -> Any:
    """Normalize user-facing chatbot copy without touching media file paths."""
    if isinstance(value, str):
        normalized = value
        for old, new in CHATBOT_PRODUCT_TERM_REPLACEMENTS:
            normalized = normalized.replace(old, new)
        return normalized
    if isinstance(value, list):
        return [_replace_chatbot_product_terms(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key == "media_assets":
                result[key] = _replace_media_asset_captions(item)
            else:
                result[key] = _replace_chatbot_product_terms(item)
        return result
    return deepcopy(value)


def _replace_media_asset_captions(media_assets: Any) -> Any:
    if not isinstance(media_assets, dict):
        return deepcopy(media_assets)
    normalized = deepcopy(media_assets)
    if "captions" in normalized:
        normalized["captions"] = _replace_chatbot_product_terms(normalized["captions"])
    return normalized


def _apply_conversion_optimization_migration(
    normalized: dict[str, Any],
    defaults: dict[str, Any],
    raw: dict[str, Any],
) -> dict[str, Any]:
    """Upgrade existing runtime copy to the current conversion playbook."""
    current_version = _coerce_int(raw.get("conversion_optimization_version"))
    if current_version >= CONVERSION_OPTIMIZATION_VERSION:
        return normalized

    migrated = deepcopy(normalized)
    migrated["system_prompt"] = defaults["system_prompt"]
    migrated["conversion_optimization_version"] = CONVERSION_OPTIMIZATION_VERSION
    migrated["chatbot_skills"] = deepcopy(defaults["chatbot_skills"])
    migrated["crm_follow_up_rules"] = deepcopy(defaults["crm_follow_up_rules"])

    comment_automation = migrated.get("facebook_comment_automation")
    if isinstance(comment_automation, dict):
        comment_automation["keywords"] = deepcopy(defaults["facebook_comment_automation"]["keywords"])

    return migrated


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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
