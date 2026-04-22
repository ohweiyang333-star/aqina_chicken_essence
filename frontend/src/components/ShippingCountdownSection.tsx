'use client';

import { useTranslations } from 'next-intl';
import { Truck } from 'lucide-react';
import useEvergreenCountdown from '@/hooks/useEvergreenCountdown';

const FORTY_EIGHT_HOURS_MS = 48 * 60 * 60 * 1000;

export default function ShippingCountdownSection() {
  const t = useTranslations('Index.marketing.shippingCountdown');
  const { formatted } = useEvergreenCountdown({
    storageKey: 'aqina_shipping_countdown_deadline_v1',
    durationMs: FORTY_EIGHT_HOURS_MS,
  });

  const [hours, minutes, seconds] = formatted.split(':');

  return (
    <section className="py-10" id="shipping-countdown">
      <div className="section-shell">
        <div className="surface-panel rounded-[1.5rem] border border-secondary/35 bg-[linear-gradient(120deg,rgba(255,184,0,0.09),rgba(9,26,20,0.94)_38%)] p-6 md:p-8">
          <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-secondary/35 bg-secondary/20 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.17em] text-secondary">
                <Truck size={13} />
                <span>{t('eyebrow')}</span>
              </div>
              <h2 className="mt-4 font-heading text-4xl font-semibold text-text-light md:text-5xl">{t('title')}</h2>
              <p className="mt-3 text-sm leading-7 text-text-light/82 md:text-base">{t('description')}</p>
            </div>

            <div className="grid grid-cols-3 gap-3" aria-live="polite" aria-atomic="true">
              {[hours, minutes, seconds].map((value, index) => (
                <div
                  key={`${value}-${index}`}
                  className="min-w-[5.8rem] rounded-xl border border-primary/26 bg-background-dark/70 px-3 py-3 text-center"
                >
                  <p className="font-mono text-3xl font-bold text-secondary md:text-4xl">{value}</p>
                  <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-text-light/70">
                    {index === 0 ? t('hours') : index === 1 ? t('minutes') : t('seconds')}
                  </p>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
