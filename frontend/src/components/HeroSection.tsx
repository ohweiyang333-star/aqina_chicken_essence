'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import Image from 'next/image';
import { IMAGES } from '@/lib/image-utils';

export default function HeroSection() {
  const t = useTranslations('Index');

  return (
    <section className="relative isolate flex min-h-[85vh] items-end overflow-hidden pt-16">
      <Image
        src={IMAGES.hero}
        alt="Aqina premium heritage"
        fill
        priority
        className="object-cover object-center opacity-45"
      />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(9,26,20,0.2)_0%,rgba(9,26,20,0.58)_36%,rgba(9,26,20,0.95)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,184,0,0.14),transparent_28%)]" />

      <div className="section-shell relative z-10 flex w-full flex-col gap-8 pb-14 pt-24 sm:pb-18">
        <div className="max-w-xl space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/60 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.3em] text-primary">
            <span className="inline-flex h-2 w-2 rounded-full bg-secondary animate-pulse-gold" />
            <span>{t('hero.badge')}</span>
          </div>

          <h1 className="font-heading text-[2.6rem] leading-[0.92] font-semibold text-text-light sm:text-6xl">
            {t('hero.title')}
            <span className="mt-2 block text-gradient-gold">{t('hero.highlight')}</span>
          </h1>

          <p className="max-w-lg text-sm leading-7 text-text-light/82 sm:text-lg sm:leading-8">
            {t('hero.description')}
          </p>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Link
            href="#products"
            className="gold-button inline-flex min-h-12 items-center justify-center rounded-md px-8 text-sm font-bold uppercase tracking-[0.2em]"
          >
            {t('hero.cta')}
          </Link>
          <div className="flex flex-wrap gap-3 text-[11px] font-medium uppercase tracking-[0.18em] text-text-light/68">
            <span className="rounded-full border border-primary/16 bg-background-dark/45 px-3 py-2">
              {t('hero.noteOne')}
            </span>
            <span className="rounded-full border border-primary/16 bg-background-dark/45 px-3 py-2">
              {t('hero.noteTwo')}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
