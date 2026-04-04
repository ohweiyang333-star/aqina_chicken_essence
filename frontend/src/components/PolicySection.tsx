'use client';

import { useTranslations } from 'next-intl';

export default function PolicySection() {
  const t = useTranslations('Index');

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-white border-t border-charcoal/5">
      <div className="max-w-3xl mx-auto text-center space-y-8">
        <h2 className="text-3xl font-bold text-charcoal">{t('policy.title')}</h2>
        <div className="p-8 bg-ivory/30 rounded-3xl border border-charcoal/5 text-charcoal/60 leading-relaxed font-inter">
          {t('policy.content')}
        </div>
      </div>
    </section>
  );
}
