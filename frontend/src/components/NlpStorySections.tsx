'use client';

import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';
import {
  AlertTriangle,
  Coins,
  HeartHandshake,
  ShieldAlert,
  Sparkles,
  Soup,
} from 'lucide-react';

function parseStringArray(input: unknown): string[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input.filter((item): item is string => typeof item === 'string' && item.length > 0);
}

export function NlpMiddleStorySection() {
  const locale = useLocale();
  const t = useTranslations('Index');

  if (locale !== 'zh') {
    return null;
  }

  const beliefPoints = parseStringArray(t.raw('nlp.beliefBreak.points'));
  const futureScenes = parseStringArray(t.raw('nlp.futurePacing.scenes'));

  return (
    <section className="scroll-mt-24 py-14 md:py-20" id="nlp-story-core">
      <div className="section-shell space-y-6">
        <article className="surface-panel rounded-[1.6rem] p-6 md:p-8" id="nlp-belief-break">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            <ShieldAlert size={14} />
            <span>{t('nlp.beliefBreak.eyebrow')}</span>
          </div>
          <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
            {t('nlp.beliefBreak.title')}
          </h2>
          <p className="mt-3 premium-copy max-w-3xl text-sm md:text-base">{t('nlp.beliefBreak.description')}</p>

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {beliefPoints.map((point) => (
              <div
                key={point}
                className="rounded-[1rem] border border-primary/16 bg-background-dark/45 px-4 py-4 text-sm leading-7 text-text-light/84"
              >
                {point}
              </div>
            ))}
          </div>
        </article>

        <article className="surface-panel rounded-[1.6rem] p-6 md:p-8" id="nlp-metaphor">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            <Soup size={14} />
            <span>{t('nlp.metaphor.eyebrow')}</span>
          </div>
          <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
            {t('nlp.metaphor.title')}
          </h2>
          <p className="mt-3 premium-copy text-sm md:text-base">{t('nlp.metaphor.description')}</p>
          <div className="mt-5 rounded-[1rem] border border-primary/18 bg-background-dark/52 p-5">
            <p className="text-sm leading-8 text-text-light/86 md:text-base">{t('nlp.metaphor.visualLine')}</p>
          </div>
        </article>

        <article className="surface-panel rounded-[1.6rem] p-6 md:p-8" id="nlp-caregiver">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            <HeartHandshake size={14} />
            <span>{t('nlp.caregiver.eyebrow')}</span>
          </div>
          <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
            {t('nlp.caregiver.title')}
          </h2>
          <p className="mt-3 premium-copy text-sm md:text-base">{t('nlp.caregiver.description')}</p>
          <p className="mt-4 rounded-[1rem] border border-secondary/35 bg-secondary/10 px-4 py-4 text-sm leading-7 text-text-light/90 md:text-base">
            {t('nlp.caregiver.decisionLine')}
          </p>
        </article>

        <article className="surface-panel rounded-[1.6rem] p-6 md:p-8" id="nlp-future-pacing">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            <Sparkles size={14} />
            <span>{t('nlp.futurePacing.eyebrow')}</span>
          </div>
          <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
            {t('nlp.futurePacing.title')}
          </h2>
          <p className="mt-3 premium-copy text-sm md:text-base">{t('nlp.futurePacing.description')}</p>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            {futureScenes.map((scene) => (
              <div
                key={scene}
                className="rounded-[1rem] border border-primary/16 bg-background-dark/45 px-4 py-4 text-sm leading-7 text-text-light/84"
              >
                {scene}
              </div>
            ))}
          </div>

          <Link
            id="nlp-future-cta"
            href="#products"
            className="gold-button mt-6 inline-flex min-h-12 items-center justify-center rounded-md px-6 text-sm font-bold uppercase tracking-[0.16em]"
          >
            {t('nlp.futurePacing.cta')}
          </Link>
        </article>
      </div>
    </section>
  );
}

export function NlpPriceReframeSection() {
  const locale = useLocale();
  const t = useTranslations('Index');

  if (locale !== 'zh') {
    return null;
  }

  return (
    <section className="py-8" id="nlp-price-reframe">
      <div className="section-shell">
        <article className="surface-panel rounded-[1.6rem] border border-secondary/35 bg-[linear-gradient(120deg,rgba(255,184,0,0.09),rgba(9,26,20,0.94)_38%)] p-6 md:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/20 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.17em] text-secondary">
            <Coins size={13} />
            <span>{t('nlp.priceReframe.eyebrow')}</span>
          </div>

          <h2 className="mt-4 font-heading text-4xl font-semibold text-text-light md:text-5xl">
            {t('nlp.priceReframe.title')}
          </h2>
          <p className="mt-3 text-sm leading-7 text-text-light/84 md:text-base">{t('nlp.priceReframe.description')}</p>
          <p className="mt-4 rounded-[1rem] border border-primary/20 bg-background-dark/55 px-4 py-4 text-sm leading-7 text-text-light/88 md:text-base">
            {t('nlp.priceReframe.conclusion')}
          </p>

          <Link
            id="nlp-price-cta"
            href="#products"
            className="gold-button mt-6 inline-flex min-h-12 items-center justify-center rounded-md px-6 text-sm font-bold uppercase tracking-[0.16em]"
          >
            {t('nlp.priceReframe.cta')}
          </Link>
        </article>
      </div>
    </section>
  );
}

export function NlpTakeawaySection() {
  const locale = useLocale();
  const t = useTranslations('Index');

  if (locale !== 'zh') {
    return null;
  }

  const excludes = parseStringArray(t.raw('nlp.takeaway.excludes'));

  return (
    <section className="pb-8" id="nlp-takeaway">
      <div className="section-shell">
        <article className="surface-panel rounded-[1.6rem] p-6 md:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            <AlertTriangle size={14} />
            <span>{t('nlp.takeaway.eyebrow')}</span>
          </div>

          <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
            {t('nlp.takeaway.title')}
          </h2>
          <p className="mt-3 premium-copy text-sm md:text-base">{t('nlp.takeaway.description')}</p>

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {excludes.map((exclude) => (
              <div
                key={exclude}
                className="rounded-[1rem] border border-primary/16 bg-background-dark/45 px-4 py-4 text-sm leading-7 text-text-light/84"
              >
                {exclude}
              </div>
            ))}
          </div>

          <p className="mt-5 rounded-[1rem] border border-secondary/30 bg-secondary/10 px-4 py-4 text-sm leading-7 text-text-light/90 md:text-base">
            {t('nlp.takeaway.finalLine')}
          </p>

          <Link
            id="nlp-takeaway-cta"
            href="#products"
            className="gold-button mt-6 inline-flex min-h-12 items-center justify-center rounded-md px-6 text-sm font-bold uppercase tracking-[0.16em]"
          >
            {t('nlp.takeaway.cta')}
          </Link>
        </article>
      </div>
    </section>
  );
}
