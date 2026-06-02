# Aqina Offer Reset Main Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the official Aqina offer-reset landing entry for `/`, `/en`, `/zh`, with WhatsApp-first CTAs, PayNow receipt checkout as the secondary path, and local API verification for the new `1盒` / `2盒` pricing.

**Architecture:** Keep old `/v2`, `/v3`, and `/v4` routes as internal experiment pages. Add a new official offer-reset content module and page component, wire only the root/locale home entry to that component, and keep the landing receipt API aligned to `pack1=SGD47.90` and `pack2=SGD79.80`. Do not deploy, send live messages, or write production customer data during this plan.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS, next-intl, FastAPI, Python 3.11, pytest, Firebase test fakes.

---

## Scope Check

This plan covers one coherent subsystem: the official public landing entry and its local PayNow receipt order chain. Chatbot runtime migration already exists in a separate spec/plan and should not be reopened here unless a test proves a direct regression.

## File Structure

- Create: `frontend/src/lib/offer-reset-content.ts`
  - Canonical bilingual offer-reset content, product cards, proof items, gift choices, Q&A, and WhatsApp prefill builders.
- Create: `frontend/src/components/pages/OfferResetLandingPage.tsx`
  - Official `/en` and `/zh` page experience, using static offer-reset content and `CheckoutModal`.
- Modify: `frontend/src/app/[locale]/page.tsx`
  - Replace `GreenLandingPage` with `OfferResetLandingPage`.
- Modify: `frontend/src/app/[locale]/layout.tsx`
  - Update metadata for official offer-reset SEO and alternates.
- Modify: `frontend/src/lib/marketing-analytics.ts`
  - Identify `/en` and `/zh` as the current official offer-reset flow instead of legacy `home`.
- Modify: `frontend/src/components/CheckoutModal.tsx`
  - Restrict landing checkout package resolution to `pack1` and `pack2`, keep total equal to the offer amount, and fix any syntax drift before build.
- Modify: `backend/app/api/v1/orders.py`
  - Use offer-reset totals for `/api/v1/orders/with-receipt` without adding a separate delivery fee.
- Modify: `backend/tests/test_marketing_api.py`
  - Add/adjust landing receipt tests for `pack1`, `pack2`, retired packages, and receipt validation.
- Add/stage assets if not already tracked:
  - `frontend/public/french-poulet-gift/minced.png`
  - `frontend/public/french-poulet-gift/boneless-breast.png`
  - `frontend/public/french-poulet-gift/chicken-wing.jpg`
  - `frontend/public/french-poulet-gift/whole-leg.jpg`
  - `frontend/public/french-poulet-gift/half-chicken-4-cut.jpg`

## Task 1: Lock Backend Receipt API Behavior

**Files:**
- Modify: `backend/tests/test_marketing_api.py`
- Modify: `backend/app/api/v1/orders.py`

- [ ] **Step 1: Rename the one-box receipt test and change expectations**

In `backend/tests/test_marketing_api.py`, find `test_landing_order_with_receipt_charges_shipping_for_one_box` and replace the method name and assertions with:

```python
    def test_landing_order_with_receipt_uses_offer_reset_total_for_one_box(self) -> None:
        client = self._build_client()

        with patch("app.api.v1.orders.upload_public_file_to_firebase", return_value="https://storage.example.com/receipt.png"):
            response = client.post(
                "/api/v1/orders/with-receipt",
                data={
                    "customer_name": "Janice Lee",
                    "customer_phone": "6598765432",
                    "customer_address": "20 Tanjong Pagar Road, Singapore 088443",
                    "product_id": "pack1",
                },
                files={"payment_receipt": ("receipt.png", b"fake-image", "image/png")},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["subtotal_amount"], 47.9)
        self.assertEqual(payload["shipping_fee"], 0.0)
        self.assertEqual(payload["total_amount"], 47.9)
        self.assertEqual(payload["box_count"], 1)
        self.assertEqual(payload["payment_status"], "payment_submitted")
        self.assertEqual(payload["payment_receipt_url"], "https://storage.example.com/receipt.png")
```

- [ ] **Step 2: Update the Meta CAPI receipt test value**

In `test_landing_order_with_receipt_sends_meta_capi_add_to_cart_after_consent`, change the expected custom data value to:

```python
        self.assertEqual(event["custom_data"]["value"], 47.9)
```

Also update the test fixture to represent the official entry:

```python
                    "event_source_url": "https://aqina-sg.web.app/zh?fbclid=test-click",
                    "page_path": "/zh",
                    "landing_version": "offer_reset",
```

Then update the related assertions:

```python
        self.assertEqual(event["event_source_url"], "https://aqina-sg.web.app/zh?fbclid=test-click")
        self.assertEqual(event["custom_data"]["landing_version"], "offer_reset")
        self.assertEqual(event["custom_data"]["page_path"], "/zh")
```

