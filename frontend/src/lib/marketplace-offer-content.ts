/**
 * Content source of truth for the main landing page (MarketplaceOfferPage).
 *
 * EVIDENCE DISCIPLINE — every product fact below is traceable to a client document:
 *  - [核实资料]  04_公司文件/产品资料/公司文件_滴鸡精详细核实资料_20260507.md
 *  - [鸡精介绍]  04_公司文件/产品资料/公司文件_Aqina鸡精介绍PDF.pdf
 *  - [公司简介]  04_公司文件/品牌和市场资料/公司文件_Aqina公司简介中文版.pdf
 *  - [包装实拍]  05_广告图原材料/产品图和包装/*  (box/sachet printed text)
 *  - [认证口径]  backend/app/services/chatbot_settings.py (single source of truth, commit 887d791)
 *
 * BANNED per [核实资料] §9: no 催奶/安胎/坐月必备/产后恢复保证/孕妇必喝/改善孕吐,
 * no 治疗/提高免疫力/临床证明/医生推荐/HSA approved/无副作用,
 * no 全网最低/最后一天/限量, no fabricated reviews, ratings, sales counts or "verified buyer" badges.
 */

export type MarketplaceLocale = 'en' | 'zh';

type L = Record<MarketplaceLocale, string>;

export function normalizeMarketplaceLocale(locale: string): MarketplaceLocale {
  return locale === 'zh' ? 'zh' : 'en';
}

/* ------------------------------------------------------------------ *
 * Pricing — mirrors the live offer (useLandingProducts / OFFER_RESET_PRODUCTS).
 * Unchanged pending Gino's ruling on which price regime is current.
 * ------------------------------------------------------------------ */
export const MARKETPLACE_PRICING = {
  pack1: { price: 47.9, boxes: 1, sachets: 7 },
  pack2: { price: 79.8, boxes: 2, sachets: 14 },
} as const;

export const PER_SACHET = {
  pack1: MARKETPLACE_PRICING.pack1.price / MARKETPLACE_PRICING.pack1.sachets, // 6.843
  pack2: MARKETPLACE_PRICING.pack2.price / MARKETPLACE_PRICING.pack2.sachets, // 5.700
} as const;

/* ------------------------------------------------------------------ *
 * Value equation. Competitor figure verified 2026-07-25 from Eu Yan Sang SG's
 * own product page: "Organic High-Protein Drip Chicken Essence 6s", 60g x 6,
 * listed S$68.50 (member S$62.50), page states "Halal Certified".
 * Same-format comparison only — no denigration, no claim about their formula.
 * ------------------------------------------------------------------ */
export const VALUE_EQUATION = {
  checkedOn: '2026-07-25',
  competitor: {
    brand: 'Eu Yan Sang',
    product: {
      zh: '有机高蛋白滴鸡精 6 袋装',
      en: 'Organic High-Protein Drip Chicken Essence 6s',
    } as L,
    packPrice: 68.5,
    sachets: 6,
    perSachet: 68.5 / 6, // 11.42
  },
} as const;

/* ------------------------------------------------------------------ *
 * Intent router — four openers that pre-sort the WhatsApp conversation.
 * Kept in the same language family as backend DEFAULT_TEMPLATED_OPENERS.
 * ------------------------------------------------------------------ */
export interface IntentOption {
  id: 'pregnancy' | 'confinement' | 'gift' | 'taste';
  label: L;
  hint: L;
  prefill: L;
}

