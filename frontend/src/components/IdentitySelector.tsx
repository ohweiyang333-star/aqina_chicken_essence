'use client';

import { useTranslations } from 'next-intl';
import { Baby, BriefcaseBusiness, HeartPulse, ShieldCheck } from 'lucide-react';

const items = [
  { id: 'workplace', icon: BriefcaseBusiness },
  { id: 'maternity', icon: Baby },
  { id: 'halal', icon: ShieldCheck },
  { id: 'recovery', icon: HeartPulse },
] as const;

export default function IdentitySelector() {
  const t = useTranslations('Index');

  return (
    <section className="border-y border-primary/10 bg-surface/80 py-5 backdrop-blur-md">
      <div className="section-shell">
        <div className="mb-3 text-center text-[11px] font-bold uppercase tracking-[0.34em] text-primary">
          {t('identity.title')}
        </div>

        <div className="hide-scrollbar flex gap-3 overflow-x-auto pb-1">
          {items.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="inline-flex shrink-0 items-center gap-2 rounded-full border border-primary/20 bg-background-dark/50 px-4 py-3 text-xs font-semibold text-text-light hover:border-primary/42 hover:text-primary"
            >
              <item.icon size={16} className="text-primary" />
              <span>{t(`identity.items.${item.id}`)}</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
