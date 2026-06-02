# Aqina Offer Reset Main Entry Design

## Goal

Replace Aqina's official public landing entry points with a new offer-reset sales page that matches the June 2026 promotion and buying flow.

The new page must make `/`, `/en`, `/zh`, and advertising-default landing traffic enter the current official offer page. It must be WhatsApp-first, keep PayNow receipt checkout as a secondary direct-order path, and align the order API with the new `1盒` / `2盒` offer.

## Approved Source Of Truth

- Customer-facing product term: `Aqina 纯鸡精`.
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
- Do not use `SGD75`, free-delivery-led framing, `4盒`, `6盒`, monthly pack, family pack, subscription, or shipping discount as the offer identity.
- Do not send real WhatsApp or Messenger messages, write production customer data, or deploy during the local implementation and verification phase.

## Entry And Version Boundary

The official traffic path is:

- `/`
- `/en`
- `/zh`
- advertising-default landing URLs that map to the root or locale home pages

These entry points must render the new offer-reset page directly. They should not simply redirect to `/v2/en` or reuse an old experiment identity.

Legacy experiment routes stay available only as internal comparison surfaces:

- `/v2`
- `/v2/en`
- `/v2/zh`
- `/v3`
- `/v3/en`
- `/v3/zh`
- `/v4`
- `/v4/en`
- `/v4/zh`

The new official page must not expose those old routes through navigation, primary CTAs, floating CTAs, canonical metadata, or advertising defaults.

## Page Design

The page should behave like a focused sales page, not a general brand introduction. The buyer should understand the product, the current two-option offer, the gift mechanism, and the preferred WhatsApp confirmation path within the first screen.

### Hero And Primary Buying Area

The first viewport must show:

- Real Aqina product visual.
- `1盒 SGD47.90`.
- `2盒 SGD79.80 = SGD39.90/盒`.
- `2盒送 French Poulet Cut Part 五选一`.
- Primary CTA: WhatsApp confirmation for `1盒` / `2盒` and gift choice.
- Secondary CTA: direct PayNow receipt checkout for buyers who are already ready to order.

The hero should avoid old free-delivery language and old package choices.

### Product Proof And Trust

Trust should come from checkable product and buying-process proof:

- Real Aqina box and sachet visuals.
- Real French Poulet gift images.
- PayNow / WhatsApp ordering path.
- Aqina farm.
- MD2 黄梨酵素鸡 / Pineapple Chicken.
- 7-day slow extraction / double-boiled process.
- Halal.
- No additives, only where the current product material supports that wording.

The page must not invent ratings, sold counts, buyer photos, verified-buyer labels, or review numbers.

### Offer Cards

Only two package cards are allowed:

- `1盒 SGD47.90`: for first-time buyers who want to try the product.
- `2盒 SGD79.80`: the recommended choice, equal to `SGD39.90/盒`, saves `SGD16.00`, and includes one French Poulet Cut Part gift choice.

No `3盒`, `4盒`, `6盒`, monthly packs, family packs, subscriptions, or free-delivery offer cards are part of this page.

### Gift Selector

The gift selector must show all five French Poulet Cut Part choices and make it clear that WhatsApp support confirms current stock and the selected gift.

The five choices must keep their exact customer-facing names and weights:

- French Poulet 3 Joint Wing 500g
- French Poulet Minced 400g
- French Poulet Boneless Breast 350g
- French Poulet Whole Leg 400g
- French Poulet Half Chicken Cut 4 Pieces 500g

### Q&A And Review-Ready Area

If real authorized customer reviews are not available, the page must use `购买前 Q&A` and `真实评价待导入` slots instead of presenting fake testimonials.

The Q&A should answer:

- Why is Aqina more expensive than ordinary bottled chicken essence?
- Is pineapple chicken pineapple-flavored?
- Should a first-time buyer choose 1 box or 2 boxes?
- What gift comes with 2 boxes?
- What should customers with special health conditions do?

Health-related answers must remain conservative: Aqina is a food / nourishment product and does not replace medical advice.

### Final CTA

The final CTA area repeats the same hierarchy:

- Primary: WhatsApp confirmation.
- Secondary: PayNow receipt checkout.

