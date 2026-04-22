'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { MessageCircle } from 'lucide-react';

interface UGCReview {
  name: string;
  persona: string;
  source: string;
  content: string;
  image?: string;
}

const reviewVisuals = [
  { src: '/ugc/sg-young-chinese-woman-campus.webp', objectPosition: 'object-center' },
  { src: '/ugc/sg-middle-aged-chinese-man.webp', objectPosition: 'object-center' },
  { src: '/ugc/sg-elderly-chinese-woman.webp', objectPosition: 'object-center' },
] as const;

function parseReviews(input: unknown): UGCReview[] {
  if (!Array.isArray(input)) {
    return [];
  }

  const parsed: UGCReview[] = [];

  for (const item of input) {
    if (typeof item !== 'object' || !item) {
      continue;
    }

    const name = 'name' in item && typeof item.name === 'string' ? item.name : '';
    const persona = 'persona' in item && typeof item.persona === 'string' ? item.persona : '';
    const source = 'source' in item && typeof item.source === 'string' ? item.source : '';
    const content = 'content' in item && typeof item.content === 'string' ? item.content : '';
    const image = 'image' in item && typeof item.image === 'string' ? item.image : undefined;

    if (!name || !persona || !source || !content) {
      continue;
    }

    parsed.push({ name, persona, source, content, image });
  }

  return parsed;
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

        <div className="grid gap-4 lg:grid-cols-3">
          {reviews.slice(0, 3).map((review, index) => {
            const visual = reviewVisuals[index] ?? reviewVisuals[0];
            const visualSrc = review.image || visual.src;

            return (
              <article key={`${review.name}-${review.source}-${index}`} className="surface-panel rounded-2xl p-4">
                <div className="relative mb-4 aspect-[16/10] overflow-hidden rounded-xl">
                  <Image
                    src={visualSrc}
                    alt={`${review.name} review`}
                    fill
                    priority={index < 3}
                    sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
                    className={`object-cover ${visual.objectPosition}`}
                  />
                </div>

                <div className="space-y-3">
                  <p className="text-sm leading-8 text-text-light/86">“{review.content}”</p>

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
