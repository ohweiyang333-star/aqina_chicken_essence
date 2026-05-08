'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { trackLandingFunnelEvent } from '@/lib/marketing-analytics';

export default function MobileFloatingCTA() {
  const t = useTranslations('Index');
  const pathname = usePathname();
  const isV2Landing = pathname?.startsWith('/v2/');
  const [isV2HeroVisible, setIsV2HeroVisible] = useState(true);

  useEffect(() => {
    if (!isV2Landing) {
      return;
    }

    const hero = document.getElementById('v2-hero');
    if (!hero) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsV2HeroVisible(Boolean(entry?.isIntersecting));
      },
      { threshold: 0.08 },
    );

    observer.observe(hero);

    return () => observer.disconnect();
  }, [isV2Landing]);

  if (isV2Landing && isV2HeroVisible) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[140] px-4 md:hidden">
      <div className="pointer-events-auto mx-auto max-w-md rounded-[1.1rem] border border-primary/25 bg-background-dark/92 p-2 shadow-[0_16px_40px_rgba(0,0,0,0.38)] backdrop-blur-md">
        <a
          id="mobile-floating-products-cta"
          href="#products"
          onClick={() => {
            trackLandingFunnelEvent('hero_cta_click', {
              source: 'mobile_floating_products',
              destination: 'products',
            });
          }}
          className="gold-button flex min-h-12 items-center justify-center rounded-[0.9rem] px-4 text-sm font-bold uppercase tracking-[0.2em]"
        >
          {t('mobileCta.label')}
        </a>
      </div>
    </div>
  );
}
