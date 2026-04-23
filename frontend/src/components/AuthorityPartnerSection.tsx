'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BadgeCheck, ShieldCheck } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';

const retailers = [
  {
    id: 'jaya-grocer',
    name: 'Jaya Grocer',
    src: '/brands/jaya-grocer.png',
    width: 180,
    height: 59,
  },
  {
    id: 'aeon',
    name: 'AEON',
    src: '/brands/aeon.svg',
    width: 180,
    height: 60,
  },
  {
    id: 'lotuss',
    name: "Lotus's",
    src: '/brands/lotuss.svg',
    width: 220,
    height: 72,
  },
  {
    id: 'village-grocer',
    name: 'Village Grocer',
    src: '/brands/village-grocer.jpg',
    width: 300,
    height: 188,
  },
] as const;

const certifications = [
  {
    id: 'haccp-gmp-iso',
    src: IMAGES.trust.complianceBadge,
    altKey: 'compliance.haccpGmpIsoAlt',
    labelKey: 'compliance.haccpGmpIsoLabel',
  },
  {
    id: 'jakim-halal',
    src: IMAGES.trust.halalBadge,
    altKey: 'compliance.halalAlt',
    labelKey: 'compliance.halalLabel',
  },
  {
    id: 'veterinary',
    src: IMAGES.trust.veterinaryBadge,
    altKey: 'compliance.veterinaryAlt',
    labelKey: 'compliance.veterinaryLabel',
  },
] as const;

export default function AuthorityPartnerSection() {
  const t = useTranslations('Index.marketing.authority');

  return (
    <section className="py-10" id="authority-partners">
      <div className="section-shell space-y-6">
        <div className="surface-panel rounded-[1.6rem] p-6 md:p-8">
          <article
            id="authority-certification-group"
            className="mb-6 rounded-2xl border border-emerald-400/30 bg-gradient-to-r from-emerald-500/16 to-background-dark/38 p-4 md:p-5"
          >
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-200">
              {t('complianceTitle')}
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {certifications.map((certification) => (
                <div
                  key={certification.id}
                  className="rounded-xl border border-emerald-300/45 bg-white px-3 py-3 text-charcoal"
                >
                  <div className="relative h-16 w-full">
                    <Image
                      src={certification.src}
                      alt={t(certification.altKey)}
                      fill
                      sizes="(max-width: 768px) 30vw, 220px"
                      className="object-contain"
                    />
                  </div>
                  <p className="mt-2 text-center text-[10px] font-bold uppercase tracking-[0.12em] text-emerald-700 md:text-[11px]">
                    {t(certification.labelKey)}
                  </p>
                </div>
              ))}
            </div>
          </article>

          <div className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
            <article className="rounded-2xl border border-primary/20 bg-background-dark/55 p-5 md:p-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/50 bg-emerald-500/20 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-emerald-200">
                <BadgeCheck size={13} />
                <span>{t('partnerBadge')}</span>
              </div>

              <h2 className="mt-4 font-heading text-4xl font-semibold text-text-light md:text-5xl">
                {t('title')}
              </h2>
              <p className="mt-3 text-sm leading-7 text-text-light/80 md:text-base">{t('description')}</p>

              <div className="mt-6 rounded-xl border border-primary/18 bg-white px-5 py-5">
                <div className="relative h-16 w-full">
                  <Image
                    src="/brands/resorts-world-sentosa.png"
                    alt="Resorts World"
                    fill
                    className="object-contain object-left"
                    sizes="(max-width: 768px) 90vw, 460px"
                  />
                </div>
                <p className="mt-3 text-xs font-semibold uppercase tracking-[0.14em] text-charcoal/72">
                  {t('resortWorldName')}
                </p>
                <p className="mt-1 text-sm leading-6 text-charcoal/72">{t('resortWorldNote')}</p>
              </div>
            </article>

            <article className="rounded-2xl border border-primary/20 bg-background-dark/55 p-5 md:p-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/18 bg-background-dark/70 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-primary">
                <ShieldCheck size={13} />
                <span>{t('retailEyebrow')}</span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                {retailers.map((retailer) => (
                  <article
                    key={retailer.id}
                    className="rounded-xl border border-primary/16 bg-white px-3 py-3 text-charcoal"
                  >
                    <div className="relative mb-3 h-12 w-full">
                      <Image
                        src={retailer.src}
                        alt={retailer.name}
                        fill
                        sizes="(max-width: 768px) 44vw, 14vw"
                        className="object-contain px-1"
                      />
                    </div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-charcoal/72">{retailer.name}</p>
                  </article>
                ))}
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  );
}
