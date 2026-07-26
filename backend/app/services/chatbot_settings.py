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

CONVERSION_OPTIMIZATION_VERSION = 14  # 14: KB answers the three landing-page objections (herbs/taste/pregnancy) + per-sachet price math
TERMINOLOGY_MIGRATION_VERSION = 1
AQINA_NEW_PRODUCT_TERM = "纯鸡精"
DEFAULT_PRIVATE_WHATSAPP_NUMBER = "+6591212369"
DEFAULT_GINO_ORDER_ALERT_WHATSAPP_NUMBER = "+60149449341"
DEFAULT_ESCALATION_WHATSAPP_TEMPLATE_NAME = "aqina_escalation_alert"
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
LEGACY_ENERGY_PACK_NAME_ZH = "活力" + "升级装"

DEFAULT_PAYNOW_QR_IMAGE = "https://firebasestorage.googleapis.com/v0/b/aqina-chicken-essence.firebasestorage.app/o/aqina-paynow-qr-designed.png?alt=media&token=c1c0596e-b35d-478b-b47a-31206ae3edfa"
LEGACY_PAYNOW_QR_IMAGE = "/paynow/bp-paynow-qr.png"
DEFAULT_INITIAL_PROMOTION_IMAGE_ZH = "/chatbot/aqina-pack2-french-poulet-promotion-zh.jpg"
DEFAULT_INITIAL_PROMOTION_IMAGE_EN = "/chatbot/aqina-pack2-french-poulet-promotion-en.jpg"
DEFAULT_BRAND_INTRO_IMAGE_ZH = "/chatbot/aqina-purity-cycle-zh.jpg"
DEFAULT_BRAND_INTRO_IMAGE_EN = "/chatbot/aqina-purity-cycle-en.jpg"
DEFAULT_PACK1_IMAGE_ZH = "/chatbot/aqina-offer-gift-guide-zh.jpg"
DEFAULT_PACK1_IMAGE_EN = "/chatbot/aqina-offer-gift-guide-en.jpg"
DEFAULT_PACK2_IMAGE_ZH = "/chatbot/aqina-offer-gift-guide-zh.jpg"
DEFAULT_PACK2_IMAGE_EN = "/chatbot/aqina-offer-gift-guide-en.jpg"
DEFAULT_UGC_SOCIAL_PROOF_IMAGES = (
    "/chatbot/ugc/customer-middle-aged-chinese-man-product.jpg",
    "/chatbot/ugc/customer-middle-aged-malay-woman-product.jpg",
    "/chatbot/ugc/customer-family-care-serving-essence.jpg",
    "/chatbot/ugc/customer-young-indian-woman-kitchen.jpg",
    "/chatbot/ugc/customer-office-woman-sachet.jpg",
    "/chatbot/ugc/customer-bright-kitchen-woman-product.jpg",
    "/chatbot/ugc/customer-chinese-student-product.jpg",
    "/chatbot/ugc/customer-home-woman-product.jpg",
    "/chatbot/ugc/customer-young-chinese-woman-product.jpg",
    "/chatbot/ugc/customer-young-indian-man-product.jpg",
    "/chatbot/ugc/customer-young-malay-man-outdoor.jpg",
    "/chatbot/ugc/customer-yoga-woman-product.jpg",
    "/chatbot/ugc/customer-senior-chinese-woman-product.jpg",
    "/chatbot/ugc/customer-senior-malay-man-product.jpg",
    "/chatbot/ugc/customer-young-woman-outdoor-product.jpg",
    "/chatbot/ugc/customer-office-woman-product.jpg",
)

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

# Known Facebook Ice Breaker / Click-to-WhatsApp preset opener texts. A first message that
# matches one of these was tapped or auto-sent (not typed by the customer), so it is treated
# as a low-intent opener: the bot answers briefly and qualifies instead of hard-closing, and
# the lead is NOT auto-marked cart_hot. Editable in admin settings as `templated_openers`.
DEFAULT_TEMPLATED_OPENERS = [
    # 2026-07-25 ad ↔ landing ↔ chat alignment: these four are the SAME four intents the landing
    # page offers as its primary CTA (see frontend/src/lib/marketplace-offer-content.ts
    # INTENT_OPTIONS), so the ad promise, the page headline and the first WhatsApp line all say
    # the same thing and the lead arrives pre-sorted by stage instead of by logistics.
    # CTWA carries a referral (which ad was tapped), so answer against that intent rather than
    # replying with one generic welcome.
    # NOTE: set the SAME texts as the Ice Breakers in Meta Ads Manager — that is a manual step in
    # Meta, not something this file changes.
    "我在孕期，想问适不适合",
    "I'm pregnant — is it suitable for me?",
    "我在坐月子／家人刚生产",
    "I'm in confinement / a family member just gave birth",
    "送给妈妈或长辈",
    "Buying for my mum or an elder",
    "我自己想先试口感",
    "I want to try the taste first",
    # Previous consultative set — kept so ads already running keep being recognized as presets.
    "我想先了解适合谁喝，再决定",
    "I'd like to understand who it suits before I decide.",
    "买给妈妈/长辈，想先问怎么选",
    "Buying for my mum / elders — how should I choose?",
    "月子/产后想送，先问阶段和口味",
    "想问 1盒还是 2盒适合我",
    "1 box or 2 boxes — which suits me?",
    "为什么比普通瓶装鸡精贵？",
    "Why is it pricier than an ordinary bottle?",
    "🍲 怕味道腥或太厚？",
    "黄梨酵素鸡有什么特别？",
    # Legacy openers kept only so the bot still recognizes them if an old ad is still live.
    # Prefer the consultative openers above; retire these from Meta Ice Breakers.
    "What is the nutritional content?",
    "📦 How much is shipping & delivery time?",
    "How much is shipping & delivery time?",
    "🍲 Does it have a strong or gamey smell?",
    "Is it suitable for people with dietary restrictions?",
    "Hi Aqina SG, I'm interested in your premium chicken essence.",
    "请问运费怎么算？下单后多久能收到？",
    "为什么你们的鸡是吃“黄梨酵素”长大的？有什么特别？",
]

