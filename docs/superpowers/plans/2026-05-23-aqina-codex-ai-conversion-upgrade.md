# Aqina Codex AI Conversion Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 把 Aqina 目前“广告能带来询问，但 inbox 没有稳定转成订单”的问题，改成可追踪、可接手、可复盘的 `conversation -> cart_hot -> order -> payment` 流程。

**Architecture:** 先不大改整个系统，只对 chatbot routing、saved settings、follow-up、订单归因、admin inbox 标记、landing page BOFU 区块和报告脚本做手术式改动。核心是把高意向顾客从普通咨询流分离出来，进入明确下单流程，并让订单回写到 conversation 和 ad attribution。

**Tech Stack:** Python/FastAPI backend, Firestore, pytest, Next.js/React frontend, TypeScript, Firebase/Cloud Run deployment through GitHub Actions only.

---

## Scope

本计划只覆盖 **Codex AI / 技术侧能做的事**。不包含广告投放手的预算调整，也不替 Aqina 决定 COD、价格、配送承诺或孕期安全边界。

输入依据：
- `backend/exports/inbox-analysis/aqina-inbox-conversion-analysis-2026-05-23.md`
- `backend/exports/ads-analysis/aqina-ads-inbox-performance-report-2026-05-23.md`
- 高价值案例：Messenger `2737...0322`，顾客已问运费、价格、COD，并明确回复 `二盒`，但没有形成可追踪订单。

## Success Metrics

技术侧完成后，应该能做到：

- `cart_hot` 顾客被稳定识别，不再混在普通咨询。
- 顾客回复 `二盒`、`2 boxes`、`要买`、`how to order` 后，bot 进入下单步骤，而不是继续泛诊断。
- `cart_hot` 超过 5-15 分钟没有完成资料或付款截图时，admin inbox 能提醒真人客服。
- 新订单能回写 `marketing_contact_id`、`conversation_id`、`channel`，并尽量保留 campaign/ad attribution。
- Landing page 有清楚的 BOFU 信息：配套、免运、配送时间、PayNow、味道证明、FAQ、WhatsApp/Messenger CTA。
- 每周报告能看 `spend -> conversation -> cart_hot -> order -> payment_status`。

## File Map

### Backend chatbot and inbox

- `backend/app/services/chatbot_skill_router.py`  
  负责根据用户文本、tag、历史上下文选择 chatbot skill。要加入更强的 checkout/cart intent。

- `backend/app/services/chatbot_settings.py`  
  负责默认 chatbot settings、skills、packages、FAQ、payment、follow-up rules。要加入 `cart_hot_checkout` 或同等规则。

- `backend/app/services/marketing_orchestrator.py`  
  负责收到 inbound message 后生成回复、更新 contact tag、发送 media、处理 next_tag。要确认 `cart_hot` 转换和 handoff 不被覆盖。

- `backend/app/services/marketing_contacts.py`  
  负责 contact、conversation、messages 写入。要确认 tag、lead_goal、acquisition、conversation metadata 足够支撑归因。

- `backend/app/services/follow_up.py`  
  负责 follow-up job 和 fallback。要避免 `cart_hot` 继续收到泛泛 follow-up。

- `backend/app/services/marketing_conversation_console.py`  
  负责 admin inbox conversation summary、manual reply、automation pause。要让 `cart_hot` 和 handoff reason 更明显。

- `backend/app/api/v1/marketing.py`  
  负责 admin / marketing API。可能需要新增或扩展 conversation list 字段。

- `backend/tests/test_marketing_api.py`  
  现有 marketing/chatbot 测试集中处。新行为优先加在这里。

### Order tracking

- `backend/app/api/v1/orders.py`  
  负责订单创建和更新。要确认 order payload 支持 `marketing_contact_id`、`conversation_id`、`channel`、attribution fields。

- `backend/app/models/order.py`  
  负责订单模型。需要时补字段。

- `frontend/src/lib/order-service.ts`  
  负责前端 order payload serialization。需要时把 conversation/contact attribution 带到 order。

