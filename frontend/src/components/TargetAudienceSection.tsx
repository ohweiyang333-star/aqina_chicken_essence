'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { BriefcaseBusiness, Heart, HeartPulse, ShieldCheck } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';

const imageSets = {
  workplace: IMAGES.audience.workplace,
  maternity: IMAGES.audience.maternity,
  recovery: IMAGES.audience.recovery,
  halal: IMAGES.audience.halal,
} as const;

const items = [
  { id: 'workplace', icon: BriefcaseBusiness },
  { id: 'maternity', icon: Heart },
  { id: 'recovery', icon: HeartPulse },
  { id: 'halal', icon: ShieldCheck },
] as const;

export default function TargetAudienceSection() {
  const t = useTranslations('Index');

  return (
    <section className="scroll-mt-24 py-18 md:py-24" id="audience">
      <div className="section-shell space-y-6">
        <div className="space-y-3 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.32em] text-primary">
            {t('audience.subtitle')}
          </p>
          <h2 className="font-heading text-4xl font-semibold text-text-light md:text-5xl">
            {t('audience.title')}
          </h2>
        </div>

        <div className="space-y-6">
          {items.map((item, index) => {
            const images = imageSets[item.id];

            return (
              <article
                key={item.id}
                id={item.id}
                className="surface-panel scroll-mt-24 rounded-[1.7rem] p-5 md:p-7"
              >
                <div
                  className={[
                    'grid items-center gap-6 lg:grid-cols-[1.04fr_0.96fr]',
                    index % 2 === 1 ? 'lg:[&>*:first-child]:order-2 lg:[&>*:last-child]:order-1' : '',
                  ].join(' ')}
                >
                  <div className={['grid gap-3', images.length > 1 ? 'sm:grid-cols-[1.2fr_0.8fr]' : 'sm:grid-cols-1'].join(' ')}>
                    <div className="image-mask premium-outline relative min-h-[18rem] overflow-hidden rounded-[1.25rem]">
                      <Image
                        src={images[0]}
                        alt={t(`audience.items.${item.id}.title`)}
                        fill
                        className="object-cover"
                        sizes="(max-width: 1024px) 100vw, 50vw"
                      />
                    </div>
                    {images.length > 1 && (
                      <div className="grid gap-3">
                        {images.slice(1).map((src) => (
                          <div
                            key={src}
                            className="image-mask premium-outline relative min-h-[8.5rem] overflow-hidden rounded-[1rem]"
                          >
                            <Image
                              src={src}
                              alt={t(`audience.items.${item.id}.title`)}
                              fill
                              className="object-cover"
                              sizes="(max-width: 1024px) 50vw, 25vw"
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="space-y-5">
                    <div className="inline-flex items-center gap-2 rounded-full border border-primary/18 bg-background-dark/52 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.28em] text-primary">
                      <item.icon size={15} />
                      <span>{t(`audience.items.${item.id}.eyebrow`)}</span>
                    </div>

                    <div className="space-y-3">
                      <h3 className="font-heading text-4xl font-semibold leading-tight text-text-light">
                        {t(`audience.items.${item.id}.title`)}
                      </h3>
                      <p className="premium-copy text-sm md:text-base">
                        {t(`audience.items.${item.id}.description`)}
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-3">
                      {(['pointOne', 'pointTwo', 'pointThree'] as const).map((point) => (
                        <div
                          key={point}
                          className="rounded-[1rem] border border-primary/14 bg-background-dark/46 px-4 py-4 text-sm leading-6 text-text-light/82"
                        >
                          {t(`audience.items.${item.id}.${point}`)}
                        </div>
                      ))}
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
