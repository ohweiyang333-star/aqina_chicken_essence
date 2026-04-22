'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BadgeCheck, FlaskConical } from 'lucide-react';

const evidenceVisuals = {
  mygap: '/science/evidence-farm.webp',
  organic: '/science/evidence-lab.webp',
  halal: '/science/evidence-safety.webp',
  amino: '/science/evidence-research.webp',
} as const;

const evidenceIds = ['mygap', 'organic', 'halal', 'amino'] as const;

export default function ScienceEndorsementSection() {
  const t = useTranslations('Index.Science');

  const facts = [
    t('nutrition.facts.zeroFat'),
    t('nutrition.facts.zeroCholesterol'),
    t('nutrition.facts.noHormones'),
    t('nutrition.facts.highProtein'),
  ];

  return (
    <section className="scroll-mt-24 py-20 md:py-24" id="science">
      <div className="section-shell space-y-6">
        <article className="surface-panel rounded-[1.6rem] p-6 md:p-8">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.22em] text-primary">
            <FlaskConical size={14} />
            <span>{t('subtitle')}</span>
          </div>

          <div className="grid gap-6 lg:grid-cols-[1.02fr_0.98fr]">
            <div className="space-y-5">
              <h2 className="font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
                {t('title')}
              </h2>
              <p className="premium-copy max-w-xl text-sm md:text-base">
                {t('description')}
              </p>

              <div className="rounded-[1.2rem] border border-primary/16 bg-background-dark/45 p-5">
                <h3 className="font-heading text-3xl font-semibold text-primary">{t('nutrition.title')}</h3>
                <p className="mt-2 premium-copy text-sm md:text-base">{t('nutrition.description')}</p>
                <div className="mt-4 flex flex-wrap gap-2.5">
                  {facts.map((fact) => (
                    <span
                      key={fact}
                      className="rounded-full border border-primary/20 bg-surface px-3 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-text-light"
                    >
                      {fact}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {evidenceIds.map((id) => (
                <article key={id} className="surface-panel overflow-hidden rounded-[1.2rem] border border-primary/22">
                  <div className="relative aspect-[16/10]">
                    <Image
                      src={evidenceVisuals[id]}
                      alt={t(`certifications.${id}`)}
                      fill
                      sizes="(max-width: 768px) 100vw, 50vw"
                      className="object-cover"
                    />
                    <div className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-emerald-500/88 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white">
                      <BadgeCheck size={11} />
                      <span>{t('evidenceTag')}</span>
                    </div>
                  </div>

                  <div className="space-y-2 px-4 py-4">
                    <h3 className="font-heading text-2xl font-semibold text-text-light">
                      {t(`certifications.${id}`)}
                    </h3>
                    <p className="text-sm leading-7 text-muted">
                      {t(`certifications.${id}Desc`)}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}
