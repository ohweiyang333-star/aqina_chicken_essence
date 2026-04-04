'use client';

import { useTranslations } from 'next-intl';
import { Bolt, Heart } from 'lucide-react';
import Image from 'next/image';

export default function ProblemSolutionSection() {
  const t = useTranslations('ProblemSolution');

  const solutions = [
    {
      icon: Bolt,
      title: t('urban.title') || 'Urban Vitality',
      subtitle: t('urban.subtitle') || 'For the Busy Professional',
      problem: t('urban.problem') || 'Singapore urbanites often feel exhausted and stressed. Traditional chicken soup has a bitter, gamey taste that makes you "hold your nose" to drink.',
      solution: t('urban.solution') || 'Say goodbye to bitterness, awaken your vitality. Aqina uses MD2 pineapple enzyme circular ecosystem farming, double-boiled with steam extraction. No water added, zero moisture, no gamey taste. Every sip is fresh and rich like soup—ending the days of holding your nose to drink chicken essence.',
      image: '/images/urban-professional.jpg',
      imageAlt: 'Urban professional',
    },
    {
      icon: Heart,
      title: t('mother.title') || 'Mother\'s Care',
      subtitle: t('mother.subtitle') || 'For Expecting & New Mothers',
      problem: t('mother.problem') || 'Need scientific nourishment during pregnancy but worried about safety?',
      solution: t('mother.solution') || 'Specially formulated for pregnant and postpartum mothers. No hormones, rich in carnosine. The taste that even severe nausea can accept—Halal certified for peace of mind.',
      image: '/images/mother-care.jpg',
      imageAlt: 'Expecting mother with baby',
    },
  ];

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-ivory" id="solutions">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <span className="text-secondary font-bold tracking-widest text-sm uppercase">
            {t('subtitle') || 'The Problem & Our Solution'}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-charcoal">
            {t('title') || 'Say Goodbye to Bitter, Hello to Vitality'}
          </h2>
        </div>

        {/* Solution Blocks */}
        <div className="space-y-16">
          {solutions.map((solution, index) => (
            <div
              key={index}
              className={`flex flex-col ${index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'} gap-12 items-center`}
            >
              {/* Image Side */}
              <div className="relative w-full lg:w-1/2 aspect-[4/3] rounded-3xl overflow-hidden shadow-2xl border-4 border-primary/20">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-secondary/10"></div>
                <Image
                  src={solution.image}
                  alt={solution.imageAlt}
                  fill
                  className="object-cover"
                  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
                />
              </div>

              {/* Content Side */}
              <div className="w-full lg:w-1/2 space-y-6">
                {/* Icon & Title */}
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center text-white shadow-lg">
                    <solution.icon size={28} />
                  </div>
                  <div>
                    <h3 className="text-3xl font-bold text-charcoal">{solution.title}</h3>
                    <p className="text-secondary font-semibold">{solution.subtitle}</p>
                  </div>
                </div>

                {/* Problem */}
                <div className="p-6 bg-red-50 rounded-2xl border-l-4 border-red-300">
                  <p className="text-sm font-bold text-red-700 mb-2">{t('problem') || 'Problem'}</p>
                  <p className="text-charcoal/70">{solution.problem}</p>
                </div>

                {/* Solution */}
                <div className="p-6 bg-green-50 rounded-2xl border-l-4 border-green-300">
                  <p className="text-sm font-bold text-green-700 mb-2">{t('solution') || 'Solution'}</p>
                  <p className="text-charcoal/70 leading-relaxed">{solution.solution}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
