'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BadgeCheck } from 'lucide-react';

interface TickerItem {
  caption: string;
  src: string;
}

const fallbackPhotoSources = [
  '/ugc/sg-middle-aged-chinese-man.webp',
  '/ugc/sg-middle-aged-malay-woman.webp',
  '/ugc/sg-teenage-chinese-student.webp',
  '/ugc/sg-young-chinese-woman-campus.webp',
  '/ugc/sg-young-indian-office-man.webp',
  '/ugc/sg-young-indian-home-woman.webp',
  '/ugc/sg-young-malay-man-park.webp',
  '/ugc/sg-young-fitness-woman.webp',
  '/ugc/sg-elderly-chinese-woman.webp',
  '/ugc/sg-older-malay-man.webp',
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
      const src = 'src' in item && typeof item.src === 'string' ? item.src : '';
      if (!caption) {
        return null;
      }
      return {
        caption,
        src,
      };
    })
    .filter((item): item is TickerItem => item !== null);
}

export default function UGCPhotoTicker() {
  const t = useTranslations('Index.marketing.ugcTicker');
  const tickerItems = parseTickerItems(t.raw('items'));
  const merged = tickerItems.map((item, index) => ({
    caption: item.caption,
    src: item.src || fallbackPhotoSources[index % fallbackPhotoSources.length],
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
