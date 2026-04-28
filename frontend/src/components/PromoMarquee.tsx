'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BadgeCheck, Sparkles } from 'lucide-react';
import { withImageVersion } from '@/lib/image-utils';

const LOOP_SEGMENTS = 4;

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
      className="relative z-30 mt-16 overflow-hidden border-y border-[#f3bf2f]/28 bg-[linear-gradient(180deg,#272005_0%,#141f10_100%)]"
    >
      <div className="absolute inset-y-0 left-0 w-56 bg-[radial-gradient(circle_at_left,rgba(255,205,63,0.28),transparent_72%)]" />
      <div className="section-shell pointer-events-none absolute inset-y-0 left-0 right-0 z-[5] hidden items-center lg:flex">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#ffd36a]/40 bg-[#30240c]/85 px-3 py-1 text-[10px] font-bold tracking-[0.08em] text-[#ffe9a6]">
          <Sparkles size={12} />
          <span>{t('badge')}</span>
        </div>
      </div>

      <div className="promo-marquee-shell">
        <div className="promo-marquee-loop" aria-hidden="true">
          {Array.from({ length: LOOP_SEGMENTS }).map((_, loopIndex) => (
            <div key={loopIndex} className="promo-marquee-segment">
              <div className="promo-chip relative hidden h-8 w-8 overflow-hidden rounded-full border border-[#ffd36a]/40 bg-white/95 lg:block">
                <Image src={withImageVersion('/images/pack-1.webp')} alt="Aqina Product" fill sizes="32px" className="object-cover" />
              </div>
              {items.map((item, index) => (
                <div
                  key={`${loopIndex}-${item}-${index}`}
                  className="promo-chip inline-flex items-center gap-2 whitespace-nowrap rounded-full border border-[#f3bf2f]/40 bg-[linear-gradient(180deg,rgba(255,203,55,0.24),rgba(255,184,0,0.12))] px-4 py-2 text-[11px] font-semibold tracking-[0.06em] text-[#ffe9a6]"
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