- [ ] **Step 3: Add retired package rejection coverage**

Add this test after the two-box landing receipt test:

```python
    def test_landing_order_with_receipt_rejects_retired_offer_packages(self) -> None:
        client = self._build_client()

        for product_id in ["pack4", "pack6", "unknown-pack"]:
            with self.subTest(product_id=product_id):
                response = client.post(
                    "/api/v1/orders/with-receipt",
                    data={
                        "customer_name": "Kelvin Tan",
                        "customer_phone": "6591234567",
                        "customer_address": "1 Orchard Road, Singapore 238823",
                        "product_id": product_id,
                    },
                    files={"payment_receipt": ("receipt.webp", b"fake-image", "image/webp")},
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], "Unknown package")
```

- [ ] **Step 4: Run the focused backend tests and confirm the one-box total fails before implementation**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "landing_order_with_receipt" -q
```

Expected before implementation: at least the one-box total test fails because the current endpoint still returns `shipping_fee=8.0` and `total_amount=55.9`.

- [ ] **Step 5: Add an offer-reset shipping helper**

In `backend/app/api/v1/orders.py`, keep `_shipping_fee_for()` unchanged for broader order flows and add this helper below it:

```python
def _landing_receipt_shipping_fee_for(box_count: int) -> float:
    """Offer-reset landing receipt checkout uses the visible package total."""
    del box_count
    return 0.0
```

- [ ] **Step 6: Use the landing helper only in `/with-receipt`**

In `create_landing_order_with_receipt`, replace:

```python
    shipping_fee = _shipping_fee_for(box_count)
```

with:

```python
    shipping_fee = _landing_receipt_shipping_fee_for(box_count)
```

- [ ] **Step 7: Run focused backend tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "landing_order_with_receipt" -q
```

Expected: all selected landing receipt tests pass.

- [ ] **Step 8: Commit backend API behavior**

Run:

```bash
git add backend/app/api/v1/orders.py backend/tests/test_marketing_api.py
git commit -m "fix(orders): align landing receipt checkout with offer reset"
```

## Task 2: Add Canonical Offer Reset Frontend Content

**Files:**
- Create: `frontend/src/lib/offer-reset-content.ts`

- [ ] **Step 1: Create the content module**

Create `frontend/src/lib/offer-reset-content.ts` with:

