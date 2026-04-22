'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BadgeCheck, MessageCircle, Star } from 'lucide-react';

interface UGCReview {
  name: string;
  persona: string;
  source: string;
  content: string;
}

const reviewVisuals = [
  { src: '/ugc/morning-kitchen.jpg', objectPosition: 'object-center' },
  { src: '/ugc/cozy-sofa.jpg', objectPosition: 'object-center' },
  { src: '/ugc/office-corner.jpg', objectPosition: 'object-center' },
  { src: '/ugc/home-study.jpg', objectPosition: 'object-center' },
  { src: '/ugc/yoga-studio.jpg', objectPosition: 'object-center' },
  { src: '/ugc/morning-kitchen.jpg', objectPosition: 'object-left' },
] as const;

function parseReviews(input: unknown): UGCReview[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input
    .map((item) => {
      if (typeof item !== 'object' || !item) {
        return null;
      }

      const name = 'name' in item && typeof item.name === 'string' ? item.name : '';
      const persona = 'persona' in item && typeof item.persona === 'string' ? item.persona : '';
      const source = 'source' in item && typeof item.source === 'string' ? item.source : '';
      const content = 'content' in item && typeof item.content === 'string' ? item.content : '';

      if (!name || !persona || !source || !content) {
        return null;
      }

      return { name, persona, source, content };
    })
    .filter((item): item is UGCReview => item !== null);
}

export default function UGCReviewGrid() {
  const t = useTranslations('Index.marketing.ugcReviews');
  const reviews = parseReviews(t.raw('items'));

  return (
    <section className="py-12" id="ugc-reviews">
      <div className="section-shell space-y-5">
        <div className="space-y-2 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.26em] text-primary">{t('eyebrow')}</p>
          <h2 className="font-heading text-4xl font-semibold text-text-light md:text-5xl">{t('title')}</h2>
          <p className="mx-auto max-w-3xl text-sm leading-7 text-muted md:text-base">{t('subtitle')}</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {reviews.slice(0, 6).map((review, index) => {
            const visual = reviewVisuals[index] ?? reviewVisuals[0];

            return (
              <article key={`${review.name}-${review.source}-${index}`} className="surface-panel rounded-2xl p-4">
                <div className="relative mb-4 aspect-[16/10] overflow-hidden rounded-xl">
                  <Image
                    src={visual.src}
                    alt={`${review.name} review`}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
                    className={`object-cover ${visual.objectPosition}`}
                  />
                  <div className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-emerald-500/90 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white">
                    <BadgeCheck size={12} />
                    <span>{t('verified')}</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-1 text-amber-300">
                    {Array.from({ length: 5 }).map((_, starIndex) => (
                      <Star key={starIndex} size={14} className="fill-amber-300" />
                    ))}
                  </div>

                  <p className="text-sm leading-7 text-text-light/86">“{review.content}”</p>

                  <div className="gold-divider" />

                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-text-light">{review.name}</p>
                      <p className="text-xs text-muted">{review.persona}</p>
                    </div>

                    <div className="inline-flex items-center gap-1 rounded-full border border-primary/22 bg-background-dark/52 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-primary">
                      <MessageCircle size={11} />
                      <span>{review.source}</span>
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
