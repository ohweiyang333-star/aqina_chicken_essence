'use client';

import { useTranslations } from 'next-intl';
import { ChartNoAxesCombined } from 'lucide-react';

interface StatItem {
  value: string;
  label: string;
}

function parseStats(input: unknown): StatItem[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input
    .map((item) => {
      if (typeof item !== 'object' || !item) {
        return null;
      }

      const value = 'value' in item && typeof item.value === 'string' ? item.value : '';
      const label = 'label' in item && typeof item.label === 'string' ? item.label : '';
      if (!value || !label) {
        return null;
      }

      return { value, label };
    })
    .filter((item): item is StatItem => item !== null);
}

export default function TrustStatsStrip() {
  const t = useTranslations('Index.marketing.stats');
  const stats = parseStats(t.raw('items'));

  return (
    <section className="py-8" id="trust-stats">
      <div className="section-shell">
        <div className="surface-panel rounded-[1.4rem] p-5 md:p-7">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background-dark/55 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-primary">
            <ChartNoAxesCombined size={14} />
            <span>{t('eyebrow')}</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((item) => (
              <article
                key={`${item.value}-${item.label}`}
                className="rounded-xl border border-primary/14 bg-background-dark/48 px-4 py-5"
              >
                <p className="font-heading text-4xl font-semibold text-primary">{item.value}</p>
                <p className="mt-1 text-sm font-medium text-text-light/84">{item.label}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