```ts
import type { DisplayProduct } from './product-display';

export type OfferResetLocale = 'en' | 'zh';

export interface OfferResetGift {
  id: string;
  name: string;
  weight: string;
  image: string;
  alt: Record<OfferResetLocale, string>;
}

export interface OfferResetProofItem {
  id: string;
  title: Record<OfferResetLocale, string>;
  body: Record<OfferResetLocale, string>;
  image?: string;
  alt?: Record<OfferResetLocale, string>;
}

export interface OfferResetQaItem {
  question: Record<OfferResetLocale, string>;
  answer: Record<OfferResetLocale, string>;
}

export const OFFER_RESET_PRODUCTS: DisplayProduct[] = [
  {
    id: 'pack1',
    name: 'Aqina 纯鸡精 1盒',
    price: 47.9,
    image: '/v2/aqina-v2-hero-product-real.webp',
    label: '7 PACKS x 60g',
    badge: '1盒试喝',
  },
  {
    id: 'pack2',
    name: 'Aqina 纯鸡精 2盒',
    price: 79.8,
    image: '/v2/aqina-v2-hero-product-real.webp',
    label: '14 PACKS x 60g + French Poulet Cut Part 五选一',
    badge: '推荐：SGD39.90/盒 + 赠品',
    popular: true,
  },
];

export const OFFER_RESET_GIFTS: OfferResetGift[] = [
  {
    id: 'joint-wing',
    name: 'French Poulet 3 Joint Wing',
    weight: '500g',
    image: '/french-poulet-gift/chicken-wing.jpg',
    alt: {
      en: 'French Poulet 3 Joint Wing 500g gift option',
      zh: 'French Poulet 3 Joint Wing 500g 赠品选项',
    },
  },
  {
    id: 'minced',
    name: 'French Poulet Minced',
    weight: '400g',
    image: '/french-poulet-gift/minced.png',
    alt: {
      en: 'French Poulet Minced 400g gift option',
      zh: 'French Poulet Minced 400g 赠品选项',
    },
  },
  {
    id: 'boneless-breast',
    name: 'French Poulet Boneless Breast',
    weight: '350g',
    image: '/french-poulet-gift/boneless-breast.png',
    alt: {
      en: 'French Poulet Boneless Breast 350g gift option',
      zh: 'French Poulet Boneless Breast 350g 赠品选项',
    },
  },
  {
    id: 'whole-leg',
    name: 'French Poulet Whole Leg',
    weight: '400g',
    image: '/french-poulet-gift/whole-leg.jpg',
    alt: {
      en: 'French Poulet Whole Leg 400g gift option',
      zh: 'French Poulet Whole Leg 400g 赠品选项',
    },
  },
  {
    id: 'half-chicken',
    name: 'French Poulet Half Chicken Cut 4 Pieces',
    weight: '500g',
    image: '/french-poulet-gift/half-chicken-4-cut.jpg',
    alt: {
      en: 'French Poulet Half Chicken Cut 4 Pieces 500g gift option',
      zh: 'French Poulet Half Chicken Cut 4 Pieces 500g 赠品选项',
    },
  },
];

export function normalizeOfferResetLocale(locale: string): OfferResetLocale {
  return locale === 'zh' ? 'zh' : 'en';
}

export function getOfferResetWhatsAppMessage(locale: string, intent: 'confirm' | 'pack1' | 'pack2' = 'confirm') {
  const safeLocale = normalizeOfferResetLocale(locale);

  if (safeLocale === 'zh') {
    if (intent === 'pack1') {
      return 'Hi Aqina SG，我想先确认 Aqina 纯鸡精 1盒 SGD47.90 适不适合我。';
    }
    if (intent === 'pack2') {
      return 'Hi Aqina SG，我想确认 Aqina 纯鸡精 2盒 SGD79.80 的 French Poulet Cut Part 赠品可以选哪一款。';
    }
    return 'Hi Aqina SG，我想确认 Aqina 纯鸡精 1盒 / 2盒配套。请帮我确认 2盒 SGD79.80 的 French Poulet Cut Part 赠品可以选哪一款。';
  }

  if (intent === 'pack1') {
    return 'Hi Aqina SG, I want to confirm if the 1-box Aqina Pure Chicken Essence at SGD47.90 suits me.';
  }
  if (intent === 'pack2') {
    return 'Hi Aqina SG, I want to confirm the 2-box Aqina Pure Chicken Essence offer at SGD79.80 and the French Poulet Cut Part gift choice.';
  }
  return 'Hi Aqina SG, I want to confirm whether I should choose the 1-box or 2-box Aqina Pure Chicken Essence offer, and which French Poulet Cut Part gift is available for the 2-box offer.';
}

export function getOfferResetCopy(locale: string) {
  const safeLocale = normalizeOfferResetLocale(locale);

  return safeLocale === 'zh'
    ? {
        heroEyebrow: 'Aqina 纯鸡精｜6月新版配套',
        heroTitle: '不是普通瓶装鸡精的价格比较，是 Aqina 纯鸡精的原汤等级。',
        heroBody: '1盒 SGD47.90。2盒 SGD79.80，等于每盒 SGD39.90，并送 French Poulet Cut Part 五选一。',
        primaryCta: 'WhatsApp 确认 1盒 / 2盒和赠品',
        secondaryCta: '直接 PayNow 上传收据下单',
        productProofTitle: '先看真实产品和购买证明，再决定配套。',
        productProofBody: '用真实包装、French Poulet 赠品、PayNow/WhatsApp 成交流程、Aqina farm、MD2 黄梨酵素鸡、7天慢炼、Halal、无添加建立信任。',
        offersTitle: '这次只保留 1盒和 2盒',
        giftsTitle: '2盒送 French Poulet Cut Part，五选一',
        giftsBody: '赠品库存由客服在 WhatsApp 确认。赠品不能大过主产品，主角仍然是 Aqina 纯鸡精。',
        qaTitle: '购买前 Q&A',
        reviewTitle: '真实评价待导入',
        reviewBody: '当前区块先保留真实评价槽位。等客服收集到授权反馈后，再导入真实文字、截图或买家秀。',
        finalTitle: '想先确认，走 WhatsApp；已经决定，走 PayNow。',
      }
    : {
        heroEyebrow: 'Aqina Pure Chicken Essence | June offer reset',
        heroTitle: 'Not an ordinary bottled chicken essence price comparison.',
        heroBody: '1 box at SGD47.90. 2 boxes at SGD79.80, equal to SGD39.90 per box, with one French Poulet Cut Part gift choice.',
        primaryCta: 'Confirm 1 box / 2 boxes and gift on WhatsApp',
        secondaryCta: 'PayNow and upload receipt directly',
        productProofTitle: 'Check product proof before choosing a pack.',
        productProofBody: 'Build trust with real packaging, French Poulet gift photos, PayNow / WhatsApp order path, Aqina farm, MD2 pineapple chicken, 7-day slow extraction, Halal, and no-additive proof.',
        offersTitle: 'This reset keeps only 1 box and 2 boxes',
        giftsTitle: 'Buy 2 boxes and choose one French Poulet Cut Part',
        giftsBody: 'Support confirms available gift stock on WhatsApp. The gift supports the offer, while Aqina Pure Chicken Essence remains the main product.',
        qaTitle: 'Buying Q&A',
        reviewTitle: 'Real reviews pending import',
        reviewBody: 'This section keeps real-ready review slots. Import real text, screenshots, or customer photos only after support collects approved feedback.',
        finalTitle: 'Need confirmation? Use WhatsApp. Ready to order? Use PayNow.',
      };
}
```

