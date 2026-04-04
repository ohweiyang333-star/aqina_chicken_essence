'use client';

import { useTranslations } from 'next-intl';
import { Award, FlaskConical, Leaf, ShieldCheck } from 'lucide-react';

export default function ScienceEndorsementSection() {
  const t = useTranslations('Index.Science');

  const certifications = [
    {
      icon: ShieldCheck,
      title: t('certifications.mygap'),
      description: t('certifications.mygapDesc'),
    },
    {
      icon: Award,
      title: t('certifications.organic'),
      description: t('certifications.organicDesc'),
    },
    {
      icon: ShieldCheck,
      title: t('certifications.halal'),
      description: t('certifications.halalDesc'),
    },
    {
      icon: Leaf,
      title: t('certifications.amino'),
      description: t('certifications.aminoDesc'),
    },
  ];

  const facts = [
    t('nutrition.facts.zeroFat'),
    t('nutrition.facts.zeroCholesterol'),
    t('nutrition.facts.noHormones'),
    t('nutrition.facts.highProtein'),
  ];

  return (
    <section className="scroll-mt-24 py-20 md:py-24" id="science">
      <div className="section-shell">
        <div className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="surface-panel rounded-[1.6rem] p-6 md:p-8">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-primary/18 bg-background-dark/60 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.28em] text-primary">
              <FlaskConical size={14} />
              <span>{t('subtitle')}</span>
            </div>

            <div className="space-y-5">
              <h2 className="font-heading text-4xl font-semibold leading-tight text-text-light md:text-5xl">
                {t('title')}
              </h2>
              <p className="premium-copy max-w-xl text-sm md:text-base">
                {t('description')}
              </p>
            </div>

            <div className="my-8 gold-divider" />

            <div className="rounded-[1.3rem] border border-primary/16 bg-background-dark/46 p-5">
              <h3 className="mb-3 font-heading text-3xl font-semibold text-primary">
                {t('nutrition.title')}
              </h3>
              <p className="premium-copy text-sm md:text-base">
                {t('nutrition.description')}
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                {facts.map((fact) => (
                  <span
                    key={fact}
                    className="rounded-full border border-primary/20 bg-surface px-3 py-2 text-xs font-bold uppercase tracking-[0.22em] text-text-light"
                  >
                    {fact}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {certifications.map((cert) => (
              <div key={cert.title} className="surface-panel rounded-[1.4rem] p-5">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-primary/22 bg-background-dark/54 text-primary">
                  <cert.icon size={20} />
                </div>
                <h3 className="font-heading text-2xl font-semibold text-text-light">
                  {cert.title}
                </h3>
                <p className="mt-2 text-sm leading-7 text-muted">{cert.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
