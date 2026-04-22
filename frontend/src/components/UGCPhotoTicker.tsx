'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BadgeCheck } from 'lucide-react';

interface TickerItem {
  caption: string;
}

const photoSources = [
  '/ugc/morning-kitchen.jpg',
  '/ugc/cozy-sofa.jpg',
  '/ugc/office-corner.jpg',
  '/ugc/home-study.jpg',
  '/ugc/yoga-studio.jpg',
] as const;

function parseTickerItems(input: unknown): TickerItem[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input
    .map((item) => {
      if (typeof item !== 'object' || !item) {
        return null;
      }
      const caption = 'caption' in item && typeof item.caption === 'string' ? item.caption : '';
      return caption ? { caption } : null;
    })
    .filter((item): item is TickerItem => item !== null);
}

export default function UGCPhotoTicker() {
  const t = useTranslations('Index.marketing.ugcTicker');
  const tickerItems = parseTickerItems(t.raw('items'));
  const merged = tickerItems.slice(0, photoSources.length).map((item, index) => ({
    ...item,
    src: photoSources[index],
  }));
  const loopItems = [...merged, ...merged];

  return (
    <section className="py-8" id="ugc-photo-ticker">
      <div className="section-shell space-y-4">
        <div className="space-y-2 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.26em] text-primary">{t('eyebrow')}</p>
          <h2 className="font-heading text-4xl font-semibold text-text-light md:text-5xl">{t('title')}</h2>
        </div>

        <div className="ugc-ticker-shell">
          <div className="ugc-ticker-track">
            {loopItems.map((item, index) => (
              <article
                key={`${item.caption}-${index}`}
                className="surface-panel min-w-[17rem] overflow-hidden rounded-2xl border border-primary/20"
              >
                <div className="relative aspect-[4/3]">
                  <Image
                    src={item.src}
                    alt={item.caption}
                    fill
                    sizes="(max-width: 768px) 70vw, 24vw"
                    className="object-cover"
                  />
                  <div className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-emerald-500/90 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-white">
                    <BadgeCheck size={12} />
                    <span>{t('verified')}</span>
                  </div>
                </div>
                <div className="px-4 py-3 text-sm font-medium text-text-light/88">{item.caption}</div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
