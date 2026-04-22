'use client';

import { useTranslations } from 'next-intl';
import { BadgeCheck } from 'lucide-react';

export default function PromoMarquee() {
  const t = useTranslations('Index.marketing.marquee');
  const rawItems = t.raw('items');
  const items = Array.isArray(rawItems)
    ? rawItems.filter((item): item is string => typeof item === 'string')
    : [];
  const tickerItems = [...items, ...items];

  return (
    <section
      id="promo-marquee"
      aria-label={t('ariaLabel')}
      className="relative z-30 mt-16 border-y border-primary/20 bg-background-dark/90"
    >
      <div className="promo-marquee-shell">
        <div className="promo-marquee-track">
          {tickerItems.map((item, index) => (
            <div
              key={`${item}-${index}`}
              className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-surface/80 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-text-light"
            >
              <BadgeCheck size={14} className="text-secondary" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