- [ ] **Step 2: Commit the content module**

Run:

```bash
git add frontend/src/lib/offer-reset-content.ts
git commit -m "feat(frontend): add Aqina offer reset content source"
```

## Task 3: Fix Checkout Modal For Offer Reset Products

**Files:**
- Modify: `frontend/src/components/CheckoutModal.tsx`

- [ ] **Step 1: Restrict package resolution to active products**

Replace `resolvePackage` with:

```ts
function resolvePackage(product: NonNullable<CheckoutModalProps['product']>) {
  const text = `${product.id} ${product.name} ${product.label}`.toLowerCase();

  if (text.includes('pack2') || text.includes('14') || text.includes('2盒') || text.includes('2 box')) {
    return { productId: 'pack2', boxCount: 2 };
  }

  return { productId: 'pack1', boxCount: 1 };
}
```

- [ ] **Step 2: Remove visible checkout shipping add-on**

Replace:

```ts
  const shippingFee = selectedPackage.boxCount >= 2 ? 0 : 8;
```

with:

```ts
  const shippingFee = 0;
```

- [ ] **Step 3: Replace the shipping-fee line with offer-reset neutral copy**

In the selected-plan total card, replace the conditional delivery/free line:

```tsx
                <p className={shippingFee === 0 ? 'text-xs font-bold text-green-600' : 'text-xs text-charcoal/50'}>
                  {shippingFee === 0
                    ? (ct('form.free') || 'FREE')
                    : `${ct('form.delivery') || 'Delivery Fee'} SGD ${shippingFee.toFixed(2)}`}
                </p>
```

with:

```tsx
                <p className="text-xs font-bold text-green-700">
                  {ct('form.offerResetTotal') || 'Offer reset total shown. Gift and delivery details can be confirmed on WhatsApp.'}
                </p>
```

- [ ] **Step 4: Fix syntax drift before build**

Search the file for an extra closing block around `trackLandingFunnelEvent('checkout_submit_success'...)`. The correct section is:

```ts
      trackLandingFunnelEvent('checkout_submit_success', {
        source: 'checkout_modal',
        product_id: selectedPackage.productId,
        product_name: product.name,
        order_id: result || undefined,
        value: total,
        currency: 'SGD',
      });
      setIsSuccess(true);
```

There must not be an extra `});` between the tracking call and `setIsSuccess(true)`.

- [ ] **Step 5: Run TypeScript build to expose remaining checkout issues**

Run:

```bash
cd frontend && npm run build
```

Expected: build may still fail because the official page is not created yet, but it must not fail from `CheckoutModal.tsx` syntax.

- [ ] **Step 6: Commit checkout compatibility**

Run:

```bash
git add frontend/src/components/CheckoutModal.tsx
git commit -m "fix(frontend): align checkout modal with offer reset packages"
```

## Task 4: Build The Official Offer Reset Page

**Files:**
- Create: `frontend/src/components/pages/OfferResetLandingPage.tsx`
- Add/stage: `frontend/public/french-poulet-gift/*`

- [ ] **Step 1: Create the page component**

Create `frontend/src/components/pages/OfferResetLandingPage.tsx`:

