# Aqina 纯鸡精 Offer Reset - Source Of Truth

Date: 2026-06-01

## Dispatcher Routing

我是总调度。我判断本次应由【广告图总监】主导，【落地页设计师】、【客服成交设计师】支持；短视频提示词沿用广告创意主线，不另开一套卖点。

## Current Judgment

- 任务表面：Aqina 纯鸡精新销售方式、landing page、广告图、短视频、chatbot 回复 prompt pack
- Lead worker：广告图总监
- Support workers：落地页设计师、客服成交设计师
- Read depth：worker registry + 广告图/落地页/短视频/chatbot worker page + Aqina repo/PDF facts
- Safety gate：本次只写 Markdown prompts，不改 live chatbot、不改价格系统、不部署、不投放、不调用付费生成

## New Offer Facts

### Product Positioning

- Customer-facing Chinese product term: `Aqina 纯鸡精`
- English/category reference for internal prompts: premium sachet / drip-style chicken essence category
- Education angle: many customers compare Aqina with ordinary traditional bottled chicken essence, but Aqina should be framed as a higher-grade pure chicken essence route, not as the cheapest bottled chicken essence substitute.
- Do not attack competitor brands. Use the comparison to clarify category, ingredient level, and value.
- Do not write Aqina as free-range or 走地鸡. Use `French Poulet`, `黄梨酵素鸡`, or `pineapple enzyme-fed French Poulet` when needed.

### Pricing And Promotion

- 1-box price: `1盒 = SGD47.90`
- 2-box offer: `2盒 = SGD79.80`
- 2-box effective price: `SGD39.90 / box`
- 2-box price gap: buying 2 single boxes would be `SGD95.80`; the 2-box offer is `SGD16.00` lower before counting the gift.
- 2-box gift: buy 2 boxes and choose 1 French Poulet cut part, market value `SGD8`
- Use only 1-box and 2-box offers in this prompt pack. Do not create 3-box, 4-box, or 6-box bundles unless Aqina confirms a separate offer later.
- Avoid making `包邮`, `免运`, `free shipping`, or `shipping fee` the advertising hook.
- If shipping is asked directly in chatbot, answer operationally without turning it into the main offer.

[Assumption] Only the 2-box gift is confirmed. Do not automatically promise multi-box gift scaling unless Aqina confirms it.

### Cut Part Gift Options

Source: `/Users/ginooh/Downloads/AqinaFarm Product List.pdf`, with user override for minced weight.

| Gift option | Weight | Customer-facing label |
|---|---:|---|
| French Poulet 3 Joint Wing | 500g | French Poulet 3 Joint Wing 500g |
| French Poulet Minced | 400g | French Poulet Minced 400g |
| French Poulet Boneless Breast | 350g | French Poulet Boneless Breast 350g |
| French Poulet Whole Leg | 400g | French Poulet Whole Leg 400g |
| French Poulet Half Chicken Cut 4 Pieces | 500g | French Poulet Half Chicken Cut 4 Pieces 500g |

## Messaging Rules

Use:

- `不是普通瓶装鸡精的价格比较，而是更高级别的 Aqina 纯鸡精。`
- `1盒 SGD47.90；2盒 SGD79.80，等于每盒 SGD39.90，再加送 French Poulet Cut Part 任选一包。`
- `Cut Part 来自 Aqina French Poulet / 黄梨酵素鸡，不是普通肉鸡。`
- `如果你本来就想试纯鸡精，两盒更像 14 天起步，也多一包可煮的 French Poulet。`

Avoid:

- `免运`, `包邮`, `free shipping` as headline or main sell point
- Medical, disease, recovery, fertility, or guaranteed health claims
- Fake testimonials, invented reviews, or before/after claims
- Real competitor logos or packaging in generated ads
- Calling the product by any Chinese name other than `Aqina 纯鸡精`

## Review Checklist

- Does every prompt use the same price logic: `1盒 SGD47.90`; `2盒 SGD79.80`; 2-box effective price `SGD39.90 / box`?
- Does every prompt mention the 2-box gift as 1 selectable French Poulet cut part?
- Does every prompt avoid creating 3-box, 4-box, or 6-box packages?
- Are the five cut part options and weights consistent?
- Is the education angle clear without attacking traditional chicken essence brands?
- Are shipping/free-shipping terms removed from headline and main CTA?
- Are all claims conservative and food/nourishment-based?
