'use client';

import { useTranslations } from 'next-intl';

export default function MobileFloatingCTA() {
  const t = useTranslations('Index');

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[140] px-4 md:hidden">
      <div className="pointer-events-auto mx-auto max-w-md rounded-[1.1rem] border border-primary/25 bg-background-dark/92 p-2 shadow-[0_16px_40px_rgba(0,0,0,0.38)] backdrop-blur-md">
        <a
          href="#products"
          className="gold-button flex min-h-12 items-center justify-center rounded-[0.9rem] px-4 text-sm font-bold uppercase tracking-[0.2em]"
        >
          {t('mobileCta.label')}
        </a>
      </div>
    </div>
  );
}
