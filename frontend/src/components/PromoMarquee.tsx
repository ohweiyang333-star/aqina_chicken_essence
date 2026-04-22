'use client';

import { useTranslations } from 'next-intl';
import { BadgeCheck } from 'lucide-react';

const LOOP_SEGMENTS = 6;

export default function PromoMarquee() {
  const t = useTranslations('Index.marketing.marquee');
  const rawItems = t.raw('items');
  const items = Array.isArray(rawItems)
    ? rawItems.filter((item): item is string => typeof item === 'string')
    : [];

  return (
    <section
      id="promo-marquee"
      aria-label={t('ariaLabel')}
      className="relative z-30 mt-16 border-y border-[#f3bf2f]/28 bg-[linear-gradient(180deg,#1c210f_0%,#141f10_100%)]"
    >
      <div className="promo-marquee-shell">
        <div className="promo-marquee-loop" aria-hidden="true">
          {Array.from({ length: LOOP_SEGMENTS }).map((_, loopIndex) => (
            <div key={loopIndex} className="promo-marquee-segment">
              {items.map((item, index) => (
                <div
                  key={`${loopIndex}-${item}-${index}`}
                  className="inline-flex items-center gap-2 rounded-full border border-[#f3bf2f]/40 bg-[linear-gradient(180deg,rgba(255,203,55,0.2),rgba(255,184,0,0.08))] px-4 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[#ffe9a6]"
                >
                  <BadgeCheck size={13} className="text-[#ffc929]" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