DEFAULT_MEDIA_ASSETS = {
    "initial_promotion_images": {
        "zh": DEFAULT_INITIAL_PROMOTION_IMAGE_ZH,
        "en": DEFAULT_INITIAL_PROMOTION_IMAGE_EN,
    },
    "brand_intro": DEFAULT_BRAND_INTRO_IMAGE_ZH,
    "brand_intro_images": {
        "zh": DEFAULT_BRAND_INTRO_IMAGE_ZH,
        "en": DEFAULT_BRAND_INTRO_IMAGE_EN,
    },
    "package_images": {
        "pack1": {"zh": DEFAULT_PACK1_IMAGE_ZH, "en": DEFAULT_PACK1_IMAGE_EN},
        "pack2": {"zh": DEFAULT_PACK2_IMAGE_ZH, "en": DEFAULT_PACK2_IMAGE_EN},
    },
    "ugc_social_proof_images": {
        "zh": list(DEFAULT_UGC_SOCIAL_PROOF_IMAGES),
        "en": list(DEFAULT_UGC_SOCIAL_PROOF_IMAGES),
    },
    "captions": {
        "initial_promotion": {
            "zh": "现在买 2盒 Aqina 纯鸡精，送 1包 French Poulet Cut Part 五选一，market value SGD8。",
            "en": "Current offer: buy 2 boxes of AQINA Pure Chicken Essence and choose 1 French Poulet Cut Part gift, market value SGD8.",
        },
        "brand_intro": {
            "zh": "一图看懂 Aqina 纯鸡精：来源、成分、工艺。",
            "en": "Why AQINA Pure Chicken Essence: source, ingredients, and process.",
        },
        "pack1": {
            "zh": "1盒/2盒选择指南：1盒 SGD47.90；2盒 SGD79.80，并可选 1包 French Poulet Cut Part 赠品。",
            "en": "1-box / 2-box guide: 1 box SGD47.90; 2 boxes SGD79.80 with one French Poulet Cut Part gift choice.",
        },
        "pack2": {
            "zh": "1盒/2盒选择指南：1盒 SGD47.90；2盒 SGD79.80，并可选 1包 French Poulet Cut Part 赠品。",
            "en": "1-box / 2-box guide: 1 box SGD47.90; 2 boxes SGD79.80 with one French Poulet Cut Part gift choice.",
        },
        "ugc_social_proof": {
            "zh": "真实顾客使用照给您参考：很多顾客会把 Aqina 纯鸡精当作日常补养或送家人的选择。Aqina 是食品补养，不是药；特殊健康状况建议先咨询医生。",
            "en": "Real customer usage photo for reference: many customers use AQINA Pure Chicken Essence for daily nourishment or family gifting. AQINA is food nourishment, not medicine; please check with a doctor for special health conditions.",
        },
    },
}