- `frontend/src/app/paynow/[token]/page.tsx`  
  如果 PayNow token flow 与 chat checkout 有关，需要确认付款截图/订单 token 能关联回 conversation。

### Admin inbox

- `frontend/src/app/admin/inbox/page.tsx`  
  负责目前 Aqina admin inbox。要显示 `cart_hot`、handoff pending、latest blocker、matched order status。

- `frontend/src/app/admin/whatsapp/page.tsx`  
  如果实际运营仍使用这个 console，也要同步最小显示字段。

- `frontend/src/lib/backend-conversation-service.ts`  
  负责 frontend 调 backend conversation API。需要扩展类型和字段。

### Landing page BOFU

- `frontend/src/components/pages/V2LandingPage.tsx`
- `frontend/src/components/pages/V3MaternityLandingPage.tsx`
- `frontend/src/components/pages/V4CulinaryLandingPage.tsx`
- `frontend/src/app/[locale]/page.tsx`
- `frontend/messages/zh.json`
- `frontend/messages/en.json`

先确认当前线上主入口使用哪一个 landing page，再只改对应页面，不一次性改全部版本。

### Reporting

- `backend/scripts/export_marketing_inbox.py`  
  继续增强 signal extraction：`cart_hot`, `cod_objection`, `context_repetition`, `payment_ready`。

- `backend/scripts/analyze_ads_inbox_performance.py`  
  增加 `cart_hot`、matched order、payment status、blocker 维度。

- `backend/tests/test_export_marketing_inbox.py`
- `backend/tests/test_analyze_ads_inbox_performance.py`

## Phase 1: Protect Hot Leads First

### Task 1: Define `cart_hot` Intent Rules

**Files:**
- Modify: `backend/app/services/chatbot_skill_router.py`
- Modify: `backend/app/services/chatbot_settings.py`
- Test: `backend/tests/test_marketing_api.py`

- [x] **Step 1: Add failing tests for hot checkout intent**

Add tests that prove the router treats these messages as checkout intent:

```python
hot_messages = [
    "二盒",
    "我要两盒",
    "2 boxes",
    "how to order",
    "是货到付款吗？",
    "PayNow 怎么付？",
    "下单后多久收到？",
    "可以送货吗？",
]
```

Expected behavior:
- selected skills include checkout / price / delivery / payment handling.
- next tag should become or remain `cart_hot`.
- router should not fall back to only `usage_consultation`.

- [x] **Step 2: Implement minimal routing change**

Add keyword groups:

```python
QUANTITY_BUYING_KEYWORDS = ("二盒", "两盒", "2盒", "2 box", "2 boxes", "我要", "要买", "order", "下单")
PAYMENT_KEYWORDS = ("paynow", "付款", "货到付款", "cod", "cash on delivery", "截图")
DELIVERY_KEYWORDS = ("运费", "配送", "送货", "delivery", "多久收到", "几天到")
```

Routing rule:
- if any quantity + buying keyword, current tag becomes `cart_hot`.
- if payment or delivery appears after price/package question, route to checkout close.
- if current tag is already `cart_hot`, do not downgrade.

- [x] **Step 3: Run targeted tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "skill_router or cart_hot" -q
```

Expected:
- existing router tests pass.
- new hot checkout intent tests pass.

### Task 2: Add `cart_hot_checkout` Chatbot Skill

**Files:**
- Modify: `backend/app/services/chatbot_settings.py`
- Test: `backend/tests/test_marketing_api.py`

- [x] **Step 1: Add failing test for saved settings**

Test that default settings include a checkout skill with:
- package confirmation
- recipient info request
- PayNow instruction
- receipt screenshot instruction
- human confirmation instruction

Expected content in serialized settings:

```text
确认配套
收件人姓名
联系电话
新加坡收货地址
PayNow
付款截图
真人客服
```

- [x] **Step 2: Add default skill content**

Add a skill such as `cart_hot_checkout`:

```json
{
  "goal": "Close high-intent buyers who have asked about price, delivery, payment, COD, or selected a quantity.",
  "sequence": [
    "Confirm selected package and total amount",
    "Ask for recipient name, phone, and Singapore delivery address",
    "Explain PayNow payment clearly",
    "Ask customer to send payment screenshot",
    "Tell customer a human team member will confirm the order"
  ],
  "do_not": [
    "Do not return to broad diagnosis after customer chooses package",
    "Do not ask repeated lifestyle questions",
    "Do not claim COD is available unless business settings allow it"
  ]
}
```

- [x] **Step 3: Add exact Chinese sales-close copy**

Use this as baseline:

```text
好的，我先帮您确认：您要的是 2 盒活力升级装，合计 SGD 75，并且符合免运费。