The page should never make Messenger the primary CTA for this reset. Existing Messenger backend support may remain untouched, but the official public page is WhatsApp-first.

## WhatsApp-First Flow

All primary CTAs generate WhatsApp draft links. The prefilled text should mention the current offer and gift confirmation, for example:

`Hi Aqina SG，我想确认 Aqina 纯鸡精 1盒 / 2盒配套。请帮我确认 2盒 SGD79.80 的 French Poulet Cut Part 赠品可以选哪一款。`

The frontend only opens a draft link. It must not send a real WhatsApp message automatically, call an outbound messaging API, create a customer record, or write production data.

## PayNow Receipt Checkout Flow

The PayNow checkout remains as a secondary path for buyers who are already ready to order.

It must support only:

- `pack1` -> `SGD47.90`
- `pack2` -> `SGD79.80`

The frontend product list, checkout modal, order payload, and backend landing receipt endpoint must agree on these two products and prices.

For the offer-reset page, PayNow checkout should not add a separate delivery fee to turn `1盒 SGD47.90` into `SGD55.90`. Shipping should not become the visible offer mechanic in this reset. Delivery details can be confirmed in WhatsApp or handled in a later production smoke decision.

## Backend API Design

The landing receipt endpoint must be aligned with the page offer:

- `POST /api/v1/orders/with-receipt`
- Accepts `pack1` and `pack2`.
- Rejects `pack4`, `pack6`, and unknown package IDs.
- Stores order and payment amounts using the new source of truth.
- Keeps receipt validation for allowed image types and size.
- Keeps payment status as manual verification / submitted state, not auto-paid.

The broader admin, Messenger, WhatsApp inbox, and historical order surfaces do not need to be refactored for this page reset unless tests show they break the new page flow.

## Analytics And Metadata

The official entry page should expose current metadata, not v2 experiment metadata:

- Title and description should mention `Aqina 纯鸡精`, `1盒 SGD47.90`, `2盒 SGD79.80`, and French Poulet gift.
- Canonical and language alternates should point to `/en` and `/zh`.
- Funnel event metadata should identify the page as the current offer-reset official landing flow.

## Local Verification Design

Verification must happen locally first.

### Page Entry Checks

- `/` enters the new offer-reset page.
- `/en` enters the new offer-reset page.
- `/zh` enters the new offer-reset page.
- The new page does not expose `/v2`, `/v3`, or `/v4` through official navigation or CTA paths.

### Retired-Copy Checks

The official page should not contain customer-facing retired offer copy:

- `SGD75`
- `SGD 75`
- `2盒免运`
- `free delivery`
- `free shipping`
- `4盒`
- `6盒`
- `monthly pack`
- `family pack`
- Messenger primary CTA copy

Legacy experiment routes may still contain old copy while they remain internal comparison pages.

### CTA Checks

- Primary CTAs resolve to WhatsApp draft links.
- WhatsApp draft prefill mentions `1盒`, `2盒`, `SGD79.80`, and French Poulet gift confirmation.
- No verification step sends a real WhatsApp or Messenger message.

### Checkout Checks

- PayNow checkout can open for `pack1` and shows `SGD47.90`.
- PayNow checkout can open for `pack2` and shows `SGD79.80`.
- PayNow checkout does not expose `pack4` or `pack6`.
- Uploading a test receipt exercises the local or fake backend path only.

### Backend Test Checks

Focused backend tests must prove:

- `pack1` receipt order total is `47.90`.
- `pack2` receipt order total is `79.80`.
- `pack4` and `pack6` are rejected by the landing receipt endpoint.
- Receipt validation still rejects empty, oversized, or unsupported files.

## Exclusions

This design does not include:

- Production deployment.
- GitHub Actions monitoring.
- Live WhatsApp or Messenger send tests.
- Production Firestore, Firebase Storage, customer, or payment writes.
- Real ad launch.
- Real customer review import.
- Removing old `/v2`, `/v3`, or `/v4` experiment routes.

Production smoke is a separate phase after local implementation and verification pass.

## Approved Direction Summary

The approved direction is to build a new official offer-reset entry page using the current June 2026 promotion, keep legacy experiment routes for internal comparison only, prioritize WhatsApp confirmation, preserve PayNow receipt checkout as a secondary order path, and verify the full local page/API chain before any production action.
