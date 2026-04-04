'use client';

import { useTranslations } from 'next-intl';
import Image from 'next/image';
import { CheckCircle2 } from 'lucide-react';

export default function StorySection() {
  const t = useTranslations('Index');

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-ivory" id="story">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">
        <div className="relative w-full lg:w-1/2 aspect-[4/3] rounded-3xl overflow-hidden shadow-2xl">
          <Image
            src="/images/heritage.png"
            alt="Traditional Brewing"
            fill
            className="object-cover"
          />
          <div className="absolute inset-0 bg-secondary/10 mix-blend-multiply"></div>
        </div>

        <div className="w-full lg:w-1/2 space-y-8">
          <div className="space-y-4 text-center lg:text-left">
            <span className="text-secondary font-bold tracking-widest text-sm uppercase">{t('story.subtitle')}</span>
            <h2 className="text-4xl md:text-5xl font-bold text-charcoal">{t('story.title')}</h2>
            <p className="text-charcoal/70 leading-relaxed font-inter">{t('story.description')}</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {(t.raw('story.points') as string[]).map((point, index) => (
              <div key={index} className="flex items-center space-x-3 p-4 bg-white/50 rounded-xl border border-charcoal/5">
                <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                  <CheckCircle2 size={16} />
                </div>
                <span className="font-semibold text-charcoal/80 text-sm">{point}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
