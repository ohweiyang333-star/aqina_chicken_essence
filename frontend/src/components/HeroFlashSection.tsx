'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import Link from 'next/link';
import { Zap } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';
import useEvergreenCountdown from '@/hooks/useEvergreenCountdown';

const EIGHT_HOURS_MS = 8 * 60 * 60 * 1000;

export default function HeroFlashSection() {
  const t = useTranslations('Index');
  const mt = useTranslations('Index.marketing.flashSale');
  const { formatted } = useEvergreenCountdown({
    storageKey: 'aqina_flash_sale_deadline_v1',
    durationMs: EIGHT_HOURS_MS,
  });

  const rawBadges = mt.raw('badges');
  const badges = Array.isArray(rawBadges)
    ? rawBadges.filter((badge): badge is string => typeof badge === 'string')
    : [];

  return (
    <section className="relative isolate flex min-h-[82vh] items-end overflow-hidden pt-6" id="hero">
      <Image
        src={IMAGES.hero}
        alt={mt('imageAlt')}
        fill
        priority
        className="object-cover object-center opacity-45"
      />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(9,26,20,0.2)_0%,rgba(9,26,20,0.6)_42%,rgba(9,26,20,0.97)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,184,0,0.2),transparent_30%)]" />

      <div className="section-shell relative z-10 flex w-full flex-col gap-7 pb-14 pt-24 md:pb-20">
        <div className="max-w-2xl space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/14 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-secondary">
            <Zap size={13} />
            <span>{mt('eyebrow')}</span>
          </div>

          <h1 className="font-heading text-[2.55rem] leading-[0.92] font-semibold text-text-light sm:text-6xl">
            {t('hero.title')}
            <span className="mt-2 block text-gradient-gold">{t('hero.highlight')}</span>
          </h1>

          <p className="max-w-xl text-sm leading-7 text-text-light/82 sm:text-lg sm:leading-8">
            {t('hero.description')}
          </p>

          <div className="flex flex-wrap gap-3">
            {badges.map((badge) => (
              <span
                key={badge}
                className="rounded-full border border-primary/16 bg-background-dark/55 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-text-light/80"
              >
                {badge}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Link
            id="hero-flash-sale-btn"
            href="#products"
            className="gold-button inline-flex min-h-14 items-center justify-center gap-3 rounded-md px-7 text-sm font-bold uppercase tracking-[0.14em]"
          >
            <span>{mt('buttonLabel')}</span>
            <span className="rounded-full bg-background-dark/20 px-3 py-1 font-mono text-xs tracking-[0.12em] text-background-dark">
              {formatted}
            </span>
          </Link>
          <Link
            id="hero-main-cta"
            href="#products"
            className="inline-flex min-h-12 items-center justify-center rounded-md border border-primary/28 bg-background-dark/55 px-6 text-xs font-semibold uppercase tracking-[0.2em] text-text-light hover:border-primary/42 hover:text-primary"
          >
            {t('hero.cta')}
          </Link>
        </div>
      </div>
    </section>
  );
}