export const INTENT_OPTIONS: IntentOption[] = [
  {
    id: 'pregnancy',
    label: { zh: '我在孕期，想问适不适合', en: "I'm pregnant — is it suitable for me?" },
    hint: { zh: '客服会先问阶段，再给建议', en: 'We ask your stage first, then advise' },
    prefill: {
      zh: 'Hi Aqina SG，我在孕期，想先问纯鸡精适不适合我。',
      en: "Hi Aqina SG, I'm pregnant and would like to ask whether the pure chicken essence suits me.",
    },
  },
  {
    id: 'confinement',
    label: { zh: '我在坐月子／家人刚生产', en: "I'm in confinement / a family member just gave birth" },
    hint: { zh: '帮你按天数算要几盒', en: 'We work out how many boxes by days' },
    prefill: {
      zh: 'Hi Aqina SG，我在月子期（或家人刚生产），想问要准备几盒比较合适。',
      en: 'Hi Aqina SG, I am in confinement (or a family member just gave birth). How many boxes should I prepare?',
    },
  },
  {
    id: 'gift',
    label: { zh: '送给妈妈或长辈', en: 'Buying for my mum or an elder' },
    hint: { zh: '送礼配套与配送安排', en: 'Gifting packs and delivery' },
    prefill: {
      zh: 'Hi Aqina SG，我想送给妈妈／长辈，想问怎么选比较合适。',
      en: 'Hi Aqina SG, I would like to buy this for my mum / an elder. How should I choose?',
    },
  },
  {
    id: 'taste',
    label: { zh: '我自己想先试口感', en: 'I want to try the taste first' },
    hint: { zh: '1 盒 7 天，先喝过再决定', en: '1 box = 7 days, decide after trying' },
    prefill: {
      zh: 'Hi Aqina SG，我想先试口感，1 盒 7 天装适合我吗？',
      en: 'Hi Aqina SG, I would like to try the taste first — does the 1-box 7-day pack suit me?',
    },
  },
];

/* ------------------------------------------------------------------ *
 * The three real objections, taken from actual inbox conversations
 * (backend/exports/inbox-analysis/): "Made with chinese herbs",
 * "IS THE TASTE NAUSEATIC AS A TASTE FISH ESSENSE" / "BITTER",
 * and repeated pregnancy / breastfeeding / medical questions.
 * ------------------------------------------------------------------ */
export interface Concern {
  id: string;
  question: L;
  answer: L;
  note?: L;
}

export const CONCERNS: Concern[] = [
  {
    id: 'herbs',
    question: { zh: '会不会燥？', en: 'Will it be too "heaty"?' },
    // [鸡精介绍] §2「100% 无添加：无防腐剂、无味精、不加水稀释」§6「100% 鸡骨与鸡肉熬制，不加水、不加防腐剂」
    answer: {
      zh: '配方是 100% 鸡骨与鸡肉熬制，不加水、不加防腐剂、不加味精。里面没有当归、人参这类药材，所以不是药材燥补那一路。',
      en: 'It is brewed from 100% chicken bone and chicken meat, with no added water, no preservatives and no MSG. There are no herbs such as dang gui or ginseng — it is not a herbal tonic.',
    },
    note: {
      zh: '真的有顾客问过「是不是加了中药材」，答案是没有。',
      en: 'A real customer asked us whether it contains Chinese herbs. It does not.',
    },
  },
  {
    id: 'fishy',
    question: { zh: '会不会腥？', en: 'Will it taste fishy?' },
    // [核实资料] §2 工艺表达 double-boiled / 口感方向；§7.1 口感卖点
    answer: {
      zh: '双重蒸煮会把多余的油脂和腥味滤掉，入口比较像熬久了的清鸡汤，清爽、不油腻、有自然的回甘。',
      en: 'Double-boiling filters out the excess fat and the gamey note. It drinks like a clear chicken soup that has been simmered a long time — light, not greasy, with a natural sweetness.',
    },
    note: {
      zh: '不确定合不合口味，就先拿 1 盒 7 天装试，别一次买多。',
      en: 'Not sure it suits your palate? Start with the 1-box 7-day pack rather than buying more.',
    },
  },
  {
    id: 'pregnancy',
    question: { zh: '孕期／月子能不能喝？', en: 'Can I drink it during pregnancy or confinement?' },
    answer: {
      zh: '这是食品补养，不是药。配方里没有药材。孕期、哺乳期、正在治疗或服药的话，请按自己的身体状况和医生建议安排，也可以先 WhatsApp 问清楚再决定。',
      en: 'This is food nourishment, not medicine, and the formula contains no herbs. If you are pregnant, breastfeeding, under treatment or on medication, please follow your own condition and your doctor’s advice — or ask us on WhatsApp first.',
    },
    note: {
      zh: '我们不会跟你说「一定要喝」。说不满的话，你也不会信。',
      en: 'We will not tell you that you must drink it. An overclaim would not earn your trust anyway.',
    },
  },
];

/* ------------------------------------------------------------------ *
 * Source & process chain — facts only.
 * 70 days = the chicken's grow-out period per [公司简介] p.11
 * ("在长达 70 天的悠然成长旅程中…特别添加了源自 MD2 黄梨的天然菠萝蛋白酶").
 * It is NOT a brewing duration. No brewing day-count is asserted anywhere,
 * because no client document confirms one — see the handover report.
 * ------------------------------------------------------------------ */
