'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';

export default function HeroFlashSection() {
  const t = useTranslations('Index');

  return (
    <section className="relative isolate flex min-h-[82vh] items-end overflow-hidden pt-6" id="hero">
      <Image
        src={IMAGES.hero}
        alt={t('hero.imageAlt')}
        fill
        priority
        className="object-cover object-center opacity-45"
      />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(9,26,20,0.2)_0%,rgba(9,26,20,0.6)_42%,rgba(9,26,20,0.97)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,184,0,0.2),transparent_30%)]" />

      <div className="section-shell relative z-10 flex w-full flex-col gap-7 pb-14 pt-24 md:pb-20">
        <div className="max-w-2xl space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/14 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-secondary">
            <Sparkles size={13} />
            <span>{t('hero.badge')}</span>
          </div>

          <h1 className="font-heading text-[2.55rem] leading-[0.92] font-semibold text-text-light sm:text-6xl">
            {t('hero.title')}
            <span className="mt-2 block text-gradient-gold">{t('hero.highlight')}</span>
          </h1>

          <h2 className="max-w-2xl text-base leading-8 text-text-light/86 sm:text-xl sm:leading-9">{t('hero.subheading')}</h2>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Link
            id="hero-main-cta"
            href="#products"
            className="gold-button inline-flex min-h-14 items-center justify-center rounded-md px-7 text-sm font-bold tracking-[0.08em]"
          >
            {t('hero.cta')}
          </Link>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-light/72">{t('hero.note')}</p>
        </div>
      </div>
    </section>
  );
}
