# Aqina Offer Reset Chatbot Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update Aqina's runtime chatbot defaults and migration path so production WhatsApp and Messenger replies follow the June 2026 1-box / 2-box offer reset.

**Architecture:** `backend/app/services/chatbot_settings.py` remains the canonical runtime settings source. Incrementing `CONVERSION_OPTIMIZATION_VERSION` forces existing Firestore settings to adopt the new system prompt, skills, package defaults, and follow-up rules while preserving payment and escalation config. Existing backend tests cover the API and migration behavior.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, Firebase Firestore settings document, unittest/httpx test client.

---

## File Structure

- Modify: `backend/app/services/chatbot_settings.py`
  - Version bump, prompt copy, default packages, skills, knowledge, media defaults, migration behavior.
- Modify: `backend/app/services/marketing_orchestrator.py`
  - Marketing-chat checkout shipping calculation so PayNow totals match the new 1-box / 2-box source of truth.
- Modify: `backend/tests/test_marketing_api.py`
  - Update chatbot settings migration expectations and add retired-copy regression assertions.
- Create: `docs/superpowers/specs/2026-06-02-aqina-offer-reset-chatbot-runtime-design.md`
  - Approved design record.
- Create: `docs/superpowers/plans/2026-06-02-aqina-offer-reset-chatbot-runtime.md`
  - This implementation plan.

### Task 1: Lock Regression Expectations

- [ ] **Step 1: Update chatbot settings migration tests**

In `backend/tests/test_marketing_api.py`, update expected conversion version from `4` to `5`, default package assertions from `pack1/pack2/pack4/pack6` to `pack1/pack2`, and add serialized payload checks for the new offer facts and retired copy.

- [ ] **Step 2: Run the focused tests and confirm failures before code changes**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "chatbot_settings" -q
```

Expected before implementation: failures around version, package list, and old/new offer copy.

### Task 2: Implement Runtime Defaults

- [ ] **Step 1: Update `CONVERSION_OPTIMIZATION_VERSION`**

Set:

```python
CONVERSION_OPTIMIZATION_VERSION = 5
```

- [ ] **Step 2: Replace system prompt**

Replace `AQINA_SYSTEM_PROMPT` with rules that only recommend `pack1` and `pack2`, explain Aqina's pure chicken essence category, and hand off health/order/payment/delivery/human cases.

- [ ] **Step 3: Update default packages and skills**

Keep only `pack1` and `pack2` in default `packages`. Rewrite skill defaults so `recommended_package_code`, `upgrade_package_code`, and customer-facing questions use only `pack1` or `pack2`.

- [ ] **Step 4: Update knowledge and follow-up rules**

Change price positioning, logistics wording, and follow-up copy so free shipping is not a main selling point and old 4-box / 6-box package language is absent.

### Task 3: Verify

- [ ] **Step 0: Align chatbot checkout totals**

In `backend/app/services/marketing_orchestrator.py`, keep chatbot checkout totals aligned to the new promotion source of truth by returning `0.0` from `_shipping_fee_for()` for marketing-chat checkout sessions. This prevents `1盒 SGD47.90` from becoming `SGD55.90` during PayNow generation.

- [ ] **Step 1: Run focused tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "chatbot_settings or skill_router" -q
```

Expected: pass.

- [ ] **Step 2: Run broader backend marketing tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -q
```

Expected: pass, or only unrelated pre-existing failures clearly documented.

### Task 4: Release

- [ ] **Step 1: Review diff**

Run:

```bash
git diff -- backend/app/services/chatbot_settings.py backend/app/services/marketing_orchestrator.py backend/tests/test_marketing_api.py docs/superpowers/specs/2026-06-02-aqina-offer-reset-chatbot-runtime-design.md docs/superpowers/plans/2026-06-02-aqina-offer-reset-chatbot-runtime.md
```

- [ ] **Step 2: Commit**

Run:

```bash
git add backend/app/services/chatbot_settings.py backend/app/services/marketing_orchestrator.py backend/tests/test_marketing_api.py docs/superpowers/specs/2026-06-02-aqina-offer-reset-chatbot-runtime-design.md docs/superpowers/plans/2026-06-02-aqina-offer-reset-chatbot-runtime.md
git commit -m "feat(chatbot): migrate Aqina offer reset runtime rules"
```

- [ ] **Step 3: Push and monitor GitHub Actions**

Run:

```bash
git push origin main
gh run list --branch main --limit 5
```

Monitor the deploy workflow triggered by the pushed commit until success or a concrete deploy blocker is identified.