export interface SourceStep {
  id: string;
  title: L;
  body: L;
}

export const SOURCE_CHAIN: SourceStep[] = [
  {
    id: 'farm',
    title: { zh: 'Aqina farm 自家农场', en: 'Aqina farm — our own farms' },
    body: {
      zh: '亚齐纳集团做家禽三十年，自家 46 座禽场与 8 处 MD2 黄梨种植地，从饲料、养殖到加工一条链自己掌控。',
      en: 'The Aqina group has been in poultry for thirty years, with 46 of its own poultry farms and 8 MD2 pineapple plantations — feed, farming and processing all in one chain.',
    },
  },
  {
    id: 'chicken',
    title: { zh: 'MD2 黄梨酵素喂养，70 天自然成长', en: 'MD2 pineapple enzyme feed, 70 days of natural growth' },
    body: {
      zh: '鸡只饲料里加入源自 MD2 黄梨的天然菠萝蛋白酶，在农场慢慢养到 70 天。70 天说的是鸡的成长天数，不是熬煮时间。',
      en: 'The feed includes natural bromelain from MD2 pineapple, and the birds grow on the farm for 70 days. The 70 days refers to how long the chicken is raised — not to brewing time.',
    },
  },
  {
    id: 'double-boiled',
    title: { zh: '整只黄梨鸡，双重蒸煮', en: 'Whole pineapple chicken, double-boiled' },
    body: {
      zh: '用整只黄梨鸡双重蒸煮滴出精华，过程中滤去多余油脂与腥味，所以汤色清透不浑浊。',
      en: 'Whole pineapple chickens are double-boiled and dripped. Excess fat and the gamey note are filtered out along the way, which is why the broth runs clear rather than cloudy.',
    },
  },
  {
    id: 'pure',
    title: { zh: '100% 纯鸡精，不加一滴水', en: '100% pure chicken essence, not a drop of water' },
    body: {
      zh: '不加水稀释、不加防腐剂、不加味精。盒身印着「萃取自黄梨鸡的精华 · Single Origin From Aqina Pineapple Chicken」。',
      en: 'No dilution with water, no preservatives, no MSG. The box itself reads "Single Origin From Aqina Pineapple Chicken".',
    },
  },
  {
    id: 'sachet',
    title: { zh: '金色小袋 7 PACKS × 60g', en: 'Golden sachets, 7 PACKS × 60g' },
    body: {
      zh: '一盒 7 袋，一袋 60g。盒上直接写着「一周七日，一天一袋」，撕开温热就能喝，不必熬汤。',
      en: 'Seven sachets per box, 60g each. The box says "seven days a week, one sachet a day" — tear, warm, drink. No soup-making required.',
    },
  },
];

// [核实资料] §2 营养卖点 — only these three are confirmed.
export const NUTRITION_FACTS: L[] = [
  { zh: 'High Protein 高蛋白', en: 'High Protein' },
  { zh: 'Trans Fat Free 无反式脂肪', en: 'Trans Fat Free' },
  { zh: 'Cholesterol Free 无胆固醇', en: 'Cholesterol Free' },
];

/* ------------------------------------------------------------------ *
 * Rhythm & budget re-anchor.
 * [核实资料] §2「建议每天 1 袋，1 盒约 7 天」+ printed on the box.
 * ------------------------------------------------------------------ */
export interface RhythmRow {
  stage: L;
  days: L;
  boxes: L;
  /** How that box count maps onto packs actually sold (only 1-box and 2-box exist). */
  note?: L;
}

export const RHYTHM_ROWS: RhythmRow[] = [
  {
    stage: { zh: '先试口感', en: 'Try the taste first' },
    days: { zh: '7 天', en: '7 days' },
    boxes: { zh: '1 盒', en: '1 box' },
  },
  {
    stage: { zh: '孕晚期常备', en: 'Late pregnancy, kept on hand' },
    days: { zh: '14 天', en: '14 days' },
    boxes: { zh: '2 盒', en: '2 boxes' },
  },
  {
    stage: { zh: '月子期整月', en: 'A full confinement month' },
    days: { zh: '28 天', en: '28 days' },
    boxes: { zh: '4 盒', en: '4 boxes' },
    // Only 1-box and 2-box packs are sold, so spell out how 4 boxes is actually bought.
    note: { zh: '＝ 两份 2 盒装', en: '= two 2-box packs' },
  },
];

