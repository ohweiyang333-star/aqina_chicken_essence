'use client';

import { useState } from 'react';
import { useLocale } from 'next-intl';
import Image from 'next/image';
import { Check, ChevronRight, MessageCircle, QrCode } from 'lucide-react';
import CheckoutModal from '@/components/CheckoutModal';
import useLandingProducts from '@/hooks/useLandingProducts';
import { getWhatsAppHref } from '@/lib/site-config';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';
import { Reveal, RevealGroup, RevealItem } from '@/components/motion/Reveal';
import {
  COOKING_USES,
  COPY,
  CONCERNS,
  FAQ_ITEMS,
  GIFT_OPTIONS,
  INTENT_OPTIONS,
  MARKETPLACE_PRICING,
  MEDICAL_BOUNDARY,
  NUTRITION_FACTS,
  PER_SACHET,
  PROOF_PRODUCT,
  PROOF_SCENES,
  RHYTHM_ROWS,
  SELLER_IDENTITY,
  SOURCE_CHAIN,
  VALUE_EQUATION,
  getMarketplaceWhatsAppMessage,
  normalizeMarketplaceLocale,
  type IntentOption,
} from '@/lib/marketplace-offer-content';

const LANDING_VERSION = 'marketplace_offer';

/** One shared measure for the page. */
const SHELL = 'mx-auto w-full max-w-[76rem] px-5 md:px-8';
/** Hairline rule — the page's primary structural device instead of card borders. */
const RULE = 'border-paper-edge';

