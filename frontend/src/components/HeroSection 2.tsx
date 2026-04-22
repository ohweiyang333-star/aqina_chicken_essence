'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

interface HeroSectionProps {
  onScrollToProducts?: () => void;
}

export default function HeroSection({ onScrollToProducts }: HeroSectionProps) {
  const t = useTranslations('Index');

  return (
    <section className="relative w-full min-h-[90vh] flex items-center justify-center overflow-hidden bg-ivory pt-20">
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-white to-transparent"></div>
      <div className="max-w-7xl mx-auto px-6 sm:px-12 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center z-10">
        <div className="space-y-8 animate-in fade-in slide-in-from-left duration-1000">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold tracking-widest uppercase">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            <span>{t('hero.badge')}</span>
          </div>

          <h1 className="text-6xl md:text-8xl font-bold text-charcoal tracking-tighter leading-[0.9]">
            {t('hero.title').split(' ').map((word, i) => (
              <span key={i} className={i === 1 ? "text-secondary block" : ""}>{word} </span>
            ))}
          </h1>

          <p className="text-lg md:text-xl text-charcoal/60 max-w-lg font-inter leading-relaxed">
            {t('hero.description')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <Link
              href="#products"
              className="group px-8 py-5 rounded-2xl bg-charcoal text-ivory font-bold hover:bg-primary transition-all flex items-center justify-center space-x-3 shadow-xl shadow-charcoal/20"
            >
              <span>{t('hero.cta')}</span>
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="#story"
              className="px-8 py-5 rounded-2xl border-2 border-charcoal/10 text-charcoal font-bold hover:bg-ivory transition-all text-center"
            >
              {t('hero.secondaryCta')}
            </Link>
          </div>
        </div>

        <div className="relative aspect-square w-full scale-110 lg:scale-125 animate-in fade-in zoom-in duration-1000 delay-300">
          <div className="absolute inset-0 bg-secondary/5 blur-[120px] rounded-full"></div>
          <Image
            src="/images/aqina_hero_chicken_essence_premium.png"
            alt="Aqina Premium Chicken Essence"
            fill
            className="object-contain drop-shadow-[0_35px_35px_rgba(0,0,0,0.15)]"
            priority
          />
        </div>
      </div>
    </section>
  );
}
