'use client';

import { useLocale, useTranslations } from 'next-intl';
import Image from 'next/image';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';

export default function HeroFlashSection() {
  const locale = useLocale();
  const t = useTranslations('Index');
  const isZh = locale === 'zh';

  return (
    <section className="relative isolate flex min-h-[80vh] items-end overflow-hidden pt-6 lg:min-h-[84vh]" id="hero">
      <Image
        src={IMAGES.hero}
        alt={t('hero.imageAlt')}
        fill
        priority
        className="object-cover object-[74%_center] opacity-80"
      />
      <div className="absolute inset-0 bg-[linear-gradient(100deg,rgba(9,26,20,0.92)_0%,rgba(9,26,20,0.88)_34%,rgba(9,26,20,0.44)_66%,rgba(9,26,20,0.16)_100%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(9,26,20,0.04)_0%,rgba(9,26,20,0.2)_54%,rgba(9,26,20,0.76)_100%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_82%_42%,rgba(255,184,0,0.22),transparent_34%)]" />

      <div className="section-shell relative z-10 w-full pb-14 pt-24 md:pb-20">
        <div className="min-w-0 max-w-[44rem] space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/14 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-secondary">
            <Sparkles size={13} />
            <span>{t('hero.badge')}</span>
          </div>

          <h1
            className={[
              'max-w-[16ch] text-[clamp(2.2rem,5vw,4.45rem)] leading-[1.03] text-text-light',
              isZh ? 'font-body font-semibold tracking-[0.02em]' : 'font-heading font-semibold',
            ].join(' ')}
          >
            {t('hero.title')}
            <span className="mt-2 block text-gradient-gold">{t('hero.highlight')}</span>
          </h1>

          <h2 className="max-w-[36rem] text-base leading-8 text-text-light/86 sm:text-lg sm:leading-8 xl:text-xl xl:leading-9">
            {t('hero.subheading')}
          </h2>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <Link
              id="hero-main-cta"
              href="#products"
              className="gold-button inline-flex min-h-14 items-center justify-center rounded-md px-7 text-sm font-bold tracking-[0.08em]"
            >
              {t('hero.cta')}
            </Link>
            <p className="text-xs font-semibold tracking-[0.08em] text-text-light/72">{t('hero.note')}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