麻烦您发我：
1. 收件人姓名
2. 联系电话
3. 新加坡收货地址

我们目前是 PayNow 付款。您付款后把截图发回来，我会让客服帮您确认订单并安排配送。
```

COD objection baseline:

```text
目前我们没有货到付款哦。我们是用 PayNow 先付款，付款截图发回来后，客服会帮您确认订单并安排新加坡配送。
```

- [x] **Step 4: Run settings tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "chatbot_settings or default_settings or cart_hot_checkout" -q
```

Expected: default settings include new checkout skill and no retired package references.

### Task 3: Prevent `cart_hot` From Receiving Generic Follow-Up

**Files:**
- Modify: `backend/app/services/follow_up.py`
- Modify: `backend/app/services/chatbot_settings.py`
- Test: `backend/tests/test_marketing_api.py`

- [x] **Step 1: Add failing test for `cart_hot` follow-up**

Given:
- contact tag is `cart_hot`
- no payment screenshot
- last message asks about payment or package

Expected:
- follow-up asks for order details / PayNow screenshot.
- follow-up does not ask broad diagnosis questions.
- follow-up does not only say `reply YES to keep chat open`.

- [x] **Step 2: Add cart-specific follow-up fallback**

Use baseline:

```text
您好，我帮您保留刚才的配套。您可以直接把收件人姓名、联系电话和新加坡地址发来；如果已经 PayNow 付款，也可以把截图发回来，我会让客服帮您确认订单。
```

- [x] **Step 3: Keep Meta window protection but add buying reason**

If 23-hour window needs YES:

```text
如果您要我下个月/稍后继续提醒您，可以回复 YES 保持聊天开启。若您现在要完成订单，也可以直接发收件资料或付款截图。
```

- [x] **Step 4: Run follow-up tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "follow_up or cart_hot" -q
```

Expected: `cart_hot` receives checkout follow-up, not generic nurture.

## Phase 2: Human Handoff and Admin Visibility

### Task 4: Make `cart_hot` Visible in Admin Inbox

**Files:**
- Modify: `backend/app/services/marketing_conversation_console.py`
- Modify: `backend/app/api/v1/marketing.py`
- Modify: `frontend/src/lib/backend-conversation-service.ts`
- Modify: `frontend/src/app/admin/inbox/page.tsx`
- Test: `backend/tests/test_marketing_api.py`

- [x] **Step 1: Add backend response fields**

Conversation summary should include:

```json
{
  "current_tag": "cart_hot",
  "latest_blockers": ["delivery", "payment", "price_or_package"],
  "handoff_recommended": true,
  "handoff_reason": "Customer selected 2 boxes or asked payment/COD",
  "matched_order_count": 0,
  "latest_order_status": null,
  "latest_payment_status": null
}
```

- [x] **Step 2: Add backend test**

Create a fake conversation with:
- `current_tag = cart_hot`
- latest message `二盒`
- no matched order

Expected API summary:
- `handoff_recommended = true`
- `handoff_reason` mentions selected quantity or payment.

- [x] **Step 3: Update frontend types**

Extend `frontend/src/lib/backend-conversation-service.ts` with fields:

```ts
current_tag?: string | null;
latest_blockers?: string[];
handoff_recommended?: boolean;
handoff_reason?: string | null;
matched_order_count?: number;
latest_order_status?: string | null;
latest_payment_status?: string | null;
```

- [x] **Step 4: Update admin inbox UI**

For `cart_hot` conversations:
- show a clear `cart_hot` badge.
- show `Needs human follow-up` if no matched order.
- show latest blocker tags.
- keep the UI operational and dense, not decorative.

- [x] **Step 5: Verify**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "conversation_console or marketing" -q
cd frontend && npm run lint
```

