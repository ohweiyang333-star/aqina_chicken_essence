# Landing Page Prompt - Aqina 纯鸡精 Offer Reset

Use this prompt in the AI / coding / design window that will generate the new landing page brief or implementation.

```text
你是 Landing Page Builder + direct-response conversion copywriter。请为 Singapore Aqina 纯鸡精制作一个 mobile-first landing page 方案，目标是把顾客从“为什么这么贵，我拿 Brand's / traditional bottled chicken essence 比较”引导到“原来这是更高级别的 pure chicken essence，2盒还有 French Poulet cut part 赠品，可以咨询/下单”。

请只输出 landing page brief / implementation plan，不要部署，不要改 production。

必须使用的事实：
- 产品名：Aqina 纯鸡精
- 核心教育：很多顾客用 ordinary traditional bottled chicken essence 做价格锚点，但 Aqina 纯鸡精属于更高等级的 pure chicken essence / premium sachet route，不是最低价瓶装鸡精替代品。
- 原料/价值表达：Aqina 使用 French Poulet / 黄梨酵素鸡，不能写成 free-range / 走地鸡。可以说它不是普通肉鸡，属于更高级别的 pineapple enzyme-fed French Poulet。
- 价格：1盒 SGD47.90；2盒 SGD79.80。
- 两盒优惠表达：2盒等于每盒 SGD39.90，比买两盒单盒价 SGD95.80 少 SGD16.00，还多送 Cut Part。
- 促销：买2盒送1包 French Poulet Cut Part，market value SGD8，可以任选以下其中一包：
  1. French Poulet 3 Joint Wing 500g
  2. French Poulet Minced 400g
  3. French Poulet Boneless Breast 350g
  4. French Poulet Whole Leg 400g
  5. French Poulet Half Chicken Cut 4 Pieces 500g
- 不要把包邮/免运/运费当成页面 headline 或主卖点。主卖点是：1盒 SGD47.90；2盒 SGD79.80，等于每盒 SGD39.90，并加送有实际价值的 French Poulet Cut Part。
- 不要设计 3盒、4盒、6盒或其他多盒配套；这次页面只呈现 1盒和2盒。

页面目标：
1. 第一屏 3 秒内讲清楚：这不是 ordinary bottled chicken essence 的价格比较；这是 Aqina 纯鸡精，1盒 SGD47.90，2盒 SGD79.80 等于每盒 SGD39.90，还送 French Poulet Cut Part。
2. 教育顾客为什么 traditional chicken essence 和 Aqina 纯鸡精不是同一等级。
3. 让顾客看到 2盒配套不是单纯买多，而是得到 14天纯鸡精 + 一包可煮的 French Poulet cut part。
4. CTA 引导 WhatsApp / Messenger 咨询或下单。

页面结构要求：
- `title` 和 `meta description` 要包含 Aqina 纯鸡精、1盒 SGD47.90、2盒 SGD79.80、2盒赠 French Poulet Cut Part。
- 使用 semantic HTML5 structure，并给关键 CTA / offer / FAQ section unique IDs。
- Mobile-first；第一屏不要太满，价格和赠品必须一眼看到。
- 页面不要像科普文章，也不要像品牌自夸；每个 section 都要服务“看懂、相信、行动”。

建议页面模块：
1. Hero
   - Headline 方向：`不是普通瓶装鸡精的价格比较，是 Aqina 纯鸡精的原汤等级。`
   - Price line：`1盒 SGD47.90`
   - Offer line：`2盒 SGD79.80，等于每盒 SGD39.90，送 French Poulet Cut Part 任选一包`
   - CTA：`问客服适合哪一盒` / `查看2盒赠品`
   - Visual：Aqina 纯鸡精 packshot + French Poulet cut part selector hint，不要用抽象 stock food。
2. Comparison education
   - 用温和表格说明：ordinary traditional bottled chicken essence vs Aqina 纯鸡精。
   - 不贬低 competitor，不出现真实 competitor logo。
   - 重点讲 category、原料等级、pouch/原汤浓缩、日常滋养场景。
3. Offer block
   - 1盒：SGD47.90，适合第一次试口感。
   - 2盒：SGD79.80，适合 14天起步，等于每盒 SGD39.90，比买两盒单盒价少 SGD16.00，并送 French Poulet Cut Part 任选一包。
   - 不要出现 3盒、4盒、6盒或其他配套。
4. Cut Part chooser
   - 五个 gift card，每个显示英文名 + 重量 + `market value SGD8`。
   - 文案强调：这不是普通肉鸡，是 Aqina French Poulet / 黄梨酵素鸡。
5. Trust / proof block
   - 用保守、可证明的说法：French Poulet、pineapple enzyme-fed, pure chicken essence route。
   - 如果要写 `no added water / no preservatives / no MSG / no caramel coloring`，请标记为需要项目资料确认后才上正式文案。
6. FAQ
   - `为什么比普通瓶装鸡精贵？`
   - `和 traditional chicken essence 有什么不同？`
   - `2盒送的 Cut Part 可以选什么？`
   - `第一次买应该拿1盒还是2盒？`
   - `孕妇、长辈、术后/疾病相关问题怎么办？` 回答必须保守：这是日常食品滋养，不替代医疗建议，有特殊状况请先问医生或真人客服。
7. Final CTA
   - `我想问2盒赠品`
   - `我想先试1盒`
   - CTA message should prefill: `Hi Aqina SG，我想了解 Aqina 纯鸡精 2盒 SGD79.80 送 French Poulet Cut Part 的配套。`

Tone：
- 中文为主，新加坡华人能懂，直接、有信任感，不要过度保健品式夸大。
- 可以有 English product names: French Poulet, Cut Part, 3 Joint Wing, Boneless Breast。
- 不要用恐吓式健康焦虑，不要保证效果。

请输出：
1. Landing page section-by-section brief
2. 每个 section 的 headline / body copy / CTA
3. 每个 section 需要的视觉素材描述
4. FAQ 文案
5. Mobile layout notes
6. A/B test ideas: hero education angle vs 2-box gift angle
```