/* ------------------------------------------------------------------ *
 * Cooking / golden stock. [核实资料] §6.7 + §7.4 explicitly allow this.
 * Not framed as food therapy.
 * ------------------------------------------------------------------ */
export const COOKING_USES: L[] = [
  { zh: '加进面线', en: 'Into mee sua' },
  { zh: '拌蒸蛋', en: 'Into steamed egg' },
  { zh: '当汤底', en: 'As a soup base' },
  { zh: '淋热菜', en: 'Over a hot dish' },
  { zh: '直接温热喝', en: 'Or simply warmed and drunk' },
];

/* ------------------------------------------------------------------ *
 * Seller identity. Every row below is verifiable:
 *  - Boong Poultry Pte Ltd — the PayNow payee (src/lib/site-config.ts) AND
 *    the group's first Singapore subsidiary, founded 1994 [公司简介 p.3]
 *  - certifications — chatbot_settings.py knowledge base (owner-confirmed, 887d791)
 * UEN and a named/photographed representative are NOT in any client document,
 * so they are deliberately absent rather than invented. See handover report.
 * ------------------------------------------------------------------ */
export interface IdentityRow {
  label: L;
  value: L;
}

export const SELLER_IDENTITY: IdentityRow[] = [
  {
    label: { zh: 'PayNow 收款方', en: 'PayNow payee' },
    value: { zh: 'Boong Poultry Pte Ltd', en: 'Boong Poultry Pte Ltd' },
  },
  {
    label: { zh: '公司背景', en: 'Company background' },
    value: {
      zh: '亚齐纳集团于 1994 年在新加坡成立的子公司，集团做家禽已三十年',
      en: "The group's Singapore subsidiary, incorporated 1994; thirty years in poultry",
    },
  },
  {
    label: { zh: '认证', en: 'Certifications' },
    value: { zh: 'JAKIM Halal 认证 · SFA 注册 · HACCP · GMP', en: 'JAKIM Halal · SFA registered · HACCP · GMP' },
  },
  {
    label: { zh: '配送', en: 'Delivery' },
    value: { zh: '新加坡现货，2–3 天冷链送达', en: 'Singapore stock, 2–3 day cold-chain delivery' },
  },
  {
    label: { zh: '真人客服', en: 'Talk to a person' },
    value: { zh: 'WhatsApp +65 9626 5734（营业时间内回复）', en: 'WhatsApp +65 9626 5734 (replies during business hours)' },
  },
  {
    label: { zh: '电邮', en: 'Email' },
    value: { zh: 'aqina_marketing@aqinafarm.com', en: 'aqina_marketing@aqinafarm.com' },
  },
];

/* ------------------------------------------------------------------ *
 * Proof assets — real photographs only. Captions describe what is in the
 * frame. No image is labelled as a named buyer or a "verified buyer".
 * ------------------------------------------------------------------ */
export interface ProofItem {
  src: string;
  caption: L;
  alt: L;
}

export const PROOF_PRODUCT: ProofItem[] = [
  {
    src: '/proof/product-unboxing-bowl.webp',
    caption: { zh: '开盒：外盒、独立小袋与倒出来的金汤', en: 'Unboxed: outer box, single sachet, and the poured broth' },
    alt: { zh: 'Aqina 纯鸡精开盒，盒装、单包与一碗金汤', en: 'Aqina Pure Chicken Essence unboxed with a bowl of golden broth' },
  },
  {
    src: '/proof/pack-detail-single-origin.webp',
    caption: { zh: '盒身细节：Pure Chicken Essence · Single Origin', en: 'Box detail: Pure Chicken Essence · Single Origin' },
    alt: { zh: 'Aqina 纯鸡精包装侧面细节特写', en: 'Close-up of the Aqina Pure Chicken Essence box side panel' },
  },
  {
    src: '/proof/pour-golden-broth.webp',
    caption: { zh: '倒出来是清透的金汤色，不浑浊', en: 'It pours a clear golden colour, not cloudy' },
    alt: { zh: '纯鸡精倒入碗中的近景', en: 'Pure chicken essence being poured into a bowl' },
  },
  {
    src: '/proof/seven-sachets-flatlay.webp',
    caption: { zh: '一盒 7 袋，一袋 60g', en: 'Seven sachets per box, 60g each' },
    alt: { zh: 'Aqina 纯鸡精多包平铺', en: 'Aqina Pure Chicken Essence sachets laid flat' },
  },
  {
    src: '/proof/sachet-bowl-overhead.webp',
    caption: { zh: '单包 60g Per Serving，撕开温热即饮', en: 'One 60g serving per sachet — tear, warm, drink' },
    alt: { zh: '单包纯鸡精与碗的俯拍', en: 'Overhead view of a sachet and a bowl' },
  },
  {
    src: '/proof/golden-broth-macro.webp',
    caption: { zh: '汤体微距：滤去多余油脂后的清爽质地', en: 'Macro: the light texture left after the fat is filtered out' },
    alt: { zh: '金黄色鸡精汤微距特写', en: 'Macro close-up of the golden chicken essence' },
  },
];