```tsx
'use client';

import dynamic from 'next/dynamic';
import Image from 'next/image';
import { MessageCircle, QrCode } from 'lucide-react';
import { useState } from 'react';
import { useLocale } from 'next-intl';
import Footer from '@/components/Footer';
import {
  OFFER_RESET_GIFTS,
  OFFER_RESET_PRODUCTS,
  getOfferResetCopy,
  getOfferResetWhatsAppMessage,
  normalizeOfferResetLocale,
} from '@/lib/offer-reset-content';
import { getWhatsAppHref } from '@/lib/site-config';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';
import type { DisplayProduct } from '@/lib/product-display';

const CheckoutModal = dynamic(() => import('@/components/CheckoutModal'), {
  ssr: false,
});

export default function OfferResetLandingPage() {
  const locale = useLocale();
  const safeLocale = normalizeOfferResetLocale(locale);
  const copy = getOfferResetCopy(locale);
  const [selectedProduct, setSelectedProduct] = useState<DisplayProduct | null>(null);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);

  const openCheckout = (product: DisplayProduct) => {
    trackLandingFunnelEvent('checkout_open', {
      source: 'offer_reset_direct_paynow',
      product_id: product.id,
      product_name: product.name,
      product_value: Number(product.price),
      landing_version: 'offer_reset',
    });
    setSelectedProduct(product);
    setIsCheckoutOpen(true);
  };

  const whatsappHref = getWhatsAppHref(getOfferResetWhatsAppMessage(locale));

  const trackWhatsApp = (source: string) => {
    trackLandingFunnelEvent('whatsapp_cta_click', {
      source,
      destination: 'whatsapp',
      landing_version: 'offer_reset',
    });
  };

  return (
    <main className="min-h-screen bg-[#fff7e8] pb-24 text-[#23170d]">
      <section id="offer-reset-hero" className="bg-[#fffaf1] px-4 py-10 md:py-16">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
          <div className="space-y-6">
            <p className="text-xs font-black uppercase tracking-[0.22em] text-[#9b6b1f]">{copy.heroEyebrow}</p>
            <h1 className="max-w-3xl text-4xl font-black leading-tight tracking-normal text-[#23170d] md:text-6xl">
              {copy.heroTitle}
            </h1>
            <p className="max-w-2xl text-lg font-semibold leading-8 text-[#5f492f]">{copy.heroBody}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <a
                id="offer-reset-hero-whatsapp-cta"
                href={whatsappHref}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackWhatsApp('offer_reset_hero')}
                className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#25D366] px-5 text-center text-sm font-black text-white shadow-[0_18px_36px_rgba(37,211,102,0.24)] transition hover:-translate-y-0.5"
              >
                <MessageCircle size={19} />
                <span>{copy.primaryCta}</span>
              </a>
              <button
                id="offer-reset-hero-paynow-cta"
                type="button"
                onClick={() => openCheckout(OFFER_RESET_PRODUCTS[1])}
                className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg border border-[#9b6b1f] bg-white px-5 text-center text-sm font-black text-[#23170d] shadow-[0_14px_30px_rgba(91,57,24,0.08)] transition hover:-translate-y-0.5"
              >
                <QrCode size={18} />
                <span>{copy.secondaryCta}</span>
              </button>
            </div>
          </div>
          <figure className="relative min-h-[26rem] overflow-hidden rounded-lg border border-[#d8b774] bg-white shadow-[0_24px_70px_rgba(91,57,24,0.16)]">
            <Image
              src="/v2/aqina-v2-hero-product-real.webp"
              alt={safeLocale === 'zh' ? 'Aqina 纯鸡精真实盒装与小袋' : 'Real Aqina Pure Chicken Essence box and sachets'}
              fill
              priority
              sizes="(max-width: 1024px) 92vw, 48vw"
              className="object-contain p-8"
            />
          </figure>
        </div>
      </section>

      <section id="offer-reset-proof" className="px-4 py-14 md:py-20">
        <div className="mx-auto max-w-7xl space-y-8">
          <div className="max-w-3xl space-y-3">
            <h2 className="text-3xl font-black leading-tight md:text-5xl">{copy.productProofTitle}</h2>
            <p className="text-base font-semibold leading-8 text-[#6f5a43]">{copy.productProofBody}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ['/v2/aqina-v2-pineapple-farm.webp', 'Aqina farm / MD2 黄梨酵素鸡'],
              ['/v2/aqina-v2-golden-essence.webp', '7天慢炼 / double-boiled'],
              ['/paynow/aqina-paynow-qr-designed.png', 'PayNow / WhatsApp order path'],
            ].map(([src, title]) => (
              <article key={title} className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_14px_34px_rgba(91,57,24,0.07)]">
                <div className="relative aspect-[4/3] bg-[#f8ecd5]">
                  <Image src={src} alt={title} fill sizes="(max-width: 768px) 92vw, 31vw" className="object-cover" />
                </div>
                <div className="p-5">
                  <p className="text-lg font-black">{title}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="offer-reset-products" className="bg-[#fffaf1] px-4 py-14 md:py-20">
        <div className="mx-auto max-w-7xl space-y-8">
          <h2 className="text-3xl font-black leading-tight md:text-5xl">{copy.offersTitle}</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {OFFER_RESET_PRODUCTS.map((product) => (
              <article key={product.id} className="rounded-lg border border-[#d8b774] bg-white p-5 shadow-[0_16px_38px_rgba(91,57,24,0.08)]">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-[#9b6b1f]">{product.badge}</p>
                    <h3 className="mt-2 text-2xl font-black">{product.name}</h3>
                    <p className="mt-1 text-sm font-semibold text-[#6f5a43]">{product.label}</p>
                  </div>
                  <p className="text-3xl font-black">SGD {product.price.toFixed(2)}</p>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <a
                    href={getWhatsAppHref(getOfferResetWhatsAppMessage(locale, product.id === 'pack2' ? 'pack2' : 'pack1'))}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => trackWhatsApp(`offer_reset_${product.id}`)}
                    className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#25D366] px-4 text-center text-sm font-black text-white"
                  >
                    <MessageCircle size={17} />
                    <span>{copy.primaryCta}</span>
                  </a>
                  <button
                    type="button"
                    onClick={() => openCheckout(product)}
                    className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg border border-[#9b6b1f] px-4 text-center text-sm font-black text-[#23170d]"
                  >
                    <QrCode size={17} />
                    <span>{copy.secondaryCta}</span>
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="offer-reset-gifts" className="px-4 py-14 md:py-20">
        <div className="mx-auto max-w-7xl space-y-8">
          <div className="max-w-3xl space-y-3">
            <h2 className="text-3xl font-black leading-tight md:text-5xl">{copy.giftsTitle}</h2>
            <p className="text-base font-semibold leading-8 text-[#6f5a43]">{copy.giftsBody}</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {OFFER_RESET_GIFTS.map((gift) => (
              <article key={gift.id} className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_12px_28px_rgba(91,57,24,0.08)]">
                <div className="relative aspect-square bg-[#f8ecd5]">
                  <Image src={gift.image} alt={gift.alt[safeLocale]} fill sizes="(max-width: 768px) 45vw, 18vw" className="object-cover" />
                </div>
                <div className="p-4">
                  <p className="text-sm font-black leading-6">{gift.name}</p>
                  <p className="mt-1 text-sm font-bold text-[#9b6b1f]">{gift.weight}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="offer-reset-qa" className="bg-[#23170d] px-4 py-14 text-[#fffaf1] md:py-20">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <aside className="space-y-3">
            <h2 className="text-3xl font-black leading-tight md:text-5xl">{copy.qaTitle}</h2>
            <div className="rounded-lg border border-[#e9c371]/30 p-5">
              <p className="font-black text-[#e9c371]">{copy.reviewTitle}</p>
              <p className="mt-2 text-sm font-semibold leading-7 text-[#e8d7b9]">{copy.reviewBody}</p>
            </div>
          </aside>
          <div className="grid gap-3">
            {getOfferResetQa(safeLocale).map((item) => (
              <article key={item.question} className="rounded-lg border border-[#e9c371]/24 bg-white/8 p-5">
                <h3 className="font-black text-[#e9c371]">{item.question}</h3>
                <p className="mt-2 text-sm font-semibold leading-7 text-[#e8d7b9]">{item.answer}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="offer-reset-final-cta" className="px-4 py-14 md:py-20">
        <div className="mx-auto max-w-4xl rounded-lg border border-[#d8b774] bg-white p-6 text-center shadow-[0_18px_50px_rgba(91,57,24,0.1)] md:p-8">
          <h2 className="text-3xl font-black leading-tight">{copy.finalTitle}</h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <a
              id="offer-reset-final-whatsapp-cta"
              href={whatsappHref}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => trackWhatsApp('offer_reset_final')}
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#25D366] px-5 text-sm font-black text-white"
            >
              <MessageCircle size={19} />
              <span>{copy.primaryCta}</span>
            </a>
            <button
              id="offer-reset-final-paynow-cta"
              type="button"
              onClick={() => openCheckout(OFFER_RESET_PRODUCTS[1])}
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg border border-[#9b6b1f] px-5 text-sm font-black text-[#23170d]"
            >
              <QrCode size={18} />
              <span>{copy.secondaryCta}</span>
            </button>
          </div>
        </div>
      </section>

      <Footer />
      {isCheckoutOpen || selectedProduct ? (
        <CheckoutModal
          isOpen={isCheckoutOpen}
          onClose={() => setIsCheckoutOpen(false)}
          product={selectedProduct}
        />
      ) : null}
    </main>
  );
}

function getOfferResetQa(locale: 'en' | 'zh') {
  return locale === 'zh'
    ? [
        { question: '为什么比普通瓶装鸡精贵？', answer: 'Aqina 纯鸡精走的是来源、原料和工艺路线：Aqina farm、MD2 黄梨酵素鸡、7天慢炼和纯鸡精小袋，不是最低价瓶装鸡精比较。' },
        { question: '黄梨鸡是不是黄梨味？', answer: '不是黄梨口味。黄梨酵素鸡指的是使用 MD2 Pineapple Enzyme 饲养路线的鸡只。' },
        { question: '第一次买 1盒还是 2盒？', answer: '想先试口感可以选 1盒。已经决定认真喝或买给家人，2盒等于每盒 SGD39.90，并送 French Poulet Cut Part 五选一。' },
        { question: '2盒送什么？', answer: '2盒送 1包 French Poulet Cut Part，五选一：3 Joint Wing、Minced、Boneless Breast、Whole Leg、Half Chicken Cut 4 Pieces。' },
        { question: '有特殊健康状况可以喝吗？', answer: 'Aqina 纯鸡精是日常食品滋养，不替代医疗建议。有特殊健康状况、孕产或治疗中的顾客，请先咨询医生或 WhatsApp 真人客服。' },
      ]
    : [
        { question: 'Why is it more expensive than ordinary bottled chicken essence?', answer: 'Aqina is positioned around source, ingredient, and process: Aqina farm, MD2 pineapple chicken, 7-day slow extraction, and pure chicken essence sachets, not the lowest-price bottled category.' },
        { question: 'Is pineapple chicken pineapple-flavored?', answer: 'No. Pineapple Chicken refers to the MD2 Pineapple Enzyme feeding route, not a pineapple flavor.' },
        { question: 'Should I start with 1 box or 2 boxes?', answer: 'Choose 1 box to try the taste first. Choose 2 boxes if you are ready to start seriously or buying for family, with SGD39.90 per box and one French Poulet Cut Part gift choice.' },
        { question: 'What gift comes with 2 boxes?', answer: '2 boxes include one French Poulet Cut Part gift choice: 3 Joint Wing, Minced, Boneless Breast, Whole Leg, or Half Chicken Cut 4 Pieces.' },
        { question: 'Can customers with special health conditions drink it?', answer: 'Aqina Pure Chicken Essence is a food nourishment product and does not replace medical advice. Customers with special conditions, pregnancy, or treatment should ask a doctor or WhatsApp support first.' },
      ];
}
```

