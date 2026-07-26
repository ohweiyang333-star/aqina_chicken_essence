'use client';

import { useState } from 'react';
import { useLocale } from 'next-intl';
import Image from 'next/image';
import {
  Award,
  Building2,
  CalendarDays,
  Check,
  ChevronRight,
  Gift,
  HelpCircle,
  Info,
  MessageCircle,
  QrCode,
  ShieldCheck,
  Truck,
  Utensils,
} from 'lucide-react';
import CheckoutModal from '@/components/CheckoutModal';
import useLandingProducts from '@/hooks/useLandingProducts';
import { getWhatsAppHref } from '@/lib/site-config';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';
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

export default function MarketplaceOfferPage() {
  const locale = useLocale();
  const lang = normalizeMarketplaceLocale(locale);
  const t = (entry: Record<'en' | 'zh', string>) => entry[lang];

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
    const giftLabel = GIFT_OPTIONS.find((g) => g.value === selectedGift);
    handleBuyNow({
      ...activeProduct,
      label:
        activeTab === 'pack2' && giftLabel
          ? `${activeProduct.label} (${lang === 'zh' ? '已选赠品' : 'gift'}: ${giftLabel.name} ${giftLabel.weight})`
          : activeProduct.label,
    });
  };

  const trustChips = [COPY.trustStrip1, COPY.trustStrip2, COPY.trustStrip3, COPY.trustStrip4];

  return (
    <div className="min-h-screen bg-[#faf8f5] pb-24 text-charcoal font-sans md:pb-0">
      {/* Verifiable trust strip — replaces the old rating / units-sold row */}
      <div className="w-full border-b border-primary/20 bg-[#1b261b] px-4 py-2.5 text-[#f2e7d5]">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] font-bold tracking-wide md:px-6 md:text-xs">
          {trustChips.map((chip, i) => (
            <span key={t(chip)} className="flex items-center gap-3">
              {i > 0 && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
              <span>{t(chip)}</span>
            </span>
          ))}
        </div>
      </div>

      {/* ---------------------------------------------------------- 1. HERO */}
      <section className="mx-auto max-w-7xl px-4 pt-8 md:px-8 md:pt-12">
        <div className="grid items-start gap-8 lg:grid-cols-12">
          <div className="space-y-5 lg:col-span-6">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#9b6b1f]">
              {t(COPY.heroEyebrow)}
            </p>
            <h1 className="text-3xl font-black leading-tight tracking-tight text-charcoal md:text-5xl">
              {t(COPY.heroTitle)}
            </h1>
            <p className="text-base font-semibold leading-8 text-charcoal/70 md:text-lg">
              {t(COPY.heroSub)}
            </p>

            {/* price at a glance — so 390px screen 1 answers "how much" */}
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-2xl border border-primary/25 bg-white px-4 py-3">
              <span className="text-sm font-bold text-charcoal/60">
                {lang === 'zh' ? '1 盒 7 袋' : '1 box · 7 sachets'}
              </span>
              <span className="text-lg font-black text-primary">SGD 47.90</span>
              <span className="text-sm font-bold text-charcoal/60">
                {lang === 'zh' ? '2 盒 14 袋' : '2 boxes · 14 sachets'}
              </span>
              <span className="text-lg font-black text-primary">SGD 79.80</span>
              <span className="text-xs font-bold text-charcoal/45">
                {lang === 'zh' ? '（每盒 39.90，含配送）' : '(SGD 39.90 a box, delivery included)'}
              </span>
            </div>

            <button
              type="button"
              onClick={() => openWhatsApp('hero_primary')}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#25D366] px-5 py-4 text-sm font-bold tracking-wide text-white shadow-lg shadow-[#25d366]/20 transition hover:brightness-105 active:scale-[0.99]"
            >
              <MessageCircle fill="currentColor" size={18} />
              <span>{t(COPY.ctaWhatsApp)}</span>
            </button>
          </div>

          <div className="lg:col-span-6">
            <div className="relative aspect-[4/3] overflow-hidden rounded-3xl border border-charcoal/5 bg-white shadow-xl">
              <Image
                src="/proof/product-unboxing-bowl.webp"
                alt={
                  lang === 'zh'
                    ? 'Aqina 纯鸡精盒装、独立小袋与倒出的金汤'
                    : 'Aqina Pure Chicken Essence box, sachet and poured golden broth'
                }
                fill
                priority
                sizes="(max-width: 1024px) 92vw, 46vw"
                className="object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 2. VALUE EQUATION */}
      <section className="mx-auto mt-10 max-w-7xl px-4 md:px-8">
        <div className="rounded-3xl border border-primary/25 bg-white p-6 shadow-lg md:p-8">
          <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.valueTitle)}</h2>
          <p className="mt-2 text-sm font-semibold text-charcoal/60">{t(COPY.valueSubtitle)}</p>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-charcoal/10 bg-[#faf8f5] p-5">
              <p className="text-xs font-bold text-charcoal/50">{VALUE_EQUATION.competitor.brand}</p>
              <p className="mt-1 text-sm font-bold leading-6">
                {t(VALUE_EQUATION.competitor.product)}
              </p>
              <p className="mt-3 text-xs font-semibold text-charcoal/50">
                60g × {VALUE_EQUATION.competitor.sachets} · SGD{' '}
                {VALUE_EQUATION.competitor.packPrice.toFixed(2)}
              </p>
              <p className="mt-1 text-2xl font-black text-charcoal">
                SGD {VALUE_EQUATION.competitor.perSachet.toFixed(2)}
                <span className="ml-1 text-xs font-bold text-charcoal/50">
                  {t(COPY.valuePerSachet)}
                </span>
              </p>
            </div>

            <div className="rounded-2xl border-2 border-primary bg-primary/5 p-5">
              <p className="text-xs font-bold text-primary">Aqina {lang === 'zh' ? '纯鸡精' : 'Pure Chicken Essence'}</p>
              <p className="mt-1 text-sm font-bold leading-6">
                {lang === 'zh' ? '1 盒 · 7 袋 · SGD 47.90' : '1 box · 7 sachets · SGD 47.90'}
              </p>
              <p className="mt-3 text-xs font-semibold text-charcoal/50">60g × 7</p>
              <p className="mt-1 text-2xl font-black text-primary">
                SGD {PER_SACHET.pack1.toFixed(2)}
                <span className="ml-1 text-xs font-bold text-charcoal/50">
                  {t(COPY.valuePerSachet)}
                </span>
              </p>
            </div>

            <div className="rounded-2xl border-2 border-primary bg-primary/5 p-5">
              <p className="text-xs font-bold text-primary">Aqina {lang === 'zh' ? '纯鸡精' : 'Pure Chicken Essence'}</p>
              <p className="mt-1 text-sm font-bold leading-6">
                {lang === 'zh' ? '2 盒 · 14 袋 · SGD 79.80' : '2 boxes · 14 sachets · SGD 79.80'}
              </p>
              <p className="mt-3 text-xs font-semibold text-charcoal/50">60g × 14</p>
              <p className="mt-1 text-2xl font-black text-primary">
                SGD {PER_SACHET.pack2.toFixed(2)}
                <span className="ml-1 text-xs font-bold text-charcoal/50">
                  {t(COPY.valuePerSachet)}
                </span>
              </p>
            </div>
          </div>

          <p className="mt-5 flex gap-2 text-[11px] leading-5 text-charcoal/45">
            <Info size={14} className="mt-0.5 shrink-0" />
            <span>{t(COPY.valueDisclaimer)}</span>
          </p>
        </div>
      </section>

      {/* ------------------------------------------- 3. INTENT ROUTER */}
      <section className="mx-auto mt-12 max-w-7xl px-4 md:px-8">
        <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.intentTitle)}</h2>
        <p className="mt-2 text-sm font-semibold text-charcoal/60">{t(COPY.intentSubtitle)}</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {INTENT_OPTIONS.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => openWhatsApp(`intent_${option.id}`, option.id)}
              className="group flex min-h-[7rem] flex-col justify-between rounded-2xl border-2 border-charcoal/10 bg-white p-5 text-left transition hover:-translate-y-0.5 hover:border-primary hover:shadow-md"
            >
              <span className="text-sm font-black leading-6">{t(option.label)}</span>
              <span className="mt-3 flex items-center gap-1.5 text-xs font-bold text-primary">
                <MessageCircle size={13} />
                {t(option.hint)}
                <ChevronRight size={13} className="transition group-hover:translate-x-0.5" />
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* ------------------------------------------- 4. BUY BOX */}
      {/* id matches the shared Header/Footer "选配套" anchor (Header.tsx:42, Footer.tsx:27) */}
      <section id="offer-reset-products" className="mx-auto mt-12 max-w-7xl px-4 md:px-8">
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-7">
            <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.offersTitle)}</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                {
                  id: 'pack2' as const,
                  title: lang === 'zh' ? '2 盒 · 14 袋' : '2 boxes · 14 sachets',
                  sub: lang === 'zh' ? '每盒 SGD 39.90 + 赠品' : 'SGD 39.90 a box + gift',
                  price: 'SGD 79.80',
                },
                {
                  id: 'pack1' as const,
                  title: lang === 'zh' ? '1 盒 · 7 袋' : '1 box · 7 sachets',
                  sub: lang === 'zh' ? '先试口感' : 'Try the taste first',
                  price: 'SGD 47.90',
                },
              ].map((pack) => (
                <button
                  key={pack.id}
                  type="button"
                  onClick={() => setActiveTab(pack.id)}
                  className={`relative flex flex-col justify-between rounded-2xl border-2 p-4 text-left transition ${
                    activeTab === pack.id
                      ? 'border-primary bg-primary/5 ring-4 ring-primary/5'
                      : 'border-charcoal/10 bg-white hover:border-charcoal/30'
                  }`}
                >
                  <span className="text-sm font-black">{pack.title}</span>
                  <span className="mt-1 text-xs text-charcoal/60">{pack.sub}</span>
                  <span className="mt-3 text-sm font-black text-primary">{pack.price}</span>
                </button>
              ))}
            </div>

            {activeTab === 'pack2' && (
              <div className="space-y-3 rounded-2xl border border-charcoal/5 bg-white p-5">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-primary">
                  <Gift size={14} />
                  <span>{t(COPY.giftsTitle)}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                  {GIFT_OPTIONS.map((gift) => (
                    <button
                      key={gift.value}
                      type="button"
                      onClick={() => setSelectedGift(gift.value)}
                      className={`overflow-hidden rounded-xl border-2 text-left transition ${
                        selectedGift === gift.value
                          ? 'border-primary ring-2 ring-primary/20'
                          : 'border-charcoal/10 hover:border-charcoal/30'
                      }`}
                    >
                      <div className="relative aspect-square bg-[#f8ecd5]">
                        <Image
                          src={gift.image}
                          alt={`${gift.name} ${gift.weight}`}
                          fill
                          sizes="(max-width: 640px) 45vw, 15vw"
                          className="object-cover"
                        />
                        {selectedGift === gift.value && (
                          <span className="absolute right-1.5 top-1.5 rounded-full bg-primary p-1 text-charcoal-dark">
                            <Check size={11} strokeWidth={3} />
                          </span>
                        )}
                      </div>
                      <div className="p-2">
                        <p className="text-[10px] font-black leading-tight">{gift.name}</p>
                        <p className="text-[10px] font-bold text-primary">{gift.weight}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-5">
            <div className="space-y-4 rounded-3xl border border-charcoal/5 bg-white p-6 shadow-xl md:p-7">
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-bold text-charcoal/55">
                  {activeTab === 'pack1'
                    ? lang === 'zh'
                      ? '1 盒 · 7 袋'
                      : '1 box · 7 sachets'
                    : lang === 'zh'
                      ? '2 盒 · 14 袋'
                      : '2 boxes · 14 sachets'}
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-xs font-bold text-primary">SGD</span>
                  <span className="text-3xl font-black text-primary">{activePrice.toFixed(2)}</span>
                </div>
              </div>

              <ul className="space-y-2 border-t border-charcoal/5 pt-4 text-xs font-semibold text-charcoal/65">
                {[
                  lang === 'zh' ? '新加坡现货，2–3 天冷链送达' : 'Singapore stock, 2–3 day cold-chain delivery',
                  lang === 'zh' ? '配送已含在价格内' : 'Delivery already included in the price',
                  lang === 'zh'
                    ? 'PayNow 转账给 Boong Poultry Pte Ltd，真人核对'
                    : 'PayNow to Boong Poultry Pte Ltd, checked by a real person',
                ].map((line) => (
                  <li key={line} className="flex gap-2">
                    <Check size={14} className="mt-0.5 shrink-0 text-primary" />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>

              <div className="space-y-3 pt-1">
                <button
                  type="button"
                  onClick={() => openWhatsApp('buybox_whatsapp')}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#25D366] py-4 text-sm font-bold tracking-wide text-white shadow-lg shadow-[#25d366]/20 transition hover:brightness-105 active:scale-[0.99]"
                >
                  <MessageCircle fill="currentColor" size={18} />
                  <span>{t(COPY.ctaWhatsApp)}</span>
                </button>
                <button
                  type="button"
                  onClick={() => handlePayNowSubmit('buybox_paynow')}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-charcoal py-4 text-sm font-bold text-ivory transition hover:bg-primary hover:text-charcoal-dark active:scale-[0.99]"
                >
                  <QrCode size={17} />
                  <span>{t(COPY.ctaPayNow)}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 5. THREE CONCERNS */}
      <section className="mt-16 border-y border-charcoal/5 bg-white py-14 md:py-16">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.concernsTitle)}</h2>
          <p className="mt-2 text-sm font-semibold text-charcoal/60">{t(COPY.concernsSubtitle)}</p>
          <div className="mt-7 grid gap-4 md:grid-cols-3">
            {CONCERNS.map((concern) => (
              <article
                key={concern.id}
                className="flex flex-col rounded-2xl border border-charcoal/10 bg-[#faf8f5] p-6"
              >
                <h3 className="text-lg font-black text-charcoal">{t(concern.question)}</h3>
                <p className="mt-3 flex-1 text-sm leading-7 text-charcoal/70">{t(concern.answer)}</p>
                {concern.note && (
                  <p className="mt-4 border-t border-charcoal/10 pt-3 text-xs font-semibold leading-6 text-[#9b6b1f]">
                    {t(concern.note)}
                  </p>
                )}
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 6. SOURCE & PROCESS */}
      <section className="py-14 md:py-16">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="grid gap-8 lg:grid-cols-12 lg:items-start">
            <div className="lg:col-span-7">
              <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.sourceTitle)}</h2>
              <p className="mt-2 text-sm font-semibold text-charcoal/60">{t(COPY.sourceSubtitle)}</p>

              <ol className="mt-6 space-y-4">
                {SOURCE_CHAIN.map((step, i) => (
                  <li key={step.id} className="flex gap-4">
                    <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-black text-charcoal-dark">
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-sm font-black text-charcoal">{t(step.title)}</p>
                      <p className="mt-1 text-sm leading-7 text-charcoal/70">{t(step.body)}</p>
                    </div>
                  </li>
                ))}
              </ol>

              <p className="mt-6 rounded-2xl border border-[#9b6b1f]/25 bg-[#fffaf1] p-4 text-sm font-bold leading-7 text-[#9b6b1f]">
                {t(COPY.notPineappleFlavour)}
              </p>

              <div className="mt-6">
                <p className="text-xs font-black uppercase tracking-wider text-charcoal/45">
                  {t(COPY.nutritionTitle)}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {NUTRITION_FACTS.map((fact) => (
                    <span
                      key={t(fact)}
                      className="rounded-full border border-charcoal/10 bg-white px-3 py-1.5 text-xs font-bold text-charcoal/70"
                    >
                      {t(fact)}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-4 lg:col-span-5">
              <div className="relative aspect-[4/3] overflow-hidden rounded-3xl border border-charcoal/5 shadow-lg">
                <Image
                  src="/proof/pineapple-chicken-story.webp"
                  alt={lang === 'zh' ? 'MD2 黄梨酵素鸡与产品场景' : 'MD2 pineapple enzyme chicken and the product'}
                  fill
                  sizes="(max-width: 1024px) 92vw, 38vw"
                  className="object-cover"
                />
              </div>
              <div className="relative aspect-[4/3] overflow-hidden rounded-3xl border border-charcoal/5 shadow-lg">
                <Image
                  src="/proof/pack-detail-single-origin.webp"
                  alt={lang === 'zh' ? '包装上的 Single Origin 字样' : 'The "Single Origin" wording on the pack'}
                  fill
                  sizes="(max-width: 1024px) 92vw, 38vw"
                  className="object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 7. RHYTHM & BUDGET */}
      <section className="border-y border-charcoal/5 bg-white py-14 md:py-16">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="grid gap-8 lg:grid-cols-12 lg:items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-extrabold uppercase tracking-wider text-primary">
                <CalendarDays size={12} />
                <span>{lang === 'zh' ? '用量节奏' : 'How much you need'}</span>
              </div>
              <h2 className="mt-4 text-2xl font-black tracking-tight md:text-3xl">
                {t(COPY.rhythmTitle)}
              </h2>
              <p className="mt-2 text-sm font-semibold leading-7 text-charcoal/60">
                {t(COPY.rhythmSubtitle)}
              </p>

              <div className="mt-6 overflow-hidden rounded-2xl border border-charcoal/10">
                {RHYTHM_ROWS.map((row, i) => (
                  <div
                    key={t(row.stage)}
                    className={`grid grid-cols-3 items-center gap-2 px-5 py-4 text-sm ${
                      i % 2 ? 'bg-[#faf8f5]' : 'bg-white'
                    }`}
                  >
                    <span className="font-bold text-charcoal">{t(row.stage)}</span>
                    <span className="text-center font-semibold text-charcoal/60">{t(row.days)}</span>
                    <span className="text-right">
                      <span className="block text-base font-black text-primary">
                        {t(row.boxes)}
                      </span>
                      {row.note && (
                        <span className="block text-[11px] font-semibold text-charcoal/45">
                          {t(row.note)}
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>

              <p className="mt-5 text-sm leading-7 text-charcoal/60">{t(COPY.rhythmBudget)}</p>

              <button
                type="button"
                onClick={() => openWhatsApp('rhythm_cta', 'confinement')}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-[#25D366] px-5 py-4 text-sm font-bold text-white shadow-lg shadow-[#25d366]/20 transition hover:brightness-105 active:scale-[0.99] sm:w-auto"
              >
                <MessageCircle fill="currentColor" size={18} />
                <span>{t(COPY.rhythmCta)}</span>
              </button>
            </div>

            <div className="lg:col-span-5">
              <div className="relative aspect-[4/5] overflow-hidden rounded-3xl border border-charcoal/5 shadow-lg">
                <Image
                  src="/proof/scene-family-handover.webp"
                  alt={lang === 'zh' ? '家人递上一袋纯鸡精' : 'Handing a sachet to family'}
                  fill
                  sizes="(max-width: 1024px) 92vw, 38vw"
                  className="object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 8. GOLDEN STOCK / COOKING */}
      <section className="py-14 md:py-16">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="grid gap-8 lg:grid-cols-12 lg:items-center">
            <div className="lg:col-span-5">
              <div className="relative aspect-[4/3] overflow-hidden rounded-3xl border border-charcoal/5 shadow-lg">
                <Image
                  src="/proof/golden-broth-macro.webp"
                  alt={lang === 'zh' ? '金黄色鸡精汤微距' : 'Macro of the golden broth'}
                  fill
                  sizes="(max-width: 1024px) 92vw, 38vw"
                  className="object-cover"
                />
              </div>
            </div>
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-extrabold uppercase tracking-wider text-primary">
                <Utensils size={12} />
                <span>{lang === 'zh' ? '黄金原汤' : 'Golden stock'}</span>
              </div>
              <h2 className="mt-4 text-2xl font-black tracking-tight md:text-3xl">
                {t(COPY.cookingTitle)}
              </h2>
              <p className="mt-3 text-sm leading-7 text-charcoal/70">{t(COPY.cookingBody)}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                {COOKING_USES.map((use) => (
                  <span
                    key={t(use)}
                    className="rounded-full border border-charcoal/10 bg-white px-4 py-2 text-sm font-bold text-charcoal/75"
                  >
                    {t(use)}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 9. SELLER IDENTITY */}
      <section className="border-y border-charcoal/5 bg-white py-14 md:py-16">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs font-extrabold uppercase tracking-wider text-primary">
            <Building2 size={12} />
            <span>{lang === 'zh' ? '卖家资料' : 'Seller details'}</span>
          </div>
          <h2 className="mt-4 text-2xl font-black tracking-tight md:text-3xl">
            {t(COPY.identityTitle)}
          </h2>
          <p className="mt-2 max-w-3xl text-sm font-semibold leading-7 text-charcoal/60">
            {t(COPY.identitySubtitle)}
          </p>

          <div className="mt-7 grid gap-6 lg:grid-cols-12">
            <div className="overflow-hidden rounded-2xl border border-charcoal/10 lg:col-span-7">
              {SELLER_IDENTITY.map((row, i) => (
                <div
                  key={t(row.label)}
                  className={`grid gap-1 px-5 py-4 sm:grid-cols-[10rem_1fr] sm:gap-4 ${
                    i % 2 ? 'bg-[#faf8f5]' : 'bg-white'
                  }`}
                >
                  <span className="text-xs font-black uppercase tracking-wider text-charcoal/45">
                    {t(row.label)}
                  </span>
                  <span className="text-sm font-bold leading-6 text-charcoal">{t(row.value)}</span>
                </div>
              ))}
            </div>

            <div className="lg:col-span-5">
              <div className="rounded-2xl border border-charcoal/10 bg-[#faf8f5] p-5">
                <div className="relative mx-auto aspect-square w-full max-w-[15rem] overflow-hidden rounded-xl bg-white">
                  <Image
                    src="/paynow/aqina-paynow-qr-designed.png"
                    alt="Boong Poultry Pte Ltd PayNow QR"
                    fill
                    sizes="15rem"
                    className="object-contain p-2"
                  />
                </div>
                <p className="mt-4 flex gap-2 text-xs font-semibold leading-6 text-charcoal/60">
                  <ShieldCheck size={14} className="mt-0.5 shrink-0 text-primary" />
                  <span>{t(COPY.identityPaynowNote)}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 10. PROOF */}
      <section className="py-14 md:py-16">
        <div className="mx-auto max-w-7xl px-4 md:px-8">
          <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.proofTitle)}</h2>
          <p className="mt-2 text-sm font-semibold text-charcoal/60">{t(COPY.proofSubtitle)}</p>

          <p className="mt-5 text-xs font-black uppercase tracking-wider text-charcoal/45">
            {t(COPY.proofProductHeading)}
          </p>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {PROOF_PRODUCT.map((item) => (
              <figure
                key={item.src}
                className="overflow-hidden rounded-2xl border border-charcoal/5 bg-white shadow-sm"
              >
                <div className="relative aspect-[4/3]">
                  <Image
                    src={item.src}
                    alt={t(item.alt)}
                    fill
                    sizes="(max-width: 640px) 92vw, (max-width: 1024px) 45vw, 30vw"
                    className="object-cover"
                  />
                </div>
                <figcaption className="p-4 text-xs font-semibold leading-6 text-charcoal/70">
                  {t(item.caption)}
                </figcaption>
              </figure>
            ))}
          </div>

          <p className="mt-10 text-xs font-black uppercase tracking-wider text-charcoal/45">
            {t(COPY.proofSceneHeading)}
          </p>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {PROOF_SCENES.map((item) => (
              <figure
                key={item.src}
                className="overflow-hidden rounded-2xl border border-charcoal/5 bg-white shadow-sm"
              >
                <div className="relative aspect-[4/5]">
                  <Image
                    src={item.src}
                    alt={t(item.alt)}
                    fill
                    sizes="(max-width: 640px) 92vw, 23vw"
                    className="object-cover"
                  />
                </div>
                <figcaption className="p-4 text-xs font-semibold leading-6 text-charcoal/70">
                  {t(item.caption)}
                </figcaption>
              </figure>
            ))}
          </div>

          <p className="mt-8 max-w-3xl rounded-2xl border border-charcoal/10 bg-white p-5 text-sm leading-7 text-charcoal/65">
            {t(COPY.proofHonesty)}
          </p>
        </div>
      </section>

      {/* ------------------------------------------- 11. FAQ */}
      <section className="border-t border-charcoal/5 bg-white py-14 md:py-16">
        <div className="mx-auto max-w-3xl px-4 md:px-8">
          <h2 className="text-center text-2xl font-black tracking-tight md:text-3xl">
            {t(COPY.faqTitle)}
          </h2>
          <div className="mt-8 space-y-4">
            {FAQ_ITEMS.map((item) => (
              <div key={t(item.q)} className="rounded-2xl border border-charcoal/5 bg-[#faf8f5] p-5">
                <div className="flex items-start gap-2.5">
                  <HelpCircle className="mt-0.5 shrink-0 text-primary" size={18} />
                  <h3 className="text-base font-extrabold text-charcoal">{t(item.q)}</h3>
                </div>
                <p className="mt-2 pl-7 text-sm leading-7 text-charcoal/70">{t(item.a)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------- 12. FINAL CTA + MEDICAL BOUNDARY */}
      <section className="py-14 md:py-16">
        <div className="mx-auto max-w-4xl px-4 md:px-8">
          <div className="rounded-3xl border border-primary/25 bg-white p-6 text-center shadow-lg md:p-8">
            <h2 className="text-2xl font-black tracking-tight md:text-3xl">{t(COPY.intentTitle)}</h2>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => openWhatsApp('final_whatsapp')}
                className="flex items-center justify-center gap-2 rounded-2xl bg-[#25D366] px-5 py-4 text-sm font-bold text-white shadow-lg shadow-[#25d366]/20 transition hover:brightness-105 active:scale-[0.99]"
              >
                <MessageCircle fill="currentColor" size={18} />
                <span>{t(COPY.ctaWhatsApp)}</span>
              </button>
              <button
                type="button"
                onClick={() => handlePayNowSubmit('final_paynow')}
                className="flex items-center justify-center gap-2 rounded-2xl bg-charcoal px-5 py-4 text-sm font-bold text-ivory transition hover:bg-primary hover:text-charcoal-dark active:scale-[0.99]"
              >
                <QrCode size={17} />
                <span>{t(COPY.ctaPayNow)}</span>
              </button>
            </div>
          </div>

          {/* Medical boundary — always visible, desktop and mobile */}
          <p className="mt-6 flex gap-2 rounded-2xl border border-charcoal/10 bg-[#faf8f5] p-5 text-xs leading-6 text-charcoal/60">
            <ShieldCheck size={15} className="mt-0.5 shrink-0 text-primary" />
            <span>{t(MEDICAL_BOUNDARY)}</span>
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-[11px] font-bold text-charcoal/45">
            <span className="flex items-center gap-1.5">
              <Award size={12} className="text-primary" /> JAKIM Halal · SFA · HACCP · GMP
            </span>
            <span className="flex items-center gap-1.5">
              <Truck size={12} className="text-primary" />
              {lang === 'zh' ? '新加坡 2–3 天冷链' : 'Singapore 2–3 day cold chain'}
            </span>
          </div>
        </div>
      </section>

      {/* ------------------------------------------- STICKY BAR (mobile) */}
      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-charcoal/10 bg-white/95 px-3 py-2.5 shadow-[0_-8px_24px_rgba(0,0,0,0.08)] backdrop-blur md:hidden">
        <div className="flex items-center gap-3">
          <div className="shrink-0">
            <p className="text-[10px] font-bold leading-none text-charcoal/50">
              {activeTab === 'pack1' ? (lang === 'zh' ? '1 盒' : '1 box') : t(COPY.stickyPrefix)}
            </p>
            <p className="text-lg font-black leading-tight text-primary">
              SGD {activePrice.toFixed(2)}
            </p>
          </div>
          <button
            type="button"
            onClick={() => openWhatsApp('sticky_whatsapp')}
            className="flex min-h-12 flex-1 items-center justify-center gap-2 rounded-xl bg-[#25D366] text-sm font-bold text-white active:scale-[0.99]"
          >
            <MessageCircle fill="currentColor" size={17} />
            <span>{t(COPY.ctaWhatsApp)}</span>
          </button>
        </div>
      </div>

      {activeProduct && (
        <CheckoutModal isOpen={isCheckoutOpen} onClose={closeCheckout} product={selectedProduct} />
      )}
    </div>
  );
}