export const PROOF_SCENES: ProofItem[] = [
  {
    src: '/proof/scene-family-handover.webp',
    caption: { zh: '家人递上一袋的日常场景', en: 'Handing a sachet to family' },
    alt: { zh: '家人递纯鸡精的关怀场景', en: 'A family member passing over a sachet of chicken essence' },
  },
  {
    src: '/proof/scene-kitchen-woman.webp',
    caption: { zh: '厨房里温一袋', en: 'Warming one in the kitchen' },
    alt: { zh: '明亮厨房里手持纯鸡精的女生', en: 'A woman holding the product in a bright kitchen' },
  },
  {
    src: '/proof/scene-office-sachet.webp',
    caption: { zh: '办公桌上的一袋', en: 'One sachet at the desk' },
    alt: { zh: '办公室里手持纯鸡精单包', en: 'Holding a single sachet in an office' },
  },
  {
    src: '/proof/scene-elder-woman.webp',
    caption: { zh: '长辈也容易入口', en: 'Easy for elders to drink' },
    alt: { zh: '年长女士手持纯鸡精', en: 'An older woman holding the product' },
  },
];

/* ------------------------------------------------------------------ *
 * Gift options — names and weights mirror OFFER_RESET_GIFTS exactly.
 * The "market value $8" line from the old page is dropped: it is a price
 * claim with no basis in any client document.
 * ------------------------------------------------------------------ */
export interface GiftOption {
  value: string;
  name: string;
  weight: string;
  image: string;
}

export const GIFT_OPTIONS: GiftOption[] = [
  { value: 'French Poulet Minced 400g', name: 'French Poulet Minced', weight: '400g', image: '/french-poulet-gift/minced.png' },
  { value: 'French Poulet 3 Joint Wing 500g', name: 'French Poulet 3 Joint Wing', weight: '500g', image: '/french-poulet-gift/chicken-wing.jpg' },
  { value: 'French Poulet Boneless Breast 350g', name: 'French Poulet Boneless Breast', weight: '350g', image: '/french-poulet-gift/boneless-breast.png' },
  { value: 'French Poulet Whole Leg 400g', name: 'French Poulet Whole Leg', weight: '400g', image: '/french-poulet-gift/whole-leg.jpg' },
  { value: 'French Poulet Half Chicken Cut 4 Pieces 500g', name: 'French Poulet Half Chicken Cut 4 Pieces', weight: '500g', image: '/french-poulet-gift/half-chicken-4-cut.jpg' },
];

/* ------------------------------------------------------------------ *
 * FAQ — rewritten against the real questions in the 2026-05-23 inbox analysis.
 * ------------------------------------------------------------------ */
export interface FaqItem {
  q: L;
  a: L;
}