- [ ] **Step 2: Verify required assets exist**

Run:

```bash
test -f frontend/public/french-poulet-gift/minced.png
test -f frontend/public/french-poulet-gift/boneless-breast.png
test -f frontend/public/french-poulet-gift/chicken-wing.jpg
test -f frontend/public/french-poulet-gift/whole-leg.jpg
test -f frontend/public/french-poulet-gift/half-chicken-4-cut.jpg
```

Expected: all commands exit with code `0`.

- [ ] **Step 3: Commit official page and assets**

Run:

```bash
git add frontend/src/components/pages/OfferResetLandingPage.tsx frontend/public/french-poulet-gift
git commit -m "feat(frontend): build Aqina offer reset landing page"
```

## Task 5: Wire Official Entry, Metadata, And Analytics

**Files:**
- Modify: `frontend/src/app/[locale]/page.tsx`
- Modify: `frontend/src/app/[locale]/layout.tsx`
- Modify: `frontend/src/lib/marketing-analytics.ts`

- [ ] **Step 1: Replace the locale home page component**

Replace `frontend/src/app/[locale]/page.tsx` with:

```tsx
import OfferResetLandingPage from '@/components/pages/OfferResetLandingPage';

export default function HomePage() {
  return <OfferResetLandingPage />;
}
```

