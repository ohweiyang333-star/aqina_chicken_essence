'use client';

import { useTranslations } from 'next-intl';
import { ShieldCheck, Award, Leaf } from 'lucide-react';

export default function ScienceEndorsementSection() {
  const t = useTranslations('Science');

  const certifications = [
    {
      icon: ShieldCheck,
      title: t('certifications.mygap') || 'MyGAP Certified',
      description: t('certifications.mygapDesc') || 'Good Agricultural Practices',
    },
    {
      icon: Award,
      title: t('certifications.organic') || 'MY Organic',
      description: t('certifications.organicDesc') || 'Organic Certification',
    },
    {
      icon: ShieldCheck,
      title: t('certifications.halal') || 'Halal Certified',
      description: t('certifications.halalDesc') || 'Muslim-Friendly Production',
    },
    {
      icon: Leaf,
      title: t('certifications.amino') || 'High Amino Acid',
      description: t('certifications.aminoDesc') || 'Rich in BCAA & Carnosine',
    },
  ];

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-white" id="science">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <span className="text-secondary font-bold tracking-widest text-sm uppercase">
            {t('subtitle') || 'Science & Certifications'}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-charcoal">
            {t('title') || 'Backed by Science, Trusted by Experts'}
          </h2>
          <p className="text-charcoal/60 max-w-2xl mx-auto">
            {t('description') || 'Every drop is laboratory-tested and certified for your peace of mind.'}
          </p>
        </div>

        {/* Certifications Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {certifications.map((cert, index) => (
            <div
              key={index}
              className="group p-8 bg-ivory rounded-3xl border border-charcoal/5 hover:border-primary/30 hover:shadow-xl transition-all"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-all">
                  <cert.icon size={32} />
                </div>
                <div>
                  <h3 className="font-bold text-charcoal text-lg mb-2">{cert.title}</h3>
                  <p className="text-sm text-charcoal/60">{cert.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Nutrition Highlights */}
        <div className="mt-16 p-8 bg-gradient-to-r from-secondary/5 to-primary/5 rounded-3xl border border-charcoal/5">
          <div className="text-center space-y-4">
            <h3 className="text-2xl font-bold text-charcoal">
              {t('nutrition.title') || 'Nutritional Excellence'}
            </h3>
            <p className="text-charcoal/70 max-w-3xl mx-auto leading-relaxed">
              {t('nutrition.description') || 'Rich in branched-chain amino acids (BCAA), carnosine, and bromelain. 0% fat, 0% cholesterol, no growth hormones. The scientific choice for post-surgery recovery, maternal nourishment, and daily wellness.'}
            </p>
            <div className="flex flex-wrap justify-center gap-4 pt-4">
              <span className="px-4 py-2 bg-white rounded-full text-sm font-semibold text-charcoal shadow-sm">
                {t('nutrition.facts.zeroFat') || '0% Fat'}
              </span>
              <span className="px-4 py-2 bg-white rounded-full text-sm font-semibold text-charcoal shadow-sm">
                {t('nutrition.facts.zeroCholesterol') || '0% Cholesterol'}
              </span>
              <span className="px-4 py-2 bg-white rounded-full text-sm font-semibold text-charcoal shadow-sm">
                {t('nutrition.facts.noHormones') || 'No Hormones'}
              </span>
              <span className="px-4 py-2 bg-white rounded-full text-sm font-semibold text-charcoal shadow-sm">
                {t('nutrition.facts.highProtein') || 'High Protein'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
