# Aqina Offer Reset Chatbot Runtime Design

## Goal

Move Aqina's live WhatsApp and Messenger chatbot runtime rules to the June 2026 offer reset: only 1-box and 2-box recommendations, stronger category education, and safer human handoff for health, order, payment, delivery, complaint, and person-in-charge requests.

## Current Context

The repo already stores canonical chatbot defaults in `backend/app/services/chatbot_settings.py`. Runtime Firestore settings are normalized by `ChatbotSettingsService.get_settings()`, and older documents are force-upgraded when `conversion_optimization_version` is lower than the code default.

The current code still contains retired runtime copy: `SGD 75`, `4盒`, `6盒`, and free-shipping-led package framing. That conflicts with the approved Aqina offer reset.

## Source Of Truth

- Product term: `Aqina 纯鸡精`.
- 1 box: `SGD47.90`.
- 2 boxes: `SGD79.80`.
- 2-box effective price: `SGD39.90/盒`.
- 2 boxes save `SGD16.00` versus two single boxes.
- 2 boxes include 1 French Poulet Cut Part gift, market value `SGD8`.
- Gift choices:
  - French Poulet 3 Joint Wing 500g
  - French Poulet Minced 400g
  - French Poulet Boneless Breast 350g
  - French Poulet Whole Leg 400g
  - French Poulet Half Chicken Cut 4 Pieces 500g

## Runtime Design

Update `backend/app/services/chatbot_settings.py` as the backend source of truth:

- Increase `CONVERSION_OPTIMIZATION_VERSION` from `4` to `5`.
- Replace `AQINA_SYSTEM_PROMPT` with the offer-reset sales advisor rules.
- Keep `pack1` and `pack2` only in default `packages`.
- Remove `pack4` and `pack6` from default runtime packages and default media package maps.
- Update chatbot skills so every recommendation falls back to `pack1` or `pack2`.
- Update price objection handling to explain source, ingredient, process, and pure chicken essence category before package choice.
- Preserve PayNow configuration, but keep payment/order/delivery disputes and human requests as handoff-first situations.
- Keep router keyword recognition for customer text, including old package terms, but do not let runtime recommendations produce old packages.
- Update marketing-chat checkout amount calculation so chatbot PayNow totals match the new promotion source of truth. In this chatbot flow, `1盒` totals `SGD47.90` and `2盒` totals `SGD79.80`; shipping is not added as a separate sales lever.

## Testing Design

Update `backend/tests/test_marketing_api.py` around existing chatbot settings tests:

- Expected `conversion_optimization_version` becomes `5`.
- Default settings contain `pack1` and `pack2`, but not `pack4` or `pack6`.
- Serialized chatbot settings contain the new prices, gift options, category education, and handoff rules.
- Serialized chatbot settings do not contain customer-facing retired package phrases such as `SGD 75`, `SGD 149`, `SGD 219`, `4盒`, `6盒`, or `free shipping`.
- Saved Firestore documents with old conversion versions are migrated to the new defaults without overwriting payment QR or handoff phone configuration.

## Deployment Design

Use the project release path:

1. Implement and test locally.
2. Commit on `main`.
3. Push `main`.
4. Monitor GitHub Actions for backend deployment success.

No local production deploy commands are used.

## Exclusions

This task does not change landing pages, ad images, short videos, order API package catalogs, or real customer data. If downstream order APIs still allow old product IDs, that is outside this chatbot runtime migration unless tests show a direct chatbot regression.