export const FAQ_ITEMS: FaqItem[] = [
  {
    q: { zh: '为什么比普通瓶装鸡精贵？', en: 'Why is it pricier than an ordinary bottled chicken essence?' },
    a: {
      zh: '差别在来源和工艺：自家农场的整只黄梨鸡、双重蒸煮、100% 纯鸡精不加水。同样是 60g 一袋的滴鸡精，Aqina 反而比 premium 有机滴鸡精便宜——上面的价格表可以自己核对。',
      en: 'The difference is source and process: whole pineapple chickens from our own farms, double-boiled, 100% pure with no water added. Compared like-for-like against a 60g premium organic drip chicken essence sachet, Aqina actually costs less — check the table above yourself.',
    },
  },
  {
    q: { zh: '黄梨鸡是不是黄梨味？', en: 'Does pineapple chicken taste of pineapple?' },
    a: {
      zh: '不是。黄梨指的是鸡的饲养方式——饲料里加了源自 MD2 黄梨的天然酵素。喝起来是清鸡汤味，没有果味。',
      en: 'No. "Pineapple" describes how the chicken is raised — its feed contains natural enzyme from MD2 pineapple. It tastes like clear chicken soup, not fruit.',
    },
  },
  {
    q: { zh: '第一次买几盒？', en: 'How many boxes should I start with?' },
    a: {
      zh: '没喝过就 1 盒 7 天装，先确认口味。已经决定要连续喝，或买给孕期、月子的家人，就 2 盒——每盒等于 SGD 39.90，还有一份 French Poulet 赠品。月子整月是 28 天 = 4 盒，也就是两份 2 盒装；直接跟客服说，我们帮你一次安排好。',
      en: 'If you have never tried it, take the 1-box 7-day pack and confirm the taste first. If you already intend to drink it daily, or are buying for someone pregnant or in confinement, take 2 boxes — that works out to SGD 39.90 a box plus one French Poulet gift. A full confinement month is 28 days = 4 boxes, i.e. two 2-box packs; just tell us and we will set it up in one go.',
    },
  },
  {
    q: { zh: '2 盒送什么？', en: 'What comes with 2 boxes?' },
    a: {
      zh: '送 1 份 French Poulet 冷冻鸡肉，五选一：Minced 400g、3 Joint Wing 500g、Boneless Breast 350g、Whole Leg 400g、Half Chicken Cut 4 Pieces 500g。下单时选，跟鸡精一起冷链送到。',
      en: 'One French Poulet frozen chicken item, your pick of five: Minced 400g, 3 Joint Wing 500g, Boneless Breast 350g, Whole Leg 400g, or Half Chicken Cut 4 Pieces 500g. Choose at checkout; it ships cold-chain together with the essence.',
    },
  },
  {
    q: { zh: '怎么喝？能不能入菜？', en: 'How do I take it? Can I cook with it?' },
    a: {
      zh: '撕开温热就能喝，一天一袋。也可以当黄金原汤用——加进面线、拌蒸蛋、当汤底、淋热菜都行。家人不爱直接喝补养饮品的话，这是最自然的办法。',
      en: 'Tear it open, warm it, drink it — one sachet a day. You can also use it as a golden stock: in mee sua, steamed egg, a soup base, or over a hot dish. If your family will not drink a tonic straight, this is the easiest way around it.',
    },
  },
  {
    q: { zh: '几天到货？', en: 'How long does delivery take?' },
    a: {
      zh: '新加坡现货，确认订单后一般 2–3 个工作日冷链送达，配送已包含在价格里。',
      en: 'Stocked in Singapore. After your order is confirmed it usually arrives in 2–3 working days by cold chain, and delivery is already included in the price.',
    },
  },
  {
    q: { zh: 'PayNow 怎么付？付款之后会发生什么？', en: 'How does PayNow work, and what happens after I pay?' },
    a: {
      zh: '收款方是 Boong Poultry Pte Ltd——就是我们在新加坡的公司主体，转账前你可以在 PayNow 上看到这个名字再决定。步骤是：选配套 → 扫我们的 PayNow QR → 备注填 WhatsApp 号码 → 把转账截图发回来 → 真人客服核对后确认订单并安排配送。没有 COD。截图核对之前，我们不会先出货，你也不用先给任何证件资料。',
      en: 'The payee is Boong Poultry Pte Ltd — our Singapore entity. You will see that name in PayNow before you confirm the transfer. The steps: pick a pack → scan our PayNow QR → put your WhatsApp number in the reference → send the transfer screenshot back → a real person checks it, confirms the order and arranges delivery. There is no COD. Nothing ships before the screenshot is checked, and you never need to hand over identity documents.',
    },
  },
  {
    q: { zh: '有什么认证？Halal 是哪一个？', en: 'What certifications do you have, and which Halal is it?' },
    a: {
      zh: 'JAKIM Halal 认证（马来西亚），加上 SFA 注册、HACCP、GMP。说清楚一点：是 JAKIM，不是新加坡的 MUIS，因为生产在马来西亚的清真认证工厂。',
      en: 'JAKIM Halal (Malaysia), plus SFA registration, HACCP and GMP. To be precise: it is JAKIM, not Singapore’s MUIS, because production is at our Halal-certified plant in Malaysia.',
    },
  },
  {
    q: { zh: '有特殊健康状况怎么办？', en: 'What if I have a special health condition?' },
    a: {
      // verbatim from OfferResetLandingPage.tsx:302 / :328
      zh: 'Aqina 纯鸡精是日常食品滋养，不替代医疗建议。有特殊健康状况、孕产或治疗中的顾客，请先咨询医生或 WhatsApp 真人客服。',
      en: 'Aqina Pure Chicken Essence is a food nourishment product and does not replace medical advice. Customers with special conditions, pregnancy, or treatment should ask a doctor or WhatsApp support first.',
    },
  },
];

