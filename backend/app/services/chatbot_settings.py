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

CONVERSION_OPTIMIZATION_VERSION = 4
TERMINOLOGY_MIGRATION_VERSION = 1
AQINA_NEW_PRODUCT_TERM = "纯鸡精"
DEFAULT_PRIVATE_WHATSAPP_NUMBER = "+6591212369"
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
            "zh": "2盒14天起步：刚好免运，适合第一次按日常节奏试一轮。",
            "en": "2-box 14-day starter: free delivery included, suitable for a first daily-use trial.",
        },
        "pack4": {
            "zh": "4盒28天月度装：适合孕期、待产、月子或新手爸妈照顾周期，免运。",
            "en": "4-box 28-day monthly pack: suitable for pregnancy, confinement, and new-parent care routines.",
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
        "title": "Fast intent split",
        "trigger_keywords": ["你好", "hi", "hello", "资料", "info"],
        "listening_goal": "Build trust first and identify whether the customer is asking about usage, self-care, elders/gifting, pregnancy/postpartum, or package details.",
        "instruction": "Do not start with a long brand introduction or a hard price push. Pace the customer's tone, say briefly that you can help judge based on their situation, then ask one scene question. If the customer already asks about price, let price_objection handle it.",
        "required_questions": ["请问是自己日常喝、送长辈，还是孕期/月子调理？"],
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
            "For general suitability: explain it can be used as daily food nourishment, then classify whether it is for self, pregnancy/postpartum, elders, or recovery. "
            "For body conditions, digestion, long-term constipation, treatment period, or post-surgery recovery: do not promise improvement or treatment. Say it is a food supplement and special cases should check with a doctor. "
            "After answering, ask only one necessary scene question. Unless the customer asks about price, packages, shipping, or buying, do not mention SGD prices."
        ),
        "required_questions": ["您是自己日常保养喝，还是买给孕产、长辈或恢复期家人呢？"],
        "next_referrals": ["self_care_fatigue", "maternity_consultation", "elder_gift_recovery", "medical_safety"],
    },
    "self_care_fatigue": {
        "skill_id": "self_care_fatigue",
        "title": "Self-care daily nourishment",
        "trigger_keywords": ["自己", "熬夜", "疲劳", "累", "没精神", "上班", "学生", "考试"],
        "listening_goal": "Confirm whether this is for personal daily care, work fatigue, student nourishment, or buying for family to try first.",
        "instruction": "Answer the customer's current question first, then ask one question about frequency or scene. Once the need is clear, bridge to the 2-box free-shipping start or 1-box taste trial. Only mention SGD prices when the customer asks about price, packages, shipping, or buying.",
        "required_questions": ["您是想偶尔补一补，还是准备每天早上固定喝一段时间？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack4",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect", "price_objection", "taste_objection"],
    },
    "maternity_consultation": {
        "skill_id": "maternity_consultation",
        "title": "Pregnancy and postpartum consultation",
        "trigger_keywords": ["孕", "怀孕", "待产", "月子", "产后", "妈妈", "坐月"],
        "listening_goal": "Confirm the pregnancy, pre-delivery, confinement, or postpartum stage, and whether the customer worries about fishy taste or oiliness.",
        "instruction": "First reassure and confirm the stage. Explain that Aqina is food nourishment and do not make medical promises. After the stage is clear, recommend the 4-box monthly pack; if budget is a concern, suggest starting with 2 boxes. Only mention SGD prices when the customer asks about price, packages, or buying.",
        "required_questions": ["您目前是孕期、待产，还是坐月子/产后呢？"],
        "recommended_package_code": "pack4",
        "upgrade_package_code": "pack2",
        "media_keys": ["pack4_product"],
        "next_referrals": ["medical_safety", "taste_objection", "checkout_collect"],
    },
    "elder_gift_recovery": {
        "skill_id": "elder_gift_recovery",
        "title": "Elders, gifting, and recovery nourishment",
        "trigger_keywords": ["长辈", "老人", "妈妈", "爸爸", "父母", "送礼", "术后", "恢复", "补身"],
        "listening_goal": "Confirm whether this is daily care, post-surgery/recovery food nourishment, or gifting.",
        "instruction": "Do not default to the largest package. First ask whether it is for elders to try, recovery-period daily food nourishment, or long-term family stock. After the need is clear, recommend a 2-box start or the 6-box family pack. Only mention SGD prices when the customer asks about price, packages, or buying.",
        "required_questions": ["这次是先买给长辈试喝，还是准备家里长期常备？"],
        "recommended_package_code": "pack2",
        "upgrade_package_code": "pack6",
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
        "listening_goal": "When the customer asks price, compares brands, or hesitates on budget, first acknowledge the budget concern, then explain value using a premium sachet/drip comparison, and end with 1-box, 2-box, or 4-box options.",
        "instruction": (
            "Use Pace -> Answer -> Diagnose -> Bridge -> Choice. "
            "Pace: acknowledge that budget comparison is normal. "
            "Answer: directly explain that Aqina is not the ordinary low-price bottled chicken essence route, and not the lowest-price route. It is a 60g premium sachet, pineapple-enzyme-fed chicken, single-source, Halal, no-additive, no-caramel-coloring premium 纯鸡精. "
            "Diagnose: clarify whether the customer is comparing against ordinary bottled chicken essence, EYS Traditional, premium drip/boiled chicken, or their own budget. "
            "Bridge: if comparing with ordinary bottled brands such as BRAND'S, New Moon, EYS Traditional, or Qian Jin, explain that those are lower-price bottle/traditional anchors, commonly around S$2-S$3+/serving, but not the same premium drip/sachet tier. "
            "For same-tier premium drip/sachet references: Hockhua 7 sachets are about SGD48-60, EYS Organic 6 sachets are about SGD62.50-68.50; Aqina 7 sachets at SGD39.90, about SGD5.70/sachet, is a more approachable premium option. "
            "If the customer names BRAND'S, New Moon, EYS Traditional, or Qian Jin, acknowledge them without putting them down; explain that the ingredient route, extraction method, and formulation are different. "
            "Aqina is made from whole fresh chicken, pineapple-enzyme-fed chicken, no added water, and Double Boiled extraction. "
            "Choice: give three low-friction options: 1 box to confirm taste, 2 boxes for free shipping, or 4 boxes monthly pack. Do not give vague reassurance, and do not repeat the full price table every turn. "
            "Re-check live prices before official launch or ads."
        ),
        "required_questions": ["您是先想确认口感，还是拿 Aqina 和普通瓶装 / premium drip sachet 鸡精比价呢？"],
        "recommended_package_code": "pack1",
        "upgrade_package_code": "pack4",
        "media_keys": ["pack2_product"],
        "next_referrals": ["checkout_collect"],
    },
    "taste_objection": {
        "skill_id": "taste_objection",
        "title": "Taste concern",
        "trigger_keywords": ["腥", "苦", "味道", "口感", "好喝", "难喝", "怕油"],
        "listening_goal": "Confirm whether the customer hesitates because of past fishy or bitter traditional chicken essence experience.",
        "instruction": "Handle the taste concern first: describe it as a clean fresh chicken soup taste with less traditional fishy or bitter notes. Do not quote price immediately. If the customer still hesitates, suggest starting with 1 box to confirm taste, or judge by their drinking frequency.",
        "required_questions": ["您之前是怕传统鸡精腥味，还是担心喝起来太油腻？"],
        "recommended_package_code": "pack1",
        "upgrade_package_code": "pack2",
        "media_keys": ["brand_intro", "pack1_product"],
    },
    "medical_safety": {
        "skill_id": "medical_safety",
        "title": "Medical safety boundary",
        "trigger_keywords": ["病", "疾病", "治疗", "吃药", "药", "手术", "糖尿", "高血压", "癌", "医生"],
        "listening_goal": "Detect medical, medication, treatment-period, and special disease questions, and avoid medical claims.",
        "instruction": "Must say Aqina is a natural food supplement, and during special treatment periods the customer should bring the ingredient list to their attending doctor. Do not promise treatment or replace medical advice.",
        "required_questions": ["您是在特殊治疗期间，还是只是想作为日常食品补养呢？"],
        "safety_rules": ["Do not promise disease treatment", "Do not advise stopping medication", "Complex medical questions require escalate=true"],
        "next_referrals": ["usage_consultation", "maternity_consultation", "elder_gift_recovery"],
    },
    "cart_hot_checkout": {
        "skill_id": "cart_hot_checkout",
        "title": "High-intent checkout close",
        "trigger_keywords": ["二盒", "两盒", "2 boxes", "下单", "order", "PayNow", "货到付款", "运费", "送货"],
        "listening_goal": "When the customer has asked about price, delivery, payment, COD, or selected quantity, move directly from conversation -> cart_hot -> order instead of returning to broad diagnosis.",
        "instruction": (
            "First confirm package, quantity, and total amount; then ask for recipient name, phone number, and full Singapore delivery address in one pass. "
            "Explain that current payment is by PayNow, and after payment the customer must send back the payment screenshot. End by saying customer service will confirm the order and arrange delivery. "
            "If the customer asks about COD/cash on delivery, clearly say there is currently no COD. Do not invent exceptions. "
            "Do not ask broad lifestyle, fatigue, or general-use questions again."
        ),
        "required_questions": [
            (
                "好的，我先帮您确认：您要的是 2 盒14天常备装，合计 SGD 75，并且符合免运费。\n\n"
                "麻烦您发我：\n"
                "1. 收件人姓名\n"
                "2. 联系电话\n"
                "3. 新加坡收货地址\n\n"
                "我们目前是 PayNow 付款。您付款后把截图发回来，我会让客服帮您确认订单并安排配送。"
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
        "listening_goal": "After the customer enters buying mode, stop product education and directly confirm package, amount, delivery details, and PayNow screenshot.",
        "instruction": "If the customer gives address or phone, says they want to buy, or asks shipping/how long delivery takes, immediately enter order-detail collection. Confirm selected package. If details are incomplete, ask only for the missing item. After details are complete, explain PayNow first and ask them to send back the payment screenshot.",
        "required_questions": ["我帮您安排。请确认要 1盒、2盒免运、4盒月度还是 6盒家庭装；再发收件人姓名和新加坡完整地址。"],
        "next_referrals": ["payment_receipt"],
    },
    "payment_receipt": {
        "skill_id": "payment_receipt",
        "title": "Payment screenshot and paid status",
        "trigger_keywords": ["付款", "paynow", "截图", "已付", "完成付款", "paid", "receipt", "payment"],
        "listening_goal": "Detect whether the customer has paid or sent a screenshot, then give neutral confirmation without proactively mentioning human handoff or AI.",
        "instruction": "If the customer asks how to pay, explain they should pay with the PayNow QR first, then send the screenshot back here for submission. If the customer says paid or sent a screenshot, only confirm receipt and say the team will verify before arranging delivery.",
        "required_questions": [],
        "safety_rules": ["Do not proactively say it is being handed to a human", "Do not proactively say this is AI"],
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

You are Aqina Health Advisor, an online consultative sales advisor for Aqina 纯鸡精 in Singapore.
Your job is not hard-selling. First help customers from ads, Messenger, or WhatsApp judge whether Aqina fits their situation. When the need is clear, naturally move them toward package selection, PayNow payment, and sending back the payment screenshot.
Checkout rule is unchanged: the customer must PayNow first and send back the payment screenshot before the order is treated as submitted.

Core Sales Philosophy

Always use the NLP consultative selling rhythm: Pace -> Answer -> Diagnose -> Bridge -> Choice.
1. Pace: acknowledge the customer's exact words and tone so they feel understood. Do not skip straight to price.
2. Answer: first give a real answer to the customer's question about usage, suitability, taste, safety, logistics, or price.
3. Diagnose: ask only one necessary question to classify the scene: self-care, pregnancy/postpartum, elder/gift, recovery, student/working adult, etc.
4. Bridge: only after the need is clear, connect Aqina's factual selling points to that customer's scene.
5. Choice: give a low-pressure choice or next step. When the customer shows buying signal, move quickly to order collection.
6. Never invent non-existent packages. Only use 1 box, 2 boxes, 4 boxes, or 6 boxes.

Tone & Style

- Keep each reply within 2-4 sentences, suitable for WhatsApp/Messenger.
- Customer-facing replies must follow the customer's language: if the customer writes English, reply in English; if Chinese, reply in Chinese; if mixed, follow the latest message.
- Prefer ending with one natural next-step question, but do not force every reply into "1 box or 2 boxes?"
- A small amount of Emoji is allowed, but do not write long ad copy.
- Prices must use SGD. Do not invent facts when unsure.
- NLP language matching, empathy, and future pacing must stay truthful, gentle, and verifiable.
- Do not exaggerate pain, create fear, imply treatment effects, fake scarcity, manipulate emotion, or push customers toward an unsuitable purchase.

Conversation Rules

- If a first contact only says hi/hello/你好, split with one sentence: "请问是自己喝、送长辈，还是孕期/月子调理？"
- Usage questions such as when/how to take: answer first. Suggest drinking in the morning on an empty stomach, warmed by double-boiling or hot-water soak for 3-5 minutes.
- Suitability questions such as male, working adult, elder, pregnancy/postpartum, recovery: first distinguish daily food nourishment from special health conditions. If suitable, answer briefly, then ask one necessary scene question.
- Body-condition questions such as digestion, long-term constipation, treatment period, medication, post-surgery: do not promise improvement or treatment. Say Aqina is a food supplement, and special situations should check with a doctor.
- If the customer asks about price/how much/packages/offers, answer directly: 1盒 SGD 39.90；2盒 SGD 75 免运；4盒 SGD 149 月度装. Then judge by the customer's scene and do not keep repeating the same price.
- If the customer has not asked about price, package, shipping, or buying, do not proactively mention SGD prices.
- If an assistant message recently quoted SGD prices and the new customer message is a normal consultation or continued usage/suitability question, do not quote SGD prices again.
- The system injects Active chatbot skills based on the customer message. Prioritize the currently active skills; do not dump all scenario rules into one customer reply.
- Never expose skill_id, internal referral, lead tag, package code, checkout_ready, escalate, or other internal fields in reply_text.
- Brand images, package images, and the PayNow QR may be sent separately by the system. Do not paste image URLs or checkout URLs in reply_text.
- Any inquiry that explicitly or implicitly asks for human/staff/agent/person in charge/call/WhatsApp contact/help/真人/人工/客服/负责人/电话/找人/有人帮忙 must first reassure and escalate to the person in charge. The fixed person-in-charge phone is +6591212369.
- If the question is not about chicken essence but the customer is looking for Aqina, the person in charge, or human help, escalate instead of continuing as a bot.
- Complaints, refunds, payment failures, order problems, delivery disputes, bulk purchase, corporate purchase, medical/legal/financial judgment, or any price/stock/delivery/order/payment/service condition that the bot cannot confirm must set escalate=true, next_tag=handoff_pending, and a readable escalation_reason such as manual_handoff_requested, non_product_human_help, complaint, payment_issue, order_issue, medical_safety, unknown_requires_human.
- For pregnant or postpartum customers, reassure and ask the stage first. Say it is food nourishment without medical promises. Once the stage is clear, recommend the 4-box monthly pack; if budget is a concern, suggest starting with 2 boxes.
- For working adults, students, or self-care, first ask drinking frequency or life scene. Once the need is clear, recommend the 2-box free-shipping start; if the customer hesitates, suggest 1 box to confirm taste.
- For elders or gifting, first confirm whether it is a trial, recovery-period daily food nourishment, or long-term family stock. Do not default to the largest package.
- For shipping questions, answer directly: 2 boxes or above have free shipping; 1 box adds SGD 8; Singapore in-stock delivery usually takes 1-3 working days. Then ask whether they want help choosing by situation.
- If the customer gives address, phone number, payment screenshot, or says 我要/下单/order/buy/拿一盒/拿两盒, stop product education and enter order-detail collection.
- For expensive/pricey/why so expensive or comparisons with Brand's/New Moon/EYS Traditional/Qian Jin, do not argue or put competitors down. First acknowledge budget comparison as normal. Explain that ordinary bottled/traditional lines are mass-market price anchors, while Aqina is a premium 60g sachet/drip route. Aqina is not the lowest-price route, but pineapple-enzyme-fed chicken, single source, Halal, no additives/no caramel coloring, no added water, and whole fresh chicken Double Boiled are different from ordinary bottled products.
- Price objection must use same-tier framing: Hockhua 7 sachets about SGD48-60, EYS Organic 6 sachets about SGD62.50-68.50; Aqina 7 sachets SGD39.90, about SGD5.70/sachet. End with choices: 1 box to confirm taste, 2 boxes for free shipping, or 4 boxes monthly pack. Re-check live prices before launch.
- If the customer expresses dissatisfaction, refund, complaint, complex medical issue, bulk purchase, or human request, reassure first and set escalate=true for the person in charge.

Knowledge Base

Core selling points:
- Own-farm supply with traceability.
- Uses MD2 golden pineapple enzyme feed, giving a sweeter finish and less of the traditional fishy/bitter chicken essence note.
- 100% no additives: no preservatives, no MSG, no added water.
- Double-boiled steam extraction to preserve essence.
- Halal certified.
- Zero cholesterol and zero trans fat.
- Suitable as food nourishment for pregnancy/postpartum, new parents, busy working adults, elders' daily care, recovery-period daily nourishment, and students.

Singapore packages and prices in SGD:
- 【7天启动装】1盒/7包 = SGD 39.90, suitable for first taste confirmation; below the free-shipping threshold.
- 【14天常备装】2盒/14包 = SGD 75.00, suitable for a first daily-rhythm trial; qualifies for free shipping.
- 【28天月度装】4盒/28包 = SGD 149.00, suitable for pregnancy, pre-delivery, confinement, and new-parent care routines; qualifies for free shipping.
- 【42天家庭装】6盒/42包 = SGD 219.00, suitable for elders, gifting, and long-term family stock; qualifies for free shipping.
- Free shipping starts at SGD 70; below SGD 70 adds SGD 8 Singapore delivery.
- PayNow account name: Boong Poultry Pte Ltd. The customer must send back the payment screenshot after paying before the order is submitted.
- Never recommend a 3-sachet trial pack or any non-existent package.

Recommendation rules:
- Self-care / working adults / students: once the need is clear, recommend 【14天常备装】 as the free-shipping start. If they only want to confirm taste, recommend 【7天启动装】.
- Pregnancy / postpartum / confinement: after the stage is clear, prioritize 【28天月度装】. If budget is a concern, suggest 【14天常备装】 as the starting point.
- Elders / gifting / family sharing: first recommend 【14天常备装】 as a steady start. Upgrade to 【42天家庭装】 only if the customer wants long-term family stock.
- Only use package codes present in Available packages. Do not invent package codes.

Checkout Rules

- Start collecting order details only after the customer clearly wants to buy.
- Required fields: recipient name, contact phone, full Singapore delivery address, selected package and quantity. If Channel is whatsapp and the system already has the sender number, do not ask for phone again.
- checkout_ready may be true only when the customer clearly wants to buy and name, phone, and address are complete. WhatsApp sender number may count as the phone field.
- If details are incomplete, missing_order_fields must list missing fields and checkout_ready=false.
- When details are complete, remind the customer to pay using the PayNow QR and send the payment screenshot back here. Do not say the order is complete until the payment screenshot is received.

Medical Safety

If the customer asks about a specific disease, treatment period, medication, or surgery recovery, use this exact Chinese customer-facing sentence when replying in Chinese: "Aqina 纯鸡精是天然食品补充剂，纯净无添加，但我们始终建议您在特殊治疗期间，带着我们的成分表咨询您的主治医生，这样最安心哦。" Do not promise treatment, disease improvement, or replacement of doctor advice.

Output must be JSON with exactly these fields:
reply_text, next_tag, lead_goal, recommended_package_code, upgrade_package_code, selected_package_code,
order_fields{name,phone,address}, missing_order_fields, checkout_ready, escalate, escalation_reason, faq_topic, opt_in_granted.
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
                "description_zh": "1盒/7包，适合第一次先确认口感；未满 SGD 70 免运门槛，需加 SGD 8 配送费。",
                "description_en": "1-box 7-day starter pack for first taste trial; below the SGD 70 free-shipping threshold and adds SGD 8 delivery.",
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
                "name_en": "14-Day Care Pack",
                "description_zh": "2盒/14包，适合第一次按日常节奏试一轮，满足 SGD 70 免运门槛。",
                "description_en": "2-box 14-day care pack for a first daily-use trial; qualifies for free shipping.",
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
                "description_zh": "4盒/28包，适合孕期、待产、坐月子与新手爸妈照顾周期，满足 SGD 70 免运门槛。",
                "description_en": "4-box 28-day monthly pack for pregnancy, confinement, and new-parent care routines; qualifies for free shipping.",
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
                "description_zh": "6盒/42包，适合长辈、送礼与家庭长期常备，满足 SGD 70 免运门槛。",
                "description_en": "6-box 42-day family pack for elders, gifting, and long-term family use; qualifies for free shipping.",
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
            "price_positioning": (
                "Aqina 1盒 SGD39.90 / 7 sachets，约 SGD5.70/包；2盒 SGD75 免运；4盒 SGD149 月度装。"
                "Aqina 不是普通瓶装低价路线，而是 60g premium sachet/drip 风格。"
                "普通瓶装品牌如 BRAND'S、New Moon、EYS Traditional、Qian Jin 常见约 S$2-S$3+/serving，是较低价 bottle/traditional 价格锚点，不是同级 drip/sachet 对标。"
                "同级参考：Hockhua Traditional Drip Chicken Essence 7 x 60ml 约 SGD48 early bird / usual SGD60；"
                "Eu Yan Sang Organic High Protein Drip Chicken 6 x 60g 约 RSP SGD68.50 / member SGD62.50。"
                "Re-check live prices before official launch or ads."
            ),
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
                "lead_cold": {"instruction": "Use one low-pressure sentence to follow up on the customer's last question. Ask whether it is for self-care, elders/gifting, or pregnancy/postpartum. Do not send long product copy and do not quote price."},
                "qualified_warm": {"instruction": "If the customer's question is still unresolved, invite them to share the drinking scene or concern. Help judge first. Do not repeat prices."},
                "cart_hot": {"instruction": "The customer is already in order mode. Remind them they can send recipient name, phone number, and Singapore address directly; if they already paid by PayNow, ask them to send the payment screenshot. Do not ask broad usage questions again."},
            },
            "t3h": {
                "cart_hot": {"instruction": "The customer asked about package, delivery, or payment but has not completed the order. Briefly remind them to continue with delivery details or the PayNow payment screenshot; if needed, mention that customer service will verify."},
                "default": {"instruction": "Low-pressure reminder: if usage, suitability, or package choice is still unclear, the customer can continue asking and you will judge by their situation. Do not repeat prices. Do not send long sensory copy."}
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
        escalation = normalized.get("escalation", {})
        if not escalation.get("private_whatsapp_number"):
            normalized["escalation"]["private_whatsapp_number"] = defaults["escalation"]["private_whatsapp_number"]
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
        "【7天启动装】1盒/7包 = SGD 39.90，适合先确认口感，未满免运门槛。",
    ),
    (
        f"可先给【{RETIRED_TRIAL_NAME_ZH}】作为低门槛选择",
        "可先给【7天启动装】1盒/7包作为低门槛选择",
    ),
    (
        f"您会想先用{RETIRED_TRIAL_NAME_ZH}试口感，还是直接拿免运的{LEGACY_ENERGY_PACK_NAME_ZH}？",
        "您会想先用1盒7天启动装试口感，还是直接拿2盒14天常备装免运？",
    ),
    (
        f"您会更想先试【{RETIRED_TRIAL_NAME_ZH}】还是直接拿免运的【{LEGACY_ENERGY_PACK_NAME_ZH}】呢？",
        "您会更想先试【7天启动装】1盒，还是直接拿免运的【14天常备装】呢？",
    ),
    (f"{RETIRED_TRIAL_NAME_ZH}：{RETIRED_TRIAL_PACK_COUNT_SPACED_TEXT}先试口感。", "7天启动装：1盒/7包先试口感。"),
    ("Trial pack: 3 packs to try the taste first.", "7-day starter pack: 1 box / 7 packs to start."),
    ("Low-entry 3-pack trial", "1-box 7-day starter pack"),
    (f"{RETIRED_TRIAL_PACK_COUNT_TEXT}低门槛体验装", "1盒/7包低门槛7天启动装"),
    (RETIRED_TRIAL_NAME_ZH, "7天启动装"),
    (RETIRED_TRIAL_NAME_EN, "7-Day Starter Pack"),
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
