'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { HeartHandshake, Leaf, Sparkles, Soup } from 'lucide-react';

export default function StoryExperienceSection() {
  const t = useTranslations('Index.story');

  return (
    <section className="py-12 md:py-16" id="story-experience">
      <div className="section-shell space-y-4">
        <article className="surface-panel rounded-[1.35rem] p-6 md:p-8">
          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-primary">
                <Leaf size={14} />
                <span>{t('storyOne.eyebrow')}</span>
              </div>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
                {t('storyOne.title')}
              </h2>
              <p className="mt-3 premium-copy text-sm md:text-base">{t('storyOne.body')}</p>
            </div>
            <figure className="relative aspect-[16/10] overflow-hidden rounded-2xl border border-primary/18">
              <Image
                src="/story/pineapple-craft.webp"
                alt={t('storyOne.title')}
                fill
                sizes="(max-width: 1024px) 100vw, 40vw"
                className="object-cover"
              />
            </figure>
          </div>
        </article>

        <article className="surface-panel rounded-[1.35rem] p-6 md:p-8">
          <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
            <figure className="relative aspect-[4/5] overflow-hidden rounded-2xl border border-primary/18 lg:order-1">
              <Image
                src="/story/pure-essence-bowl.webp"
                alt={t('storyTwo.title')}
                fill
                sizes="(max-width: 1024px) 100vw, 36vw"
                className="object-cover"
              />
            </figure>
            <div className="lg:order-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-primary">
                <Soup size={14} />
                <span>{t('storyTwo.eyebrow')}</span>
              </div>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
                {t('storyTwo.title')}
              </h2>
              <p className="mt-3 premium-copy text-sm md:text-base">{t('storyTwo.body')}</p>
            </div>
          </div>
        </article>

        <article className="surface-panel rounded-[1.35rem] p-6 md:p-8">
          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-primary">
                <HeartHandshake size={14} />
                <span>{t('emotional.eyebrow')}</span>
              </div>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
                {t('emotional.title')}
              </h2>
              <p className="mt-3 premium-copy text-sm md:text-base">{t('emotional.body')}</p>
            </div>
            <figure className="relative aspect-[16/10] overflow-hidden rounded-2xl border border-primary/18">
              <Image
                src="/story/family-care.webp"
                alt={t('emotional.title')}
                fill
                sizes="(max-width: 1024px) 100vw, 40vw"
                className="object-cover"
              />
            </figure>
          </div>
        </article>

        <article className="surface-panel rounded-[1.35rem] border border-secondary/35 bg-[linear-gradient(120deg,rgba(255,184,0,0.1),rgba(9,26,20,0.94)_38%)] p-6 md:p-8">
          <div className="grid gap-6 lg:grid-cols-[1.06fr_0.94fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/20 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-secondary">
                <Sparkles size={14} />
                <span>{t('valueCta.eyebrow')}</span>
              </div>
              <h2 className="mt-4 font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
                {t('valueCta.title')}
              </h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-text-light/84 md:text-base">{t('valueCta.body')}</p>
              <Link
                id="story-value-cta"
                href="#products"
                className="gold-button mt-6 inline-flex min-h-12 items-center justify-center rounded-md px-6 text-sm font-bold tracking-[0.08em]"
              >
                {t('valueCta.button')}
              </Link>
            </div>
            <figure className="relative aspect-[3/2] overflow-hidden rounded-2xl border border-secondary/28">
              <Image
                src="/story/value-cta-product.webp"
                alt={t('valueCta.title')}
                fill
                sizes="(max-width: 1024px) 100vw, 40vw"
                className="object-cover"
              />
            </figure>
          </div>
        </article>
      </div>
    </section>
  );
}
