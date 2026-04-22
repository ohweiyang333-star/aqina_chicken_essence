'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import Link from 'next/link';
import { Camera, Sparkles } from 'lucide-react';
import { IMAGES } from '@/lib/image-utils';

const ugcCornerPhotos = [
  '/ugc/cozy-sofa.jpg',
  '/ugc/home-study.jpg',
  '/ugc/morning-kitchen.jpg',
  '/ugc/office-corner.jpg',
  '/ugc/student-exam.webp',
  '/ugc/yoga-studio.jpg',
  '/ugc/sg-middle-aged-chinese-man.webp',
  '/ugc/sg-middle-aged-malay-woman.webp',
  '/ugc/sg-teenage-chinese-student.webp',
  '/ugc/sg-young-chinese-woman-campus.webp',
  '/ugc/sg-young-indian-office-man.webp',
  '/ugc/sg-young-indian-home-woman.webp',
  '/ugc/sg-young-malay-man-park.webp',
  '/ugc/sg-young-fitness-woman.webp',
  '/ugc/sg-elderly-chinese-woman.webp',
  '/ugc/sg-older-malay-man.webp',
] as const;

export default function HeroFlashSection() {
  const t = useTranslations('Index');
  const loopPhotos = [...ugcCornerPhotos, ...ugcCornerPhotos];

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

      <div className="section-shell relative z-10 grid w-full gap-8 pb-14 pt-24 md:pb-20 lg:grid-cols-[1.03fr_0.97fr] lg:items-end">
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/14 px-4 py-2 text-[11px] font-bold uppercase tracking-[0.2em] text-secondary">
            <Sparkles size={13} />
            <span>{t('hero.badge')}</span>
          </div>

          <h1 className="font-heading text-[2.55rem] leading-[0.92] font-semibold text-text-light sm:text-6xl">
            {t('hero.title')}
            <span className="mt-2 block text-gradient-gold">{t('hero.highlight')}</span>
          </h1>

          <h2 className="max-w-2xl text-base leading-8 text-text-light/86 sm:text-xl sm:leading-9">{t('hero.subheading')}</h2>

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

        <div className="relative">
          <article className="surface-panel mx-auto w-full max-w-[30rem] rounded-[1.4rem] p-4 md:p-5">
            <div className="premium-outline relative aspect-[4/5] overflow-hidden rounded-[1.2rem] bg-[radial-gradient(circle_at_top,rgba(255,184,0,0.18),transparent_35%),linear-gradient(180deg,rgba(17,43,34,0.75),rgba(9,26,20,0.92))]">
              <Image
                src={IMAGES.products.box2}
                alt="Aqina Product"
                fill
                priority
                sizes="(max-width: 1024px) 90vw, 36vw"
                className="object-contain p-6 md:p-8"
              />
            </div>
          </article>

          <aside className="mt-4 hidden overflow-hidden rounded-2xl border border-primary/20 bg-background-dark/82 p-3 shadow-[0_20px_38px_rgba(0,0,0,0.42)] backdrop-blur-sm lg:block">
            <div className="mb-2 inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.14em] text-primary">
              <Camera size={12} />
              <span>UGC Trust Corner</span>
            </div>
            <div className="ugc-corner-shell">
              <div className="ugc-corner-track">
                {loopPhotos.map((src, index) => (
                  <div key={`${src}-${index}`} className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg border border-primary/22">
                    <Image
                      src={src}
                      alt={`UGC ${index + 1}`}
                      fill
                      sizes="48px"
                      className="object-cover"
                    />
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