- [ ] **Step 2: Update locale metadata**

In `frontend/src/app/[locale]/layout.tsx`, replace the title and description logic in `generateMetadata()` with:

```ts
  return {
    title: isZh
      ? "Aqina 纯鸡精｜1盒 SGD47.90 / 2盒 SGD79.80｜French Poulet 赠品"
      : "Aqina Pure Chicken Essence | 1 Box SGD47.90 / 2 Boxes SGD79.80",
    description: isZh
      ? "Aqina 纯鸡精新版配套：1盒 SGD47.90，2盒 SGD79.80，等于每盒 SGD39.90，并送 French Poulet Cut Part 五选一。WhatsApp 确认配套与赠品，或直接 PayNow 上传收据下单。"
      : "Aqina Pure Chicken Essence offer reset: 1 box at SGD47.90, 2 boxes at SGD79.80, equal to SGD39.90 per box with one French Poulet Cut Part gift choice. Confirm on WhatsApp or PayNow and upload your receipt directly.",
    alternates: {
      canonical: isZh ? "/zh" : "/en",
      languages: {
        en: "/en",
        zh: "/zh",
      },
    },
  };
```

- [ ] **Step 3: Update analytics landing version type**

In `frontend/src/lib/marketing-analytics.ts`, replace:

```ts
export type MarketingLandingVersion = 'home' | 'v2' | 'v3' | 'v4';
```

with:

```ts
export type MarketingLandingVersion = 'offer_reset' | 'v2' | 'v3' | 'v4';
```

- [ ] **Step 4: Mark locale home pages as `offer_reset`**

In `getMarketingPageContext()`, replace the locale-only branch with:

```ts
  if (isMarketingLanguage(firstSegment) && segments.length === 1) {
    return {
      page_path: pagePath,
      landing_version: 'offer_reset',
      language: firstSegment,
    };
  }
```

- [ ] **Step 5: Keep versioned experiment detection unchanged**

Keep `isMarketingLandingVersion()` as:

```ts
function isMarketingLandingVersion(value: string | undefined): value is MarketingLandingVersion {
  return value === 'v2' || value === 'v3' || value === 'v4';
}
```

This intentionally excludes `offer_reset` because it is not a URL segment.