Expected:
- backend tests pass.
- frontend lint passes.

### Task 5: Add Handoff Trigger Rule

**Files:**
- Modify: `backend/app/services/marketing_orchestrator.py`
- Modify: `backend/app/services/marketing_contacts.py`
- Test: `backend/tests/test_marketing_api.py`

- [x] **Step 1: Add failing test for automatic handoff recommendation**

Given inbound text:

```text
二盒
```

And previous messages include:
- delivery question
- price question
- COD/payment question

Expected contact update:

```json
{
  "current_tag": "cart_hot",
  "handoff_recommended": true,
  "handoff_reason": "high_intent_checkout"
}
```

- [x] **Step 2: Implement contact metadata update**

Do not pause automation for every `cart_hot` immediately. Instead:
- mark `handoff_recommended = true`.
- set `handoff_reason`.
- only pause automation if current rule says payment/safety/manual review is required.

- [x] **Step 3: Run targeted test**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "handoff or cart_hot" -q
```

Expected: high-intent checkout cases are visible for human follow-up.

## Phase 3: Order Attribution and Tracking

### Task 6: Ensure Chat Orders Carry Conversation Attribution

**Files:**
- Modify: `backend/app/models/order.py`
- Modify: `backend/app/api/v1/orders.py`
- Modify: `frontend/src/lib/order-service.ts`
- Test: `backend/tests/test_marketing_api.py`

- [x] **Step 1: Add failing order creation test**

Create order payload with:

```json
{
  "marketing_contact_id": "contact_dd588779c551c8bf1a3c",
  "conversation_id": "conversation_af0fe19285b39b372938",
  "channel": "messenger",
  "customer": {
    "name": "Test Buyer",
    "whatsapp": "+6500000000"
  }
}
```

Expected stored order includes:
- `marketing_contact_id`
- `conversation_id`
- `channel`
- `created_from = marketing_inbox` or equivalent source field.

- [x] **Step 2: Preserve existing checkout behavior**

Do not break normal website checkout. If no marketing fields are provided:
- order still saves.
- fields remain absent or null.

- [x] **Step 3: Update frontend order serialization**

When checkout starts from inbox, include:

```ts
marketing_contact_id
conversation_id
channel
utm_source
utm_campaign
meta_campaign_id
meta_adset_id
meta_ad_id
```

Only send fields when available.

- [x] **Step 4: Verify**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "order or receipt or marketing_contact" -q
cd frontend && npm run lint
```

Expected: orders created from chat are linkable back to conversation.

### Task 7: Improve Matched Order Logic in Admin and Reports

**Files:**
- Modify: `backend/app/services/marketing_conversation_console.py`
- Modify: `backend/scripts/export_marketing_inbox.py`
- Modify: `backend/scripts/analyze_ads_inbox_performance.py`
- Test: `backend/tests/test_export_marketing_inbox.py`
- Test: `backend/tests/test_analyze_ads_inbox_performance.py`

- [x] **Step 1: Add tests for matching by conversation and contact**

Match orders by:
- `marketing_contact_id`
- `conversation_id`
- WhatsApp phone when available

Expected:
- one conversation can show matched pending order.
- pending vs paid status is visible.

- [x] **Step 2: Extend export JSON**

For each conversation include:

```json
{
  "has_order": true,
  "orders": [
    {
      "order_id": "order_...",
      "order_status": "pending",
      "payment_status": "pending",
      "total_amount": 75.0
    }
  ],
  "cart_hot_without_order": false
}
```

- [x] **Step 3: Extend report metrics**

Report should include:
- total conversations
- `cart_hot_count`
- `cart_hot_without_order_count`
- matched order count
- pending payment count
- paid order count