/* The medical boundary sentence, shown on desktop and mobile. */
export const MEDICAL_BOUNDARY: L = {
  zh: 'Aqina 纯鸡精是日常食品滋养，不替代医疗建议。有特殊健康状况、孕产或治疗中的顾客，请先咨询医生或 WhatsApp 真人客服。',
  en: 'Aqina Pure Chicken Essence is a food nourishment product and does not replace medical advice. Customers with special conditions, pregnancy, or treatment should ask a doctor or WhatsApp support first.',
};

/* ------------------------------------------------------------------ *
 * Section copy
 * ------------------------------------------------------------------ */
export const COPY: Record<string, L> = {
  heroEyebrow: {
    zh: '新加坡现货 · JAKIM Halal 认证 · 每天一袋',
    en: 'Singapore stock · JAKIM Halal certified · one sachet a day',
  },
  heroTitle: {
    zh: '整只黄梨鸡，双重蒸煮滴出的纯鸡精',
    en: 'Whole pineapple chicken, double-boiled into pure chicken essence',
  },
  heroSub: {
    zh: '清爽像清汤，不油不腻；孕期、月子、家人日常，每天温热一袋。',
    en: 'Light as a clear soup, never greasy. For pregnancy, confinement and everyday family care — one warm sachet a day.',
  },
  trustStrip1: { zh: '新加坡现货', en: 'Singapore stock' },
  trustStrip2: { zh: 'JAKIM Halal', en: 'JAKIM Halal' },
  trustStrip3: { zh: '2–3 天送达', en: '2–3 day delivery' },
  trustStrip4: { zh: 'WhatsApp 真人咨询', en: 'Talk to a real person' },

  valueTitle: { zh: '同规格比一比，价格自己核对', en: 'Compare like for like — then check it yourself' },
  valueSubtitle: {
    zh: '同样是一袋 60g 的滴鸡精，同样有 Halal 认证。',
    en: 'Same 60g drip chicken essence sachet. Both Halal certified.',
  },
  valuePerSachet: { zh: '每袋约', en: 'about / sachet' },
  valueDisclaimer: {
    zh: '竞品价格为 2026-07-25 查自 Eu Yan Sang 新加坡官网的标价（会员价另计），会变动，请以对方官网为准。此处只做同规格价格对比，不代表两者成分或配方相同。',
    en: 'Competitor price is the list price shown on Eu Yan Sang Singapore’s own site on 2026-07-25 (member price differs) and may change — please verify on their site. This compares pack format and price only, and implies nothing about the two formulas.',
  },

  intentTitle: { zh: '你是哪一种情况？', en: 'Which one is you?' },
  intentSubtitle: {
    zh: '选一个，客服接手时就已经知道你的情况，不用从头问起。',
    en: 'Pick one and our team already knows your situation — no starting from scratch.',
  },

  concernsTitle: { zh: '买之前，多数人先卡在这三件事', en: 'Three things most people want settled first' },
  concernsSubtitle: {
    zh: '下面是真实顾客问过的问题，我们照实回答。',
    en: 'These are questions real customers asked us. Here are the straight answers.',
  },

  sourceTitle: { zh: '一袋纯鸡精，是怎么来的', en: 'Where a sachet actually comes from' },
  sourceSubtitle: {
    zh: '不讲功效，只讲来源和工艺。',
    en: 'No efficacy talk — just source and process.',
  },
  notPineappleFlavour: {
    zh: '黄梨鸡不是黄梨味：黄梨说的是饲养方式，喝起来是清鸡汤味。',
    en: 'Pineapple chicken is not pineapple-flavoured: "pineapple" describes the feed. It tastes of clear chicken soup.',
  },
  nutritionTitle: { zh: '已确认的营养标示', en: 'Confirmed nutrition claims' },

  rhythmTitle: { zh: '要买几盒，其实算得出来', en: 'How many boxes? You can just do the maths' },
  rhythmSubtitle: {
    zh: '每天 1 袋，1 盒 7 天——盒上就是这么写的。所以月子 28 天等于 4 盒，不用猜。',
    en: 'One sachet a day, one box lasts 7 days — it says so on the box. So a 28-day confinement month is 4 boxes. No guessing.',
  },
  rhythmBudget: {
    zh: '新加坡的月子开销本来就是几千块起跳——月嫂、月子餐、月子中心。一个月的纯鸡精，是这笔预算里比较小的一项。要不要买、买多少，还是按你自己的安排来。',
    en: 'A confinement month in Singapore already runs into the thousands — the nanny, the meals, the centre. A month of chicken essence is one of the smaller lines in that budget. Whether and how much to buy is still your call.',
  },
  rhythmCta: { zh: '告诉客服你在孕期还是月子期，让客服帮你算要几盒', en: 'Tell us your stage and we will work out the box count with you' },

  cookingTitle: { zh: '不想直接喝？它本来就是一包黄金原汤', en: 'Don’t want to drink it straight? It is a golden stock' },
  cookingBody: {
    zh: '家人不一定愿意端起一碗补养饮品，但没有人会拒绝一碗更鲜的面线。一袋纯鸡精就是现成的原汤，直接倒进去就行，不用另外熬。',
    en: 'Not everyone will pick up a bowl of tonic, but nobody refuses a better bowl of mee sua. A sachet is ready-made stock — pour it in, no simmering required.',
  },

  identityTitle: { zh: '你在跟谁买', en: 'Who you are buying from' },
  identitySubtitle: {
    zh: '我们不开平台店，付款走 PayNow 转账。所以这些资料我们自己列出来，你可以逐条核对。',
    en: 'We do not run a marketplace storefront and payment is a PayNow transfer — so here are the details, laid out for you to check line by line.',
  },
  identityPaynowNote: {
    zh: '转账前你会在 PayNow 上看到收款名称「Boong Poultry Pte Ltd」，对得上再付。',
    en: 'Before you transfer, PayNow will show the payee name "Boong Poultry Pte Ltd". Match it, then pay.',
  },

  proofTitle: { zh: '真实产品，真实场景', en: 'Real product, real scenes' },
  proofSubtitle: {
    zh: '以下都是实拍照片。',
    en: 'Every photograph below is real.',
  },
  proofProductHeading: { zh: '产品实拍', en: 'The product itself' },
  proofSceneHeading: { zh: '使用场景', en: 'In use' },
  proofHonesty: {
    zh: '我们没有在这一页放评分、销量或署名好评。真实顾客的原话，要等顾客本人授权之后才会刊登——在那之前，我们宁可让你看产品本身。',
    en: 'You will not find a rating, a units-sold figure or a signed testimonial on this page. Real customer words go up only after that customer has given permission — until then we would rather show you the product itself.',
  },

  offersTitle: { zh: '选配套', en: 'Choose your pack' },
  giftsTitle: { zh: '2 盒专享：French Poulet 赠品五选一', en: '2-box exclusive: pick one French Poulet gift' },
  faqTitle: { zh: '常见问答', en: 'Common questions' },

  ctaWhatsApp: { zh: 'WhatsApp 问客服', en: 'Ask us on WhatsApp' },
  ctaPayNow: { zh: 'PayNow 直接下单', en: 'Order now with PayNow' },
  stickyPrefix: { zh: '2 盒', en: '2 boxes' },
};

export function getMarketplaceWhatsAppMessage(locale: string, intentId?: IntentOption['id']) {
  const safe = normalizeMarketplaceLocale(locale);
  const intent = INTENT_OPTIONS.find((option) => option.id === intentId);
  if (intent) return intent.prefill[safe];
  return safe === 'zh'
    ? 'Hi Aqina SG，我想问 Aqina 纯鸡精，麻烦帮我看看哪个配套适合我。'
    : 'Hi Aqina SG, I would like to ask about Aqina Pure Chicken Essence — which pack suits me?';
}