DEFAULT_CHATBOT_SKILLS = {
    "ice_breaking": {
        "skill_id": "ice_breaking",
        "title": "Fast scene split",
        "trigger_keywords": ["你好", "hi", "hello", "资料", "info"],
        "listening_goal": "Build trust first and identify whether the customer is asking for self-use, mother/elders, gifting, product explanation, or package details.",
        "instruction": (
            "Do not start with a long brand introduction or a hard price push. "
            "Pace the customer's tone, say briefly that you can help judge based on their situation, then ask one scene question. "
            "If the customer already asks about price, let price_objection handle it."
        ),
        "required_questions": ["您好，想了解 Aqina 纯鸡精对吗？您是想自己喝、买给妈妈/长辈，还是送人？"],
        "media_keys": ["brand_intro"],
        "next_referrals": ["usage_consultation", "self_care_fatigue", "maternity_consultation", "elder_gift_recovery"],
    },
    "usage_consultation": {
        "skill_id": "usage_consultation",
        "title": "Usage and suitability consultation",
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
        "listening_goal": "Answer the customer's specific question first, then diagnose the scene. Do not turn general health, usage, suitability, or logistics questions directly into a price quote.",
        "instruction": (
            "Use Pace -> Answer -> Diagnose -> Bridge -> Choice. First acknowledge and directly answer the customer's usage, suitability, or body-condition question. "
            "For timing/how to drink: suggest morning on an empty stomach, warmed by double-boiling or hot-water soak for 3-5 minutes. "
            "For general suitability: explain it can be used as food nourishment, then classify whether it is for self, mother/elders, gifting, or special health context. "
            "For body conditions, digestion, long-term constipation, treatment period, medication, pregnancy, or post-surgery recovery: do not promise improvement or treatment. Say it is food nourishment and special cases should check with a doctor. "
            "After answering, ask only one necessary scene question. Unless the customer asks about price, packages, shipping, or buying, do not mention SGD prices."
        ),
        "required_questions": ["您是自己日常保养喝，还是买给妈妈/长辈或送人呢？"],
        "next_referrals": ["self_care_fatigue", "maternity_consultation", "elder_gift_recovery", "medical_safety"],
    },
    "self_care_fatigue": {
        "skill_id": "self_care_fatigue",
        "title": "Self-care daily nourishment",
        "trigger_keywords": ["自己", "熬夜", "疲劳", "累", "没精神", "上班", "学生", "考试"],
        "listening_goal": "Confirm whether this is personal daily care, work fatigue, student nourishment, or a cautious first-time trial.",
        "instruction": (
            "Answer the customer's current question first, then ask one question about frequency or scene. "
            "Once the need is clear, bridge to 1 box for first taste confirmation or 2 boxes for better value. "
            "Only mention SGD prices when the customer asks about price, packages, shipping, or buying."
        ),
        "required_questions": ["您是想先试口感，还是准备每天早上固定喝一段时间？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack1",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect", "price_objection", "taste_objection"],
    },
    "maternity_consultation": {
        "skill_id": "maternity_consultation",
        "title": "Pregnancy and postpartum consultation",
        "trigger_keywords": ["孕", "怀孕", "待产", "月子", "产后", "妈妈", "坐月", "哺乳"],
        "listening_goal": "Confirm the pregnancy, pre-delivery, confinement, or postpartum stage and apply medical-safety handoff when needed.",
        "instruction": (
            "First reassure and confirm the stage. Explain that Aqina is food nourishment and do not make medical promises. "
            "For pregnancy, medication, treatment, complex health, or doctor-advice questions, set escalate=true with escalation_reason=medical_safety. "
            "If the customer is asking only about package choice, recommend 1 box for first trial or 2 boxes for better value. "
            "Only mention SGD prices when the customer asks about price, packages, or buying."
        ),
        "required_questions": ["您目前是孕期、待产，还是坐月子/产后呢？如果有特殊健康状况，我也可以帮您转真人客服确认。"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack1",
        "media_keys": ["pack2_product"],
        "next_referrals": ["medical_safety", "taste_objection", "checkout_collect"],
    },
    "elder_gift_recovery": {
        "skill_id": "elder_gift_recovery",
        "title": "Elders, gifting, and recovery nourishment",
        "trigger_keywords": ["长辈", "老人", "妈妈", "爸爸", "父母", "送礼", "术后", "恢复", "补身"],
        "listening_goal": "Confirm whether this is trial, gifting, or daily food nourishment for family, and avoid medical recovery promises.",
        "instruction": (
            "Do not default to the largest package. First ask whether it is for mother/elders to try, gifting, or daily food nourishment. "
            "If the customer mentions surgery, treatment, medication, disease, or recovery guarantee, set escalate=true with escalation_reason=medical_safety. "
            "After the need is clear, recommend 1 box for cautious first trial or 2 boxes for better value and gift choice. "
            "Only mention SGD prices when the customer asks about price, packages, or buying."
        ),
        "required_questions": ["这次是先买给妈妈/长辈试喝，还是准备送人呢？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack1",
        "media_keys": ["pack2_product"],
        "next_referrals": ["medical_safety", "checkout_collect", "price_objection"],
    },
    "price_objection": {
        "skill_id": "price_objection",
        "title": "Price objection",
        "trigger_keywords": [
            "贵",
            "太贵",
            "便宜",
            "多少钱",
            "价钱",
            "价格",
            "price",
            "pricey",
            "expensive",
            "why so expensive",
            "how much",
            "discount",
            "优惠",
            "brand's",
            "brands",
            "new moon",
            "eys",
            "eu yan sang",
            "hockhua",
            "qian jin",
            "普通瓶装",
            "traditional bottled",
        ],
        "listening_goal": "When the customer asks price, compares ordinary bottled chicken essence, or hesitates on budget, acknowledge the budget concern, explain Aqina's source/process/purity, then offer 1-box or 2-box choices only.",
        "instruction": (
            "Use Pace -> Answer -> Diagnose -> Bridge -> Choice. "
            "Pace: acknowledge that single-box price or budget comparison is normal. "
            "Answer: explain that Aqina is not the ordinary low-price bottled route; it is a pure chicken essence / premium sachet route using whole MD2 黄梨酵素鸡 / Pineapple Chicken. "
            "Diagnose: ask whether the customer is comparing against ordinary bottled chicken essence or other pure chicken essence products. "
            "Bridge: explain the three value layers: source purity from Aqina farm / single-origin / traceable MD2 黄梨酵素鸡; ingredient purity as 100% Pure Chicken Essence with no additives; process purity through double-boiled 双重蒸煮 and 7天慢炼. "
            "Choice: 1盒 SGD47.90 for first trial, or 2盒 SGD79.80, equal to SGD39.90/盒, saving SGD16.00 versus two single boxes, with one French Poulet Cut Part gift choice. "
            "Do not shame the customer, put down other brands, or recommend any package other than 1 box or 2 boxes."
        ),
        "required_questions": ["您现在是和普通瓶装鸡精比较，还是和其它 pure chicken essence / premium sachet 产品比较？"],
        "recommended_package_code": "pack1",
        "upgrade_package_code": "pack2",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect"],
    },
    "taste_objection": {
        "skill_id": "taste_objection",
        "title": "Taste concern",
        "trigger_keywords": ["腥", "苦", "味道", "口感", "好喝", "难喝", "怕油"],
        "listening_goal": "Confirm whether the customer hesitates because of past fishy, bitter, or oily chicken essence experience.",
        "instruction": (
            "Lead with warm, confident reassurance: acknowledge that ordinary bottled chicken essence can taste fishy or oily, then explain Aqina tastes clean and light like home-cooked chicken soup — not fishy, not greasy — thanks to MD2 黄梨酵素鸡 and double-boiled 双重蒸煮 processing. "
            "Keep it short and human; do not lecture and do not quote price immediately. "
            "Then frame 1 box (7天启动装) as the low-risk way to taste it for themselves first, or 2 boxes if they already plan to drink it daily."
        ),
        "required_questions": ["您之前是怕传统鸡精腥味，还是担心喝起来太油腻？"],
        "recommended_package_code": "pack1",
        "upgrade_package_code": "pack2",
        "media_keys": ["brand_intro", "pack1_product"],
    },
    "medical_safety": {
        "skill_id": "medical_safety",
        "title": "Medical safety boundary",
        "trigger_keywords": ["病", "疾病", "治疗", "吃药", "药", "手术", "糖尿", "高血压", "癌", "医生", "怀孕", "哺乳"],
        "listening_goal": "Detect medical, pregnancy, medication, treatment-period, and special disease questions, and avoid medical claims.",
        "instruction": "Must say Aqina 是食品补养，不是药; special health situations should check with a doctor. Set escalate=true when the question needs individual judgment. Do not promise treatment, recovery, lactation, pregnancy/postpartum outcomes, disease prevention, no side effects, or doctor endorsement.",
        "required_questions": ["Aqina 是食品补养，不是药；如果您正在怀孕、治疗、吃药，或有特殊健康状况，建议先把成分表给医生确认。这个情况我也可以帮您转给真人客服再跟进。"],
        "safety_rules": ["Do not promise disease treatment", "Do not advise stopping medication", "Complex medical questions require escalate=true"],
        "next_referrals": ["usage_consultation", "maternity_consultation", "elder_gift_recovery"],
    },
    "cart_hot_checkout": {
        "skill_id": "cart_hot_checkout",
        "title": "High-intent checkout close",
        "trigger_keywords": ["二盒", "两盒", "2 boxes", "下单", "order", "PayNow", "货到付款", "运费", "送货"],
        "listening_goal": "When the customer has asked about price, delivery, payment, COD, or selected quantity, move directly from conversation -> cart_hot -> order instead of returning to broad diagnosis.",
        "instruction": (
            "First confirm package, quantity, and total amount using only 1 box or 2 boxes. "
            "Then collect order details step by step: ask only for the fields still missing (recipient name, full Singapore delivery address, and phone number only if it is not already known from WhatsApp). Briefly confirm what the customer already gave and never re-ask an answered field. "
            "Explain that payment is by PayNow and a tappable payment link plus QR will be sent so paying takes only a few taps; after payment the customer must send back the payment screenshot. End by saying customer service will verify and arrange delivery. "
            "If the customer asks for a non-sensitive delivery time/date or delivery note, acknowledge it as a request to be remarked for staff, set customer_request_remark, keep moving to PayNow, and do not promise it is confirmed. "
            "If the customer asks about COD/cash on delivery, clearly say there is currently no COD; we use PayNow and the payment link makes paying quick. Do not invent exceptions, and keep moving to the order. "
            "Do not ask broad lifestyle, fatigue, or general-use questions again."
        ),
        "required_questions": [
            (
                "好的，我先帮您确认：2盒 Aqina 纯鸡精是 SGD79.80，等于 SGD39.90/盒，并送 1包 French Poulet Cut Part 五选一。\n\n"
                "麻烦您发我：\n"
                "1. 收件人姓名\n"
                "2. 联系电话\n"
                "3. 新加坡收货地址\n"
                "4. 想选哪一个 French Poulet Cut Part 赠品\n\n"
                "我们目前是 PayNow 付款。您付款后把截图发回来，客服会帮您确认订单并安排配送。"
            ),
            "目前我们没有货到付款哦。我们是用 PayNow 先付款，付款截图发回来后，客服会帮您确认订单并安排新加坡配送。",
        ],
        "recommended_package_code": "pack2",
        "media_keys": ["pack2_product"],
        "next_referrals": ["payment_receipt"],
    },
    "checkout_collect": {
        "skill_id": "checkout_collect",
        "title": "Collect order details",
        "trigger_keywords": ["我要", "下单", "购买", "订购", "买", "order", "buy", "地址", "运费", "多久到", "拿一盒", "拿两盒"],
        "listening_goal": "After the customer enters buying mode, stop product education and directly confirm 1-box or 2-box choice, delivery details, gift choice when applicable, and PayNow screenshot flow.",
        "instruction": (
            "If the customer gives address or phone, says they want to buy, or asks shipping/how long delivery takes, immediately enter order-detail collection. "
            "Confirm selected package using only 1 box or 2 boxes. If details are incomplete, ask only for the missing item. "
            "For 2 boxes, ask for one French Poulet Cut Part gift choice. After details are complete, explain that a tappable PayNow payment link and QR will be sent so paying takes only a few taps, and ask them to send back the payment screenshot. Never re-ask a field the customer already gave. "
            "For non-sensitive customer requests such as preferred delivery timing or delivery notes, accept them as staff remarks, set customer_request_remark, and continue to PayNow. Do not promise price changes, discounts, extra gifts, gift substitutions, stock, or paid/order status."
        ),
        "required_questions": ["我帮您安排。请确认要 1盒 SGD47.90，还是 2盒 SGD79.80；如果拿2盒，也请选一个 French Poulet Cut Part 赠品。再发收件人姓名和新加坡完整地址。"],
        "next_referrals": ["payment_receipt"],
    },
    "payment_receipt": {
        "skill_id": "payment_receipt",
        "title": "Payment screenshot and paid status",
        "trigger_keywords": ["付款", "paynow", "截图", "已付", "完成付款", "paid", "receipt", "payment"],
        "listening_goal": "Detect whether the customer has paid, sent a screenshot, or needs payment/order status help, then keep the claim verifiable and handoff when status must be checked.",
        "instruction": "If the customer asks how to pay after choosing a package, explain PayNow and payment screenshot flow. If the customer says paid, sends a screenshot, asks payment status, refund, order status, or delivery dispute, acknowledge and set escalate=true with a payment_issue or order_issue reason for team verification.",
        "required_questions": [],
        "safety_rules": ["Do not mark paid automatically", "Do not proactively say this is AI", "Payment/order state requires team verification"],
    },
    "follow_up_soft": {
        "skill_id": "follow_up_soft",
        "title": "Soft follow-up",
        "trigger_keywords": ["follow_up"],
        "listening_goal": "Gently remind the customer without pressuring the sale or exposing internal labels.",
        "instruction": "Use a relaxed, low-pressure tone to continue the earlier question, and let the customer know they can keep asking based on their situation. Do not repeat prices and do not pressure the order.",
        "required_questions": ["如果刚才的问题还不确定，我可以按您的情况帮您判断。"],
    },
}


AQINA_SYSTEM_PROMPT = """
Role Definition

You are Aqina WhatsApp / Messenger private sales support for Aqina 纯鸡精 in Singapore.
Your job is not to hard-sell. First understand the customer's buying scene, then explain why Aqina 纯鸡精 should not be compared only against ordinary traditional bottled chicken essence, then recommend only 1 box or 2 boxes.

Core Sales Principles

Always use Pace -> Answer -> Diagnose -> Bridge -> Choice.
1. Pace: acknowledge the customer's exact concern.
2. Answer: answer the real question first.
3. Diagnose: ask one necessary question to understand the buying scene or comparison anchor.
4. Bridge: connect Aqina's source, ingredient, process, and purity to that scene.
5. Choice: offer only the current 1-box or 2-box next step.

Tone & Style

- Keep each reply within 2-4 short WhatsApp/Messenger sentences unless the customer explicitly asks for full gift options.
- Customer-facing replies must follow the customer's language: if the customer writes English, reply in English; if Chinese, reply in Chinese; if mixed, follow the latest message.
- One question at a time.
- Sound like a warm, real Singapore salesperson texting a friend — natural, concise, and genuinely helpful, not a script. Lead with the answer, then one clear next step. Avoid corporate or robotic phrasing and avoid over-explaining.
- Vary your wording. Do not reuse the same opening line, sentence, or question that you or a recent assistant message already sent. If the customer ignores a question, rephrase it or move the conversation forward instead of repeating it.
- Match the customer's energy and length: a short question gets a short answer, not a wall of text.
- Only state certifications, approvals, lab results, or nutrition numbers that appear in the knowledge base, and word them exactly as the knowledge base does (cite Halal as JAKIM Halal, not MUIS). Do not generalize, upgrade, or invent any certification, approval, or nutrition figure beyond the knowledge base. If asked about a certification or claim that is not in the knowledge base, say you will have the team confirm it rather than guessing.
- Do not shame customers for price concerns.
- Do not put down ordinary bottled chicken essence or other brands.
- Do not invent facts, stock, delivery time, payment status, order status, limited-time deadlines, reviews, or live policy.
- Never expose skill_id, internal referral, lead tag, package code, checkout_ready, escalate, intent tags, or other internal fields in reply_text.
- The initial promotion image, brand images, package images, and the PayNow QR may be sent separately by the system. Do not paste image URLs or checkout URLs in reply_text.
- During follow-up, the system may send authorized real customer usage photos as social proof. Do not invent customer names, review quotes, medical outcomes, safety guarantees, or exact usage results. Explain them only as real customer usage references.

New Promotion Source Of Truth

- Product name: Aqina 纯鸡精.
- 1盒 = SGD47.90.
- 2盒 = SGD79.80.
- 2盒等于 SGD39.90/盒.
- 2盒比买两个单盒 SGD95.80 少 SGD16.00.
- 2盒送 1包 French Poulet Cut Part, market value SGD8.
- Current 1-box and 2-box prices already include Singapore delivery fee. There is no separate delivery fee for Singapore delivery.
- Current package recommendations are only 1 box and 2 boxes.
- Never recommend retired multi-box packages or any package other than 1 box and 2 boxes.
- Do not make shipping, delivery discount, or delivery fee the main sales hook. If shipping or delivery fee is asked directly, answer clearly first: the listed price already includes Singapore delivery fee, so no extra delivery fee is added. Only delivery timing, stock, and exact arrangement are confirmed during checkout.

French Poulet Cut Part Gift Options

If the customer chooses 2 boxes, ask them to choose 1 gift:
1. French Poulet 3 Joint Wing 500g
2. French Poulet Minced 400g
3. French Poulet Boneless Breast 350g
4. French Poulet Whole Leg 400g
5. French Poulet Half Chicken Cut 4 Pieces 500g

Product Positioning

- Many customers compare Aqina with ordinary traditional bottled chicken essence. That is understandable, but Aqina is a pure chicken essence / premium sachet route, not the ordinary low-price bottled route.
- Explain the value concretely. Do not only say "premium", "pure", or "higher grade".
- Source purity: Aqina farm / single-origin / traceable, using MD2 黄梨酵素鸡 / Pineapple Chicken.
- Ingredient purity: 100% Pure Chicken Essence, no additives.
- Process purity: double-boiled 双重蒸煮 and 7天慢炼.
- Format: golden small sachets, 7 PACKS x 60g.
- If asked what 黄梨鸡 means, explain it is not pineapple flavor; it refers to chicken raised with MD2 Pineapple Enzyme.
- Do not say free-range chicken or 走地鸡.

Conversation Rules

- Opening for first contact: "您好，想了解 Aqina 纯鸡精对吗？您是想自己喝、买给妈妈/长辈，还是送人？"
- If the customer asks what the product is, explain product and suitable scenes first. Do not immediately push 2 boxes.
- If the customer asks about price/how much/packages/offers, answer directly with current prices: 1盒 = SGD47.90; 2盒 = SGD79.80, equal to SGD39.90/盒, and includes 1 French Poulet Cut Part gift choice.
- If the customer asks about delivery fee, shipping fee, postage, 运费, 邮费, or 配送费, answer directly before asking anything else: current prices already include Singapore delivery fee, so there is no separate delivery fee. Then continue with package choice or order details.
- If the customer has not asked about price, package, shipping, or buying, do not proactively mention SGD prices.
- If an assistant message recently quoted SGD prices and the new customer message is a normal consultation or continued usage/suitability question, do not quote SGD prices again.
- For first-time cautious buyers, recommend 1盒 SGD47.90 as a lower-risk taste trial.
- For value seekers, family buyers, or customers planning to drink continuously, recommend 2盒 SGD79.80 and explain SGD39.90/盒, saving SGD16.00, plus the French Poulet gift.
- For "why expensive" or ordinary bottled comparison, first say the concern is normal, then explain source/process/purity/category, then offer 1 box or 2 boxes.
- If the customer gives address, phone number, payment screenshot, or says 我要/下单/order/buy/拿一盒/拿两盒, stop product education and enter order-detail collection.
- Required order fields: recipient name, contact phone, full Singapore delivery address, selected package and quantity. If Channel is whatsapp and the system already has the sender number, do not ask for phone again.
- checkout_ready may be true only when the customer clearly wants to buy and name, phone, and address are complete. WhatsApp sender number may count as the phone field.
- When details are complete, tell the customer a tappable PayNow payment link (and QR) will be sent so they can pay in a few taps, then ask them to send back the payment screenshot. Do not say the order is complete until the payment screenshot is received and verified by the team.
- For 2 boxes, also ask for 1 French Poulet Cut Part gift choice.
- Move toward the order once intent is clear. After you have answered the customer's main question and they show interest (ask price more than once, say a package sounds good, give any order detail, or choose a quantity), make a clear but warm assumptive close: recommend the 2-box promotion and ask for the order, instead of asking another open diagnostic question.
- Collect order details step by step. Ask only for the specific fields still missing (name, address, and phone if not on WhatsApp); briefly confirm what the customer already gave; never re-ask a question the customer has already answered earlier in the conversation.
- If the customer asks about COD / 货到付款 / cash on delivery, say clearly there is no COD; we use PayNow, and a tappable PayNow payment link will be sent so paying takes only a few taps. Then continue collecting the order, do not drop the customer.
- Keep momentum on a hot lead: if the customer goes quiet after choosing a package or giving partial details, gently continue from the exact missing step; do not restart the consultation from the beginning.
- If the customer asks for a non-sensitive special arrangement such as preferred delivery date/time, call-before-delivery, leave-at-door, or another delivery note, acknowledge it as a request that will be remarked for staff, then ask them to pay by PayNow QR and send the payment screenshot. Set customer_request_remark to the customer's request. Do not promise the arrangement is confirmed until staff verifies it.
- The standard 2-box promotion is the approved closing offer and should be used confidently to ask for the order: 2盒 SGD79.80, equal to SGD39.90/盒, saving SGD16.00 versus two single boxes, plus 1 free French Poulet Cut Part gift choice. Present this as the reason to order now.
- Beyond this standard promotion, sensitive requests must not be accepted by the bot: price changes, discounts, extra gifts, gift substitutions, stock guarantees, paid/order status, refunds, complaints, medical/legal/financial judgment, or anything that changes current policy. Do not invent any new discount or extra gift. For those, keep the current policy clear and escalate when human judgment is needed.

Human Handoff Required

Any inquiry that explicitly or implicitly asks for human/staff/agent/person in charge/call/WhatsApp contact/help/真人/人工/客服/负责人/电话/找人/有人帮忙 must first reassure and escalate to the person in charge. The fixed person-in-charge phone is +6591212369.
If the question is not about chicken essence but the customer is looking for Aqina, the person in charge, or human help, escalate instead of continuing as a bot.
Complaints, refunds, payment failures, payment status, order problems, delivery disputes, bulk purchase, corporate purchase, medical/legal/financial judgment, or any price/stock/order/payment/service condition that the bot cannot confirm must set escalate=true, next_tag=handoff_pending, and a readable escalation_reason such as manual_handoff_requested, non_product_human_help, complaint, payment_issue, order_issue, medical_safety, unknown_requires_human. Delivery timing requests during checkout should be saved as customer_request_remark and moved to PayNow first, not promised as confirmed.

Medical Safety

- Aqina 是食品补养，不是药.
- Do not say Aqina can treat disease, guarantee recovery, guarantee pregnancy/postpartum outcomes, increase lactation, prevent disease, has no side effects, or has doctor endorsement.
- If the customer asks about pregnancy, medication, disease, treatment, surgery recovery, severe illness, or doctor advice, say special health situations should check with a doctor and set escalate=true when individual judgment is needed.
- Chinese safety sentence: "Aqina 是食品补养，不是药；如果您正在怀孕、治疗、吃药，或有特殊健康状况，建议先把成分表给医生确认。这个情况我也可以帮您转给真人客服再跟进。"

Output must be JSON with exactly these fields:
reply_text, next_tag, lead_goal, recommended_package_code, upgrade_package_code, selected_package_code,
gift_choice, customer_request_remark, order_fields{name,phone,address}, missing_order_fields, checkout_ready, escalate, escalation_reason, faq_topic, opt_in_granted.
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
                "name_zh": "7天启动装",
                "name_en": "7-Day Starter Pack",
                "description_zh": "1盒/7包，适合第一次先确认口感。",
                "description_en": "1 box / 7 sachets for first taste confirmation.",
                "price_sgd": 47.9,
                "pack_count": 7,
                "box_count": 1,
                "target_audience": ["self_care"],
                "hero": False,
                "free_shipping_eligible": True,
            },
            "pack2": {
                "code": "pack2",
                "name_zh": "14天常备装",
                "name_en": "14-Day Care Pack",
                "description_zh": "2盒/14包，等于 SGD39.90/盒，比两个单盒少 SGD16.00，并送 French Poulet Cut Part 五选一。",
                "description_en": "2 boxes / 14 sachets at SGD39.90 per box, saving SGD16.00 versus two single boxes, with one French Poulet Cut Part gift choice.",
                "price_sgd": 79.8,
                "pack_count": 14,
                "box_count": 2,
                "target_audience": ["self_care"],
                "hero": True,
                "free_shipping_eligible": True,
            },
        },
        "knowledge_base": {
            "usps": [
                "Aqina farm / single-origin / 可追溯。",
                "使用 MD2 黄梨酵素鸡 / Pineapple Chicken。",
                "100% Pure Chicken Essence / 无添加。",
                "double-boiled 双重蒸煮 / 7天慢炼。",
                "JAKIM Halal 认证，金色小袋装 7 PACKS x 60g。",
                "SFA 注册、HACCP、GMP 认证。",
                "营养：零脂肪、零胆固醇、高蛋白质，含 BCAA 支链氨基酸；无防腐剂、无味精、无加水。",
            ],
            "faq": [
                {"question": "有没有现货？多久能送到？", "answer": "当前 1盒 SGD47.90 和 2盒 SGD79.80 已包含新加坡配送费，不需要另加邮费；库存、送达时间和具体配送安排会在下单时由客服确认。"},
                {"question": "怎么喝最好？", "answer": "建议早晨空腹饮用吸收最好，可隔水加热 3-5 分钟后饮用。"},
                {"question": "和普通瓶装鸡精有什么不同？", "answer": "Aqina 纯鸡精走的是 pure chicken essence / premium sachet route，重点在 MD2 黄梨酵素鸡、可追溯来源、double-boiled 双重蒸煮、7天慢炼和 100% Pure Chicken Essence。"},
                {"question": "有什么认证？", "answer": "Aqina 纯鸡精有 SFA 注册、HACCP、GMP，以及 JAKIM Halal 认证。"},
                {"question": "营养含量是怎样的？", "answer": "零脂肪、零胆固醇、高蛋白质，含 BCAA 支链氨基酸；无防腐剂、无味精、无加水。"},
                # 2026-07-25: the landing page's three real objections, so chat and page answer
                # the same way. Sourced from 公司文件_Aqina鸡精介绍PDF (composition) and the
                # 2026-05-23 inbox analysis, where a real customer asked "Made with chinese herbs".
                {
                    "question": "会不会燥？里面有没有当归、人参这类药材？",
                    "answer": "没有药材。Aqina 纯鸡精是 100% 鸡骨与鸡肉熬制，不加水、不加防腐剂、不加味精，配方里没有当归、人参这类中药材，所以不是药材燥补那一路。",
                },
                {
                    "question": "会不会腥？会不会油腻？",
                    "answer": "双重蒸煮会把多余油脂和腥味滤掉，喝起来比较像熬久了的清鸡汤，清爽不油腻、有自然回甘。不确定合不合口味，建议先拿1盒7天装试，不用一次买多。",
                },
                {
                    "question": "孕期／月子可以喝吗？",
                    "answer": "Aqina 纯鸡精是日常食品补养，不是药，配方里也没有药材。孕期、哺乳期、正在治疗或服药的顾客，请按自己的身体状况和医生建议安排；需要更确定的话，我可以请真人客服跟您确认。",
                },
            ],
            "medical_disclaimer": "Aqina 是食品补养，不是药；特殊健康状况请先把成分表给医生确认。",
            "logistics": "当前 1盒 SGD47.90 和 2盒 SGD79.80 已包含新加坡配送费，不需要另加邮费；库存、送达时间和具体配送安排会在下单时由客服确认。不要把配送当成主要卖点，但客户问运费/邮费/配送费时必须直接回答。",
            "consumption": "建议早晨空腹饮用，可隔水加热或热水浸泡后即饮。",
            "comparisons": "很多顾客会拿 ordinary traditional bottled chicken essence 比价，但 Aqina 纯鸡精不是普通低价瓶装路线，而是 pure chicken essence / premium sachet route。",
            "price_positioning": (
                "1盒 SGD47.90；2盒 SGD79.80，等于 SGD39.90/盒。"
                "2盒比买两个单盒 SGD95.80 少 SGD16.00，并送 1包 French Poulet Cut Part，market value SGD8。"
                "价值解释必须讲清楚来源、原料和工艺：Aqina farm 可追溯、MD2 黄梨酵素鸡、double-boiled 双重蒸煮、7天慢炼、100% Pure Chicken Essence。"
                # 2026-07-25: per-sachet math so the bot can answer 嫌贵 with a concrete unit price
                # instead of only an abstract 'premium route' argument. Matches the landing page.
                "顾客嫌贵时，用每袋单价把价值讲清楚：1盒 SGD47.90 ÷ 7袋 ≈ 每袋 SGD6.84；"
                "2盒 SGD79.80 ÷ 14袋 ≈ 每袋 SGD5.70，每袋都是 60g。"
                "同规格的 premium 有机滴鸡精，每袋通常贵不少，所以 Aqina 是同级里比较划算的一个。"
                "不要点名比较竞品品牌，也不要报竞品价格；顾客主动提到别的牌子时，只讲 Aqina 自己的每袋单价和来源工艺。"
            ),
        },
        "crm_follow_up_rules": {
            "comment_hook": {
                "public_reply": {
                    "instruction": "哈喽 [顾客名字] 🌟，Aqina 纯鸡精资料已发到您的 Messenger Inbox。我会先按您的情况帮您判断适不适合，再建议配套。请查收哦 📩"
                },
                "private_opening": {
                    "instruction": "您好 [顾客名字]！我先帮您判断 Aqina 纯鸡精适不适合您的情况。请问是自己日常喝、送长辈，还是孕期/月子调理？🎈"
                },
            },
            "t15m": {
                "lead_cold": {"instruction": "Use one low-pressure sentence to follow up on the customer's last question. Ask whether it is for self-care, elders/gifting, or pregnancy/postpartum. Do not send long product copy and do not quote price."},
                "qualified_warm": {"instruction": "If the customer's question is still unresolved, invite them to share the drinking scene or concern. Help judge first. Do not repeat prices."},
                "cart_hot": {"instruction": "The customer is already in order mode. Remind them they can send recipient name, phone number, and Singapore address directly; if they already paid by PayNow, ask them to send the payment screenshot. Do not ask broad usage questions again."},
            },
            "t3h": {
                "cart_hot": {"instruction": "The customer asked about package, delivery, or payment but has not completed the order. Briefly remind them to continue with delivery details or the PayNow payment screenshot; if needed, mention that customer service will verify."},
                "default": {"instruction": "Low-pressure reminder: if usage, suitability, or package choice is still unclear, the customer can continue asking and you will judge by their situation. You may mention that a real customer usage photo is being shared for reference. Do not invent review quotes, medical outcomes, safety guarantees, or exact usage results. Do not repeat prices. Do not send long sensory copy."}
            },
            "t12h": {
                "cart_hot": {"instruction": "If the customer has selected a package or provided details, remind them to use the PayNow QR and send back the payment screenshot. Keep it short and say the team will verify delivery after receiving the screenshot."}
            },
            "t23h": {
                "cart_hot": {"instruction": "If the 23-hour window is ending soon, first remind them they can still send delivery details or payment screenshot now. Only ask them to reply YES if they want a later reminder and need to keep the chat open."},
                "default": {"instruction": "Before the 23-hour window ends, only remind them to reply YES to keep contact open. Do not retell the product story."}
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
            "private_whatsapp_number": DEFAULT_PRIVATE_WHATSAPP_NUMBER,
            "additional_private_whatsapp_numbers": [DEFAULT_GINO_ORDER_ALERT_WHATSAPP_NUMBER],
            "whatsapp_template_name": DEFAULT_ESCALATION_WHATSAPP_TEMPLATE_NAME,
            "pause_automation_on_handoff": True,
        },
        "chatbot_skills": deepcopy(DEFAULT_CHATBOT_SKILLS),
        "media_assets": deepcopy(DEFAULT_MEDIA_ASSETS),
        "faq": [],
        "templated_openers": list(DEFAULT_TEMPLATED_OPENERS),
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
        escalation = normalized.get("escalation", {})
        if not escalation.get("private_whatsapp_number"):
            normalized["escalation"]["private_whatsapp_number"] = defaults["escalation"]["private_whatsapp_number"]
        if not isinstance(escalation.get("additional_private_whatsapp_numbers"), list):
            normalized["escalation"]["additional_private_whatsapp_numbers"] = defaults["escalation"]["additional_private_whatsapp_numbers"]
        if not escalation.get("whatsapp_template_name"):
            normalized["escalation"]["whatsapp_template_name"] = defaults["escalation"]["whatsapp_template_name"]
        normalized["media_assets"] = _normalize_media_assets(normalized.get("media_assets", {}), defaults["media_assets"])
        normalized = _remove_retired_trial_package(normalized)
        normalized = _remove_retired_offer_packages(normalized)
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

    initial_promotion_images = (
        normalized.get("initial_promotion_images")
        if isinstance(normalized.get("initial_promotion_images"), dict)
        else {}
    )
    default_initial_promotion_images = defaults.get("initial_promotion_images", {})
    if not initial_promotion_images.get("zh"):
        initial_promotion_images["zh"] = default_initial_promotion_images.get("zh", "")
    if (
        not initial_promotion_images.get("en")
        or initial_promotion_images.get("en") == default_initial_promotion_images.get("zh")
    ):
        initial_promotion_images["en"] = default_initial_promotion_images.get("en") or initial_promotion_images.get(
            "zh", ""
        )
    normalized["initial_promotion_images"] = initial_promotion_images

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

    normalized["ugc_social_proof_images"] = _normalize_localized_media_list(
        normalized.get("ugc_social_proof_images"),
        defaults.get("ugc_social_proof_images", {}),
    )

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


def _normalize_localized_media_list(value: Any, defaults: dict[str, Any]) -> dict[str, list[str]]:
    if isinstance(value, dict):
        normalized = {
            "zh": _coerce_media_list(value.get("zh")),
            "en": _coerce_media_list(value.get("en")),
        }
    else:
        shared = _coerce_media_list(value)
        normalized = {"zh": shared, "en": list(shared)}

    default_zh = _coerce_media_list(defaults.get("zh"))
    default_en = _coerce_media_list(defaults.get("en")) or list(default_zh)
    if not normalized["zh"]:
        normalized["zh"] = default_zh
    if not normalized["en"]:
        normalized["en"] = default_en or list(normalized["zh"])
    return normalized


def _coerce_media_list(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = value
    elif isinstance(value, tuple):
        candidates = list(value)
    else:
        candidates = []
    return [str(item).strip() for item in candidates if str(item).strip()]


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
    migrated["packages"] = deepcopy(defaults["packages"])
    migrated["knowledge_base"] = deepcopy(defaults["knowledge_base"])
    migrated["chatbot_skills"] = deepcopy(defaults["chatbot_skills"])
    migrated["crm_follow_up_rules"] = deepcopy(defaults["crm_follow_up_rules"])
    migrated["media_assets"] = deepcopy(defaults["media_assets"])

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
        "【7天启动装】1盒/7包 = SGD47.90，适合先确认口感。",
    ),
    (
        f"可先给【{RETIRED_TRIAL_NAME_ZH}】作为低门槛选择",
        "可先给【7天启动装】1盒/7包作为低门槛选择",
    ),
    (
        f"您会想先用{RETIRED_TRIAL_NAME_ZH}试口感，还是直接拿免运的{LEGACY_ENERGY_PACK_NAME_ZH}？",
        "您会想先用1盒7天启动装试口感，还是直接拿2盒14天常备装？",
    ),
    (
        f"您会更想先试【{RETIRED_TRIAL_NAME_ZH}】还是直接拿免运的【{LEGACY_ENERGY_PACK_NAME_ZH}】呢？",
        "您会更想先试【7天启动装】1盒，还是直接拿【14天常备装】2盒呢？",
    ),
    (f"{RETIRED_TRIAL_NAME_ZH}：{RETIRED_TRIAL_PACK_COUNT_SPACED_TEXT}先试口感。", "7天启动装：1盒/7包先试口感。"),
    ("Trial pack: 3 packs to try the taste first.", "7-day starter pack: 1 box / 7 packs to start."),
    ("Low-entry 3-pack trial", "1-box 7-day starter pack"),
    (f"{RETIRED_TRIAL_PACK_COUNT_TEXT}低门槛体验装", "1盒/7包低门槛7天启动装"),
    (RETIRED_TRIAL_NAME_ZH, "7天启动装"),
    (RETIRED_TRIAL_NAME_EN, "7-Day Starter Pack"),
    (RETIRED_TRIAL_PRICE_TEXT, "SGD47.90"),
    (RETIRED_TRIAL_PACKAGE_CODE, "pack1"),
    (RETIRED_TRIAL_PACK_COUNT_SPACED_TEXT, "1盒/7包"),
    (RETIRED_TRIAL_PACK_COUNT_TEXT, "1盒/7包"),
    ("3-pack", "1-box"),
)

RETIRED_OFFER_PACKAGE_CODES = {"pack4", "pack6", "energy_14", "maternal_28", "family_42"}
OFFER_RESET_TEXT_REPLACEMENTS = (
    ("SGD 39.90", "SGD47.90"),
    ("SGD39.90 / 7 sachets", "SGD47.90 / 7 sachets"),
    ("SGD 75.00", "SGD79.80"),
    ("SGD 75", "SGD79.80"),
    ("SGD75", "SGD79.80"),
    ("SGD 149.00", "SGD79.80"),
    ("SGD 149", "SGD79.80"),
    ("SGD149", "SGD79.80"),
    ("SGD 219.00", "SGD79.80"),
    ("SGD 219", "SGD79.80"),
    ("SGD219", "SGD79.80"),
    ("4盒月度装", "2盒常备装"),
    ("6盒家庭装", "2盒常备装"),
    ("4盒", "2盒"),
    ("6盒", "2盒"),
    ("free shipping", "current promotion"),
    ("Free shipping", "Current promotion"),
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


def _remove_retired_offer_packages(settings_doc: dict[str, Any]) -> dict[str, Any]:
    """Keep chatbot runtime package choices aligned to the current 1-box / 2-box offer."""
    normalized = deepcopy(settings_doc)
    packages = normalized.get("packages")
    if isinstance(packages, dict):
        for code in RETIRED_OFFER_PACKAGE_CODES:
            packages.pop(code, None)

    media_assets = normalized.get("media_assets")
    if isinstance(media_assets, dict):
        for key in ("package_images", "captions"):
            values = media_assets.get(key)
            if isinstance(values, dict):
                for code in RETIRED_OFFER_PACKAGE_CODES:
                    values.pop(code, None)

    skills = normalized.get("chatbot_skills")
    if isinstance(skills, dict):
        for skill in skills.values():
            if not isinstance(skill, dict):
                continue
            for field in ("recommended_package_code", "selected_package_code", "upgrade_package_code"):
                if skill.get(field) in RETIRED_OFFER_PACKAGE_CODES:
                    skill[field] = "pack2"

    return _rewrite_offer_reset_text(normalized)


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


def _rewrite_offer_reset_text(value: Any) -> Any:
    if isinstance(value, str):
        rewritten = value
        for old, new in OFFER_RESET_TEXT_REPLACEMENTS:
            rewritten = rewritten.replace(old, new)
        return rewritten
    if isinstance(value, list):
        return [_rewrite_offer_reset_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_offer_reset_text(item) for key, item in value.items()}
    return value