- [x] **Step 4: Verify scripts**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_export_marketing_inbox.py backend/tests/test_analyze_ads_inbox_performance.py -q
backend/.venv/bin/python backend/scripts/export_marketing_inbox.py --project aqina-chicken-essence --gcloud-account ohweiyang333@gmail.com --channel all --limit 200
python3 backend/scripts/analyze_ads_inbox_performance.py
```

Expected: generated reports show cart-hot leakage clearly.

## Phase 4: Landing Page BOFU Patch

### Task 8: Identify Active Landing Page

**Files:**
- Inspect: `deployment-targets.json`
- Inspect: `frontend/src/app/[locale]/page.tsx`
- Inspect: `frontend/src/components/pages/V2LandingPage.tsx`
- Inspect: `frontend/src/components/pages/V3MaternityLandingPage.tsx`
- Inspect: `frontend/src/components/pages/V4CulinaryLandingPage.tsx`

- [x] **Step 1: Confirm current public route**

Check which page renders `https://aqina-sg.web.app/` and campaign landing links.

- [x] **Step 2: Choose one page to patch first**

Patch only the active highest-traffic page first.

Expected decision:
- If homepage uses V2, patch `V2LandingPage.tsx`.
- If maternity campaign uses V3, patch `V3MaternityLandingPage.tsx`.
- If culinary page is not used by current ads, do not patch it yet.

### Task 9: Add BOFU Conversion Blocks

**Files:**
- Modify: active landing component from Task 8
- Modify: `frontend/messages/zh.json`
- Modify: `frontend/messages/en.json`

- [x] **Step 1: Add package comparison block**

Must show:
- 1 box: 7 packs, SGD 39.90, good for first trial.
- 2 boxes: SGD 75, free delivery, recommended for daily start.
- 4 boxes: monthly routine / family usage, if confirmed by existing product facts.

Use only verified package details already present in chatbot settings or current site.

- [x] **Step 2: Add delivery and payment FAQ**

Must answer:
- 2 boxes or above free delivery.
- 1 box delivery fee SGD 8.
- Singapore stock normally 1-3 working days.
- Payment via PayNow.
- Customer sends payment screenshot after payment.
- COD availability depends on Aqina decision; if not confirmed, do not claim COD.

- [x] **Step 3: Add taste-risk proof section**

Goal: reduce first-purchase fear.

Use:
- product photo
- preparation / open-pack proof if available
- concise copy: clear, chicken-soup-like, not oily

Avoid unsupported medical or guaranteed result claims.

- [x] **Step 4: Add CTA that matches inbox flow**

CTA labels:
- `Ask about 2-box free delivery`
- `WhatsApp us to order`
- `Message us on Messenger`

CTA should route to the same channel currently used by ads where possible.

- [x] **Step 5: Verify frontend**

Run:

```bash
cd frontend && npm run lint && npm run build
```

Then use browser QA on desktop and mobile:
- hero still visible.
- package block not cramped.
- CTA visible before checkout friction.
- no text overlaps.

## Phase 5: Reporting and Weekly Operating Loop

### Task 10: Create Weekly Codex Report Command

**Files:**
- Modify: `backend/scripts/export_marketing_inbox.py`
- Modify: `backend/scripts/analyze_ads_inbox_performance.py`
- Create: `backend/scripts/run_conversion_report.py`
- Test: `backend/tests/test_analyze_ads_inbox_performance.py`

- [x] **Step 1: Add combined report runner**

`run_conversion_report.py` should:
- accept latest Ads Manager CSV paths.
- run inbox export.
- run report generation.
- write one Markdown report.
- print output file path and key stats.

Command shape:

```bash
backend/.venv/bin/python backend/scripts/run_conversion_report.py \
  --project aqina-chicken-essence \
  --gcloud-account ohweiyang333@gmail.com \
  --ads-dir backend/exports/ads-analysis
```

- [x] **Step 2: Add report sections**