export default function MarketplaceOfferPage() {
  const locale = useLocale();
  const lang = normalizeMarketplaceLocale(locale);
  const t = (entry: Record<'en' | 'zh', string>) => entry[lang];
  const zh = lang === 'zh';

  const { products, selectedProduct, isCheckoutOpen, handleBuyNow, closeCheckout } =
    useLandingProducts();

  const [activeTab, setActiveTab] = useState<'pack1' | 'pack2'>('pack2');
  const [selectedGift, setSelectedGift] = useState(GIFT_OPTIONS[0].value);

  const activeProduct = products.find((p) => p.id === activeTab) || products[0];
  const activePrice =
    activeTab === 'pack1' ? MARKETPLACE_PRICING.pack1.price : MARKETPLACE_PRICING.pack2.price;

  const openWhatsApp = (source: string, intentId?: IntentOption['id']) => {
    trackLandingFunnelEvent('whatsapp_cta_click', {
      source,
      destination: 'whatsapp',
      landing_version: LANDING_VERSION,
      intent: intentId ?? 'general',
    });
    window.open(getWhatsAppHref(getMarketplaceWhatsAppMessage(locale, intentId)), '_blank');
  };

  const handlePayNowSubmit = (source: string) => {
    if (!activeProduct) return;
    trackLandingFunnelEvent('product_buy_click', {
      source,
      landing_version: LANDING_VERSION,
      product_id: activeProduct.id,
      product_value: Number(activeProduct.price),
    });
    const gift = GIFT_OPTIONS.find((g) => g.value === selectedGift);
    handleBuyNow({
      ...activeProduct,
      label:
        activeTab === 'pack2' && gift
          ? `${activeProduct.label} (${zh ? '已选赠品' : 'gift'}: ${gift.name} ${gift.weight})`
          : activeProduct.label,
    });
  };

  const priceRows = [
    {
      key: 'competitor',
      name: `${VALUE_EQUATION.competitor.brand} ${t(VALUE_EQUATION.competitor.product)}`,
      spec: `60g × ${VALUE_EQUATION.competitor.sachets} · SGD ${VALUE_EQUATION.competitor.packPrice.toFixed(2)}`,
      per: VALUE_EQUATION.competitor.perSachet,
      ours: false,
    },
    {
      key: 'pack1',
      name: zh ? 'Aqina 纯鸡精 · 1 盒' : 'Aqina Pure Chicken Essence · 1 box',
      spec: '60g × 7 · SGD 47.90',
      per: PER_SACHET.pack1,
      ours: true,
    },
    {
      key: 'pack2',
      name: zh ? 'Aqina 纯鸡精 · 2 盒' : 'Aqina Pure Chicken Essence · 2 boxes',
      spec: '60g × 14 · SGD 79.80',
      per: PER_SACHET.pack2,
      ours: true,
    },
  ];

  const primaryBtn =
    'inline-flex min-h-[3.25rem] items-center justify-center gap-2 rounded-xl bg-[#1f8a4c] px-6 text-[0.95rem] font-semibold text-white transition duration-200 hover:bg-[#1a763f] active:translate-y-px';
  const secondaryBtn =
    'inline-flex min-h-[3.25rem] items-center justify-center gap-2 rounded-xl border border-ink/25 px-6 text-[0.95rem] font-semibold text-ink transition duration-200 hover:border-ink/50 hover:bg-ink/[0.04] active:translate-y-px';

  return (
    // pt-16 clears the shared fixed header (h-16); without it the masthead strip
    // renders underneath it.
    <div className="world-paper min-h-screen pt-16 pb-28 md:pb-0">
      {/* ── Masthead rule: verifiable facts, set as a hairline strip, not a second dark bar ── */}
      <div className={`border-b ${RULE} bg-paper-deep/60`}>
        <div className={`${SHELL} flex flex-wrap items-center justify-center gap-x-6 gap-y-1 py-2.5`}>
          {[COPY.trustStrip1, COPY.trustStrip2, COPY.trustStrip3, COPY.trustStrip4].map((chip) => (
            <span key={t(chip)} className="text-[0.7rem] font-medium tracking-wide text-ink-soft">
              {t(chip)}
            </span>
          ))}
        </div>
      </div>

      {/* ───────────────────────────────── 1. HERO ───────────────────────────────── */}
      <header className={`${SHELL} pt-14 md:pt-24`}>
        <div className="grid gap-12 lg:grid-cols-12 lg:items-end lg:gap-10">
          <Reveal className="lg:col-span-7">
            <p className="text-[0.78rem] font-medium tracking-wide text-gold-deep">
              {t(COPY.heroEyebrow)}
            </p>
            <h1 className="display mt-5 text-[2.6rem] leading-[1.05] md:text-[4.4rem] md:leading-[0.98]">
              {t(COPY.heroTitle)}
            </h1>
            <p className="mt-6 max-w-[46ch] text-[1.05rem] leading-[1.75] text-ink-soft md:text-[1.15rem]">
              {t(COPY.heroSub)}
            </p>

            {/* Price stated as a line of type, not boxed in a card. */}
            <div className={`mt-9 flex flex-wrap items-baseline gap-x-8 gap-y-3 border-t ${RULE} pt-6`}>
              <span className="flex items-baseline gap-2.5">
                <span className="text-[0.8rem] text-ink-faint">{zh ? '1 盒 7 袋' : '1 box · 7'}</span>
                <span className="figure text-[1.7rem] font-semibold text-ink">47.90</span>
              </span>
              <span className="flex items-baseline gap-2.5">
                <span className="text-[0.8rem] text-ink-faint">{zh ? '2 盒 14 袋' : '2 boxes · 14'}</span>
                <span className="figure text-[1.7rem] font-semibold text-ink">79.80</span>
              </span>
              <span className="text-[0.78rem] text-ink-faint">
                {zh ? 'SGD · 每盒 39.90 · 含配送' : 'SGD · 39.90 a box · delivery included'}
              </span>
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <button type="button" onClick={() => openWhatsApp('hero_primary')} className={primaryBtn}>
                <MessageCircle size={18} />
                {t(COPY.ctaWhatsApp)}
              </button>
              <a href="#offer-reset-products" className={secondaryBtn}>
                {t(COPY.offersTitle)}
                <ChevronRight size={16} />
              </a>
            </div>
          </Reveal>

          {/* Image bleeds past the text column baseline for asymmetry. */}
          <Reveal className="lg:col-span-5" index={1}>
            <figure className="lift-lg relative aspect-[4/5] overflow-hidden rounded-[1.25rem] bg-paper-deep lg:-mb-16">
              <Image
                src="/proof/product-unboxing-bowl.webp"
                alt={
                  zh
                    ? 'Aqina 纯鸡精盒装、独立小袋与倒出的金汤'
                    : 'Aqina Pure Chicken Essence box, sachet and poured golden broth'
                }
                fill
                priority
                sizes="(max-width: 1024px) 92vw, 40vw"
                className="object-cover"
              />
            </figure>
          </Reveal>
        </div>
      </header>

      {/* ─────────────────── 2. VALUE EQUATION — a ruled comparison ─────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <Reveal>
          <div className="max-w-[52ch]">
            <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
              {t(COPY.valueTitle)}
            </h2>
            <p className="mt-3 text-[1rem] leading-[1.7] text-ink-soft">{t(COPY.valueSubtitle)}</p>
          </div>
        </Reveal>

        <RevealGroup className="mt-10" as="dl">
          <div
            className={`hidden border-b ${RULE} pb-2 text-[0.72rem] tracking-wide text-ink-faint md:grid md:grid-cols-[1fr_auto_9rem] md:gap-6`}
          >
            <span>{zh ? '同规格产品' : 'Like-for-like product'}</span>
            <span className="text-right">{zh ? '规格与售价' : 'Pack & price'}</span>
            <span className="text-right">{zh ? '每袋' : 'Per sachet'}</span>
          </div>

          {priceRows.map((row, i) => (
            <RevealItem
              key={row.key}
              index={i}
              className={`grid grid-cols-[1fr_auto] items-baseline gap-x-6 gap-y-1 border-b ${RULE} py-5 md:grid-cols-[1fr_auto_9rem]`}
            >
              <dt
                className={`text-[1rem] leading-snug md:text-[1.05rem] ${
                  row.ours ? 'font-semibold text-ink' : 'text-ink-soft'
                }`}
              >
                {row.name}
              </dt>
              <dd className="figure order-3 text-[0.82rem] text-ink-faint md:order-none md:text-right">
                {row.spec}
              </dd>
              <dd
                className={`figure justify-self-end text-[1.65rem] md:text-[1.9rem] ${
                  row.ours ? 'font-semibold text-gold-deep' : 'font-normal text-ink-faint'
                }`}
              >
                {row.per.toFixed(2)}
              </dd>
            </RevealItem>
          ))}
        </RevealGroup>

        <Reveal>
          <p className="mt-5 max-w-[74ch] text-[0.78rem] leading-[1.7] text-ink-faint">
            {t(COPY.valueDisclaimer)}
          </p>
        </Reveal>
      </section>

      {/* ───────────────────────── 3. INTENT ROUTER ───────────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <Reveal>
          <h2 className="display max-w-[20ch] text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
            {t(COPY.intentTitle)}
          </h2>
          <p className="mt-3 max-w-[52ch] text-[1rem] leading-[1.7] text-ink-soft">
            {t(COPY.intentSubtitle)}
          </p>
        </Reveal>

        <RevealGroup className={`mt-9 border-t ${RULE}`} as="ul">
          {INTENT_OPTIONS.map((option, i) => (
            <RevealItem key={option.id} as="li" index={i}>
              <button
                type="button"
                onClick={() => openWhatsApp(`intent_${option.id}`, option.id)}
                className={`group flex w-full items-center justify-between gap-6 border-b ${RULE} py-6 text-left transition-colors duration-200 hover:bg-paper-deep/50`}
              >
                <span className="min-w-0">
                  <span className="block text-[1.1rem] font-medium leading-snug text-ink md:text-[1.3rem]">
                    {t(option.label)}
                  </span>
                  <span className="mt-1 block text-[0.85rem] text-ink-faint">{t(option.hint)}</span>
                </span>
                <span className="flex shrink-0 items-center gap-2 text-[0.82rem] font-medium text-gold-deep">
                  <span className="hidden sm:inline">{t(COPY.ctaWhatsApp)}</span>
                  <ChevronRight
                    size={17}
                    className="transition-transform duration-200 group-hover:translate-x-1"
                  />
                </span>
              </button>
            </RevealItem>
          ))}
        </RevealGroup>
      </section>

      {/* ───────────────────────── 4. OFFER + BUY BOX ───────────────────────── */}
      <section id="offer-reset-products" className={`${SHELL} pt-24 md:pt-36`}>
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-14">
          <div className="lg:col-span-7">
            <Reveal>
              <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
                {t(COPY.offersTitle)}
              </h2>
            </Reveal>

            <RevealGroup className={`mt-8 border-t ${RULE}`} as="ul">
              {(
                [
                  {
                    id: 'pack2' as const,
                    title: zh ? '2 盒 · 14 袋' : '2 boxes · 14 sachets',
                    sub: zh ? '每盒 SGD 39.90，含 French Poulet 赠品' : 'SGD 39.90 a box, with a French Poulet gift',
                    price: '79.80',
                  },
                  {
                    id: 'pack1' as const,
                    title: zh ? '1 盒 · 7 袋' : '1 box · 7 sachets',
                    sub: zh ? '先确认口味再决定' : 'Confirm the taste first',
                    price: '47.90',
                  },
                ]
              ).map((pack) => {
                const on = activeTab === pack.id;
                return (
                  <RevealItem key={pack.id} as="li">
                    <button
                      type="button"
                      onClick={() => setActiveTab(pack.id)}
                      aria-pressed={on}
                      className={`flex w-full items-center gap-4 border-b ${RULE} py-6 text-left transition-colors duration-200 ${
                        on ? 'bg-paper-deep/70' : 'hover:bg-paper-deep/40'
                      }`}
                    >
                      <span
                        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition ${
                          on ? 'border-gold-deep bg-gold-deep' : 'border-ink/30'
                        }`}
                      >
                        {on && <Check size={12} strokeWidth={3} className="text-paper" />}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-[1.1rem] font-medium text-ink md:text-[1.2rem]">
                          {pack.title}
                        </span>
                        <span className="mt-0.5 block text-[0.85rem] text-ink-faint">{pack.sub}</span>
                      </span>
                      <span className="figure shrink-0 text-[1.5rem] font-semibold text-ink">
                        {pack.price}
                      </span>
                    </button>
                  </RevealItem>
                );
              })}
            </RevealGroup>

            {activeTab === 'pack2' && (
              <div className="mt-9">
                <p className="text-[0.85rem] font-medium text-ink-soft">{t(COPY.giftsTitle)}</p>
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
                  {GIFT_OPTIONS.map((gift) => {
                    const on = selectedGift === gift.value;
                    return (
                      <button
                        key={gift.value}
                        type="button"
                        onClick={() => setSelectedGift(gift.value)}
                        aria-pressed={on}
                        className="group text-left"
                      >
                        <span
                          className={`relative block aspect-square overflow-hidden rounded-lg bg-paper-deep transition duration-200 ${
                            on ? 'ring-2 ring-gold-deep ring-offset-2 ring-offset-paper' : 'opacity-80 group-hover:opacity-100'
                          }`}
                        >
                          <Image
                            src={gift.image}
                            alt={`${gift.name} ${gift.weight}`}
                            fill
                            sizes="(max-width: 640px) 45vw, 14vw"
                            className="object-cover"
                          />
                        </span>
                        {/* Fixed two-line box so every weight lands on the same baseline
                            regardless of how long the product name is. */}
                        <span className="mt-2 flex h-[2.1rem] items-start text-[0.72rem] font-medium leading-[1.05rem] text-ink">
                          {gift.name}
                        </span>
                        <span className="figure block text-[0.72rem] text-ink-faint">{gift.weight}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* The one place elevation is earned: the transaction. */}
          <Reveal className="lg:col-span-5" index={1}>
            <div className="lift-lg sticky top-8 rounded-[1.25rem] bg-white/70 p-7 backdrop-blur-sm md:p-8">
              <div className="flex items-baseline justify-between gap-4">
                <span className="text-[0.85rem] text-ink-soft">
                  {activeTab === 'pack1'
                    ? zh
                      ? '1 盒 · 7 袋'
                      : '1 box · 7 sachets'
                    : zh
                      ? '2 盒 · 14 袋'
                      : '2 boxes · 14 sachets'}
                </span>
                <span className="figure text-[2.6rem] font-semibold leading-none text-ink">
                  {activePrice.toFixed(2)}
                </span>
              </div>

              <ul className={`mt-6 space-y-3 border-t ${RULE} pt-6`}>
                {[
                  zh ? '新加坡现货，2–3 天冷链送达' : 'Singapore stock, 2–3 day cold-chain delivery',
                  zh ? '配送已含在价格内' : 'Delivery already included in the price',
                  zh
                    ? 'PayNow 转账给 Boong Poultry Pte Ltd，真人核对'
                    : 'PayNow to Boong Poultry Pte Ltd, checked by a real person',
                ].map((line) => (
                  <li key={line} className="flex gap-2.5 text-[0.88rem] leading-[1.6] text-ink-soft">
                    <Check size={15} className="mt-0.5 shrink-0 text-gold-deep" />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-7 grid gap-2.5">
                <button
                  type="button"
                  onClick={() => openWhatsApp('buybox_whatsapp')}
                  className={`${primaryBtn} w-full`}
                >
                  <MessageCircle size={18} />
                  {t(COPY.ctaWhatsApp)}
                </button>
                <button
                  type="button"
                  onClick={() => handlePayNowSubmit('buybox_paynow')}
                  className={`${secondaryBtn} w-full`}
                >
                  <QrCode size={17} />
                  {t(COPY.ctaPayNow)}
                </button>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ───────────────────── 5. THE THREE OBJECTIONS ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <Reveal>
          <h2 className="display max-w-[24ch] text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
            {t(COPY.concernsTitle)}
          </h2>
          <p className="mt-3 max-w-[52ch] text-[1rem] leading-[1.7] text-ink-soft">
            {t(COPY.concernsSubtitle)}
          </p>
        </Reveal>

        <RevealGroup className={`mt-10 border-t ${RULE}`} as="ol">
          {CONCERNS.map((concern, i) => (
            <RevealItem key={concern.id} as="li" index={i} className={`border-b ${RULE} py-9`}>
              <div className="grid gap-4 md:grid-cols-12 md:gap-8">
                <p className="figure text-[0.8rem] text-ink-faint md:col-span-1">
                  {String(i + 1).padStart(2, '0')}
                </p>
                <h3 className="display text-[1.35rem] leading-tight text-ink md:col-span-4 md:text-[1.6rem]">
                  {t(concern.question)}
                </h3>
                <div className="md:col-span-7">
                  <p className="max-w-[58ch] text-[1rem] leading-[1.8] text-ink-soft">
                    {t(concern.answer)}
                  </p>
                  {concern.note && (
                    <p className="mt-4 max-w-[58ch] border-l-2 border-gold/50 pl-4 text-[0.88rem] leading-[1.7] text-gold-deep">
                      {t(concern.note)}
                    </p>
                  )}
                </div>
              </div>
            </RevealItem>
          ))}
        </RevealGroup>
      </section>

      {/* ───────────────────── 6. SOURCE & PROCESS ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-14">
          <div className="lg:col-span-7">
            <Reveal>
              <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
                {t(COPY.sourceTitle)}
              </h2>
              <p className="mt-3 max-w-[52ch] text-[1rem] leading-[1.7] text-ink-soft">
                {t(COPY.sourceSubtitle)}
              </p>
            </Reveal>

            <RevealGroup className={`mt-9 border-t ${RULE}`} as="ol">
              {SOURCE_CHAIN.map((step, i) => (
                <RevealItem key={step.id} as="li" index={i} className={`grid grid-cols-[2.5rem_1fr] gap-4 border-b ${RULE} py-6`}>
                  <span className="figure pt-0.5 text-[0.8rem] text-ink-faint">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div>
                    <h3 className="text-[1.05rem] font-semibold leading-snug text-ink">
                      {t(step.title)}
                    </h3>
                    <p className="mt-1.5 max-w-[56ch] text-[0.95rem] leading-[1.75] text-ink-soft">
                      {t(step.body)}
                    </p>
                  </div>
                </RevealItem>
              ))}
            </RevealGroup>

            <Reveal>
              <p className="display mt-8 max-w-[40ch] text-[1.25rem] leading-snug text-gold-deep md:text-[1.5rem]">
                {t(COPY.notPineappleFlavour)}
              </p>
              <div className={`mt-8 flex flex-wrap items-center gap-x-7 gap-y-2 border-t ${RULE} pt-5`}>
                <span className="text-[0.72rem] tracking-wide text-ink-faint">
                  {t(COPY.nutritionTitle)}
                </span>
                {NUTRITION_FACTS.map((fact) => (
                  <span key={t(fact)} className="text-[0.85rem] font-medium text-ink-soft">
                    {t(fact)}
                  </span>
                ))}
              </div>
            </Reveal>
          </div>

          <Reveal className="lg:col-span-5" index={1}>
            <div className="sticky top-8 grid gap-4">
              <figure className="lift relative aspect-[4/5] overflow-hidden rounded-[1.25rem] bg-paper-deep">
                <Image
                  src="/proof/pineapple-chicken-story.webp"
                  alt={zh ? 'MD2 黄梨酵素鸡与产品场景' : 'MD2 pineapple enzyme chicken and the product'}
                  fill
                  sizes="(max-width: 1024px) 92vw, 36vw"
                  className="object-cover"
                />
              </figure>
              <figure className="lift relative aspect-[16/10] overflow-hidden rounded-[1.25rem] bg-paper-deep">
                <Image
                  src="/proof/pack-detail-single-origin.webp"
                  alt={zh ? '包装上的 Single Origin 字样' : 'The "Single Origin" wording on the pack'}
                  fill
                  sizes="(max-width: 1024px) 92vw, 36vw"
                  className="object-cover"
                />
              </figure>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ───────────────────── 7. RHYTHM & BUDGET ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-14 lg:items-center">
          <div className="lg:col-span-7">
            <Reveal>
              <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
                {t(COPY.rhythmTitle)}
              </h2>
              <p className="mt-3 max-w-[54ch] text-[1rem] leading-[1.7] text-ink-soft">
                {t(COPY.rhythmSubtitle)}
              </p>
            </Reveal>

            <RevealGroup className={`mt-9 border-t ${RULE}`} as="dl">
              {RHYTHM_ROWS.map((row, i) => (
                <RevealItem
                  key={t(row.stage)}
                  index={i}
                  className={`flex items-baseline justify-between gap-6 border-b ${RULE} py-5`}
                >
                  <dt className="text-[1rem] font-medium text-ink">{t(row.stage)}</dt>
                  <dd className="figure flex items-baseline gap-6 text-ink-faint">
                    <span className="text-[0.9rem]">{t(row.days)}</span>
                    <span className="min-w-[6.5rem] text-right">
                      <span className="block text-[1.35rem] font-semibold leading-tight text-gold-deep">
                        {t(row.boxes)}
                      </span>
                      {row.note && (
                        <span className="mt-1 block text-[0.72rem] leading-tight text-ink-faint">
                          {t(row.note)}
                        </span>
                      )}
                    </span>
                  </dd>
                </RevealItem>
              ))}
            </RevealGroup>

            <Reveal>
              <p className="mt-6 max-w-[58ch] text-[0.95rem] leading-[1.8] text-ink-soft">
                {t(COPY.rhythmBudget)}
              </p>
              <button
                type="button"
                onClick={() => openWhatsApp('rhythm_cta', 'confinement')}
                className={`${primaryBtn} mt-7`}
              >
                <MessageCircle size={18} />
                {t(COPY.rhythmCta)}
              </button>
            </Reveal>
          </div>

          <Reveal className="lg:col-span-5" index={1}>
            <figure className="lift relative aspect-[4/5] overflow-hidden rounded-[1.25rem] bg-paper-deep">
              <Image
                src="/proof/scene-family-handover.webp"
                alt={zh ? '家人递上一袋纯鸡精' : 'Handing a sachet to family'}
                fill
                sizes="(max-width: 1024px) 92vw, 36vw"
                className="object-cover"
              />
            </figure>
          </Reveal>
        </div>
      </section>

      {/* ───────────────────── 8. GOLDEN STOCK ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <div className="grid gap-12 lg:grid-cols-12 lg:items-center lg:gap-14">
          <Reveal className="lg:col-span-6 lg:order-2">
            <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
              {t(COPY.cookingTitle)}
            </h2>
            <p className="mt-4 max-w-[52ch] text-[1rem] leading-[1.8] text-ink-soft">
              {t(COPY.cookingBody)}
            </p>
            <ul className={`mt-7 flex flex-wrap gap-x-6 gap-y-2 border-t ${RULE} pt-5`}>
              {COOKING_USES.map((use) => (
                <li key={t(use)} className="text-[0.95rem] font-medium text-ink-soft">
                  {t(use)}
                </li>
              ))}
            </ul>
          </Reveal>

          <Reveal className="lg:col-span-6 lg:order-1" index={1}>
            <figure className="lift relative aspect-[5/4] overflow-hidden rounded-[1.25rem] bg-paper-deep">
              <Image
                src="/proof/golden-broth-macro.webp"
                alt={zh ? '金黄色鸡精汤微距' : 'Macro of the golden broth'}
                fill
                sizes="(max-width: 1024px) 92vw, 44vw"
                className="object-cover"
              />
            </figure>
          </Reveal>
        </div>
      </section>

      {/* ───────────────────── 9. SELLER IDENTITY ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-14">
          <div className="lg:col-span-7">
            <Reveal>
              <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
                {t(COPY.identityTitle)}
              </h2>
              <p className="mt-3 max-w-[54ch] text-[1rem] leading-[1.7] text-ink-soft">
                {t(COPY.identitySubtitle)}
              </p>
            </Reveal>

            <RevealGroup className={`mt-9 border-t ${RULE}`} as="dl">
              {SELLER_IDENTITY.map((row, i) => (
                <RevealItem
                  key={t(row.label)}
                  index={i}
                  className={`grid gap-1 border-b ${RULE} py-5 sm:grid-cols-[11rem_1fr] sm:gap-6`}
                >
                  <dt className="text-[0.78rem] tracking-wide text-ink-faint">{t(row.label)}</dt>
                  <dd className="text-[0.98rem] leading-[1.6] text-ink">{t(row.value)}</dd>
                </RevealItem>
              ))}
            </RevealGroup>
          </div>

          <Reveal className="lg:col-span-5" index={1}>
            <div className={`rounded-[1.25rem] border ${RULE} bg-paper-deep/50 p-6`}>
              <div className="relative mx-auto aspect-square w-full max-w-[14rem] overflow-hidden rounded-lg bg-white">
                <Image
                  src="/paynow/aqina-paynow-qr-designed.png"
                  alt="Boong Poultry Pte Ltd PayNow QR"
                  fill
                  sizes="14rem"
                  className="object-contain p-2"
                />
              </div>
              <p className="mt-5 text-[0.85rem] leading-[1.7] text-ink-soft">
                {t(COPY.identityPaynowNote)}
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ───────────────────── 10. PROOF — asymmetric mosaic ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <Reveal>
          <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">
            {t(COPY.proofTitle)}
          </h2>
          <p className="mt-3 text-[1rem] text-ink-soft">{t(COPY.proofSubtitle)}</p>
        </Reveal>

        <RevealGroup className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-6 md:gap-5">
          {PROOF_PRODUCT.map((item, i) => {
            // Deliberately uneven: wide / tall / square, so it reads as a shoot, not a grid.
            const span = [
              'md:col-span-4 md:aspect-[16/10]',
              'md:col-span-2 md:aspect-[4/5]',
              'md:col-span-2 md:aspect-[4/5]',
              'md:col-span-4 md:aspect-[16/10]',
              'md:col-span-3 md:aspect-[3/2]',
              'md:col-span-3 md:aspect-[3/2]',
            ][i % 6];
            return (
              <RevealItem
                key={item.src}
                as="figure"
                index={i}
                className={`col-span-1 ${span} group overflow-hidden rounded-[1rem] bg-paper-deep`}
              >
                <span className="relative block aspect-square h-full w-full md:aspect-auto">
                  <Image
                    src={item.src}
                    alt={t(item.alt)}
                    fill
                    sizes="(max-width: 768px) 46vw, 32vw"
                    className="object-cover transition-transform duration-[900ms] ease-out group-hover:scale-[1.03]"
                  />
                </span>
                <figcaption className="px-1 pt-2.5 text-[0.78rem] leading-[1.5] text-ink-faint">
                  {t(item.caption)}
                </figcaption>
              </RevealItem>
            );
          })}
        </RevealGroup>

        <Reveal>
          <p className="mt-14 text-[0.72rem] tracking-wide text-ink-faint">
            {t(COPY.proofSceneHeading)}
          </p>
        </Reveal>
        <RevealGroup className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-5">
          {PROOF_SCENES.map((item, i) => (
            <RevealItem key={item.src} as="figure" index={i} className="group">
              <span className="relative block aspect-[4/5] overflow-hidden rounded-[1rem] bg-paper-deep">
                <Image
                  src={item.src}
                  alt={t(item.alt)}
                  fill
                  sizes="(max-width: 768px) 46vw, 22vw"
                  className="object-cover transition-transform duration-[900ms] ease-out group-hover:scale-[1.03]"
                />
              </span>
              <figcaption className="px-1 pt-2.5 text-[0.78rem] leading-[1.5] text-ink-faint">
                {t(item.caption)}
              </figcaption>
            </RevealItem>
          ))}
        </RevealGroup>

      </section>

      {/* ───────────────────── 11. FAQ ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <Reveal>
          <h2 className="display text-[1.9rem] leading-[1.15] md:text-[2.6rem]">{t(COPY.faqTitle)}</h2>
        </Reveal>

        <RevealGroup className={`mt-10 border-t ${RULE}`} as="dl">
          {FAQ_ITEMS.map((item, i) => (
            <RevealItem
              key={t(item.q)}
              index={i}
              className={`grid gap-3 border-b ${RULE} py-7 md:grid-cols-12 md:gap-8`}
            >
              <dt className="text-[1.02rem] font-semibold leading-snug text-ink md:col-span-5">
                {t(item.q)}
              </dt>
              <dd className="max-w-[62ch] text-[0.95rem] leading-[1.8] text-ink-soft md:col-span-7">
                {t(item.a)}
              </dd>
            </RevealItem>
          ))}
        </RevealGroup>
      </section>

      {/* ───────────────────── 12. CLOSE ───────────────────── */}
      <section className={`${SHELL} pt-24 md:pt-36`}>
        <Reveal>
          <div className={`border-t ${RULE} pt-12`}>
            <h2 className="display max-w-[18ch] text-[2.1rem] leading-[1.1] md:text-[3rem]">
              {t(COPY.intentTitle)}
            </h2>
            <div className="mt-8 flex flex-wrap gap-3">
              <button type="button" onClick={() => openWhatsApp('final_whatsapp')} className={primaryBtn}>
                <MessageCircle size={18} />
                {t(COPY.ctaWhatsApp)}
              </button>
              <button
                type="button"
                onClick={() => handlePayNowSubmit('final_paynow')}
                className={secondaryBtn}
              >
                <QrCode size={17} />
                {t(COPY.ctaPayNow)}
              </button>
            </div>

            <p className="mt-12 max-w-[70ch] text-[0.82rem] leading-[1.75] text-ink-faint">
              {t(MEDICAL_BOUNDARY)}
            </p>
            <p className="mt-4 text-[0.75rem] text-ink-faint">
              JAKIM Halal · SFA · HACCP · GMP —{' '}
              {zh ? '新加坡 2–3 天冷链' : 'Singapore 2–3 day cold chain'}
            </p>
          </div>
        </Reveal>
      </section>

      {/* ───────────────────── Sticky bar (mobile) ───────────────────── */}
      <div className={`fixed inset-x-0 bottom-0 z-40 border-t ${RULE} bg-paper/95 px-4 py-3 backdrop-blur md:hidden`}>
        <div className="flex items-center gap-4">
          <div className="shrink-0">
            <p className="text-[0.68rem] leading-none text-ink-faint">
              {activeTab === 'pack1' ? (zh ? '1 盒' : '1 box') : t(COPY.stickyPrefix)}
            </p>
            <p className="figure mt-1 text-[1.25rem] font-semibold leading-none text-ink">
              {activePrice.toFixed(2)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => openWhatsApp('sticky_whatsapp')}
            className={`${primaryBtn} min-h-[2.9rem] flex-1 px-4 text-[0.9rem]`}
          >
            <MessageCircle size={17} />
            {t(COPY.ctaWhatsApp)}
          </button>
        </div>
      </div>

      {activeProduct && (
        <CheckoutModal isOpen={isCheckoutOpen} onClose={closeCheckout} product={selectedProduct} />
      )}
    </div>
  );
}
