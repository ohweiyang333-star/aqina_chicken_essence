'use client';

import dynamic from 'next/dynamic';
import Image from 'next/image';
import { MessageCircle, QrCode } from 'lucide-react';
import { useLocale } from 'next-intl';
import { useState } from 'react';
import Footer from '@/components/Footer';
import {
  OFFER_RESET_GIFTS,
  OFFER_RESET_PRODUCTS,
  getOfferResetCopy,
  getOfferResetWhatsAppMessage,
  normalizeOfferResetLocale,
  type OfferResetLocale,
} from '@/lib/offer-reset-content';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';
import type { DisplayProduct } from '@/lib/product-display';
import { getWhatsAppHref } from '@/lib/site-config';

const CheckoutModal = dynamic(() => import('@/components/CheckoutModal'), {
  ssr: false,
});

const primaryProduct = OFFER_RESET_PRODUCTS.find((product) => product.id === 'pack2') ?? OFFER_RESET_PRODUCTS[0];

export default function OfferResetLandingPage() {
  const locale = useLocale();
  const safeLocale = normalizeOfferResetLocale(locale);
  const copy = getOfferResetCopy(locale);
  const [selectedProduct, setSelectedProduct] = useState<DisplayProduct | null>(null);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const whatsappHref = getWhatsAppHref(getOfferResetWhatsAppMessage(locale));

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
            <p className="text-xs font-black uppercase tracking-[0.22em] text-[#9b6b1f]">
              {copy.heroEyebrow}
            </p>
            <h1 className="max-w-3xl text-4xl font-black leading-tight tracking-normal text-[#23170d] md:text-6xl">
              {copy.heroTitle}
            </h1>
            <p className="max-w-2xl text-lg font-semibold leading-8 text-[#5f492f]">
              {copy.heroBody}
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <a
                id="offer-reset-hero-whatsapp-cta"
                href={whatsappHref}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => trackWhatsApp('offer_reset_hero')}
                className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#25d366] px-5 text-center text-sm font-black text-white shadow-[0_18px_36px_rgba(37,211,102,0.24)] transition hover:-translate-y-0.5"
              >
                <MessageCircle size={19} />
                <span>{copy.primaryCta}</span>
              </a>
              <button
                id="offer-reset-hero-paynow-cta"
                type="button"
                onClick={() => openCheckout(primaryProduct)}
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
              <article
                key={title}
                className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_14px_34px_rgba(91,57,24,0.07)]"
              >
                <div className="relative aspect-[4/3] bg-[#f8ecd5]">
                  <Image
                    src={src}
                    alt={title}
                    fill
                    sizes="(max-width: 768px) 92vw, 31vw"
                    className="object-cover"
                  />
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
              <article
                key={product.id}
                className="rounded-lg border border-[#d8b774] bg-white p-5 shadow-[0_16px_38px_rgba(91,57,24,0.08)]"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.16em] text-[#9b6b1f]">
                      {product.badge}
                    </p>
                    <h3 className="mt-2 text-2xl font-black">{product.name}</h3>
                    <p className="mt-1 text-sm font-semibold text-[#6f5a43]">{product.label}</p>
                  </div>
                  <p className="text-3xl font-black">SGD {product.price.toFixed(2)}</p>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <a
                    href={getWhatsAppHref(
                      getOfferResetWhatsAppMessage(locale, product.id === 'pack2' ? 'pack2' : 'pack1'),
                    )}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => trackWhatsApp(`offer_reset_${product.id}`)}
                    className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-[#25d366] px-4 text-center text-sm font-black text-white"
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
              <article
                key={gift.id}
                className="overflow-hidden rounded-lg border border-[#dcc08c] bg-white shadow-[0_12px_28px_rgba(91,57,24,0.08)]"
              >
                <div className="relative aspect-square bg-[#f8ecd5]">
                  <Image
                    src={gift.image}
                    alt={gift.alt[safeLocale]}
                    fill
                    sizes="(max-width: 768px) 45vw, 18vw"
                    className="object-cover"
                  />
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
              className="inline-flex min-h-14 items-center justify-center gap-2 rounded-lg bg-[#25d366] px-5 text-sm font-black text-white"
            >
              <MessageCircle size={19} />
              <span>{copy.primaryCta}</span>
            </a>
            <button
              id="offer-reset-final-paynow-cta"
              type="button"
              onClick={() => openCheckout(primaryProduct)}
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

function getOfferResetQa(locale: OfferResetLocale) {
  return locale === 'zh'
    ? [
        {
          question: '为什么比普通瓶装鸡精贵？',
          answer:
            'Aqina 纯鸡精走的是来源、原料和工艺路线：Aqina farm、MD2 黄梨酵素鸡、7天慢炼和纯鸡精小袋，不是最低价瓶装鸡精比较。',
        },
        {
          question: '黄梨鸡是不是黄梨味？',
          answer: '不是黄梨口味。黄梨酵素鸡指的是使用 MD2 Pineapple Enzyme 饲养路线的鸡只。',
        },
        {
          question: '第一次买 1盒还是 2盒？',
          answer:
            '想先试口感可以选 1盒。已经决定认真喝或买给家人，2盒等于每盒 SGD39.90，并送 French Poulet Cut Part 五选一。',
        },
        {
          question: '2盒送什么？',
          answer:
            '2盒送 1包 French Poulet Cut Part，五选一：3 Joint Wing、Minced、Boneless Breast、Whole Leg、Half Chicken Cut 4 Pieces。',
        },
        {
          question: '有特殊健康状况可以喝吗？',
          answer:
            'Aqina 纯鸡精是日常食品滋养，不替代医疗建议。有特殊健康状况、孕产或治疗中的顾客，请先咨询医生或 WhatsApp 真人客服。',
        },
      ]
    : [
        {
          question: 'Why is it more expensive than ordinary bottled chicken essence?',
          answer:
            'Aqina is positioned around source, ingredient, and process: Aqina farm, MD2 pineapple chicken, 7-day slow extraction, and pure chicken essence sachets, not the lowest-price bottled category.',
        },
        {
          question: 'Is pineapple chicken pineapple-flavored?',
          answer: 'No. Pineapple Chicken refers to the MD2 Pineapple Enzyme feeding route, not a pineapple flavor.',
        },
        {
          question: 'Should I start with 1 box or 2 boxes?',
          answer:
            'Choose 1 box to try the taste first. Choose 2 boxes if you are ready to start seriously or buying for family, with SGD39.90 per box and one French Poulet Cut Part gift choice.',
        },
        {
          question: 'What gift comes with 2 boxes?',
          answer:
            '2 boxes include one French Poulet Cut Part gift choice: 3 Joint Wing, Minced, Boneless Breast, Whole Leg, or Half Chicken Cut 4 Pieces.',
        },
        {
          question: 'Can customers with special health conditions drink it?',
          answer:
            'Aqina Pure Chicken Essence is a food nourishment product and does not replace medical advice. Customers with special conditions, pregnancy, or treatment should ask a doctor or WhatsApp support first.',
        },
      ];
}