Weekly report must include:
- spend summary
- campaign/ad set/ad winner
- conversation count
- cart_hot count
- cart_hot without order
- matched orders
- blocker signals
- recommended next action

- [x] **Step 3: Add tests for report summary**

Use fixture rows:
- 10 messaging conversations
- 3 cart_hot
- 1 paid order
- 1 pending order
- 1 cart_hot without order

Expected report includes all counts.

- [x] **Step 4: Verify**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_analyze_ads_inbox_performance.py -q
```

Expected: report metrics are deterministic.

## Phase 6: Regression and Release Safety

### Task 11: Full Regression Pass

**Files:**
- No code changes. Verification only.

- [x] **Step 1: Backend tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py backend/tests/test_export_marketing_inbox.py backend/tests/test_analyze_ads_inbox_performance.py
```

Expected: all pass.

- [x] **Step 2: Frontend checks**

Run:

```bash
cd frontend && npm run lint && npm run build
```

Expected: lint and build pass.

- [ ] **Step 3: Browser QA**

Progress: active V2 landing page desktop/mobile verified with local Chrome screenshots. Admin inbox browser view stayed on loading in local headless session without a usable logged-in/backend session; backend response tests and frontend build cover the new fields.

Check:
- active landing page desktop/mobile.
- admin inbox list shows `cart_hot`.
- selected conversation panel shows handoff reason and order status.
- no visual overlaps.

- [x] **Step 4: Generate fresh report**

Run latest export and report generation.

Expected:
- report still Chinese.
- `2737...0322` style cases are counted as `cart_hot`.
- matched orders are no longer undercounted when order has conversation/contact fields.

### Task 12: Commit and Deploy Through GitHub Actions

**Files:**
- All changed implementation and test files.

- [x] **Step 1: Review diff**

Run:

```bash
git diff --stat
git diff
```

Expected:
- changes are scoped to chatbot, tracking, admin inbox, landing BOFU, reports, and tests.
- no unrelated customer project files changed.

- [x] **Step 2: Commit on `main`**

Project policy says work directly on `main`.

```bash
git add backend/app backend/tests backend/scripts frontend/src frontend/messages docs/superpowers/plans
git commit -m "feat: improve Aqina chat conversion tracking"
```

- [ ] **Step 3: Push to `main`**

```bash
git push origin main
```

- [ ] **Step 4: Monitor GitHub Actions**

Do not run local production deploy.

Expected:
- backend/frontend deploy workflows pass.
- live site and admin inbox are verified after deployment.

## Recommended Execution Order

1. Task 1: `cart_hot` intent rules.
2. Task 2: `cart_hot_checkout` chatbot skill.
3. Task 3: cart-specific follow-up.
4. Task 4: admin inbox visibility.
5. Task 5: handoff trigger.
6. Task 6: order attribution.
7. Task 7: matched order/report logic.
8. Task 8-9: landing page BOFU patch.
9. Task 10: weekly report runner.
10. Task 11-12: regression, commit, GitHub Actions deploy.

## Decisions Needed From Aqina Before Execution

Codex can implement placeholders and safe defaults, but these should be confirmed before launch:

1. COD: available or not available.
2. Delivery promise: exact delivery fee and delivery time.
3. PayNow account name and payment instruction.
4. Main packages: 1 box, 2 boxes, 4 boxes, 6 boxes exact pricing.
5. Approved proof assets: Halal, nutrition, ingredient, reviews, taste video.
6. Pregnancy / breastfeeding / elderly / medical condition answer boundaries.

If Aqina does not decide these in time, implementation should use current verified chatbot/site values and mark uncertain areas as “ask human customer service” instead of inventing promises.

## Self-Review

- Spec coverage: Plan covers chatbot, landing page, tracking, admin inbox, reporting, and verification. It intentionally excludes ad budget changes and Aqina business decisions.
- Placeholder scan: No `TBD` or “implement later” placeholders. Open business decisions are explicitly listed as Aqina decision gates.
- Type consistency: `cart_hot`, `marketing_contact_id`, `conversation_id`, `payment_status`, and `order_status` are used consistently across tasks.