- [ ] **Step 6: Commit entry and metadata wiring**

Run:

```bash
git add frontend/src/app/[locale]/page.tsx frontend/src/app/[locale]/layout.tsx frontend/src/lib/marketing-analytics.ts
git commit -m "feat(frontend): route official entries to offer reset"
```

## Task 6: Local Frontend Verification And Retired-Copy Audit

**Files:**
- Verify: frontend build output and rendered pages

- [ ] **Step 1: Run image asset check and production build**

Run:

```bash
cd frontend && npm run check:images && npm run build
```

Expected: both commands pass. If `npm run check:images` reports missing French Poulet assets, add the missing files under `frontend/public/french-poulet-gift/` and rerun.

- [ ] **Step 2: Run retired-copy search against official implementation files**

Run:

```bash
rg -n "SGD ?75|2盒免运|free delivery|free shipping|4盒|6盒|monthly pack|family pack|Messenger" frontend/src/components/pages/OfferResetLandingPage.tsx frontend/src/lib/offer-reset-content.ts frontend/src/app/[locale]/page.tsx frontend/src/app/[locale]/layout.tsx
```

Expected: no matches. Matches in `/v2`, `/v3`, `/v4`, or old message files are acceptable only because those routes are retained as internal experiment pages.

- [ ] **Step 3: Start local dev server**

Run:

```bash
cd frontend && npm run dev
```

Expected: Next dev server starts, normally on `http://localhost:3000`.

- [ ] **Step 4: Browser-check `/`, `/en`, and `/zh`**

Use the in-app Browser plugin for:

```text
http://localhost:3000/
http://localhost:3000/en
http://localhost:3000/zh
```

Expected:

- `/` resolves to `/en` through middleware and shows the new offer-reset page.
- `/en` shows the new offer-reset page.
- `/zh` shows the new offer-reset page.
- The first viewport contains `SGD47.90`, `SGD79.80`, and French Poulet gift messaging.
- Primary CTAs are WhatsApp draft links.
- No visible primary CTA points to Messenger.
- No official page navigation points to `/v2`, `/v3`, or `/v4`.

- [ ] **Step 5: Browser-check checkout amounts**

In the local page:

- Open PayNow checkout for `pack1`.
- Confirm total displays `SGD 47.90`.
- Close modal.
- Open PayNow checkout for `pack2`.
- Confirm total displays `SGD 79.80`.
- Confirm no UI option exposes `pack4` or `pack6`.

- [ ] **Step 6: Stop the dev server**

Stop the dev server cleanly with `Ctrl+C`.

## Task 7: Full Local API Chain Verification

**Files:**
- Verify: `backend/tests/test_marketing_api.py`
- Verify: local frontend/browser behavior

- [ ] **Step 1: Run focused backend order tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -k "landing_order_with_receipt" -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run broader backend marketing tests**

Run:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_marketing_api.py -q
```

Expected: pass, or only unrelated pre-existing failures with exact failing test names documented before continuing.

- [ ] **Step 3: Run final frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: pass.

- [ ] **Step 4: Final local safety confirmation**

Confirm these facts from command output, browser inspection, and code search:

- No production deploy command was run.
- No real WhatsApp or Messenger message was sent.
- No production Firestore/Storage customer data was written by verification.
- The only backend receipt upload calls in tests patch `upload_public_file_to_firebase`.
- `/v2`, `/v3`, and `/v4` still exist but are not linked from the official page.

- [ ] **Step 5: Commit final verification notes if a docs note is created**

If an implementation worker creates a handoff note, use `docs/handover/2026-06-02-aqina-offer-reset-local-verification.md` and commit it with:

```bash
git add docs/handover/2026-06-02-aqina-offer-reset-local-verification.md
git commit -m "docs: record Aqina offer reset local verification"
```

Do not create this note if the final chat summary is sufficient.

## Completion Criteria

The implementation is complete only when current evidence proves:

- `/`, `/en`, `/zh` enter the new official offer-reset page.
- The official page is WhatsApp-first and PayNow-secondary.
- Official page copy uses `1盒 SGD47.90`, `2盒 SGD79.80`, `SGD39.90/盒`, and French Poulet gift choices.
- Official page product proof uses real product, gift, PayNow/WhatsApp, Aqina farm, MD2 黄梨酵素鸡, 7-day slow extraction, Halal, and no-additive proof where supported.
- Review area uses Q&A / real-ready review slots, not fake testimonials.
- PayNow checkout supports only `pack1` and `pack2`.
- `/api/v1/orders/with-receipt` accepts only `pack1` and `pack2` and returns the offer-reset totals.
- Backend focused tests pass.
- Frontend build passes.
- Browser checks pass on desktop/mobile enough to prove no broken first viewport, CTA, or checkout modal.
- No production deploy, production customer write, or real outbound WhatsApp/Messenger send happened.
